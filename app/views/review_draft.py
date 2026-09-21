import json
from pathlib import Path

import streamlit as st

from app.components.kpi_logic_upload import render_kpi_logic_section
from app.components.mapping_analysis import render_mapping_analysis, render_mapping_downloads, render_stm_summary
from app.components.progress_stepper import render_stepper
from app.components.story_card import render_story_card
from app.components.theme import page_header
from app.state.session import get_service


def render() -> None:
    page_header("Review Draft", "Review analysis, user stories, and the draft spec before generating tests.")
    render_stepper("Review")

    service = get_service()
    draft_id = st.session_state.get("draft_id", "")

    pending = service.review_store.list_drafts(status="pending_review")
    if pending:
        options = {f"{d['draft_id'][:8]}... | {d.get('source_files', {}).get('spec_name', 'Draft')}": d["draft_id"] for d in pending}
        selected = st.selectbox("Load pending draft", ["— current —", *options.keys()])
        if selected != "— current —":
            draft_id = options[selected]
            st.session_state["draft_id"] = draft_id
            draft = service.review_store.get_draft(draft_id)
            if draft:
                st.session_state["draft_spec_json"] = service.pretty_json(draft.get("etl_spec_draft") or {})
                st.session_state["workflow_mode"] = draft.get("source_files", {}).get("workflow_mode", "etl")

    if not draft_id:
        st.warning("No draft selected. Import or build a draft first.")
        return

    draft = service.review_store.get_draft(draft_id)
    if not draft:
        st.error("Draft not found.")
        return

    workflow_mode = draft.get("source_files", {}).get("workflow_mode", "etl")
    st.info(f"Workflow mode: **{workflow_mode}** | Draft ID: `{draft_id}`")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Requirement Analysis")
        summary = draft.get("requirement_summary") or {}
        st.write(summary.get("requirement_summary") or "No summary available.")
        if summary.get("business_rules"):
            st.markdown("**Business Rules**")
            for rule in summary["business_rules"]:
                st.markdown(f"- {rule}")

    with col2:
        missing = draft.get("missing_information") or []
        assumptions = draft.get("assumptions") or []

        with st.expander("Gaps & Assumptions", expanded=False):
            if missing:
                for item in missing:
                    st.warning(item)
            else:
                st.success("No missing information flagged.")

            if assumptions:
                st.markdown("**Assumptions**")
                for item in assumptions:
                    st.markdown(f"- {item}")

    stories = service._load_user_stories(draft.get("source_files") or {})
    if stories:
        st.subheader("User Stories")
        for story in stories:
            render_story_card(story)

    if workflow_mode != "functional":
        st.subheader("ETL Spec JSON")
        draft_spec_json = st.text_area(
            "Editable ETL spec",
            value=st.session_state.get("draft_spec_json") or service.pretty_json(draft.get("etl_spec_draft") or {}),
            height=320,
        )
        st.session_state["draft_spec_json"] = draft_spec_json

        mapping_rows = draft.get("mapping_rows") or []
        if not render_stm_summary(draft, key_prefix="review_stm") and mapping_rows:
            st.subheader("Mapping Preview")
            st.dataframe(mapping_rows[:20], use_container_width=True)
        llm_output = draft.get("llm_mapping_output") or {}
        if llm_output.get("transformation_rules") or llm_output.get("entities"):
            st.subheader("LLM mapping output")
            st.caption("Azure OpenAI wrote transformations, keys, and rules from the STM tables and pseudo-code.")
            for item in llm_output.get("entities") or []:
                pk = item.get("primary_key") or "UNKNOWN"
                st.markdown(f"- `{item.get('target_table') or 'entity'}` primary key: `{pk}`")
            for rule in (llm_output.get("transformation_rules") or [])[:20]:
                st.markdown(f"- {rule}")
        render_mapping_analysis(draft.get("mapping_analysis") or {})
        render_mapping_downloads(draft, key_prefix="review_mapping")
    else:
        st.subheader("Functional QA Draft")
        st.write("This draft will generate functional/UI test cases without requiring an ETL mapping.")

    st.divider()
    render_kpi_logic_section(draft_id=draft_id, key_prefix="review_kpi")
    kpi_path = (draft.get("source_files") or {}).get("kpi_logic_path")
    if kpi_path:
        st.caption(f"Attached KPI logic: `{kpi_path}`")

    action1, action2, action3 = st.columns(3)
    if action1.button("Save Draft", use_container_width=True):
        try:
            if workflow_mode != "functional":
                edited = json.loads(st.session_state.get("draft_spec_json") or "{}")
                if service._is_complete_etl_spec(edited):
                    service.update_draft(draft_id, edited)
            st.success("Draft saved.")
        except Exception as exc:
            st.error(str(exc))

    if action2.button("Delete Draft", use_container_width=True):
        try:
            service.review_store.delete_draft(draft_id)
            st.session_state["draft_id"] = ""
            st.session_state["draft_spec_json"] = ""
            st.success("Draft deleted.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if action3.button("Proceed to Generate", type="primary", use_container_width=True):
        st.session_state["current_page"] = "Generate QA Pack"
        st.rerun()
