import json

from src.config import adb_runtime_context
from src.mapping.analyzer import analyze_mappings
from src.mapping.normalizer import normalize_mapping_rows
from src.models.etl_spec import ETLSpecModel
from src.prompts.mapping_prompts import (
    MAPPING_AGENT_PROMPT,
    MAPPING_AGENT_SYSTEM_PROMPT,
    MAPPING_OUTPUT_PROMPT,
    MAPPING_OUTPUT_SYSTEM_PROMPT,
)
from src.utils.llm_json import invoke_llm_json

PROMPT_MAPPING_LIMIT = 80
PSEUDO_CODE_LIMIT = 12000
_LLM_ROW_FIELDS = (
    "source_table",
    "source_column",
    "source_data_type",
    "transformation",
    "target_data_type",
    "business_rule",
    "nullable",
    "primary_key",
    "notes",
)


def _mappings_for_prompt(canonical_mappings: list[dict], mapping_payload: dict) -> list | dict:
    if len(canonical_mappings) <= PROMPT_MAPPING_LIMIT:
        return canonical_mappings
    by_table: dict[str, list[dict]] = {}
    for item in canonical_mappings:
        table = str((item.get("target") or {}).get("table") or "")
        by_table.setdefault(table, []).append(item)
    samples: list[dict] = []
    for items in by_table.values():
        samples.extend(items[:3])
    return {
        "total_mappings": len(canonical_mappings),
        "entities": mapping_payload.get("stm_entities")
        or [{"target_table": name, "row_count": len(items)} for name, items in by_table.items()],
        "sample_rows_per_entity": samples,
        "note": (
            "Full column mappings were already LLM-enriched and will be attached to the spec. "
            "Do not drop columns. Summarize load type, keys, and rules. "
            "source_to_target_mapping may be partial."
        ),
    }


def mapping_rows_from_canonical(canonical_mappings: list[dict]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in canonical_mappings:
        source = item.get("source") or {}
        target = item.get("target") or {}
        transform = item.get("transformation") or {}
        source_col = str(source.get("column") or "").strip()
        target_col = str(target.get("column") or "").strip()
        if not source_col and not target_col:
            continue
        rows.append(
            {
                "source_column": source_col,
                "target_column": target_col,
                "transformation": str(transform.get("logic") or ""),
            }
        )
    return rows


def merge_llm_mapping_rows(parsed_rows: list[dict], llm_rows: list[dict]) -> list[dict]:
    by_target: dict[str, dict] = {}
    for item in llm_rows:
        key = str(item.get("target_column") or "").strip().lower()
        if key:
            by_target[key] = item
    merged: list[dict] = []
    for row in parsed_rows:
        updated = dict(row)
        overlay = by_target.get(str(row.get("target_column") or "").strip().lower()) or {}
        for field in _LLM_ROW_FIELDS:
            value = str(overlay.get(field) or "").strip()
            if value and value.upper() != "UNKNOWN":
                updated[field] = value
        if overlay.get("target_table") and not updated.get("target_table"):
            updated["target_table"] = str(overlay["target_table"]).strip()
        merged.append(updated)
    return merged


def _logic_for_table(mapping_payload: dict, target_table: str) -> str:
    for item in mapping_payload.get("entity_logic") or []:
        if str(item.get("target_table") or "") == target_table:
            text = str(item.get("pseudo_code") or "")
            if len(text) > PSEUDO_CODE_LIMIT:
                return text[:PSEUDO_CODE_LIMIT] + "\n...[truncated]"
            return text
    return ""


def _llm_mapping_for_entity(target_table: str, rows: list[dict], entity_logic: str) -> dict:
    compact_rows = [
        {
            "source_table": row.get("source_table", ""),
            "source_column": row.get("source_column", ""),
            "transformation": row.get("transformation", ""),
            "target_table": row.get("target_table", ""),
            "target_column": row.get("target_column", ""),
            "notes": row.get("notes", ""),
        }
        for row in rows
    ]
    return invoke_llm_json(
        MAPPING_OUTPUT_PROMPT.format(
            target_table=target_table or "(unscoped)",
            mapping_rows=json.dumps(compact_rows, indent=2),
            entity_logic=entity_logic or "(none)",
        ),
        system_prompt=MAPPING_OUTPUT_SYSTEM_PROMPT,
    )


def enrich_mapping_output_with_llm(mapping_payload: dict) -> dict:
    """Ask the LLM to write mapping output (logic, keys, rules) on top of parsed STM/Excel rows."""
    rows = list(mapping_payload.get("mapping_rows") or [])
    if not rows:
        return mapping_payload

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("target_table") or ""), []).append(row)

    enriched_rows: list[dict] = []
    transformation_rules: list[str] = []
    business_rules: list[str] = []
    entity_summaries: list[dict] = []
    missing: list[str] = list(mapping_payload.get("missing_information") or [])

    for target_table, group in grouped.items():
        try:
            result = _llm_mapping_for_entity(target_table, group, _logic_for_table(mapping_payload, target_table))
        except Exception as exc:
            missing.append(f"LLM mapping output failed for {target_table or 'unscoped'}: {exc}")
            enriched_rows.extend(group)
            continue
        enriched_rows.extend(merge_llm_mapping_rows(group, result.get("mapping_rows") or []))
        transformation_rules.extend(str(rule) for rule in (result.get("transformation_rules") or []) if rule)
        business_rules.extend(str(rule) for rule in (result.get("business_rules") or []) if rule)
        entity_summaries.append(
            {
                "target_table": target_table or result.get("target_table") or "",
                "primary_key": str(result.get("primary_key") or "").strip(),
                "load_type": str(result.get("load_type") or "").strip(),
                "not_null_columns": list(result.get("not_null_columns") or []),
            }
        )
        missing.extend(str(item) for item in (result.get("missing_information") or []) if item)

    payload = dict(mapping_payload)
    payload["mapping_rows"] = enriched_rows
    payload["llm_mapping_output"] = {
        "transformation_rules": list(dict.fromkeys(transformation_rules)),
        "business_rules": list(dict.fromkeys(business_rules)),
        "entities": entity_summaries,
    }
    payload["missing_information"] = list(dict.fromkeys(missing))
    return payload


