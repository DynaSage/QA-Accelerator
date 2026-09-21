import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.agents.kpi_sql_agent import normalize_kpi_sql_queries
from src.agents.kpi_validation_runner import run_kpi_and_functional_validation
from src.agents.mapping_agent import build_etl_spec
from src.agents.reporting_agent import format_qa_report
from src.agents.requirement_agent import analyze_requirements
from src.agents.test_case_agent import generate_test_cases
from src.graph.nodes import execute_on_adb, safety_check
from src.parsers.kpi_logic_parser import parse_kpi_logic_document
from src.exporters.bundle_exporter import export_qa_pack_zip
from src.exporters.excel_exporter import export_test_cases_to_excel
from src.graph import build_qa_sql_agent
from src.inputs.json_loader import load_etl_spec_from_json
from src.metadata.store import MetadataStore
from src.models.etl_spec import ETLSpecModel
from src.parsers.document_parser import read_requirement_document
from src.parsers.mapping_file import parse_mapping_file
from src.integrations.ado_importer import AdoImporter
from src.review.review_store import ReviewStore
from src.utils.output_paths import safe_write_text
from src.utils.run_logger import RunLogger
from src.utils.workflow_mode import detect_workflow_mode


def _resolve_project_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return Path.cwd() / path


def _mapping_source_files(
    mapping_path: Path,
    mapping_payload: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, str]:
    files: dict[str, str] = {
        "mapping_path": str(mapping_payload.get("normalized_excel_path") or mapping_path),
        "mapping_source_path": str(mapping_path),
        "document_kind": str(mapping_payload.get("document_kind") or ""),
        "stm_entity_count": str(len(mapping_payload.get("stm_entities") or [])),
    }
    if extra:
        files.update({key: str(value) for key, value in extra.items() if value is not None})
    return files


