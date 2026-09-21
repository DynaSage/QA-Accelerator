from src.agents.reporting_agent import format_qa_report
from src.agents.test_case_agent import generate_test_cases
from src.graph.nodes import execute_on_adb, safety_check
from src.graph.state import AgentState


def run_kpi_and_functional_validation(state: AgentState) -> AgentState:
    """Generate functional test cases, merge KPI SQL tests, safety-check, and optionally execute."""
    result = dict(state)
    result.update(generate_test_cases(result))

    kpi_tests = list(result.get("tests") or [])
    if kpi_tests:
        checked = safety_check({**result, "tests": kpi_tests})
        result["tests"] = checked.get("tests") or []
        rejected = list(result.get("rejected_queries") or [])
        rejected.extend(checked.get("rejected_queries") or [])
        result["rejected_queries"] = rejected

        existing_ids = {case["test_id"] for case in (result.get("test_cases") or [])}
        from src.models.test_case import StructuredTestCase

        for test in result["tests"]:
            if test["test_id"] in existing_ids:
                continue
            case = StructuredTestCase.from_validation_test(
                test,
                source_table=(result.get("etl_spec") or {}).get("source_table", ""),
                target_table=(result.get("etl_spec") or {}).get("target_table", ""),
                spec_version=result.get("spec_version") or "",
            ).model_dump()
            case["requirement_id"] = test.get("kpi_id") or case.get("requirement_id", "")
            case["module"] = test.get("module") or case.get("module", "")
            case["feature"] = test.get("kpi_name") or case.get("feature", "")
            case["test_type"] = "KPI Data Validation"
            result.setdefault("test_cases", []).append(case)

        if result.get("execute_queries"):
            result.update(execute_on_adb(result))
        else:
            result["execution_results"] = [
                {
                    "test_id": test.get("test_id", "UNKNOWN"),
                    "status": "SKIPPED",
                    "error": "ADB execution disabled.",
                }
                for test in result["tests"]
            ]

    result.update(format_qa_report(result))
    return result
