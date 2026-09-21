import json
from pathlib import Path

import streamlit as st

from app.state.session import get_service


def render_export_center(result: dict, *, prefix: str = "export") -> None:
    if not result:
        st.info("No results available yet. Generate a QA pack first.")
        return

    service = get_service()
    report_path = Path(result["report_path"]) if result.get("report_path") else None
    test_cases_path = Path(result["test_cases_path"]) if result.get("test_cases_path") else None

    st.subheader("Downloads")
    col1, col2, col3 = st.columns(3)

    with col1:
        if report_path and report_path.exists():
            st.download_button(
                "QA Report (.md)",
                data=report_path.read_text(encoding="utf-8"),
                file_name=report_path.name,
                mime="text/markdown",
                use_container_width=True,
                key=f"{prefix}_report",
            )

    with col2:
        if test_cases_path and test_cases_path.exists():
            st.download_button(
                "Test Cases (.xlsx)",
                data=test_cases_path.read_bytes(),
                file_name=test_cases_path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"{prefix}_excel",
            )

    with col3:
        zip_bytes = service.build_qa_pack_zip(result)
        st.download_button(
            "Full QA Pack (.zip)",
            data=zip_bytes,
            file_name=f"qa_pack_{result.get('run_id', 'run')[:8]}.zip",
            mime="application/zip",
            use_container_width=True,
            key=f"{prefix}_zip",
        )

    artifacts = result.get("test_case_artifacts") or {}
    if artifacts:
        st.download_button(
            "RTM & Artifacts (.json)",
            data=json.dumps(artifacts, indent=2),
            file_name=f"test_case_artifacts_{result.get('run_id', 'run')[:8]}.json",
            mime="application/json",
            key=f"{prefix}_artifacts",
        )

    if result.get("tests"):
        st.download_button(
            "SQL Tests (.json)",
            data=json.dumps(result["tests"], indent=2),
            file_name=f"sql_tests_{result.get('run_id', 'run')[:8]}.json",
            mime="application/json",
            key=f"{prefix}_sql",
        )
