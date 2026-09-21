from __future__ import annotations

import re

from src.models.mapping_analysis import UNKNOWN

_VARCHAR = re.compile(r"(?:varchar|char)\s*\(\s*(\d+)\s*\)", re.I)
_NUMERIC = re.compile(r"(?:decimal|numeric|number)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", re.I)
_BASE_TYPE = re.compile(r"^[a-z]+", re.I)

_NUMERIC_FAMILY = {"int", "integer", "bigint", "smallint", "tinyint", "decimal", "numeric", "number", "double", "float"}
_STRING_FAMILY = {"varchar", "char", "string", "text"}
_DATE_FAMILY = {"date", "timestamp", "datetime"}


def _family(base: str) -> str:
    if base in _NUMERIC_FAMILY:
        return "numeric"
    if base in _STRING_FAMILY:
        return "string"
    if base in _DATE_FAMILY:
        return "datetime"
    return base


def _blank(value: str) -> bool:
    return not (value or "").strip() or (value or "").strip().upper() == UNKNOWN


def _base(data_type: str) -> str:
    match = _BASE_TYPE.match((data_type or "").strip())
    return match.group(0).lower() if match else ""


def _length(data_type: str) -> int | None:
    match = _VARCHAR.search(data_type or "")
    return int(match.group(1)) if match else None


def detect_gaps(
    *,
    source_table: str,
    source_column: str,
    target_table: str,
    target_column: str,
    transformation: str,
    transform_type: str,
    business_rule: str,
    source_data_type: str,
    target_data_type: str,
    load_type: str = "",
    incremental_column: str = "",
) -> list[str]:
    gaps: list[str] = []
    if _blank(source_table):
        gaps.append("missing source table")
    if _blank(source_column):
        gaps.append("missing source column")
    if _blank(target_table):
        gaps.append("missing target table")
    if _blank(target_column):
        gaps.append("missing target column")
    if _blank(transformation) or transformation.strip().upper() == UNKNOWN:
        gaps.append("missing transformation logic")
    if transform_type in {"LOOKUP", "JOIN", "COMPLEX_SQL"} and "join" not in (transformation or "").lower() and "lookup" not in (transformation or "").lower():
        gaps.append("missing join condition")
    if _blank(business_rule):
        gaps.append("missing business rule")
    if _blank(source_data_type):
        gaps.append("missing source datatype")
    if _blank(target_data_type):
        gaps.append("missing target datatype")

    src_base = _base(source_data_type)
    tgt_base = _base(target_data_type)
    if src_base and tgt_base:
        src_fam = _family(src_base)
        tgt_fam = _family(tgt_base)
        if src_fam != tgt_fam:
            gaps.append(f"potential source-target datatype mismatch ({source_data_type} → {target_data_type})")

    src_len = _length(source_data_type)
    tgt_len = _length(target_data_type)
    if src_len and tgt_len and tgt_len < src_len:
        gaps.append(f"target length/precision risk (source {src_len} > target {tgt_len})")

    src_num = _NUMERIC.search(source_data_type or "")
    tgt_num = _NUMERIC.search(target_data_type or "")
    if src_num and tgt_num:
        if int(tgt_num.group(1)) < int(src_num.group(1)) or int(tgt_num.group(2)) < int(src_num.group(2)):
            gaps.append("target length/precision risk (numeric precision/scale reduced)")

    if transform_type == "COMPLEX_SQL":
        gaps.append("ambiguous or overly complex transformation")

    load = (load_type or "").strip().lower()
    if load in {"incremental", "cdc"} and _blank(incremental_column):
        gaps.append("missing incremental/CDC criteria")

    return list(dict.fromkeys(gaps))