class QAWorkflowService:
    def __init__(
        self,
        metadata_store: MetadataStore | None = None,
        review_store: ReviewStore | None = None,
        run_logger: RunLogger | None = None,
    ) -> None:
        self.metadata_store = metadata_store or MetadataStore()
        self.review_store = review_store or ReviewStore()
        self.run_logger = run_logger or RunLogger()

    def process_kpi_logic_document(
        self,
        path: Path,
        *,
        requirement_context: str = "",
    ) -> dict[str, Any]:
        entries = parse_kpi_logic_document(path)
        normalized = normalize_kpi_sql_queries(entries, requirement_context=requirement_context)
        output_dir = Path("uploads") / "kpi_logic"
        output_dir.mkdir(parents=True, exist_ok=True)

        raw_path = output_dir / f"{path.stem}_raw.json"
        norm_path = output_dir / f"{path.stem}_normalized.json"
        raw_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        norm_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")

        normalized["source_path"] = str(path)
        normalized["raw_json_path"] = str(raw_path)
        normalized["normalized_json_path"] = str(norm_path)
        return normalized

    def attach_kpi_logic_to_draft(self, draft_id: str, normalized: dict[str, Any]) -> dict[str, Any]:
        draft = self.review_store.get_draft(draft_id)
        if not draft:
            raise FileNotFoundError(f"Draft not found: {draft_id}")

        source_files = dict(draft.get("source_files") or {})
        source_files["kpi_logic_path"] = normalized.get("source_path", "")
        source_files["kpi_logic_normalized_path"] = normalized.get("normalized_json_path", "")
        if source_files.get("workflow_mode") == "functional":
            source_files["workflow_mode"] = "hybrid"

        return self.review_store.update_draft(draft_id, {"source_files": source_files})

    @staticmethod
    def kpi_source_files(normalized: dict[str, Any] | None) -> dict[str, str]:
        if not normalized:
            return {}
        return {
            "kpi_logic_path": normalized.get("source_path", ""),
            "kpi_logic_normalized_path": normalized.get("normalized_json_path", ""),
        }

    def import_from_azure_devops(
        self,
        *,
        organization: str | None = None,
        project: str | None = None,
        work_item_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        from src.config import get_azure_devops_settings
        from src.integrations.azure_devops_client import AzureDevOpsClient

        settings = get_azure_devops_settings(
            organization=organization,
            project=project,
            work_item_ids=work_item_ids,
        )
        return AdoImporter(AzureDevOpsClient(settings)).import_user_stories()

    def build_draft_from_ado(
        self,
        *,
        import_id: str | None = None,
        mapping_path: Path | None = None,
        spec_name: str | None = None,
        workflow_mode: str | None = None,
        ui_context: str = "",
    ) -> dict[str, Any]:
        metadata = (
            AdoImporter.load_import(import_id)
            if import_id
            else AdoImporter.load_latest_import()
        )
        if not metadata:
            raise FileNotFoundError(
                "No Azure DevOps import found. Import user stories first, or build from a mapping document instead."
            )

        requirement_path = Path(metadata["requirements_path"])
        requirement_text = read_requirement_document(requirement_path)
        user_stories: list[dict[str, Any]] = []
        stories_json_path = metadata.get("stories_json_path")
        if stories_json_path and Path(stories_json_path).exists():
            user_stories = json.loads(Path(stories_json_path).read_text(encoding="utf-8"))

        requirement_analysis = analyze_requirements(requirement_text)
        resolved_mapping = mapping_path
        if resolved_mapping is None and metadata.get("mapping_path"):
            candidate = Path(metadata["mapping_path"])
            if candidate.exists():
                resolved_mapping = candidate

        mode = workflow_mode or detect_workflow_mode(
            requirement_text=requirement_text,
            requirement_summary=requirement_analysis,
            user_stories=user_stories,
            has_mapping=resolved_mapping is not None,
        )
        draft_name = spec_name or f"ado_{metadata['import_id']}"

        if mode == "functional":
            return self.build_functional_draft(
                requirement_text=requirement_text,
                requirement_analysis=requirement_analysis,
                user_stories=user_stories,
                spec_name=draft_name,
                source_files={
                    "ado_import_id": metadata["import_id"],
                    "requirements_path": metadata["requirements_path"],
                    "stories_json_path": metadata.get("stories_json_path", ""),
                    "story_count": str(metadata.get("story_count", 0)),
                    "spec_name": draft_name,
                    "workflow_mode": "functional",
                    "ui_context": ui_context,
                },
            )

        if resolved_mapping is None:
            fallback = Path("samples/mappings/sample_mapping.xlsx")
            if fallback.exists():
                resolved_mapping = fallback
            else:
                raise FileNotFoundError(
                    "No mapping file found in the ADO import. Attach a mapping .xlsx, .csv, or .docx to a user story "
                    "or provide a mapping file, or use functional workflow mode."
                )

        from src.parsers.mapping_file import parse_mapping_file as parse_uploaded_mapping

        mapping_payload = parse_uploaded_mapping(resolved_mapping)
        built = build_etl_spec(requirement_analysis, mapping_payload)

        draft = self.review_store.create_draft(
            etl_spec_draft=built["etl_spec"],
            requirement_summary={
                **requirement_analysis,
                "ado_import_id": metadata["import_id"],
                "ado_story_count": metadata.get("story_count", 0),
            },
            mapping_rows=built.get("mapping_rows") or mapping_payload["mapping_rows"],
            mapping_analysis=built.get("mapping_analysis") or {},
            canonical_mappings=built.get("canonical_mappings") or [],
            entity_logic=mapping_payload.get("entity_logic") or [],
            stm_entities=mapping_payload.get("stm_entities") or [],
            llm_mapping_output=built.get("llm_mapping_output") or {},
            source_files=_mapping_source_files(
                resolved_mapping,
                mapping_payload,
                extra={
                    "ado_import_id": metadata["import_id"],
                    "requirements_path": metadata["requirements_path"],
                    "stories_json_path": metadata.get("stories_json_path", ""),
                    "story_count": str(metadata.get("story_count", 0)),
                    "spec_name": draft_name,
                    "workflow_mode": mode,
                    "ui_context": ui_context,
                },
            ),
            missing_information=built["missing_information"],
            assumptions=built["assumptions"],
        )
        draft["spec_name"] = draft_name
        draft["workflow_mode"] = mode
        draft["ado_import"] = metadata
        return draft

    def build_functional_draft(
        self,
        *,
        requirement_text: str,
        requirement_analysis: dict[str, Any] | None = None,
        user_stories: list[dict[str, Any]] | None = None,
        spec_name: str | None = None,
        source_files: dict[str, str] | None = None,
        ui_context: str = "",
    ) -> dict[str, Any]:
        analysis = requirement_analysis or analyze_requirements(requirement_text)
        draft_name = spec_name or "functional_qa"
        files = {
            "spec_name": draft_name,
            "workflow_mode": "functional",
            "ui_context": ui_context,
            **(source_files or {}),
        }
        if requirement_text and "requirements_path" not in files:
            req_path = Path("uploads") / f"{draft_name}_requirements.txt"
            req_path.parent.mkdir(parents=True, exist_ok=True)
            req_path.write_text(requirement_text, encoding="utf-8")
            files["requirements_path"] = str(req_path)

        existing_stories_path = files.get("stories_json_path")
        if user_stories and not (existing_stories_path and _resolve_project_path(existing_stories_path).exists()):
            stories_path = Path("uploads") / f"{draft_name}_user_stories.json"
            stories_path.parent.mkdir(parents=True, exist_ok=True)
            stories_path.write_text(json.dumps(user_stories, indent=2), encoding="utf-8")
            files["stories_json_path"] = str(stories_path)

        draft = self.review_store.create_draft(
            etl_spec_draft={},
            requirement_summary=analysis,
            mapping_rows=[],
            source_files=files,
            missing_information=analysis.get("missing_information") or [],
            assumptions=analysis.get("assumptions") or [],
        )

        draft["spec_name"] = draft_name
        draft["workflow_mode"] = "functional"
        draft["user_stories"] = user_stories or []
        return draft

    def build_draft_from_manual_story(
        self,
        *,
        title: str,
        description: str,
        acceptance_criteria: str,
        business_rules: list[str] | None = None,
        spec_name: str | None = None,
        ui_context: str = "",
    ) -> dict[str, Any]:
        requirement_text = "\n".join(
            [
                f"## User Story: {title}",
                "",
                "### Description",
                description,
                "",
                "### Acceptance Criteria",
                acceptance_criteria or "No acceptance criteria provided.",
            ]
        )
        user_stories = [
            {
                "id": "MANUAL",
                "title": title,
                "description": description,
                "acceptance_criteria": acceptance_criteria,
                "work_item_type": "User Story",
            }
        ]
        analysis = analyze_requirements(requirement_text)
        if business_rules:
            analysis["business_rules"] = list(analysis.get("business_rules") or []) + business_rules

        return self.build_functional_draft(
            requirement_text=requirement_text,
            requirement_analysis=analysis,
            user_stories=user_stories,
            spec_name=spec_name or title.replace(" ", "_")[:40],
            ui_context=ui_context,
        )

    def build_draft_from_files(
        self,
        *,
        mapping_path: Path,
        requirement_path: Path | None = None,
        spec_name: str | None = None,
        ui_context: str = "",
    ) -> dict[str, Any]:
        requirement_text = ""
        if requirement_path and requirement_path.exists():
            requirement_text = read_requirement_document(requirement_path)

        requirement_analysis = analyze_requirements(requirement_text)
        from src.parsers.mapping_file import parse_mapping_file as parse_uploaded_mapping

        mapping_payload = parse_uploaded_mapping(mapping_path)
        built = build_etl_spec(requirement_analysis, mapping_payload)

        draft_name = spec_name or self._default_spec_name(built["etl_spec"])
        draft = self.review_store.create_draft(
            etl_spec_draft=built["etl_spec"],
            requirement_summary=requirement_analysis,
            mapping_rows=built.get("mapping_rows") or mapping_payload["mapping_rows"],
            mapping_analysis=built.get("mapping_analysis") or {},
            canonical_mappings=built.get("canonical_mappings") or [],
            entity_logic=mapping_payload.get("entity_logic") or [],
            stm_entities=mapping_payload.get("stm_entities") or [],
            llm_mapping_output=built.get("llm_mapping_output") or {},
            source_files=_mapping_source_files(
                mapping_path,
                mapping_payload,
                extra={
                    "requirement_path": str(requirement_path) if requirement_path else "",
                    "spec_name": draft_name,
                    "workflow_mode": "etl",
                    "ui_context": ui_context,
                },
            ),
            missing_information=built["missing_information"],
            assumptions=built["assumptions"],
        )
        draft["spec_name"] = draft_name
        draft["workflow_mode"] = "etl"
        return draft

    def build_draft_from_json(self, spec_path: Path, *, spec_name: str | None = None) -> dict[str, Any]:
        spec_model = load_etl_spec_from_json(spec_path)
        draft_name = spec_name or self._default_spec_name(spec_model.to_agent_dict())
        draft = self.review_store.create_draft(
            etl_spec_draft=spec_model.to_agent_dict(),
            requirement_summary={"requirement_summary": "Imported directly from JSON ETL spec."},
            mapping_rows=[],
            source_files={"json_spec_path": str(spec_path), "spec_name": draft_name},
        )
        draft["spec_name"] = draft_name
        return draft

    def update_draft(self, draft_id: str, etl_spec: dict[str, Any]) -> dict[str, Any]:
        if not self._is_complete_etl_spec(etl_spec):
            return self.review_store.update_draft(draft_id, {"etl_spec_draft": etl_spec or {}})
        validated = ETLSpecModel.model_validate(etl_spec)
        return self.review_store.update_draft_spec(draft_id, validated.to_agent_dict())

    def approve_draft(self, draft_id: str) -> dict[str, Any]:
        draft = self.review_store.get_draft(draft_id)
        if not draft:
            raise FileNotFoundError(f"Draft not found: {draft_id}")

        workflow_mode = draft.get("source_files", {}).get("workflow_mode", "etl")
        spec = draft.get("etl_spec_draft") or {}
        if workflow_mode == "functional" or not self._is_complete_etl_spec(spec):
            approved = self.review_store.approve_draft(draft_id)
            approved["saved_spec"] = None
            if not self._is_complete_etl_spec(spec) and workflow_mode == "etl":
                approved["workflow_mode"] = "functional"
            else:
                approved["workflow_mode"] = workflow_mode
            return approved

        validated = ETLSpecModel.model_validate(spec)
        spec_name = draft.get("source_files", {}).get("spec_name") or self._default_spec_name(validated.to_agent_dict())
        saved = self.metadata_store.save_spec(validated, name=spec_name)
        approved = self.review_store.approve_draft(draft_id)
        approved["saved_spec"] = saved
        approved["workflow_mode"] = workflow_mode
        return approved

    def run_validation(
        self,
        *,
        etl_spec: dict[str, Any],
        spec_id: str | None = None,
        spec_name: str = "",
        spec_version: str = "",
        execute_queries: bool = False,
        report_path: Path | None = None,
        test_cases_path: Path | None = None,
        requirement_text: str = "",
        requirement_summary: dict[str, Any] | None = None,
        user_stories: list[dict[str, Any]] | None = None,
        ui_context: str = "",
        kpi_normalization: dict[str, Any] | None = None,
        mapping_analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        run_id = str(uuid4())
        agent = build_qa_sql_agent()
        invoke_state: dict[str, Any] = {
            "etl_spec": etl_spec,
            "spec_id": spec_id or "",
            "spec_name": spec_name,
            "spec_version": spec_version,
            "run_id": run_id,
            "execute_queries": execute_queries,
            "requirement_text": requirement_text,
            "requirement_summary": requirement_summary or {},
            "user_stories": user_stories or [],
            "ui_context": ui_context,
            "kpi_normalization": kpi_normalization or {},
            "mapping_analysis": mapping_analysis or {},
        }
        result = agent.invoke(invoke_state)
        result["mapping_analysis"] = mapping_analysis or result.get("mapping_analysis") or {}

        kpi_normalization = kpi_normalization or invoke_state.get("kpi_normalization")
        if kpi_normalization and kpi_normalization.get("tests"):
            from src.models.test_case import StructuredTestCase

            merged_tests = list(kpi_normalization["tests"]) + list(result.get("tests") or [])
            result["tests"] = merged_tests
            result["kpi_normalization"] = kpi_normalization
            checked = safety_check({**result, "tests": merged_tests})
            result["tests"] = checked.get("tests") or []
            result["rejected_queries"] = list(result.get("rejected_queries") or []) + list(
                checked.get("rejected_queries") or []
            )

            existing_ids = {case["test_id"] for case in (result.get("test_cases") or [])}
            for test in kpi_normalization["tests"]:
                if test["test_id"] in existing_ids:
                    continue
                case = StructuredTestCase.from_validation_test(
                    test,
                    source_table=(etl_spec or {}).get("source_table", ""),
                    target_table=(etl_spec or {}).get("target_table", ""),
                    spec_version=spec_version,
                ).model_dump()
                case["requirement_id"] = test.get("kpi_id") or case.get("requirement_id", "")
                case["module"] = test.get("module") or case.get("module", "")
                case["feature"] = test.get("kpi_name") or case.get("feature", "")
                case["test_type"] = "KPI Data Validation"
                result.setdefault("test_cases", []).append(case)

            if execute_queries:
                result.update(execute_on_adb(result))
            result.update(format_qa_report(result))

        report_file = report_path or Path("output") / "qa_validation_pack.md"
        report_file = safe_write_text(report_file, result.get("qa_report") or "No report generated.")

        test_cases = result.get("test_cases") or []
        artifacts = dict(result.get("test_case_artifacts") or {})
        if mapping_analysis or result.get("mapping_analysis"):
            artifacts["mapping_analysis"] = mapping_analysis or result.get("mapping_analysis")
            result["test_case_artifacts"] = artifacts
        excel_file = None
        if test_cases or artifacts.get("mapping_analysis"):
            excel_file = test_cases_path or Path("output") / "qa_test_cases.xlsx"
            export_test_cases_to_excel(
                test_cases,
                excel_file,
                artifacts=artifacts,
            )

        summary = result.get("execution_summary") or {}
        self.run_logger.save(
            run_id=run_id,
            spec_id=spec_id,
            spec_name=spec_name,
            result=result,
            report_path=str(report_file),
            test_cases_path=str(excel_file) if excel_file else None,
        )
        if spec_id:
            self.metadata_store.record_run(
                run_id=run_id,
                spec_id=spec_id,
                summary={"test_count": len(result.get("tests") or []), "execution_summary": summary},
                report_path=str(report_file),
            )

        result["run_id"] = run_id
        result["report_path"] = str(report_file)
        result["test_cases_path"] = str(excel_file) if excel_file else None
        result["spec_name"] = spec_name
        return result

    def run_functional_validation(
        self,
        *,
        spec_name: str = "functional_qa",
        execute_queries: bool = False,
        report_path: Path | None = None,
        test_cases_path: Path | None = None,
        requirement_text: str = "",
        requirement_summary: dict[str, Any] | None = None,
        user_stories: list[dict[str, Any]] | None = None,
        ui_context: str = "",
        etl_spec: dict[str, Any] | None = None,
        kpi_normalization: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        run_id = str(uuid4())
        state: dict[str, Any] = {
            "etl_spec": etl_spec or {},
            "spec_name": spec_name,
            "run_id": run_id,
            "execute_queries": execute_queries,
            "requirement_text": requirement_text,
            "requirement_summary": requirement_summary or {},
            "user_stories": user_stories or [],
            "ui_context": ui_context,
            "tests": list((kpi_normalization or {}).get("tests") or []),
            "kpi_normalization": kpi_normalization or {},
            "kpi_logic_entries": (kpi_normalization or {}).get("queries") or [],
            "rejected_queries": list((kpi_normalization or {}).get("rejected_queries") or []),
        }
        state.update(run_kpi_and_functional_validation(state))

        report_file = report_path or Path("output") / "qa_validation_pack.md"
        report_file = safe_write_text(report_file, state.get("qa_report") or "No report generated.")

        test_cases = state.get("test_cases") or []
        excel_file = None
        if test_cases:
            excel_file = test_cases_path or Path("output") / "qa_test_cases.xlsx"
            export_test_cases_to_excel(test_cases, excel_file, artifacts=state.get("test_case_artifacts"))

        self.run_logger.save(
            run_id=run_id,
            spec_id=None,
            spec_name=spec_name,
            result=state,
            report_path=str(report_file),
            test_cases_path=str(excel_file) if excel_file else None,
        )

        state["run_id"] = run_id
        state["report_path"] = str(report_file)
        state["test_cases_path"] = str(excel_file) if excel_file else None
        state["workflow_mode"] = "hybrid" if kpi_normalization else "functional"
        return state

    def build_qa_pack_zip(self, result: dict[str, Any], *, extra_files: dict[str, str | bytes] | None = None) -> bytes:
        run_id = result.get("run_id") or "unknown"
        return export_qa_pack_zip(
            run_id=run_id,
            result=result,
            report_path=Path(result["report_path"]) if result.get("report_path") else None,
            test_cases_path=Path(result["test_cases_path"]) if result.get("test_cases_path") else None,
            extra_files=extra_files,
        )

    def _load_user_stories(self, source_files: dict[str, Any]) -> list[dict[str, Any]]:
        candidates: list[str] = []
        if source_files.get("stories_json_path"):
            candidates.append(source_files["stories_json_path"])
        ado_import_id = source_files.get("ado_import_id")
        if ado_import_id:
            candidates.append(str(Path("imports") / "ado" / ado_import_id / "user_stories.json"))

        seen: set[str] = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            path = _resolve_project_path(candidate)
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        return []

    def _load_kpi_normalization(self, source_files: dict[str, Any]) -> dict[str, Any] | None:
        norm_path = source_files.get("kpi_logic_normalized_path")
        if not norm_path:
            return None
        path = _resolve_project_path(norm_path)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _draft_context(self, draft: dict[str, Any]) -> dict[str, Any]:
        requirement_text = ""
        source_files = draft.get("source_files") or {}
        requirements_path = source_files.get("requirements_path")
        if requirements_path:
            req_path = _resolve_project_path(requirements_path)
            if req_path.exists():
                requirement_text = req_path.read_text(encoding="utf-8")

        user_stories = self._load_user_stories(source_files)
        kpi_normalization = self._load_kpi_normalization(source_files)
        workflow_mode = source_files.get("workflow_mode", "etl")
        if kpi_normalization and workflow_mode == "functional":
            workflow_mode = "hybrid"

        return {
            "requirement_text": requirement_text,
            "requirement_summary": draft.get("requirement_summary") or {},
            "user_stories": user_stories,
            "ui_context": source_files.get("ui_context", ""),
            "spec_name": source_files.get("spec_name") or draft.get("spec_name") or "qa_pack",
            "workflow_mode": workflow_mode,
            "kpi_normalization": kpi_normalization,
            "kpi_logic_path": source_files.get("kpi_logic_path", ""),
            "mapping_analysis": draft.get("mapping_analysis") or {},
        }

    def approve_and_validate(
        self,
        draft_id: str,
        *,
        execute_queries: bool = False,
        report_path: Path | None = None,
        test_cases_path: Path | None = None,
    ) -> dict[str, Any]:
        draft = self.review_store.get_draft(draft_id)
        if not draft:
            raise FileNotFoundError(f"Draft not found: {draft_id}")

        context = self._draft_context(draft)
        approved = self.approve_draft(draft_id)

        if not approved.get("saved_spec"):
            validation = self.run_functional_validation(
                spec_name=context["spec_name"],
                execute_queries=execute_queries,
                report_path=report_path,
                test_cases_path=test_cases_path,
                requirement_text=context["requirement_text"],
                requirement_summary=context["requirement_summary"],
                user_stories=context["user_stories"],
                ui_context=context["ui_context"],
                kpi_normalization=context.get("kpi_normalization"),
            )
            return {"approval": approved, "validation": validation}

        saved = approved["saved_spec"]
        validation = self.run_validation(
            etl_spec=approved["etl_spec_draft"],
            spec_id=saved["id"],
            spec_name=saved["name"],
            spec_version=str(saved["version"]),
            execute_queries=execute_queries,
            report_path=report_path,
            test_cases_path=test_cases_path,
            requirement_text=context["requirement_text"],
            requirement_summary=context["requirement_summary"],
            user_stories=context["user_stories"],
            ui_context=context["ui_context"],
            kpi_normalization=context.get("kpi_normalization"),
            mapping_analysis=context.get("mapping_analysis"),
        )
        return {"approval": approved, "validation": validation}

    @staticmethod
    def _is_complete_etl_spec(etl_spec: dict[str, Any] | None) -> bool:
        if not etl_spec:
            return False
        return all(str(etl_spec.get(field) or "").strip() for field in ("source_table", "target_table", "primary_key"))

    @staticmethod
    def _default_spec_name(etl_spec: dict[str, Any]) -> str:
        source = (etl_spec.get("source_table") or "source").split(".")[-1]
        target = (etl_spec.get("target_table") or "target").split(".")[-1]
        return f"{source}_to_{target}"

    @staticmethod
    def pretty_json(data: dict[str, Any]) -> str:
        return json.dumps(data, indent=2)
