import html as html_mod
import json
from pathlib import Path

import streamlit as st

from app.components.export_buttons import render_export_center
from app.components.theme import page_header
from app.state.session import get_service, set_validation_result


def _load_run_result(service, run: dict) -> dict | None:
    report_path = run.get("report_path")
    if not report_path or not Path(report_path).exists():
        return None
    result = {
        "run_id": run.get("run_id"),
        "spec_name": run.get("spec_name"),
        "report_path": report_path,
        "test_cases_path": run.get("test_cases_path"),
        "tests": [],
        "test_cases": [],
        "execution_summary": run.get("execution_summary") or {},
        "qa_report": Path(report_path).read_text(encoding="utf-8"),
    }
    return result


def _breakable(text: str) -> str:
    escaped = html_mod.escape(str(text))
    return escaped.replace("_", "_<wbr>").replace("-", "-<wbr>").replace(".", ".<wbr>")


def render() -> None:
    page_header("Run History", "Browse previous QA runs and re-download outputs.")

    service = get_service()
    runs = service.run_logger.list_runs(limit=100)

    if not runs:
        st.info("No runs recorded yet.")
        return

    selected_run_id = st.session_state.get("selected_run_id") or runs[0]["run_id"]
    options = {
        f"{run['run_id'][:8]} | {run.get('spec_name', 'QA Run')} | {run.get('run_at', '')[:19]}": run["run_id"]
        for run in runs
    }
    choice = st.selectbox(
        "Select run",
        list(options.keys()),
        index=list(options.values()).index(selected_run_id) if selected_run_id in options.values() else 0,
    )
    run_id = options[choice]
    run = service.run_logger.get_run(run_id)
    if not run:
        st.error("Run not found.")
        return

    spec = _breakable(run.get("spec_name") or "N/A")
    run_at = _breakable((run.get("run_at") or "")[:19].replace("T", " ") or "N/A")
    sql_tests = html_mod.escape(str(run.get("test_count", 0)))
    test_cases = html_mod.escape(str(run.get("test_case_count", 0)))
    st.markdown(
        '<div class="summary-grid equal-cards">'
        f'<div class="summary-card"><div class="title">Spec</div><div class="value compact">{spec}</div></div>'
        f'<div class="summary-card"><div class="title">SQL Tests</div><div class="value compact">{sql_tests}</div></div>'
        f'<div class="summary-card"><div class="title">Test Cases</div><div class="value compact">{test_cases}</div></div>'
        f'<div class="summary-card"><div class="title">Run At</div><div class="value compact">{run_at}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    result = _load_run_result(service, run)
    if result:
        set_validation_result(result)
        render_export_center(result, prefix="history")

    with st.expander("Run metadata"):
        st.json(run)

    if run.get("report_path") and Path(run["report_path"]).exists():
        st.subheader("Report Preview")
        st.markdown(Path(run["report_path"]).read_text(encoding="utf-8"))
