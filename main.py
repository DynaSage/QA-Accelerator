from venv_bootstrap import ensure_project_venv

ensure_project_venv()

import argparse
import json
from pathlib import Path
from uuid import uuid4

from src.exporters.excel_exporter import export_test_cases_to_excel
from src.graph import build_qa_sql_agent
from src.inputs.json_loader import load_etl_spec_from_json
from src.metadata.store import MetadataStore
from src.services.qa_workflow import QAWorkflowService
from src.utils.run_logger import RunLogger


def _resolve_spec(args: argparse.Namespace, store: MetadataStore) -> dict:
    if args.spec_id:
        record = store.get_spec(args.spec_id)
        if not record:
            raise FileNotFoundError(f"ETL spec not found in metadata store: {args.spec_id}")
        return {
            "etl_spec": record["content"],
            "spec_id": record["id"],
            "spec_name": record["name"],
            "spec_version": str(record["version"]),
        }

    if args.spec_name:
        record = store.get_latest_spec_by_name(args.spec_name)
        if not record:
            raise FileNotFoundError(f"ETL spec name not found in metadata store: {args.spec_name}")
        return {
            "etl_spec": record["content"],
            "spec_id": record["id"],
            "spec_name": record["name"],
            "spec_version": str(record["version"]),
        }

    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise FileNotFoundError(f"ETL spec not found: {spec_path}")

    spec_model = load_etl_spec_from_json(spec_path)
    saved = store.save_spec(spec_model, name=args.spec_name_override)
    return {
        "etl_spec": spec_model.to_agent_dict(),
        "spec_id": saved["id"],
        "spec_name": saved["name"],
        "spec_version": str(saved["version"]),
    }


