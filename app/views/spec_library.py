import json

import streamlit as st

from app.components.theme import page_header
from app.state.session import OUTPUT, get_service, set_validation_result


def render() -> None:
    page_header("Spec Library", "Browse approved ETL specs and re-run validation.")

    service = get_service()
    specs = service.metadata_store.list_specs()

    if not specs:
        st.info("No approved ETL specs yet.")
        return

    for spec in specs:
        with st.expander(f"{spec['name']} | v{spec['version']} | updated {spec['updated_at'][:19]}"):
            record = service.metadata_store.get_latest_spec_by_name(spec["name"])
            if not record:
                continue
            st.json(record["content"])

            execute = st.checkbox("Execute on Databricks", key=f"adb_{spec['id']}")
            col1, col2 = st.columns(2)
            if col1.button("Re-run Validation", key=f"rerun_{spec['id']}", use_container_width=True):
                try:
                    with st.spinner("Re-running validation..."):
                        result = service.run_validation(
                            etl_spec=record["content"],
                            spec_id=record["id"],
                            spec_name=record["name"],
                            spec_version=str(record["version"]),
                            execute_queries=execute,
                            report_path=OUTPUT / f"qa_validation_pack_{spec['name']}.md",
                            test_cases_path=OUTPUT / f"qa_test_cases_{spec['name']}.xlsx",
                        )
                    set_validation_result(result)
                    st.success("Validation complete.")
                    st.session_state["current_page"] = "Results & Exports"
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

            col2.download_button(
                "Download Spec JSON",
                data=json.dumps(record["content"], indent=2),
                file_name=f"{record['name']}_v{record['version']}.json",
                mime="application/json",
                key=f"download_{spec['id']}",
                use_container_width=True,
            )
