import re

FORBIDDEN_SQL = re.compile(
    r"\b(DELETE|UPDATE|DROP|TRUNCATE|ALTER|INSERT|MERGE|CREATE|GRANT|REVOKE|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)
SQL_PLACEHOLDER = re.compile(r"\$\{[^}]+\}")
SELECT_PREFIX = re.compile(r"^\s*(WITH|SELECT)\b", re.IGNORECASE | re.DOTALL)


def is_select_only(sql: str) -> bool:
    cleaned = (sql or "").strip()
    if not cleaned:
        return False
    if FORBIDDEN_SQL.search(cleaned):
        return False
    return bool(SELECT_PREFIX.search(cleaned))


def has_unresolved_placeholders(sql: str) -> bool:
    return bool(SQL_PLACEHOLDER.search(sql or ""))


def validate_sql_test(test: dict) -> tuple[bool, str]:
    test_id = test.get("test_id", "UNKNOWN")
    sql = (test.get("sql_query") or "").strip()
    if not sql:
        return False, f"{test_id}: empty SQL"
    if not is_select_only(sql):
        return False, f"{test_id}: blocked non-SELECT SQL"
    return True, ""
