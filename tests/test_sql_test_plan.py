from src.mapping.analyzer import analyze_mappings
from src.mapping.sql_test_plan import (
    build_sql_test_plan,
    compact_mapping_context,
    merge_plan_with_llm_tests,
    plan_for_llm,
)
from src.utils.sql_safety import is_select_only


def _sample_analysis():
    rows = [
        {
            "source_table": "main.stg.customer_raw",
            "target_table": "main.dw.dim_customer",
            "source_column": "cust_id",
            "target_column": "customer_id",
            "source_data_type": "BIGINT",
            "target_data_type": "BIGINT",
            "transformation": "DIRECT",
            "business_rule": "Must be unique",
            "nullable": "N",
            "primary_key": "Y",
        },
        {
            "source_table": "main.stg.customer_raw",
            "target_table": "main.dw.dim_customer",
            "source_column": "cust_name",
            "target_column": "customer_name",
            "source_data_type": "VARCHAR(100)",
            "target_data_type": "VARCHAR(100)",
            "transformation": "UPPER(cust_name)",
            "business_rule": "Mandatory",
            "nullable": "N",
            "primary_key": "N",
        },
    ]
    return analyze_mappings({"mapping_rows": rows}, load_type="incremental", incremental_column="updated_at")


def _sample_spec():
    return {
        "catalog": "main",
        "source_table": "main.stg.customer_raw",
        "target_table": "main.dw.dim_customer",
        "primary_key": "customer_id",
        "load_type": "incremental",
        "incremental_column": "updated_at",
    }


def test_sql_plan_uses_mapping_agent_rules():
    analysis = _sample_analysis()
    plan = build_sql_test_plan(analysis, _sample_spec(), catalog="main")
    keys = {(item["mapping_id"], item["rule_id"]) for item in plan}

    assert any(item["rule_id"] == "VR12" and item["mapping_id"] == "MAP-002" for item in plan)
    assert any(item["rule_id"] == "VR02" for item in plan)
    assert ("LOAD", "VR21") in keys
    assert sum(1 for item in plan if item["rule_id"] == "VR01") == 1

    null_test = next(item for item in plan if item["rule_id"] == "VR02" and item["target_column"] == "customer_id")
    assert is_select_only(null_test["sql_query"])
    assert "customer_id" in null_test["sql_query"]
    assert "IS NULL" in null_test["sql_query"]

    transform = next(item for item in plan if item["rule_id"] == "VR12")
    assert "UPPER" in transform["sql_query"]
    assert transform["source_column"] == "cust_name"


def test_merge_prefers_llm_select_and_keeps_mapping_ids():
    analysis = _sample_analysis()
    plan = build_sql_test_plan(analysis, _sample_spec(), catalog="main")
    item = next(row for row in plan if row["rule_id"] == "VR02")
    llm_tests = [
        {
            "mapping_id": item["mapping_id"],
            "rule_id": "VR02",
            "sql_query": "SELECT t.customer_id FROM main.dw.dim_customer t WHERE t.customer_id IS NULL LIMIT 100",
            "test_scenario": "LLM null check",
            "expected_result": "0 rows",
        },
        {
            "mapping_id": item["mapping_id"],
            "rule_id": "VR02",
            "sql_query": "DELETE FROM main.dw.dim_customer",
        },
    ]
    tests, missing = merge_plan_with_llm_tests([item], llm_tests)
    assert len(tests) == 1
    assert tests[0]["mapping_id"] == item["mapping_id"]
    assert tests[0]["rule_id"] == "VR02"
    assert "LIMIT 100" in tests[0]["sql_query"]
    assert tests[0]["test_id"] == "QA-ETL-001"
    assert missing == []


def test_merge_falls_back_to_mapping_template_when_llm_omits_sql():
    analysis = _sample_analysis()
    plan = build_sql_test_plan(analysis, _sample_spec(), catalog="main")
    item = next(row for row in plan if row["sql_query"] and row["rule_id"] == "VR03")
    tests, missing = merge_plan_with_llm_tests([item], [])
    assert tests[0]["sql_query"] == item["sql_query"]
    assert "HAVING COUNT(*) > 1" in tests[0]["sql_query"]
    assert missing == []


def test_compact_mapping_context_and_llm_plan_are_bounded():
    analysis = _sample_analysis()
    context = compact_mapping_context(analysis)
    assert context["column_mappings"] == 2
    assert "load_type_rules" in context
    plan = build_sql_test_plan(analysis, _sample_spec())
    compact = plan_for_llm(plan, limit=3)
    assert len(compact) <= 3
    assert all("what_to_test" in item for item in compact)
