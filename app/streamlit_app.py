import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from venv_bootstrap import ensure_project_venv

ensure_project_venv(ROOT)

import streamlit as st

st.set_page_config(
    page_title="ETL QA Accelerator",
    page_icon=str(ROOT / "assets" / "favicon.svg"),
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    "app.state.session",
    "app.views.import_stories",
    "app.views.build_spec",
    "app.views.review_draft",
    "app.components.mapping_analysis",
    "app.views",
)

for _name in _PARSER_MODULES:
    _module = sys.modules.get(_name)
    if _module is not None:
        importlib.reload(_module)
st.session_state.pop("qa_service", None)

from app.components.sidebar import render_sidebar
from app.components.theme import apply_theme
from app.state.session import get_service, init_session
from app.views import PAGES

apply_theme()
init_session()
with st.spinner("Starting QA workspace..."):
    get_service()

with st.sidebar:
    page = render_sidebar()

PAGES[page]()
