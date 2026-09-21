from typing import Any

from databricks import sql

from src.config import DatabricksSettings, get_databricks_settings

FORBIDDEN_KEYWORDS = (
    "DELETE",
    "UPDATE",
    "DROP",
    "TRUNCATE",
    "ALTER",
    "INSERT",
    "MERGE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "COPY",
    "PUT",
    "REMOVE",
)


def _assert_select_only(query: str) -> None:
    stripped = query.strip().rstrip(";").strip()
    upper = stripped.upper()
    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        raise ValueError("ADB execution allows SELECT / WITH queries only.")
    for keyword in FORBIDDEN_KEYWORDS:
        if f" {keyword} " in f" {upper} ":
            raise ValueError(f"ADB execution blocked forbidden keyword: {keyword}")


def _serialize_row(columns: list[str], row: tuple[Any, ...]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name, value in zip(columns, row):
        payload[name] = value if isinstance(value, (str, int, float, bool)) or value is None else str(value)
    return payload


def execute_select(query: str, settings: DatabricksSettings | None = None) -> dict[str, Any]:
    settings = settings or get_databricks_settings()
    _assert_select_only(query)

    with sql.connect(
        server_hostname=settings.server_hostname,
        http_path=settings.http_path,
        access_token=settings.access_token,
        catalog=settings.catalog or None,
        _socket_timeout=settings.query_timeout_seconds,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in (cursor.description or [])]
            rows = cursor.fetchmany(settings.preview_rows + 1)
            truncated = len(rows) > settings.preview_rows
            preview_rows = rows[: settings.preview_rows]
            return {
                "row_count_preview": len(preview_rows),
                "truncated": truncated,
                "columns": columns,
                "preview": [_serialize_row(columns, row) for row in preview_rows],
            }
