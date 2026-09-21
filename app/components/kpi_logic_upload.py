from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.components.file_upload import save_upload
from app.state.session import UPLOADS, get_service


def _requirement_context() -> str:
    parts: list[str] = []
    latest = st.session_state.get("latest_ado_import")
    if latest and latest.get("requirements_path"):
        req_path = Path(latest["requirements_path"])
        if req_path.exists():
            parts.append(req_path.read_text(encoding="utf-8")[:4000])

    draft_id = st.session_state.get("draft_id", "")
    if draft_id:
        draft = get_service().review_store.get_draft(draft_id)
        if draft:
            req_path = (draft.get("source_files") or {}).get("requirements_path", "")
            if req_path and Path(req_path).exists():
                parts.append(Path(req_path).read_text(encoding="utf-8")[:4000])
    return "\n\n".join(parts)


def render_kpi_logic_section(*, draft_id: str | None = None, key_prefix: str = "kpi") -> None:
    """Upload a developer KPI logic document, normalize SQL for Databricks, and preview results."""
    service = get_service()
    st.subheader("KPI Logic Document")
    st.caption(
        "Upload developer SQL for UI KPI validation. Each query is reviewed and normalized "
        "to be runnable on Azure Databricks."
    )

    kpi_upload = st.file_uploader(
        "KPI Logic Document",
        type=["xlsx", "xlsm", "csv", "sql", "txt", "docx", "pdf", "md", "json"],
        key=f"{key_prefix}_file",
    )

    if st.button("Process & Normalize SQL for Databricks", type="primary", key=f"{key_prefix}_process"):
        if kpi_upload is None:
            st.error("Upload a KPI logic document first.")
            return
        try:
            saved_path = save_upload(kpi_upload, UPLOADS / "kpi_logic")
            with st.spinner("Parsing and normalizing KPI SQL — this may take a minute..."):
                normalized = service.process_kpi_logic_document(
                    saved_path,
                    requirement_context=_requirement_context(),
                )
            st.session_state["kpi_logic_normalized"] = normalized

            if draft_id:
                service.attach_kpi_logic_to_draft(draft_id, normalized)

            st.success(
                f"Normalized {normalized.get('runnable_count', 0)} of "
                f"{normalized.get('total_count', 0)} KPI queries for Databricks."
            )
        except Exception as exc:
            st.error(str(exc))

    normalized = st.session_state.get("kpi_logic_normalized")
    if not normalized and draft_id:
        draft = service.review_store.get_draft(draft_id)
        if draft:
            normalized = service._load_kpi_normalization(draft.get("source_files") or {})

    if not normalized:
        return

    runnable = normalized.get("runnable_count", 0)
    total = normalized.get("total_count", 0)
    rejected = normalized.get("rejected_queries") or []

    col1, col2, col3 = st.columns(3)
    col1.metric("Total KPI Queries", total)
    col2.metric("Databricks-Ready", runnable)
    col3.metric("Rejected / Blocked", len(rejected))

    if normalized.get("global_notes"):
        with st.expander("Normalization notes"):
            for note in normalized["global_notes"]:
                st.markdown(f"- {note}")

    queries = normalized.get("queries") or []
    if queries:
        with st.expander("Normalized SQL preview", expanded=False):
            for entry in queries:
                status = "Ready" if entry.get("runnable") else "Blocked"
                st.markdown(f"**{entry.get('kpi_id', '')} — {entry.get('kpi_name', '')}** ({status})")
                if entry.get("fixes_applied"):
                    st.caption("Fixes: " + "; ".join(entry["fixes_applied"]))
                if entry.get("issues_remaining"):
                    st.warning("; ".join(entry["issues_remaining"]))
                sql = entry.get("normalized_sql") or entry.get("original_sql") or ""
                if sql:
                    st.code(sql, language="sql")

    if rejected:
        with st.expander("Rejected queries"):
            for item in rejected:
                st.markdown(f"- {item}")
