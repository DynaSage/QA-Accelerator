import json
from datetime import UTC, datetime
from pathlib import Path

import streamlit as st

from app.components.file_upload import save_upload, ui_context_from_uploads
from app.components.kpi_logic_upload import render_kpi_logic_section
from app.components.progress_stepper import render_stepper
from app.components.story_card import render_story_card
from app.components.theme import page_header
from app.state.session import UPLOADS, get_service
from src.integrations.ado_importer import AdoImporter


def _parse_work_item_ids(raw: str) -> list[int]:
    if not raw.strip():
        return []
    return [int(item.strip()) for item in raw.split(",") if item.strip()]


def _replace_imported_stories(metadata: dict, stories: list[dict]) -> dict:
    stories_path = Path(metadata["stories_json_path"])
    requirements_path = Path(metadata["requirements_path"])
    import_dir = Path("imports") / "ado" / str(metadata["import_id"])

    lines = [
        "ETL QA Requirements imported from Azure DevOps User Stories",
        f"Organization: {metadata.get('organization') or ''}",
        f"Project: {metadata.get('project') or ''}",
        f"Imported at: {datetime.now(UTC).isoformat()}",
        "",
    ]
    for index, story in enumerate(stories, start=1):
        lines.extend(
            [
                f"## User Story {index}: {story.get('id')} - {story.get('title')}",
                f"Type: {story.get('work_item_type')}",
                f"State: {story.get('state')}",
                f"Area Path: {story.get('area_path', '')}",
                f"Iteration Path: {story.get('iteration_path', '')}",
                f"Tags: {story.get('tags') or 'None'}",
                "",
                "### Description",
                story.get("description") or "No description provided.",
                "",
                "### Acceptance Criteria",
                story.get("acceptance_criteria") or "No acceptance criteria provided.",
                "",
                "---",
                "",
            ]
        )

    stories_path.parent.mkdir(parents=True, exist_ok=True)
    stories_path.write_text(json.dumps(stories, indent=2), encoding="utf-8")
    requirements_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    updated = {
        **metadata,
        "story_count": len(stories),
        "story_ids": [story.get("id") for story in stories],
    }
    import_dir.mkdir(parents=True, exist_ok=True)
    (import_dir / "import_metadata.json").write_text(json.dumps(updated, indent=2), encoding="utf-8")
    (Path("imports") / "ado" / "latest.json").write_text(json.dumps(updated, indent=2), encoding="utf-8")
    return updated


