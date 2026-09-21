import html as html_module

import streamlit as st

from app.components.connection_status import render_connection_cards
from app.components.export_buttons import render_export_center
from app.components.theme import page_header
from app.state.session import SAMPLES, get_service


def _kpi_card(title: str, value, accent: str = "var(--primary,#38bdf8)") -> str:
    return (
        f'<div class="summary-card" style="border-left-color:{accent};">'
        f'<div class="title">{html_module.escape(str(title))}</div>'
        f'<div class="value">{html_module.escape(str(value))}</div></div>'
    )


def render() -> None:
    page_header(
        "QA Accelerator Dashboard",
        "Import user stories, mapping documents, build specs, generate test cases, and export QA packs.",
    )

    render_connection_cards()
    st.divider()

    service = get_service()
    drafts  = service.review_store.list_drafts(status="pending_review")
    runs    = service.run_logger.list_runs(limit=5)
    last    = st.session_state.get("last_validation_result") or {}
    n_tests = len(last.get("test_cases") or [])

    cards_html = (
        _kpi_card("Pending Drafts",  len(drafts),                                   "var(--tertiary,#a78bfa)")
        + _kpi_card("Recent Runs",   len(runs),                                     "var(--primary,#38bdf8)")
        + _kpi_card("Approved Specs",len(service.metadata_store.list_specs()),       "var(--secondary,#4ade80)")
        + _kpi_card("Last Run Tests",n_tests,                                        "var(--primary,#38bdf8)")
    )
    st.markdown(
        f'<div class="summary-grid">{cards_html}</div>',
        unsafe_allow_html=True,
    )

    # Quick actions
    st.markdown('<div class="section-title">Quick Actions</div>', unsafe_allow_html=True)
    action1, action2, action3 = st.columns(3)
    if action1.button("Go to Import", use_container_width=True):
        st.session_state["current_page"] = "Import"
        st.rerun()
    if action2.button("Run Sample Demo", use_container_width=True):
        with st.spinner("Building sample draft..."):
            draft = service.build_draft_from_files(
                mapping_path=SAMPLES / "mappings" / "sample_mapping.xlsx",
                requirement_path=SAMPLES / "requirements" / "sample_brd.txt",
                spec_name="sample_demo",
            )
            st.session_state["draft_id"]        = draft["draft_id"]
            st.session_state["draft_spec_json"] = service.pretty_json(draft["etl_spec_draft"])
            st.session_state["workflow_mode"]   = draft.get("workflow_mode", "etl")
            st.session_state["current_page"]    = "Review Draft"
            st.rerun()
    if action3.button("View Latest Results", use_container_width=True):
        st.session_state["current_page"] = "Results & Exports"
        st.rerun()

    # Recent Runs
    st.markdown('<div class="section-title">Recent Runs</div>', unsafe_allow_html=True)
    if not runs:
        st.info("No runs yet. Import a user story and generate a QA pack.")
    else:
        rows_html = ""
        for run in runs:
            name  = html_module.escape(run.get("spec_name") or "QA Run")
            ts    = run.get("run_at", "")[:19].replace("T", " ")
            count = run.get("test_case_count", 0)
            rid   = run.get("run_id", "")
            rows_html += (
                f'<tr class="main-row">'
                f'<td><strong>{name}</strong></td>'
                f'<td class="timestamp">{ts}</td>'
                f'<td><span class="section-badge">{count} tests</span></td>'
                f'</tr>'
            )
        st.markdown(
            '<div class="table-container"><table>'
            '<thead><tr><th>Spec</th><th>Run At</th><th>Tests</th></tr></thead>'
            f'<tbody>{rows_html}</tbody></table></div>',
            unsafe_allow_html=True,
        )

    if st.session_state.get("last_validation_result"):
        st.divider()
        st.markdown('<div class="section-title">Latest QA Pack</div>', unsafe_allow_html=True)
        render_export_center(st.session_state["last_validation_result"], prefix="home")