def cmd_validate(args: argparse.Namespace) -> None:
    store = MetadataStore()
    run_id = str(uuid4())
    spec_payload = _resolve_spec(args, store)
    agent = build_qa_sql_agent()
    result = agent.invoke(
        {
            **spec_payload,
            "run_id": run_id,
            "execute_queries": not args.no_execute,
        }
    )

    report = result.get("qa_report") or "No report generated."
    report_path = Path(args.out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    test_cases = result.get("test_cases") or []
    test_cases_path = None
    if test_cases:
        test_cases_path = export_test_cases_to_excel(test_cases, Path(args.test_cases_out))

    summary = result.get("execution_summary") or {}
    RunLogger().save(
        run_id=run_id,
        spec_id=spec_payload.get("spec_id"),
        spec_name=spec_payload.get("spec_name", ""),
        result=result,
        report_path=str(report_path),
        test_cases_path=str(test_cases_path) if test_cases_path else None,
    )
    if spec_payload.get("spec_id"):
        store.record_run(
            run_id=run_id,
            spec_id=spec_payload["spec_id"],
            summary={"test_count": len(result.get("tests") or []), "execution_summary": summary},
            report_path=str(report_path),
        )

    print(report)
    print(f"\nSaved QA pack to {report_path}")
    if test_cases_path:
        print(f"Saved structured test cases to {test_cases_path}")
    print(f"Generated {len(result.get('tests') or [])} validation test(s).")
    print(f"Structured test cases: {len(test_cases)}")
    print(f"Run ID: {run_id}")
    if summary:
        print(f"ADB execution summary: {', '.join(f'{status}: {count}' for status, count in summary.items())}")


def _ado_settings_from_args(args: argparse.Namespace):
    from src.config import get_azure_devops_settings

    work_item_ids = None
    if getattr(args, "work_item_id", None):
        work_item_ids = [int(args.work_item_id)]
    return get_azure_devops_settings(
        organization=getattr(args, "org", None),
        project=getattr(args, "project", None),
        work_item_ids=work_item_ids,
    )


def cmd_ado_test(args: argparse.Namespace) -> None:
    from src.integrations.azure_devops_client import AzureDevOpsClient

    result = AzureDevOpsClient(_ado_settings_from_args(args)).test_connection()
    print("Azure DevOps connection successful.")
    print(f"Organization: {result['organization']}")
    print(f"Project: {result['project']}")
    print(f"Projects visible to PAT: {result['project_count']}")


def cmd_ado_import(args: argparse.Namespace) -> None:
    service = QAWorkflowService()
    work_item_ids = [int(args.work_item_id)] if getattr(args, "work_item_id", None) else None
    metadata = service.import_from_azure_devops(
        organization=getattr(args, "org", None),
        project=getattr(args, "project", None),
        work_item_ids=work_item_ids,
    )
    print("Azure DevOps user stories imported.")
    print(f"Import ID: {metadata['import_id']}")
    print(f"Stories imported: {metadata['story_count']}")
    print(f"Requirements file: {metadata['requirements_path']}")
    if metadata.get("mapping_path"):
        print(f"Mapping attachment: {metadata['mapping_path']}")
    else:
        print("Mapping attachment: not found (sample mapping or manual upload will be used during build)")
    print("\nNext step:")
    print("  python main.py build --from-ado")
    print("  python main.py approve --draft-id <draft-id> --no-execute")
    if args.build:
        draft = service.build_draft_from_ado(import_id=metadata["import_id"], spec_name=args.spec_name)
        print(f"\nDraft created: {draft['draft_id']}")
        print(f"Approve with: python main.py approve --draft-id {draft['draft_id']} --no-execute")


def cmd_build(args: argparse.Namespace) -> None:
    service = QAWorkflowService()
    mapping_path = Path(args.mapping) if args.mapping else None
    requirement_path = Path(args.requirements) if args.requirements else None

    if args.from_ado:
        draft = service.build_draft_from_ado(
            import_id=args.ado_import_id,
            mapping_path=mapping_path,
            spec_name=args.spec_name,
        )
    elif args.use_samples:
        mapping_path = Path("samples/mappings/sample_mapping.xlsx")
        requirement_path = Path("samples/requirements/sample_brd.txt")
        draft = service.build_draft_from_files(
            mapping_path=mapping_path,
            requirement_path=requirement_path,
            spec_name=args.spec_name,
        )
    elif args.json_spec:
        draft = service.build_draft_from_json(Path(args.json_spec), spec_name=args.spec_name)
    else:
        if mapping_path is None:
            mapping_path = Path("samples/mappings/sample_mapping.xlsx")
        if not mapping_path.exists():
            raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
        draft = service.build_draft_from_files(
            mapping_path=mapping_path,
            requirement_path=requirement_path,
            spec_name=args.spec_name,
        )

    print("Draft ETL spec created and waiting for review.")
    print(f"Draft ID: {draft['draft_id']}")
    print(f"Spec name: {draft.get('spec_name')}")
    print(f"Review file: review/drafts/{draft['draft_id']}.json")
    print("\nNext step:")
    print(f"  python main.py approve --draft-id {draft['draft_id']} --no-execute")
    if draft.get("missing_information"):
        print("\nMissing information:")
        for item in draft["missing_information"]:
            print(f"  - {item}")


def cmd_review(args: argparse.Namespace) -> None:
    service = QAWorkflowService()
    draft = service.review_store.get_draft(args.draft_id)
    if not draft:
        raise FileNotFoundError(f"Draft not found: {args.draft_id}")
    print(json.dumps(draft["etl_spec_draft"], indent=2))


def cmd_approve(args: argparse.Namespace) -> None:
    service = QAWorkflowService()
    draft = service.review_store.get_draft(args.draft_id)
    if not draft:
        raise FileNotFoundError(f"Draft not found: {args.draft_id}")

    if args.spec_json:
        etl_spec = json.loads(Path(args.spec_json).read_text(encoding="utf-8"))
        service.update_draft(args.draft_id, etl_spec)

    result = service.approve_and_validate(
        args.draft_id,
        execute_queries=not args.no_execute,
        report_path=Path(args.out),
        test_cases_path=Path(args.test_cases_out),
    )
    validation = result["validation"]
    print("Draft approved and QA pack generated.")
    saved_spec = result["approval"].get("saved_spec")
    if saved_spec:
        print(f"Saved spec: {saved_spec['name']} v{saved_spec['version']}")
    else:
        print("Functional QA pack generated (no ETL spec saved).")
    print(f"Report: {validation['report_path']}")
    if validation.get("test_cases_path"):
        print(f"Test cases: {validation['test_cases_path']}")
    print(f"Run ID: {validation['run_id']}")


def cmd_list_specs(_: argparse.Namespace) -> None:
    store = MetadataStore()
    specs = store.list_specs()
    if not specs:
        print("No ETL specs stored yet.")
        return
    for item in specs:
        print(f"{item['id']} | {item['name']} | v{item['version']} | updated {item['updated_at']}")


def cmd_list_drafts(_: argparse.Namespace) -> None:
    service = QAWorkflowService()
    drafts = service.review_store.list_drafts(status="pending_review")
    if not drafts:
        print("No pending drafts.")
        return
    for draft in drafts:
        print(
            f"{draft['draft_id']} | {draft.get('source_files', {}).get('spec_name', 'ETL Spec')} | "
            f"created {draft['created_at']}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI-Powered ETL QA Accelerator — build specs, review, and generate QA validation packs"
    )
    subparsers = parser.add_subparsers(dest="command")

    validate = subparsers.add_parser("validate", help="Run SQL Agent against an approved ETL spec")
    validate.add_argument("--spec", default="samples/specs/sample_etl_spec.json", help="Path to ETL specification JSON")
    validate.add_argument("--spec-id", help="Load a versioned ETL spec from metadata by ID")
    validate.add_argument("--spec-name", help="Load the latest named ETL spec from metadata")
    validate.add_argument("--spec-name-override", help="Optional metadata name when importing JSON")
    validate.add_argument("--out", default="output/qa_validation_pack.md", help="Output markdown report path")
    validate.add_argument("--test-cases-out", default="output/qa_test_cases.xlsx", help="Output Excel path")
    validate.add_argument("--no-execute", action="store_true", help="Skip Azure Databricks execution")
    validate.set_defaults(func=cmd_validate)

    ado_test = subparsers.add_parser("ado-test", help="Test Azure DevOps connection using .env settings")
    ado_test.add_argument("--org", help="Override AZURE_DEVOPS_ORG")
    ado_test.add_argument("--project", help="Override AZURE_DEVOPS_PROJECT")
    ado_test.add_argument("--work-item-id", type=int, help="Override AZURE_DEVOPS_WORK_ITEM_IDS for a single story")
    ado_test.set_defaults(func=cmd_ado_test)

    ado_import = subparsers.add_parser("ado-import", help="Import user stories from Azure DevOps")
    ado_import.add_argument("--org", help="Override AZURE_DEVOPS_ORG")
    ado_import.add_argument("--project", help="Override AZURE_DEVOPS_PROJECT")
    ado_import.add_argument("--work-item-id", type=int, help="Import a specific user story by ID")
    ado_import.add_argument("--spec-name", help="Optional draft/spec name when combined with --build")
    ado_import.add_argument("--build", action="store_true", help="Immediately build a draft ETL spec after import")
    ado_import.set_defaults(func=cmd_ado_import)

    build = subparsers.add_parser("build", help="Build a draft ETL spec from requirements + mapping")
    build.add_argument("--mapping", help="Mapping Excel path")
    build.add_argument("--requirements", help="Requirement document path (.txt/.docx/.pdf)")
    build.add_argument("--json-spec", help="Import an existing ETL spec JSON as a draft")
    build.add_argument("--from-ado", action="store_true", help="Build using the latest Azure DevOps import")
    build.add_argument("--ado-import-id", help="Build using a specific Azure DevOps import ID")
    build.add_argument("--spec-name", help="Optional draft/spec name")
    build.add_argument("--use-samples", action="store_true", help="Use built-in sample requirement and mapping files")
    build.set_defaults(func=cmd_build)

    review = subparsers.add_parser("review", help="Show a draft ETL spec JSON")
    review.add_argument("--draft-id", required=True)
    review.set_defaults(func=cmd_review)

    approve = subparsers.add_parser("approve", help="Approve a draft and generate the QA pack")
    approve.add_argument("--draft-id", required=True)
    approve.add_argument("--spec-json", help="Optional edited ETL spec JSON to save before approval")
    approve.add_argument("--out", default="output/qa_validation_pack.md")
    approve.add_argument("--test-cases-out", default="output/qa_test_cases.xlsx")
    approve.add_argument("--no-execute", action="store_true")
    approve.set_defaults(func=cmd_approve)

    subparsers.add_parser("list-specs", help="List approved ETL specs").set_defaults(func=cmd_list_specs)
    subparsers.add_parser("list-drafts", help="List pending draft ETL specs").set_defaults(func=cmd_list_drafts)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        print("\nTip: run `python main.py build --use-samples` or double-click `run_ui.ps1` for the web UI.")
        return
    args.func(args)


if __name__ == "__main__":
    main()
