from unittest.mock import patch

from src.agents.kpi_sql_agent import normalize_kpi_sql_queries


def test_normalize_kpi_sql_queries_marks_invalid_as_rejected():
    entries = [
        {
            "kpi_id": "KPI-001",
            "kpi_name": "Bad query",
            "sql_query": "DELETE FROM main.app.orders",
            "expected_result": "0 rows",
        }
    ]
    mock_payload = {
        "global_notes": ["Removed destructive statement."],
        "queries": [
            {
                "kpi_id": "KPI-001",
                "kpi_name": "Bad query",
                "original_sql": entries[0]["sql_query"],
                "normalized_sql": "",
                "expected_result": "0 rows",
                "priority": "High",
                "runnable": False,
                "fixes_applied": [],
                "issues_remaining": ["DELETE statements are not allowed for QA validation."],
            }
        ],
    }

    with patch("src.agents.kpi_sql_agent.invoke_llm_json", return_value=mock_payload):
        result = normalize_kpi_sql_queries(entries)

    assert result["total_count"] == 1
    assert result["runnable_count"] == 0
    assert result["tests"] == []
    assert len(result["rejected_queries"]) == 1


def test_normalize_kpi_sql_queries_accepts_select_only():
    entries = [
        {
            "kpi_id": "KPI-002",
            "kpi_name": "Active users",
            "sql_query": "SELECT COUNT(*) FROM main.analytics.users",
            "expected_result": "0 rows",
        }
    ]
    mock_payload = {
        "global_notes": [],
        "queries": [
            {
                "kpi_id": "KPI-002",
                "kpi_name": "Active users",
                "original_sql": entries[0]["sql_query"],
                "normalized_sql": "SELECT COUNT(*) FROM main.analytics.users LIMIT 1000",
                "expected_result": "0 rows",
                "priority": "High",
                "runnable": True,
                "fixes_applied": ["Added LIMIT for preview safety."],
                "issues_remaining": [],
            }
        ],
    }

    with patch("src.agents.kpi_sql_agent.invoke_llm_json", return_value=mock_payload):
        result = normalize_kpi_sql_queries(entries)

    assert result["runnable_count"] == 1
    assert len(result["tests"]) == 1
    assert "LIMIT 1000" in result["tests"][0]["sql_query"]
