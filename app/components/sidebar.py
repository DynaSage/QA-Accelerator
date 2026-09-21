from __future__ import annotations

import html

import streamlit as st

NAV_GROUPS: dict[str, list[tuple[str, str, str]]] = {
    "Workflow": [
        ("Home", "Home", "Dashboard and quick actions"),
        ("Import", "Import", "Mapping, ADO, or manual entry"),
        ("Build ETL Spec", "Build Spec", "Create draft spec"),
        ("Review Draft", "Review", "Edit before approval"),
        ("Generate QA Pack", "Generate", "Run test case agent"),
        ("Results & Exports", "Exports", "Download outputs"),
    ],
    "Explore": [
        ("Test Case Explorer", "Test Cases", "Filter and inspect cases"),
        ("Spec Library", "Spec Library", "Approved ETL specs"),
        ("Run History", "History", "Past QA runs"),
    ],
    "System": [
        ("Settings", "Settings", "Connections and health"),
    ],
}

WORKFLOW_STEPS = [
    ("Import", "Import stories"),
    ("Build ETL Spec", "Build spec"),
    ("Review Draft", "Review draft"),
    ("Generate QA Pack", "Generate pack"),
    ("Results & Exports", "Export results"),
]


def _workflow_index(current_page: str) -> int:
    for index, (page, _) in enumerate(WORKFLOW_STEPS):
        if page == current_page:
            return index + 1
    return 0


def render_sidebar() -> str:
    from app.views import PAGES

    page_names = list(PAGES.keys())
    current = st.session_state.get("current_page", "Home")
    if current not in page_names:
        current = "Home"
        st.session_state["current_page"] = current

    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="sidebar-brand-icon">QA</div>
          <div class="sidebar-brand-text">
            <div class="sidebar-brand-eyebrow">QA Platform</div>
            <div class="sidebar-brand-title">Accelerator</div>
          </div>
          <span class="sidebar-collapse-slot" role="button" tabindex="0" aria-label="Collapse sidebar"></span>
        </div>
        <div class="sidebar-tagline">AI-powered test case &amp; ETL validation</div>
        """,
        unsafe_allow_html=True,
    )

    for group_name, items in NAV_GROUPS.items():
        st.markdown(
            f'<div class="sb-group-label">{html.escape(group_name)}</div>',
            unsafe_allow_html=True,
        )
        for page_name, short_label, hint in items:
            if page_name not in PAGES:
                continue
            is_active = page_name == current
            if st.button(
                short_label,
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["current_page"] = page_name
                st.rerun()

    page = st.session_state.get("current_page", current)
    draft_id = st.session_state.get("draft_id", "")
    workflow_mode = st.session_state.get("workflow_mode", "etl")
    last = st.session_state.get("last_validation_result") or {}
    step_index = _workflow_index(page)

    status_bits: list[str] = []
    if draft_id:
        status_bits.append(
            '<div class="sidebar-status-row"><span>Draft</span>'
            f"<code>{html.escape(draft_id[:8])}…</code></div>"
        )
        status_bits.append(
            '<div class="sidebar-status-row"><span>Mode</span>'
            f"<strong>{html.escape(str(workflow_mode))}</strong></div>"
        )
    else:
        status_bits.append(
            '<div class="sidebar-status-row"><span>Draft</span><strong>None yet</strong></div>'
        )
    if last.get("run_id"):
        status_bits.append(
            '<div class="sidebar-status-row"><span>Last run</span>'
            f"<code>{html.escape(str(last['run_id'])[:8])}</code></div>"
        )
    if last.get("test_cases"):
        status_bits.append(
            '<div class="sidebar-status-row"><span>Test cases</span>'
            f"<strong>{len(last['test_cases'])}</strong></div>"
        )

    st.markdown(
        f'<div class="sidebar-section-label">Session</div>'
        f'<div class="sidebar-status-card">{"".join(status_bits)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-section-label">Workflow progress</div>',
        unsafe_allow_html=True,
    )

    step_items: list[str] = []
    for index, (_step_page, step_label) in enumerate(WORKFLOW_STEPS, start=1):
        if step_index == 0:
            state_class = "pending"
        elif index < step_index:
            state_class = "done"
        elif index == step_index:
            state_class = "active"
        else:
            state_class = "pending"
        marker = "✓" if state_class == "done" else str(index)
        step_items.append(
            f'<div class="sidebar-step {state_class}">'
            f'<span class="sidebar-step-dot">{marker}</span>'
            f'<span class="sidebar-step-label">{html.escape(step_label)}</span></div>'
        )
    st.markdown(f'<div class="sidebar-steps">{"".join(step_items)}</div>', unsafe_allow_html=True)

    quick_col1, quick_col2 = st.columns(2)
    with quick_col1:
        if st.button("Import", use_container_width=True, key="sidebar_quick_import"):
            st.session_state["current_page"] = "Import"
            st.rerun()
    with quick_col2:
        if st.button("Export", use_container_width=True, key="sidebar_quick_export"):
            st.session_state["current_page"] = "Results & Exports"
            st.rerun()

    st.markdown(
        '<div class="sidebar-footer">Insight Studio · ETL QA · v1.0</div>',
        unsafe_allow_html=True,
    )

    return page