def render() -> None:
    page_header(
        "Import Inputs",
        "Azure DevOps stories are optional. A mapping document is enough to run the ETL QA workflow.",
    )
    render_stepper("Import")

    service = get_service()
    tab_ado, tab_files, tab_manual = st.tabs(["Azure DevOps", "File Upload", "Manual Entry"])

    with tab_ado:
        st.subheader("Import from Azure DevOps (optional)")
        if st.session_state.pop("reset_ado_import", False):
            st.session_state["latest_ado_import"] = None
            st.session_state["ado_work_item_ids"] = ""

        col1, col2 = st.columns(2)
        org = col1.text_input("Organization (optional override)", placeholder="from .env")
        project = col2.text_input("Project (optional override)", placeholder="from .env")
        work_item_ids = st.text_input(
            "Work Item ID(s)",
            placeholder="Leave empty, then enter IDs for this import only",
            key="ado_work_item_ids",
        )
        spec_name = st.text_input("Spec name (optional)", key="ado_spec_name")
        st.caption("Optional. Skip this tab if you only have a mapping document. Empty Work Item IDs does not reuse a previous story.")

        btn1, btn2, btn3 = st.columns(3)
        if btn1.button("Test Connection", use_container_width=True):
            try:
                from src.integrations.azure_devops_client import AzureDevOpsClient
                from src.config import get_azure_devops_settings

                result = AzureDevOpsClient(
                    get_azure_devops_settings(
                        organization=org or None,
                        project=project or None,
                        work_item_ids=_parse_work_item_ids(work_item_ids),
                    )
                ).test_connection()
                st.success(f"Connected to {result['organization']}/{result['project']}")
            except Exception as err:
                st.error(str(err))

        if btn2.button("Import User Stories", type="primary", use_container_width=True):
            parsed_ids = _parse_work_item_ids(work_item_ids)
            if not parsed_ids:
                st.error("Enter one or more Work Item IDs. An empty field does not reuse a previous story.")
            else:
                try:
                    with st.spinner("Importing user stories..."):
                        metadata = service.import_from_azure_devops(
                            organization=org or None,
                            project=project or None,
                            work_item_ids=parsed_ids,
                        )
                    st.session_state["latest_ado_import"] = metadata
                    st.success(f"Imported {metadata['story_count']} user stories.")
                except Exception as err:
                    st.error(str(err))

        if btn3.button("Start new import", use_container_width=True):
            st.session_state["reset_ado_import"] = True
            st.rerun()

        latest = st.session_state.get("latest_ado_import")
        if latest is None:
            saved = AdoImporter.load_latest_import()
            if saved:
                st.caption(
                    "A previous import exists on disk but is not loaded. "
                    "This page starts empty until you import IDs or load the last save."
                )
                if st.button("Load last saved import"):
                    st.session_state["latest_ado_import"] = saved
                    st.rerun()
        if latest:
            st.info(f"Latest import: {latest['import_id']} ({latest.get('story_count', 0)} stories)")
            stories_path = latest.get("stories_json_path")
            stories: list[dict] = []
            if stories_path and Path(stories_path).exists():
                stories = json.loads(Path(stories_path).read_text(encoding="utf-8"))
            if not stories:
                st.caption("No stories remain in this import.")
            for index, story in enumerate(stories):
                story_id = story.get("id", index)
                card_col, remove_col = st.columns([12, 1], vertical_alignment="top")
                with card_col:
                    render_story_card(story)
                with remove_col:
                    if st.button(
                        "✕",
                        key=f"remove_ado_story_{latest['import_id']}_{story_id}",
                        help=f"Remove US-{story_id} from this import",
                        use_container_width=True,
                    ):
                        remaining = [item for item_index, item in enumerate(stories) if item_index != index]
                        st.session_state["latest_ado_import"] = _replace_imported_stories(
                            latest,
                            remaining,
                        )
                        st.rerun()

            st.markdown('<div class="import-action-gap"></div>', unsafe_allow_html=True)
            req_path = latest.get("requirements_path")
            action_cols = st.columns(3)
            with action_cols[0]:
                if req_path and Path(req_path).exists():
                    st.download_button(
                        "Download Requirements (.txt)",
                        data=Path(req_path).read_text(encoding="utf-8"),
                        file_name=Path(req_path).name,
                        mime="text/plain",
                        use_container_width=True,
                    )
            with action_cols[1]:
                if stories_path and Path(stories_path).exists():
                    st.download_button(
                        "Download Stories JSON",
                        data=Path(stories_path).read_text(encoding="utf-8"),
                        file_name=Path(stories_path).name,
                        mime="application/json",
                        use_container_width=True,
                    )
            with action_cols[2]:
                if st.button("Build Draft from this Import", type="primary", use_container_width=True):
                    st.session_state["build_input_source"] = "Latest ADO import"
                    st.session_state["current_page"] = "Build ETL Spec"
                    st.rerun()

    with tab_files:
        st.subheader("Upload mapping or requirement documents")
        st.caption(
            "Upload a mapping document to run the full ETL workflow. "
            "Word STM tables are extracted, then Azure OpenAI writes the mapping output "
            "(transformations, keys, and rules). Architecture tables are skipped. "
            "A requirement document and Azure DevOps import are optional."
        )
        requirement_upload = st.file_uploader("Requirement document (optional)", type=["txt", "docx", "pdf"])
        mapping_upload = st.file_uploader(
            "Mapping document (Excel, CSV, or Word STM)",
            type=["xlsx", "xlsm", "csv", "docx"],
        )
        screenshot_uploads = st.file_uploader(
            "UI screenshots / mockups (optional)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
        )
        uploaded_spec_name = st.text_input("Spec name", key="upload_spec_name")

        if st.button("Build Draft from Uploads", type="primary"):
            req_path = save_upload(requirement_upload, UPLOADS)
            map_path = save_upload(mapping_upload, UPLOADS)
            st.session_state["uploaded_requirement_path"] = str(req_path) if req_path else ""
            st.session_state["uploaded_mapping_path"] = str(map_path) if map_path else ""
            st.session_state["ui_context"] = ui_context_from_uploads(screenshot_uploads)
            st.session_state["saved_upload_spec_name"] = uploaded_spec_name
            st.session_state["build_input_source"] = "Uploaded files"

            if map_path is None and req_path is None:
                st.error("Upload a mapping document to run the ETL workflow, or a requirement document for a functional story.")
            elif map_path is not None:
                try:
                    spinner = (
                        "Extracting STM tables and generating mapping output with Azure OpenAI..."
                        if map_path.suffix.lower() == ".docx"
                        else "Generating mapping output with Azure OpenAI..."
                    )
                    with st.spinner(spinner):
                        draft = service.build_draft_from_files(
                            mapping_path=map_path,
                            requirement_path=req_path,
                            spec_name=uploaded_spec_name or map_path.stem,
                            ui_context=st.session_state.get("ui_context", ""),
                        )
                    draft_id = draft["draft_id"]
                    kpi_normalized = st.session_state.get("kpi_logic_normalized")
                    if kpi_normalized:
                        draft = service.attach_kpi_logic_to_draft(draft_id, kpi_normalized)
                    st.session_state["draft_id"] = draft_id
                    st.session_state["draft_spec_json"] = service.pretty_json(draft.get("etl_spec_draft") or {})
                    st.session_state["workflow_mode"] = draft.get("workflow_mode") or "etl"
                    st.session_state["current_page"] = "Review Draft"
                    st.rerun()
                except Exception as err:
                    st.error(str(err))
            else:
                try:
                    from src.parsers.document_parser import read_requirement_document

                    req_text = read_requirement_document(req_path)
                    with st.spinner("Analyzing requirement document..."):
                        draft = service.build_functional_draft(
                            requirement_text=req_text,
                            spec_name=uploaded_spec_name or req_path.stem,
                            ui_context=st.session_state.get("ui_context", ""),
                        )
                    draft_id = draft["draft_id"]
                    kpi_normalized = st.session_state.get("kpi_logic_normalized")
                    if kpi_normalized:
                        draft = service.attach_kpi_logic_to_draft(draft_id, kpi_normalized)
                    st.session_state["draft_id"] = draft_id
                    st.session_state["draft_spec_json"] = service.pretty_json(draft.get("etl_spec_draft") or {})
                    st.session_state["workflow_mode"] = draft.get("source_files", {}).get("workflow_mode", "functional")
                    st.session_state["current_page"] = "Review Draft"
                    st.rerun()
                except Exception as err:
                    st.error(str(err))

    with tab_manual:
        st.subheader("Enter user story manually")
        title = st.text_input("Story title", placeholder="Insight Studio login")
        description = st.text_area("Description", height=120)
        acceptance = st.text_area("Acceptance criteria", height=120)
        business_rules = st.text_area("Business rules (one per line)", height=80)
        manual_screenshots = st.file_uploader(
            "UI screenshots (optional)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="manual_screenshots",
        )
        manual_spec_name = st.text_input("Spec name", key="manual_spec_name")

        if st.button("Create Functional Draft", type="primary"):
            try:
                rules = [line.strip() for line in business_rules.splitlines() if line.strip()]
                ui_context = ui_context_from_uploads(manual_screenshots)
                with st.spinner("Analyzing story and creating draft..."):
                    draft = service.build_draft_from_manual_story(
                        title=title,
                        description=description,
                        acceptance_criteria=acceptance,
                        business_rules=rules,
                        spec_name=manual_spec_name or None,
                        ui_context=ui_context,
                    )
                draft_id = draft["draft_id"]
                kpi_normalized = st.session_state.get("kpi_logic_normalized")
                if kpi_normalized:
                    draft = service.attach_kpi_logic_to_draft(draft_id, kpi_normalized)

                st.session_state["draft_id"] = draft_id
                st.session_state["draft_spec_json"] = service.pretty_json(draft.get("etl_spec_draft") or {})
                st.session_state["workflow_mode"] = draft.get("source_files", {}).get("workflow_mode", "functional")
                st.session_state["current_page"] = "Review Draft"
                st.rerun()
            except Exception as err:
                st.error(str(err))

    st.divider()
    render_kpi_logic_section(draft_id=st.session_state.get("draft_id") or None, key_prefix="import_kpi")
