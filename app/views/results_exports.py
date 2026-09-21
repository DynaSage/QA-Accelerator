import streamlit as st

from app.components.export_buttons import render_export_center
from app.components.progress_stepper import render_stepper
from app.components.theme import page_header
from app.state.session import get_service


def render() -> None:
    page_header("Results & Exports", "Preview outputs and download reports, Excel test cases, and full QA packs.")
    render_stepper("Export")

    result = st.session_state.get("last_validation_result")
    if not result:
        st.info("No QA pack generated yet.")
        return

    cols = st.columns(4)
    cols[0].metric("SQL Tests", len(result.get("tests") or []))
    cols[1].metric("Test Cases", len(result.get("test_cases") or []))
    cols[2].metric("Run ID", result.get("run_id", "")[:8])
    cols[3].metric("Mode", result.get("workflow_mode", "etl"))

    render_export_center(result, prefix="results")

    st.divider()
    st.subheader("QA Report Preview")
    st.markdown(result.get("qa_report") or "No report generated.")

    artifacts = result.get("test_case_artifacts") or {}
    if artifacts.get("requirement_traceability_matrix"):
        st.subheader("Requirement Traceability Matrix")
        st.dataframe(artifacts["requirement_traceability_matrix"], use_container_width=True)

    if artifacts.get("test_coverage_matrix"):
        st.subheader("Test Coverage Matrix")
        st.dataframe(artifacts["test_coverage_matrix"], use_container_width=True)

    if result.get("execution_results"):
        st.subheader("Databricks Execution Results")
        st.dataframe(result["execution_results"], use_container_width=True)

    if st.button("Open Test Case Explorer"):
        st.session_state["current_page"] = "Test Case Explorer"
        st.rerun()
