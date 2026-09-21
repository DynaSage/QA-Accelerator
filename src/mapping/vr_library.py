"""Column-level validation rule library (VR01–VR26) from the Mapping Agent CoE guide."""

from __future__ import annotations

from typing import Any

VR_LIBRARY: dict[str, dict[str, str]] = {
    "VR01": {"type": "RECORD", "title": "Record Existence", "priority": "High"},
    "VR02": {"type": "NULL", "title": "NULL handling", "priority": "High"},
    "VR03": {"type": "DUPLICATE", "title": "Duplicate / uniqueness", "priority": "High"},
    "VR04": {"type": "DATATYPE", "title": "Data type compatibility", "priority": "Medium"},
    "VR05": {"type": "LENGTH", "title": "Length", "priority": "Medium"},
    "VR06": {"type": "PRECISION", "title": "Precision / scale", "priority": "Medium"},
    "VR07": {"type": "FORMAT", "title": "Format", "priority": "Medium"},
    "VR10": {"type": "TRANSFORMATION", "title": "Direct mapping", "priority": "High"},
    "VR11": {"type": "TRANSFORMATION", "title": "Calculation", "priority": "High"},
    "VR12": {"type": "TRANSFORMATION", "title": "String transformation", "priority": "High"},
    "VR13": {"type": "TRANSFORMATION", "title": "Date transformation", "priority": "High"},
    "VR14": {"type": "TRANSFORMATION", "title": "Conditional logic", "priority": "High"},
    "VR15": {"type": "LOOKUP", "title": "Lookup", "priority": "High"},
    "VR16": {"type": "JOIN", "title": "Join keys and cardinality", "priority": "High"},
    "VR17": {"type": "AGGREGATION", "title": "Aggregation", "priority": "High"},
    "VR18": {"type": "DEFAULT", "title": "Default value", "priority": "Medium"},
    "VR19": {"type": "FILTER", "title": "Filter include/exclude", "priority": "Medium"},
    "VR20": {"type": "LOAD", "title": "Full load", "priority": "Medium"},
    "VR21": {"type": "LOAD", "title": "Incremental load", "priority": "High"},
    "VR22": {"type": "LOAD", "title": "CDC", "priority": "High"},
    "VR23": {"type": "SCD", "title": "SCD Type 1", "priority": "High"},
    "VR24": {"type": "SCD", "title": "SCD Type 2", "priority": "High"},
    "VR25": {"type": "LATE_ARRIVING", "title": "Late arriving data", "priority": "Medium"},
    "VR26": {"type": "REJECT", "title": "Reject records", "priority": "Medium"},
}

TYPE_TO_RULES: dict[str, list[str]] = {
    "DIRECT": ["VR10", "VR02", "VR04", "VR05"],
    "STRING_TRANSFORMATION": ["VR12", "VR02", "VR05"],
    "DATE_TRANSFORMATION": ["VR13", "VR02", "VR07"],
    "DEFAULT_VALUE": ["VR18", "VR02"],
    "CONDITIONAL": ["VR14", "VR02"],
    "CALCULATION": ["VR11", "VR02", "VR06"],
    "DATATYPE_CONVERSION": ["VR04", "VR07", "VR02"],
    "LOOKUP": ["VR15", "VR02", "VR03"],
    "JOIN": ["VR16", "VR03", "VR02"],
    "AGGREGATION": ["VR17", "VR06"],
    "SCD": ["VR23", "VR24", "VR02"],
    "FILTER": ["VR19"],
    "COMPLEX_SQL": ["VR16", "VR15", "VR11", "VR02"],
}


def make_rule(rule_id: str, description: str, *, priority: str | None = None) -> dict[str, str]:
    meta = VR_LIBRARY[rule_id]
    return {
        "rule_id": rule_id,
        "type": meta["type"],
        "description": description,
        "priority": priority or meta["priority"],
    }


def rules_for_mapping(
    *,
    mapping_id: str,
    transform_type: str,
    logic: str,
    source_column: str,
    target_column: str,
    source_type: str,
    target_type: str,
    nullable: str,
    primary_key: str,
    business_rule: str,
) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(rule_id: str, description: str, priority: str | None = None) -> None:
        if rule_id in seen or rule_id not in VR_LIBRARY:
            return
        seen.add(rule_id)
        rules.append(make_rule(rule_id, description, priority=priority))

    add(
        "VR01",
        f"{mapping_id}: expected source records for {source_column} are represented in target {target_column}.",
    )

    for rule_id in TYPE_TO_RULES.get(transform_type, ["VR10", "VR02"]):
        title = VR_LIBRARY[rule_id]["title"]
        add(
            rule_id,
            f"{mapping_id}: {title} — target {target_column} vs source {source_column} using `{logic}`.",
        )

    nullish = (nullable or "").strip().lower()
    if nullish in {"n", "no", "false", "0", "not null", "mandatory"}:
        add(
            "VR02",
            f"{mapping_id}: {target_column} is non-nullable; reject or flag NULL source/target values.",
            "High",
        )

    pkish = (primary_key or "").strip().lower()
    business = (business_rule or "").lower()
    if pkish in {"y", "yes", "true", "1", "pk"} or "unique" in business:
        add(
            "VR03",
            f"{mapping_id}: {target_column} must be unique (primary/business key).",
            "High",
        )

    if source_type and target_type and source_type != "UNKNOWN" and target_type != "UNKNOWN":
        add(
            "VR04",
            f"{mapping_id}: source type {source_type} must be compatible with target type {target_type}.",
        )
        if "varchar" in target_type.lower() or "char" in target_type.lower():
            add("VR05", f"{mapping_id}: target length of {target_type} must hold source {source_type} values.")
        if any(token in target_type.lower() for token in ("decimal", "numeric", "number", "double", "float")):
            add("VR06", f"{mapping_id}: preserve decimal precision/scale from {source_type} to {target_type}.")

    if any(token in business for token in ("format", "date", "email", "pattern", "mask")):
        add("VR07", f"{mapping_id}: {target_column} must match the documented format/business rule.")

    if "reject" in business or "late" in business:
        add("VR26", f"{mapping_id}: rejected records for {target_column} must follow the documented reject path.")
    if "late" in business:
        add("VR25", f"{mapping_id}: late-arriving values for {target_column} must follow the documented rule.")

    return rules


def load_type_rules(load_type: str, incremental_column: str = "") -> list[dict[str, str]]:
    kind = (load_type or "").strip().lower()
    if kind in {"incremental"}:
        extra = f" using {incremental_column}" if incremental_column else ""
        return [make_rule("VR21", f"Validate incremental load watermark/delta{extra}.", priority="High")]
    if kind in {"cdc", "change data capture"}:
        return [make_rule("VR22", "Validate CDC apply (insert/update/delete) against expected change rows.", priority="High")]
    if kind in {"snapshot"}:
        return [make_rule("VR20", "Validate full/snapshot load completeness against source extract.", priority="Medium")]
    return [make_rule("VR20", "Validate full load record existence between source and target.", priority="Medium")]
