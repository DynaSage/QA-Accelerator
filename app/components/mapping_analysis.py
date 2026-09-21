from __future__ import annotations
from pathlib import Path
from typing import Any
import streamlit as st
from src.exporters.mapping_exporter import mapping_excel_bytes, mapping_json_bytes


def render_mapping_downloads(draft: dict[str, Any] | None, *, key_prefix: str = "mapping") -> None:
    if not draft:
        return
    has_output = bool(
        draft.get("mapping_rows")
        or (draft.get("mapping_analysis") or {}).get("mappings")
        or draft.get("canonical_mappings")
        or draft.get("etl_spec_draft")
    )
    if not has_output:
        return

    st.subheader("Download mapping output")
    spec_name = (draft.get("source_files") or {}).get("spec_name") or "mapping_agent"
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in spec_name)[:60]

    st.markdown(
        """
        <style>
        div[data-testid="stPopover"] {
            display: inline-block !important;
        }
        div[data-testid="stPopover"] > button {
            min-width: 250px !important;
            max-width: 280px !important;
            border-radius: 999px !important;
            padding: 0.6rem 1.2rem !important;
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            line-height: 1.2 !important;
            background: #0c6f9e !important;
            border: 1px solid #1aa3d6 !important;
            color: #f5fbff !important;
            box-shadow: 0 2px 10px rgba(12, 111, 158, 0.35) !important;
        }
        div[data-testid="stPopover"] > button:hover {
            background: #0d7fb3 !important;
            border-color: #38bdf8 !important;
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.popover("Download", use_container_width=False):
        st.download_button(
            "JSON",
            data=mapping_json_bytes(draft),
            file_name=f"{safe_name}_mapping.json",
            mime="application/json",
            type="secondary",
            use_container_width=True,
            key=f"{key_prefix}_download_json",
        )
        st.download_button(
            "Excel",
            data=mapping_excel_bytes(draft),
            file_name=f"{safe_name}_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary",
            use_container_width=True,
            key=f"{key_prefix}_download_excel",
        )


def render_stm_summary(draft: dict[str, Any] | None, *, key_prefix: str = "stm") -> bool:
    if not draft:
        return False
    source_files = draft.get("source_files") or {}
    entities = draft.get("stm_entities") or []
    logic = draft.get("entity_logic") or []
    mapping_rows = draft.get("mapping_rows") or []
    kind = source_files.get("document_kind") or ""
    if kind != "word_stm" and not entities and not logic:
        return False

    st.subheader("Word STM document")
    table_names = [item.get("target_table") for item in entities if item.get("target_table")]
    if not table_names:
        table_names = sorted({str(row.get("target_table") or "") for row in mapping_rows if row.get("target_table")})
    col1, col2, col3 = st.columns(3)
    col1.metric("Entities", len(table_names))
    col2.metric("Mapping rows", len(mapping_rows))
    col3.metric("Load-logic sections", len(logic))
    if entities:
        st.dataframe(entities, use_container_width=True)

    selected = "All entities"
    if table_names:
        selected = st.selectbox("Mapping preview entity", ["All entities", *table_names], key=f"{key_prefix}_entity")
    preview = mapping_rows
    if selected != "All entities":
        preview = [row for row in mapping_rows if row.get("target_table") == selected]
    if preview:
        st.caption(f"Showing {len(preview)} mapping row(s).")
        st.dataframe(preview, use_container_width=True)

    for item in logic:
        name = item.get("target_table") or "Entity"
        with st.expander(f"Pseudo-code / load logic — {name}"):
            st.code(item.get("pseudo_code") or "", language="text")

    source_path = source_files.get("mapping_source_path") or ""
    if source_path:
        st.caption(f"Source document: `{Path(source_path).name}`")
    excel_path = Path(source_files.get("mapping_path") or "")
    if excel_path.is_file() and excel_path.suffix.lower() in {".xlsx", ".xlsm"}:
        st.download_button(
            "Download normalized mapping Excel",
            data=excel_path.read_bytes(),
            file_name=excel_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"{key_prefix}_normalized_excel",
        )
    return True


def render_mapping_analysis(analysis: dict[str, Any] | None) -> None:
    if not analysis or not analysis.get("mappings"):
        return

    st.subheader("Mapping Analysis")
    if analysis.get("requires_review"):
        st.warning(
            "High / Very-High risk mappings or gaps need QA review before SQL generation. "
            "Resolve UNKNOWN fields where possible."
        )
    col1, col2, col3 = st.columns(3)
    col1.metric("Mappings", len(analysis.get("mappings") or []))
    col2.metric("High risk", analysis.get("high_risk_count", 0))
    col3.metric("Gaps", analysis.get("gap_count", 0))

    rows = []
    for item in analysis.get("mappings") or []:
        source = item.get("source") or {}
        target = item.get("target") or {}
        transform = item.get("transformation") or {}
        rows.append(
            {
                "Mapping ID": item.get("mapping_id"),
                "Source": f"{source.get('table', '')}.{source.get('column', '')}",
                "Target": f"{target.get('table', '')}.{target.get('column', '')}",
                "Type": transform.get("type"),
                "Logic": transform.get("logic"),
                "Risk": item.get("risk"),
                "Rules": ", ".join(rule.get("rule_id", "") for rule in (item.get("validation_rules") or [])),
                "Gaps": "; ".join(item.get("gaps") or []),
                "Review": "Yes" if item.get("requires_review") else "No",
            }
        )
    st.dataframe(rows, use_container_width=True)

    if analysis.get("load_type_rules"):
        st.caption(
            "Load-type rules: "
            + ", ".join(rule.get("rule_id", "") for rule in analysis["load_type_rules"])
        )