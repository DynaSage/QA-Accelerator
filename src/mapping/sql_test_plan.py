"""Turn Mapping Agent analysis (VR rules) into a SQL Agent test plan."""

from __future__ import annotations

import re
from typing import Any

from src.models.mapping_analysis import UNKNOWN
from src.utils.sql_safety import is_select_only

LLM_PLAN_LIMIT = 40

RULE_VALIDATION_TYPE = {
    "VR01": "Record Count",
    "VR02": "NULL",
    "VR03": "Duplicate",
    "VR04": "Transformation",
    "VR05": "Transformation",
    "VR06": "Transformation",
    "VR07": "Business Rule",
    "VR10": "Transformation",
    "VR11": "Transformation",
    "VR12": "Transformation",
    "VR13": "Transformation",
    "VR14": "Transformation",
    "VR15": "Data Reconciliation",
    "VR16": "Data Reconciliation",
    "VR17": "Transformation",
    "VR18": "Transformation",
    "VR19": "Business Rule",
    "VR20": "Record Count",
    "VR21": "Incremental Load",
    "VR22": "Incremental Load",
    "VR23": "Transformation",
    "VR24": "Transformation",
    "VR25": "Business Rule",
    "VR26": "Business Rule",
}

_VARCHAR_LEN = re.compile(r"(?:VAR)?CHAR\s*\(\s*(\d+)\s*\)", re.IGNORECASE)


def quote_ident(name: str) -> str:
    cleaned = (name or "").strip().strip("`")
    if not cleaned or cleaned == UNKNOWN:
        return cleaned
    if cleaned.replace("_", "").isalnum() and cleaned[0].isalpha():
        return cleaned
    return f"`{cleaned}`"


def qualify_table(endpoint: dict[str, Any] | None, fallback: str = "", catalog: str = "main") -> str:
    endpoint = endpoint or {}
    table = str(endpoint.get("table") or "").strip()
    if table and table != UNKNOWN and "." in table:
        return ".".join(quote_ident(part) for part in table.split(".") if part)
    database = str(endpoint.get("database") or "").strip()
    schema = str(endpoint.get("schema") or "").strip()
    if table and table != UNKNOWN:
        parts = [part for part in (database, schema, table) if part and part != UNKNOWN]
        if len(parts) == 3:
            return ".".join(quote_ident(part) for part in parts)
        if len(parts) == 2:
            return f"{quote_ident(catalog)}.{quote_ident(parts[0])}.{quote_ident(parts[1])}"
        if fallback:
            return fallback
        return f"{quote_ident(catalog)}.{quote_ident(table)}"
    return fallback


def _pk_columns(spec: dict[str, Any]) -> list[str]:
    raw = str(spec.get("primary_key") or "").strip()
    return [part.strip() for part in raw.split(",") if part.strip()]


def _source_column_for_target(mappings: list[dict[str, Any]], target_column: str) -> str:
    wanted = target_column.lower()
    for item in mappings:
        column = str((item.get("target") or {}).get("column") or "")
        if column.lower() == wanted:
            source = str((item.get("source") or {}).get("column") or "")
            if source and source != UNKNOWN:
                return source
    return target_column


def _rewrite_logic(logic: str, source_column: str, alias: str = "s") -> str | None:
    text = (logic or "").strip()
    if not text or text.upper() in {UNKNOWN, "DIRECT", "1:1", "ONE TO ONE"}:
        return f"{alias}.{quote_ident(source_column)}"
    if not source_column or source_column == UNKNOWN:
        return None
    pattern = re.compile(rf"(?<![.\w]){re.escape(source_column)}(?!\w)", re.IGNORECASE)
    if not pattern.search(text):
        return None
    return pattern.sub(f"{alias}.{quote_ident(source_column)}", text)


def _join_clause(spec: dict[str, Any], mappings: list[dict[str, Any]]) -> str | None:
    keys = _pk_columns(spec)
    if not keys:
        return None
    parts: list[str] = []
    for target_col in keys:
        source_col = _source_column_for_target(mappings, target_col)
        parts.append(f"s.{quote_ident(source_col)} = t.{quote_ident(target_col)}")
    return " AND ".join(parts)


