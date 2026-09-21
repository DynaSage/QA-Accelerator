import json

import streamlit as st

from app.components.theme import page_header
from app.state.session import get_service


def render() -> None:
    page_header("Test Case Explorer", "Filter, search, and inspect generated test cases.")

    result = st.session_state.get("last_validation_result")
    if not result or not result.get("test_cases"):
        st.info("Generate a QA pack first to explore test cases.")
        return

    test_cases = result["test_cases"]
    types = sorted({case.get("test_type") or case.get("validation_type") or "Unknown" for case in test_cases})
    priorities = sorted({case.get("priority") or "Unknown" for case in test_cases})

    col1, col2, col3 = st.columns(3)
    selected_type = col1.selectbox("Test type", ["All", *types])
    selected_priority = col2.selectbox("Priority", ["All", *priorities])
    search = col3.text_input("Search", placeholder="scenario, module, requirement id")

    filtered = test_cases
    if selected_type != "All":
        filtered = [
            case
            for case in filtered
            if (case.get("test_type") or case.get("validation_type")) == selected_type
        ]
    if selected_priority != "All":
        filtered = [case for case in filtered if case.get("priority") == selected_priority]
    if search.strip():
        needle = search.lower()
        filtered = [
            case
            for case in filtered
            if needle in json.dumps(case).lower()
        ]

    st.caption(f"Showing {len(filtered)} of {len(test_cases)} test cases")

    for case in filtered:
        with st.expander(f"{case.get('test_id')} | {case.get('test_scenario') or case.get('title')}"):
            st.markdown(f"**Requirement ID:** {case.get('requirement_id') or 'N/A'}")
            st.markdown(f"**Module / Feature:** {case.get('module') or 'N/A'} / {case.get('feature') or 'N/A'}")
            st.markdown(f"**Priority / Severity:** {case.get('priority')} / {case.get('severity') or 'N/A'}")
            st.markdown(f"**Type:** {case.get('test_type') or case.get('validation_type')}")
            st.markdown(f"**Automation:** {case.get('automation_candidate') or 'N/A'}")
            st.write(case.get("test_case_description") or "")

            steps = case.get("execution_steps") or []
            if steps:
                st.markdown("| Step | Action | Expected |")
                st.markdown("|---|---|---|")
                for step in steps:
                    st.markdown(
                        f"| {step.get('step_no')} | {step.get('user_action')} | {step.get('expected_result')} |"
                    )
            elif case.get("test_steps"):
                for step in case["test_steps"]:
                    st.markdown(f"- {step}")

            st.download_button(
                "Copy test case JSON",
                data=json.dumps(case, indent=2),
                file_name=f"{case.get('test_id', 'test_case')}.json",
                mime="application/json",
                key=f"copy_{case.get('test_id')}",
            )
