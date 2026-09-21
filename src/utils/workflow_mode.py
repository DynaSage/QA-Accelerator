from typing import Any

ETL_KEYWORDS = (
    "etl",
    "source table",
    "target table",
    "staging",
    "data warehouse",
    "incremental load",
    "mapping",
    "pipeline",
)

UI_KEYWORDS = (
    "ui",
    "screen",
    "button",
    "login",
    "portal",
    "dashboard",
    "insight studio",
    "page",
    "form",
    "dropdown",
    "modal",
    "navigation",
    "wireframe",
    "mockup",
)


def detect_workflow_mode(
    *,
    requirement_text: str = "",
    requirement_summary: dict[str, Any] | None = None,
    user_stories: list[dict[str, Any]] | None = None,
    has_mapping: bool = False,
) -> str:
    summary = requirement_summary or {}
    combined = requirement_text.lower()
    for story in user_stories or []:
        combined += " " + (story.get("title") or "").lower()
        combined += " " + (story.get("description") or "").lower()
        combined += " " + (story.get("acceptance_criteria") or "").lower()

    has_etl_tables = bool(summary.get("source_table") and summary.get("target_table"))
    has_etl_keywords = any(keyword in combined for keyword in ETL_KEYWORDS)
    has_ui_keywords = any(keyword in combined for keyword in UI_KEYWORDS)

    if has_etl_tables or (has_mapping and has_etl_keywords):
        return "hybrid" if has_ui_keywords else "etl"
    if has_ui_keywords or user_stories:
        return "functional"
    if has_mapping:
        return "etl"
    return "functional"