def _template_sql(item: dict[str, Any], spec: dict[str, Any], mappings: list[dict[str, Any]]) -> str:
    rule_id = item["rule_id"]
    source_table = item.get("source_table") or ""
    target_table = item.get("target_table") or ""
    source_column = item.get("source_column") or ""
    target_column = item.get("target_column") or ""
    logic = item.get("transformation_logic") or ""
    join_on = _join_clause(spec, mappings)

    if rule_id == "VR02" and target_table and target_column and target_column != UNKNOWN:
        return (
            f"SELECT t.{quote_ident(target_column)} AS null_value\n"
            f"FROM {target_table} t\n"
            f"WHERE t.{quote_ident(target_column)} IS NULL"
        )

    if rule_id == "VR03" and target_table and target_column and target_column != UNKNOWN:
        return (
            f"SELECT t.{quote_ident(target_column)} AS duplicate_key, COUNT(*) AS duplicate_count\n"
            f"FROM {target_table} t\n"
            f"GROUP BY t.{quote_ident(target_column)}\n"
            f"HAVING COUNT(*) > 1"
        )

    if rule_id == "VR05" and target_table and target_column:
        match = _VARCHAR_LEN.search(str(item.get("target_data_type") or ""))
        if match:
            limit = match.group(1)
            return (
                f"SELECT t.{quote_ident(target_column)} AS value, LENGTH(CAST(t.{quote_ident(target_column)} AS STRING)) AS actual_length\n"
                f"FROM {target_table} t\n"
                f"WHERE t.{quote_ident(target_column)} IS NOT NULL\n"
                f"  AND LENGTH(CAST(t.{quote_ident(target_column)} AS STRING)) > {limit}"
            )

    if rule_id in {"VR01", "VR20"} and source_table and target_table:
        if join_on:
            return (
                "SELECT 'source_not_in_target' AS mismatch_type, s.*\n"
                f"FROM {source_table} s\n"
                f"LEFT JOIN {target_table} t ON {join_on}\n"
                f"WHERE t.{quote_ident(_pk_columns(spec)[0])} IS NULL\n"
                "UNION ALL\n"
                "SELECT 'target_not_in_source' AS mismatch_type, t.*\n"
                f"FROM {target_table} t\n"
                f"LEFT JOIN {source_table} s ON {join_on}\n"
                f"WHERE s.{quote_ident(_source_column_for_target(mappings, _pk_columns(spec)[0]))} IS NULL"
            )
        return (
            "SELECT s.source_count, t.target_count\n"
            f"FROM (SELECT COUNT(*) AS source_count FROM {source_table}) s\n"
            f"CROSS JOIN (SELECT COUNT(*) AS target_count FROM {target_table}) t\n"
            "WHERE s.source_count <> t.target_count"
        )

    if rule_id == "VR21" and source_table and target_table:
        inc = str(spec.get("incremental_column") or "").strip()
        watermark = str(spec.get("watermark_column") or inc).strip()
        if inc:
            if join_on:
                return (
                    f"SELECT s.*\nFROM {source_table} s\n"
                    f"WHERE s.{quote_ident(inc)} > '${{last_watermark_ts}}'\n"
                    f"  AND NOT EXISTS (\n"
                    f"    SELECT 1 FROM {target_table} t WHERE {join_on}\n"
                    f"  )"
                )
            return (
                f"SELECT s.*\nFROM {source_table} s\n"
                f"WHERE s.{quote_ident(inc)} > '${{last_watermark_ts}}'"
            )
        if watermark:
            return (
                f"SELECT t.*\nFROM {target_table} t\n"
                f"WHERE t.{quote_ident(watermark)} IS NULL"
            )

    if (
        rule_id in {"VR10", "VR11", "VR12", "VR13", "VR14", "VR18"}
        and source_table
        and target_table
        and source_column not in {"", UNKNOWN}
        and target_column not in {"", UNKNOWN}
        and join_on
    ):
        expr = _rewrite_logic(logic, source_column)
        if expr:
            return (
                f"SELECT s.{quote_ident(source_column)} AS source_value, "
                f"t.{quote_ident(target_column)} AS target_value, "
                f"{expr} AS expected_target_value\n"
                f"FROM {source_table} s\n"
                f"JOIN {target_table} t ON {join_on}\n"
                f"WHERE NOT (({expr}) <=> t.{quote_ident(target_column)})"
            )

    return ""


