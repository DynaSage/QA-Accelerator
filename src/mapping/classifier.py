from __future__ import annotations

import re

_STRING = re.compile(r"\b(upper|lower|trim|ltrim|rtrim|concat|substring|substr|replace|initcap|lpad|rpad)\b", re.I)
_DATE = re.compile(r"\b(to_date|date_format|dateadd|date_add|datediff|to_timestamp|trunc|add_months)\b", re.I)
_DEFAULT = re.compile(r"\b(coalesce|nvl|ifnull|nvl2|isnull|default)\b", re.I)
_CONDITIONAL = re.compile(r"\b(case|when|then|iff|decode)\b", re.I)
_LOOKUP = re.compile(r"\b(lookup|lkp|reference\s+data)\b", re.I)
_HARDCODE = re.compile(r"\b(hardcoded|hard[\s-]*coded|literal\s+value|constant)\b", re.I)
_SURROGATE = re.compile(r"\b(auto-increment|surrogate|row_number|system generated|max\(existing)\b", re.I)
_JOIN = re.compile(r"\bjoin\b", re.I)
_AGG = re.compile(r"\b(sum|avg|count|min|max|group\s+by|aggregate)\b", re.I)
_SCD = re.compile(r"\b(scd|slowly\s+changing|type\s*[12]|effective_from|effective_to)\b", re.I)
_FILTER = re.compile(r"\b(where|filter|exclude|include\s+only)\b", re.I)
_CAST = re.compile(r"\b(cast|convert|try_cast|::)\b", re.I)
_CALC = re.compile(r"[*/+\-]|quantity|unit_price|amount", re.I)
_DIRECT = re.compile(r"^(direct|1:1|one[\s-]*to[\s-]*one|passthrough|pass[\s-]*through|as[\s-]*is)$", re.I)


def classify_transformation(logic: str) -> str:
    text = (logic or "").strip()
    if not text or text.upper() == "UNKNOWN":
        return "DIRECT"
    if _DIRECT.fullmatch(text):
        return "DIRECT"
    join_count = len(_JOIN.findall(text))
    if join_count >= 2 or (join_count and _LOOKUP.search(text)):
        return "COMPLEX_SQL"
    if _SCD.search(text):
        return "SCD"
    if _LOOKUP.search(text):
        return "LOOKUP"
    if _HARDCODE.search(text):
        return "DEFAULT_VALUE"
    if _SURROGATE.search(text):
        return "CALCULATION"
    if join_count:
        return "JOIN"
    if _AGG.search(text):
        return "AGGREGATION"
    if _CONDITIONAL.search(text):
        return "CONDITIONAL"
    if _DEFAULT.search(text):
        return "DEFAULT_VALUE"
    if _DATE.search(text):
        return "DATE_TRANSFORMATION"
    if _STRING.search(text):
        return "STRING_TRANSFORMATION"
    if _CAST.search(text):
        return "DATATYPE_CONVERSION"
    if _FILTER.search(text) and not _CALC.search(text):
        return "FILTER"
    if _CALC.search(text) and not _DIRECT.fullmatch(text):
        return "CALCULATION"
    return "DIRECT"
