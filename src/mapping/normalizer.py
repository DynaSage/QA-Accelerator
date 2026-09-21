from __future__ import annotations

from typing import Any

from src.mapping.classifier import classify_transformation
from src.models.mapping_analysis import UNKNOWN

CANONICAL_FIELDS = (
    "source_database",
    "source_schema",
    "source_table",
    "source_column",
    "source_data_type",
    "transformation",
    "target_database",
    "target_schema",
    "target_table",
    "target_column",
    "target_data_type",
    "business_rule",
    "nullable",
    "primary_key",
    "notes",
)


def _clean(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else UNKNOWN


def _split_table(qualified: str) -> tuple[str, str, str]:
    if not qualified or qualified == UNKNOWN:
        return UNKNOWN, UNKNOWN, UNKNOWN
    parts = [part for part in qualified.replace("`", "").split(".") if part]
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    if len(parts) == 2:
        return UNKNOWN, parts[0], parts[1]
    return UNKNOWN, UNKNOWN, parts[0]


def normalize_mapping_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn parsed Excel rows into canonical mapping JSON for the Mapping Agent."""
    last_source_table = UNKNOWN
    last_target_table = UNKNOWN
    canonical: list[dict[str, Any]] = []

    for index, raw in enumerate(rows, start=1):
        source_table = _clean(raw.get("source_table"))
        target_table = _clean(raw.get("target_table"))
        if source_table != UNKNOWN:
            last_source_table = source_table
        else:
            source_table = last_source_table
        if target_table != UNKNOWN:
            last_target_table = target_table
        else:
            target_table = last_target_table

        src_db = _clean(raw.get("source_database"))
        src_schema = _clean(raw.get("source_schema"))
        tgt_db = _clean(raw.get("target_database"))
        tgt_schema = _clean(raw.get("target_schema"))
        if src_db == UNKNOWN or src_schema == UNKNOWN:
            parsed_db, parsed_schema, parsed_table = _split_table(source_table)
            src_db = src_db if src_db != UNKNOWN else parsed_db
            src_schema = src_schema if src_schema != UNKNOWN else parsed_schema
            if source_table.count(".") >= 1:
                source_table = parsed_table if parsed_table != UNKNOWN else source_table
        if tgt_db == UNKNOWN or tgt_schema == UNKNOWN:
            parsed_db, parsed_schema, parsed_table = _split_table(target_table)
            tgt_db = tgt_db if tgt_db != UNKNOWN else parsed_db
            tgt_schema = tgt_schema if tgt_schema != UNKNOWN else parsed_schema
            if target_table.count(".") >= 1:
                target_table = parsed_table if parsed_table != UNKNOWN else target_table

        logic = _clean(raw.get("transformation"))
        transform_type = classify_transformation("" if logic == UNKNOWN else logic)
        canonical.append(
            {
                "mapping_id": f"MAP-{index:03d}",
                "source": {
                    "database": src_db,
                    "schema": src_schema,
                    "table": source_table,
                    "column": _clean(raw.get("source_column")),
                    "data_type": _clean(raw.get("source_data_type")),
                    "nullable": _clean(raw.get("nullable")),
                    "primary_key": _clean(raw.get("primary_key")),
                },
                "target": {
                    "database": tgt_db,
                    "schema": tgt_schema,
                    "table": target_table,
                    "column": _clean(raw.get("target_column")),
                    "data_type": _clean(raw.get("target_data_type")),
                    "nullable": _clean(raw.get("nullable")),
                    "primary_key": _clean(raw.get("primary_key")),
                },
                "transformation": {"type": transform_type, "logic": logic},
                "business_rule": _clean(raw.get("business_rule") or raw.get("notes")),
                "notes": str(raw.get("notes") or "").strip(),
            }
        )
    return canonical