def apply_canonical_spec(payload: dict, mapping_payload: dict, canonical_mappings: list[dict]) -> dict:
    llm_output = mapping_payload.get("llm_mapping_output") or {}
    entities = llm_output.get("entities") or []
    if mapping_payload.get("source_table") and not str(payload.get("source_table") or "").strip():
        payload["source_table"] = mapping_payload["source_table"]
    if mapping_payload.get("target_table") and not str(payload.get("target_table") or "").strip():
        payload["target_table"] = mapping_payload["target_table"]
    if not str(payload.get("source_table") or "").strip():
        payload["source_table"] = "UNKNOWN"
    if not str(payload.get("target_table") or "").strip():
        payload["target_table"] = "UNKNOWN"
    if not str(payload.get("primary_key") or "").strip():
        entity_keys = [item.get("primary_key") for item in entities if item.get("primary_key")]
        payload["primary_key"] = entity_keys[0] if entity_keys else "UNKNOWN"
        if payload["primary_key"] == "UNKNOWN":
            missing = list(payload.get("missing_information") or [])
            note = "primary_key is UNKNOWN; the mapping document did not name a primary key."
            if note not in missing:
                missing.append(note)
            payload["missing_information"] = missing
    if not (payload.get("transformation_rules") or []) and (llm_output.get("transformation_rules") or []):
        payload["transformation_rules"] = list(llm_output["transformation_rules"])
    if not (payload.get("business_rules") or []) and (llm_output.get("business_rules") or []):
        payload["business_rules"] = list(llm_output["business_rules"])

    canonical_rows = mapping_rows_from_canonical(canonical_mappings)
    llm_rows = payload.get("source_to_target_mapping") or []
    if canonical_rows and len(llm_rows) < len(canonical_rows):
        payload["source_to_target_mapping"] = canonical_rows
    return payload


def build_etl_spec(requirement_analysis: dict, mapping_payload: dict) -> dict:
    mapping_payload = enrich_mapping_output_with_llm(mapping_payload)
    mapping_analysis = analyze_mappings(
        mapping_payload,
        load_type=str((requirement_analysis or {}).get("load_type") or ""),
        incremental_column=str((requirement_analysis or {}).get("incremental_column") or ""),
    )
    canonical_mappings = normalize_mapping_rows(mapping_payload.get("mapping_rows") or [])

    payload = invoke_llm_json(
        MAPPING_AGENT_PROMPT.format(
            requirement_analysis=json.dumps(requirement_analysis, indent=2),
            canonical_mappings=json.dumps(_mappings_for_prompt(canonical_mappings, mapping_payload), indent=2),
            llm_mapping_output=json.dumps(mapping_payload.get("llm_mapping_output") or {}, indent=2),
            mapping_analysis=json.dumps(mapping_analysis, indent=2),
            entity_logic=json.dumps(mapping_payload.get("entity_logic") or [], indent=2),
            adb_context=json.dumps(adb_runtime_context(), indent=2),
        ),
        system_prompt=MAPPING_AGENT_SYSTEM_PROMPT,
    )

    payload = apply_canonical_spec(payload, mapping_payload, canonical_mappings)

    if payload.get("load_type"):
        mapping_analysis = analyze_mappings(
            mapping_payload,
            load_type=str(payload.get("load_type") or ""),
            incremental_column=str(payload.get("incremental_column") or ""),
        )

    missing = list(
        dict.fromkeys(
            (requirement_analysis.get("missing_information") or [])
            + (mapping_payload.get("missing_information") or [])
            + (payload.get("missing_information") or [])
            + (mapping_analysis.get("summary_gaps") or [])
        )
    )
    assumptions = list(
        dict.fromkeys((requirement_analysis.get("assumptions") or []) + (payload.get("assumptions") or []))
    )

    spec_payload = {key: value for key, value in payload.items() if key not in {"missing_information", "assumptions"}}
    spec_payload.setdefault("database_dialect", "Databricks SQL")
    spec_payload.setdefault("catalog", adb_runtime_context()["catalog"])

    validated = ETLSpecModel.model_validate(spec_payload)
    return {
        "etl_spec": validated.to_agent_dict(),
        "missing_information": missing,
        "assumptions": assumptions,
        "mapping_analysis": mapping_analysis,
        "canonical_mappings": canonical_mappings,
        "mapping_rows": mapping_payload.get("mapping_rows") or [],
        "llm_mapping_output": mapping_payload.get("llm_mapping_output") or {},
    }