def compact_mapping_context(mapping_analysis: dict[str, Any] | None) -> dict[str, Any]:
    analysis = mapping_analysis or {}
    mappings = list(analysis.get("mappings") or [])
    high_risk = [
        {
            "mapping_id": item.get("mapping_id"),
            "source_column": (item.get("source") or {}).get("column"),
            "target_column": (item.get("target") or {}).get("column"),
            "transformation": (item.get("transformation") or {}).get("type"),
            "logic": (item.get("transformation") or {}).get("logic"),
            "risk": item.get("risk"),
            "rules": [rule.get("rule_id") for rule in (item.get("validation_rules") or [])],
            "gaps": item.get("gaps") or [],
        }
        for item in mappings
        if item.get("risk") in {"High", "Very High"}
    ]
    return {
        "column_mappings": len(mappings),
        "high_risk_count": analysis.get("high_risk_count", len(high_risk)),
        "gap_count": analysis.get("gap_count", 0),
        "requires_review": analysis.get("requires_review", False),
        "summary_gaps": (analysis.get("summary_gaps") or [])[:25],
        "load_type_rules": analysis.get("load_type_rules") or [],
        "high_risk_mappings": high_risk[:20],
    }


def build_sql_test_plan(
    mapping_analysis: dict[str, Any] | None,
    etl_spec: dict[str, Any] | None,
    *,
    catalog: str = "main",
) -> list[dict[str, Any]]:
    analysis = mapping_analysis or {}
    spec = etl_spec or {}
    mappings = list(analysis.get("mappings") or [])
    if not mappings and not analysis.get("load_type_rules"):
        return []

    fallback_source = str(spec.get("source_table") or "")
    fallback_target = str(spec.get("target_table") or "")
    plan: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    existence_pairs: set[tuple[str, str]] = set()

    def add_item(
        *,
        mapping_id: str,
        rule: dict[str, Any],
        source: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
        transformation: dict[str, Any] | None = None,
        risk: str = "",
        gaps: list[str] | None = None,
    ) -> None:
        rule_id = str(rule.get("rule_id") or "")
        if not rule_id:
            return
        key = (mapping_id, rule_id)
        if key in seen:
            return
        source_table = qualify_table(source, fallback_source, catalog)
        target_table = qualify_table(target, fallback_target, catalog)
        if rule_id in {"VR01", "VR20"}:
            pair = (source_table, target_table)
            if pair in existence_pairs:
                return
            existence_pairs.add(pair)
        seen.add(key)
        source_column = str((source or {}).get("column") or "")
        target_column = str((target or {}).get("column") or "")
        item = {
            "mapping_id": mapping_id,
            "rule_id": rule_id,
            "rule_type": rule.get("type") or "",
            "priority": rule.get("priority") or "Medium",
            "risk": risk,
            "gaps": list(gaps or []),
            "source_table": source_table,
            "target_table": target_table,
            "source_column": source_column if source_column != UNKNOWN else "",
            "target_column": target_column if target_column != UNKNOWN else "",
            "source_data_type": str((source or {}).get("data_type") or ""),
            "target_data_type": str((target or {}).get("data_type") or ""),
            "transformation_type": str((transformation or {}).get("type") or ""),
            "transformation_logic": str((transformation or {}).get("logic") or ""),
            "what_to_test": rule.get("description") or "",
            "validation_type": RULE_VALIDATION_TYPE.get(rule_id, "Transformation"),
            "test_scenario": rule.get("description") or f"{mapping_id} {rule_id}",
            "expected_result": "0 rows returned (no validation failures).",
            "sql_query": "",
        }
        item["sql_query"] = _template_sql(item, spec, mappings)
        plan.append(item)

    for mapping in mappings:
        for rule in mapping.get("validation_rules") or []:
            add_item(
                mapping_id=str(mapping.get("mapping_id") or ""),
                rule=rule,
                source=mapping.get("source") or {},
                target=mapping.get("target") or {},
                transformation=mapping.get("transformation") or {},
                risk=str(mapping.get("risk") or ""),
                gaps=list(mapping.get("gaps") or []),
            )

    for rule in analysis.get("load_type_rules") or []:
        add_item(
            mapping_id="LOAD",
            rule=rule,
            source={"table": fallback_source},
            target={"table": fallback_target},
            risk="Medium",
        )

    return plan


