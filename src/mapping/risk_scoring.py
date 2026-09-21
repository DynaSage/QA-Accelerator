from __future__ import annotations

RISK_BY_TYPE: dict[str, str] = {
    "DIRECT": "Low",
    "STRING_TRANSFORMATION": "Low",
    "DATE_TRANSFORMATION": "Low",
    "DEFAULT_VALUE": "Medium",
    "CONDITIONAL": "Medium",
    "FILTER": "Medium",
    "CALCULATION": "High",
    "DATATYPE_CONVERSION": "High",
    "LOOKUP": "High",
    "JOIN": "High",
    "AGGREGATION": "High",
    "SCD": "High",
    "COMPLEX_SQL": "Very High",
}

_ORDER = ["Low", "Medium", "High", "Very High"]


def _bump(level: str, steps: int = 1) -> str:
    index = min(len(_ORDER) - 1, max(0, _ORDER.index(level) + steps))
    return _ORDER[index]


def score_risk(
    transform_type: str,
    *,
    gaps: list[str] | None = None,
    business_rule: str = "",
    primary_key: str = "",
) -> str:
    level = RISK_BY_TYPE.get(transform_type, "Medium")
    gap_text = " ".join(gaps or []).lower()
    if "datatype mismatch" in gap_text or "complex" in gap_text:
        level = _bump(level)
    if any(item.startswith("missing") for item in (gaps or [])):
        if level == "Low":
            level = "Medium"
    business = (business_rule or "").lower()
    pk = (primary_key or "").lower()
    if pk in {"y", "yes", "true", "1", "pk"} or "unique" in business or "mandatory" in business:
        if level == "Low":
            level = "Medium"
    return level


def requires_review(risk: str, gaps: list[str]) -> bool:
    return risk in {"High", "Very High"} or bool(gaps)
