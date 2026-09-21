from src.utils.sql_safety import has_unresolved_placeholders, is_select_only, validate_sql_test


def test_is_select_only_accepts_select():
    assert is_select_only("SELECT 1")


def test_is_select_only_accepts_with_clause():
    assert is_select_only("WITH cte AS (SELECT 1 AS x) SELECT * FROM cte")


def test_is_select_only_rejects_delete():
    assert not is_select_only("DELETE FROM main.dw.dim_customer")


def test_validate_sql_test_rejects_empty_sql():
    ok, reason = validate_sql_test({"test_id": "QA-ETL-001", "sql_query": ""})
    assert not ok
    assert "empty SQL" in reason


def test_has_unresolved_placeholders():
    assert has_unresolved_placeholders("SELECT * FROM t WHERE updated_at > '${last_watermark_ts}'")
