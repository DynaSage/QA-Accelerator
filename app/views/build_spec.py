import json
from pathlib import Path

import streamlit as st

from app.components.file_upload import save_upload, ui_context_from_uploads
from app.components.kpi_logic_upload import render_kpi_logic_section
from app.components.progress_stepper import render_stepper
from app.components.theme import page_header
from app.state.session import SAMPLES, UPLOADS, get_service
from src.parsers.document_parser import read_requirement_document
from src.utils.workflow_mode import detect_workflow_mode


def _existing_file(value: str | Path | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_file() else None


def render() -> None:
    page_header("Build ETL Spec", "Generate a draft spec from a mapping document, optional stories, or uploaded files.")
    render_stepper("Build")

    service = get_service()
    latest_ado = st.session_state.get("latest_ado_import")
    uploaded_mapping = _existing_file(st.session_state.get("uploaded_mapping_path"))
    uploaded_requirement = _existing_file(st.session_state.get("uploaded_requirement_path"))

    if uploaded_mapping and st.session_state.get("build_input_source") == "Latest ADO import" and not latest_ado:
        st.session_state["build_input_source"] = "Uploaded files"

    source = st.radio(
        "Input source",
        ["Uploaded files", "Latest ADO import", "Sample files", "ETL spec JSON"],
        horizontal=True,
        key="build_input_source",
        help="Azure DevOps import is optional. Choose Uploaded files to run from a mapping document only.",
    )
    if source == "Uploaded files" and uploaded_mapping:
        st.caption(
            f"Using mapping document: `{uploaded_mapping.name}`. "
            "Word STM warehouse docs are supported. A requirement document is optional."
        )
    elif source == "Latest ADO import" and not latest_ado:
        st.caption("No ADO import in this session. Upload a mapping document instead, or import stories first.")

    spec_name = st.text_input("Spec name (optional)")
    workflow_mode = st.selectbox(
        "Workflow mode",
        ["auto", "functional", "etl", "hybrid"],
        help="Auto detects whether the story is UI/functional or ETL/data pipeline.",
    )
    screenshot_uploads = st.file_uploader(
        "UI screenshots (optional)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="build_screenshots",
    )
    mapping_upload = st.file_uploader(
        "Mapping override (Excel, CSV, or Word STM)",
        type=["xlsx", "xlsm", "csv", "docx"],
        key="build_mapping",
    )
    json_upload = st.file_uploader("ETL spec JSON", type=["json"], key="build_json")

    if st.button("Generate Draft", type="primary"):
        try:
            ui_context = ui_context_from_uploads(screenshot_uploads) or st.session_state.get("ui_context", "")
            mode = None if workflow_mode == "auto" else workflow_mode

            with st.spinner("Building draft..."):
                if source == "Latest ADO import":
                    if not latest_ado:
                        st.error(
                            "No Azure DevOps import in this session. "
                            "Choose Uploaded files and provide a mapping document, or import stories first."
                        )
                        st.stop()
                    mapping_path = save_upload(mapping_upload, UPLOADS) if mapping_upload else None
                    draft = service.build_draft_from_ado(
                        import_id=latest_ado["import_id"],
                        mapping_path=mapping_path,
                        spec_name=spec_name or None,
                        workflow_mode=mode,
                        ui_context=ui_context,
                    )
                elif source == "Uploaded files":
                    mapping_path = save_upload(mapping_upload, UPLOADS) if mapping_upload else uploaded_mapping
                    requirement_path = uploaded_requirement
                    if mapping_path:
                        if mapping_upload:
                            st.session_state["uploaded_mapping_path"] = str(mapping_path)
                        draft = service.build_draft_from_files(
                            mapping_path=mapping_path,
                            requirement_path=requirement_path,
                            spec_name=spec_name or st.session_state.get("saved_upload_spec_name") or mapping_path.stem,
                            ui_context=ui_context,
                        )
                    elif workflow_mode in ("auto", "functional"):
                        req_text = read_requirement_document(requirement_path) if requirement_path else ""
                        if not req_text.strip():
                            st.error(
                                "Upload a mapping document to run the ETL workflow. "
                                "Azure DevOps stories are optional."
                            )
                            st.stop()
                        draft = service.build_functional_draft(
                            requirement_text=req_text,
                            spec_name=spec_name or st.session_state.get("saved_upload_spec_name") or None,
                            ui_context=ui_context,
                        )
                    else:
                        st.error(
                            "Upload a mapping document (Excel, CSV, or Word STM). "
                            "An Azure DevOps import is not required."
                        )
                        st.stop()
                elif source == "Sample files":
                    draft = service.build_draft_from_files(
                        mapping_path=SAMPLES / "mappings" / "sample_mapping.xlsx",
                        requirement_path=SAMPLES / "requirements" / "sample_brd.txt",
                        spec_name=spec_name or "sample_demo",
                        ui_context=ui_context,
                    )
                else:
                    if json_upload is None:
                        st.error("Upload an ETL spec JSON file.")
                        st.stop()
                    json_path = save_upload(json_upload, UPLOADS)
                    draft = service.build_draft_from_json(json_path, spec_name=spec_name or None)

            draft_id = draft["draft_id"]
            kpi_normalized = st.session_state.get("kpi_logic_normalized")
            if kpi_normalized:
                draft = service.attach_kpi_logic_to_draft(draft_id, kpi_normalized)

            st.session_state["draft_id"] = draft_id
            st.session_state["draft_spec_json"] = service.pretty_json(draft.get("etl_spec_draft") or {})
            st.session_state["workflow_mode"] = draft.get("workflow_mode") or draft.get("source_files", {}).get(
                "workflow_mode", "etl"
            )
            st.session_state["current_page"] = "Review Draft"
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    st.divider()
    render_kpi_logic_section(draft_id=st.session_state.get("draft_id") or None, key_prefix="build_kpi")

    if latest_ado:
        st.divider()
        st.subheader("Latest ADO Import Preview")
        stories_path = latest_ado.get("stories_json_path")
        if stories_path and Path(stories_path).exists():
            stories = json.loads(Path(stories_path).read_text(encoding="utf-8"))
            detected = detect_workflow_mode(
                requirement_text=Path(latest_ado["requirements_path"]).read_text(encoding="utf-8")
                if Path(latest_ado["requirements_path"]).exists()
                else "",
                user_stories=stories,
                has_mapping=bool(latest_ado.get("mapping_path")),
            )
            st.info(f"Detected workflow mode: **{detected}**")
