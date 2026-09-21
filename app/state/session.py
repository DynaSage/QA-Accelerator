from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
UPLOADS = ROOT / "uploads"
OUTPUT = ROOT / "output"
SAMPLES = ROOT / "samples"


def init_session() -> None:
    defaults: dict[str, Any] = {
        "current_page": "Home",
        "draft_id": "",
        "draft_spec_json": "",
        "latest_ado_import": None,
        "ado_work_item_ids": "",
        "uploaded_mapping_path": "",
        "uploaded_requirement_path": "",
        "saved_upload_spec_name": "",
        "build_input_source": "Uploaded files",
        "last_validation_result": None,
        "workflow_mode": "etl",
        "ui_context": "",
        "selected_run_id": "",
        "kpi_logic_normalized": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_validation_result(result: dict[str, Any]) -> None:
    st.session_state["last_validation_result"] = result
    st.session_state["selected_run_id"] = result.get("run_id", "")


_PARSER_MODULES = (
    "src.parsers.tabular",
    "src.parsers.stm_extract",
    "src.parsers.excel_mapping_parser",
    "src.parsers.docx_mapping_parser",
    "src.parsers.mapping_file",
    "src.prompts.mapping_prompts",
    "src.agents.mapping_agent",
    "src.review.review_store",
    "src.services.qa_workflow",
)


def reload_mapping_stack() -> None:
    import importlib
    import sys

    for name in _PARSER_MODULES:
        module = sys.modules.get(name)
        if module is not None:
            importlib.reload(module)
    st.session_state.pop("qa_service", None)


def get_service():
    from src.parsers.mapping_file import install_mapping_parser
    from src.services.qa_workflow import QAWorkflowService

    install_mapping_parser()
    service = QAWorkflowService()
    st.session_state["qa_service"] = service
    return service