def plan_for_llm(plan: list[dict[str, Any]], *, limit: int = LLM_PLAN_LIMIT) -> list[dict[str, Any]]:
    def sort_key(item: dict[str, Any]) -> tuple[int, int, int, str]:
        needs_llm = 0 if not item.get("sql_query") else 1
        risk_rank = 0 if item.get("risk") in {"Very High", "High"} else 1
        priority_rank = 0 if str(item.get("priority") or "").lower() == "high" else 1
        return (needs_llm, risk_rank, priority_rank, item.get("mapping_id") or "")

    ordered = sorted(plan, key=sort_key)
    compact = []
    for item in ordered[:limit]:
        compact.append(
            {
                "mapping_id": item.get("mapping_id"),
                "rule_id": item.get("rule_id"),
                "priority": item.get("priority"),
                "risk": item.get("risk"),
                "validation_type": item.get("validation_type"),
                "what_to_test": item.get("what_to_test"),
                "source_table": item.get("source_table"),
                "target_table": item.get("target_table"),
                "source_column": item.get("source_column"),
                "target_column": item.get("target_column"),
                "transformation_type": item.get("transformation_type"),
                "transformation_logic": item.get("transformation_logic"),
                "gaps": item.get("gaps") or [],
                "draft_sql": item.get("sql_query") or "",
            }
        )
    return compact


def merge_plan_with_llm_tests(plan: list[dict[str, Any]], llm_tests: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for test in llm_tests or []:
        key = (str(test.get("mapping_id") or ""), str(test.get("rule_id") or ""))
        if not (key[0] or key[1]):
            continue
        sql = str(test.get("sql_query") or "").strip()
        existing = by_key.get(key)
        if existing and is_select_only(str(existing.get("sql_query") or "")):
            continue
        if sql and is_select_only(sql):
            by_key[key] = test
        elif key not in by_key:
            by_key[key] = test

    merged: list[dict[str, Any]] = []
    missing: list[str] = []
    for index, item in enumerate(plan, start=1):
        key = (str(item.get("mapping_id") or ""), str(item.get("rule_id") or ""))
        llm = by_key.get(key) or {}
        sql = str(llm.get("sql_query") or "").strip()
        if sql and not is_select_only(sql):
            sql = ""
        if not sql:
            sql = str(item.get("sql_query") or "").strip()
        test = {
            "test_id": f"QA-ETL-{index:03d}",
            "test_scenario": str(llm.get("test_scenario") or item.get("test_scenario") or ""),
            "validation_type": str(llm.get("validation_type") or item.get("validation_type") or ""),
            "sql_query": sql,
            "expected_result": str(llm.get("expected_result") or item.get("expected_result") or ""),
            "priority": str(item.get("priority") or llm.get("priority") or "Medium"),
            "mapping_id": item.get("mapping_id") or "",
            "rule_id": item.get("rule_id") or "",
            "risk": item.get("risk") or "",
        }
        if not sql:
            missing.append(
                f"{item.get('mapping_id')}/{item.get('rule_id')}: Mapping Agent required this check but no SELECT SQL could be produced."
            )
        merged.append(test)
    return merged, missing
