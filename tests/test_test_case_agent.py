from src.agents import test_case_agent


def test_generate_test_cases_from_sql_tests_without_requirement_context(monkeypatch):
    monkeypatch.setattr(
        test_case_agent,
        "invoke_llm_json",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("LLM should not be called")),
    )

    state = {
        "etl_spec": {
            "source_table": "main.stg.customer_raw",
            "target_table": "main.dw.dim_customer",
        },
        "spec_version": "1",
        "tests": [
            {
                "test_id": "QA-ETL-001",
                "test_scenario": "Record count validation",
                "validation_type": "Record Count",
                "sql_query": "SELECT 1",
                "expected_result": "0 rows",
                "priority": "High",
            }
        ],
    }
    result = test_case_agent.generate_test_cases(state)
    assert len(result["test_cases"]) == 1
    assert result["test_cases"][0]["test_id"] == "QA-ETL-001"
    assert "Record count validation" in result["test_cases"][0]["test_scenario"]
    assert result["test_cases"][0]["execution_steps"]


def test_generate_functional_test_cases_from_requirement_context(monkeypatch):
    def fake_invoke_llm_json(prompt, *, system_prompt, llm_factory=None, max_retries=2):
        assert "User Story" in prompt or "Description" in prompt
        assert system_prompt
        return {
            "missing_information": [],
            "assumptions": ["UI mockups were not provided."],
            "test_scenario_summary": [
                {
                    "scenario_id": "SC-001",
                    "scenario_name": "Login validation",
                    "test_type": "Functional",
                    "priority": "High",
                    "description": "Validate login workflow",
                }
            ],
            "requirement_traceability_matrix": [
                {
                    "requirement_id": "US-19775",
                    "requirement_text": "User can access Insight Studio",
                    "test_case_ids": ["TC-INS-001"],
                    "coverage_status": "Covered",
                }
            ],
            "test_coverage_matrix": [
                {
                    "test_type": "Functional",
                    "total_cases": 1,
                    "high_priority_cases": 1,
                    "coverage_notes": "Covers primary login flow",
                }
            ],
            "automation_recommendations": [
                {
                    "test_case_id": "TC-INS-001",
                    "automation_candidate": "Yes",
                    "reason": "Stable UI workflow",
                }
            ],
            "test_cases": [
                {
                    "test_case_id": "TC-INS-001",
                    "requirement_id": "US-19775",
                    "module": "Insight Studio",
                    "feature": "Login",
                    "test_scenario": "Valid user login",
                    "test_case_description": "Verify an authorized user can log in",
                    "preconditions": ["User account exists"],
                    "test_data": "valid_user / password",
                    "priority": "High",
                    "severity": "Critical",
                    "test_type": "Functional",
                    "positive_negative": "Positive",
                    "automation_candidate": "Yes",
                    "automation_reason": "Stable UI workflow",
                    "execution_steps": [
                        {
                            "step_no": 1,
                            "user_action": "Open the Insight Studio login page",
                            "expected_result": "Login page displays username and password fields",
                            "actual_result": "",
                            "status": "",
                        },
                        {
                            "step_no": 2,
                            "user_action": "Enter valid credentials and click Sign In",
                            "expected_result": "User lands on the Insight Studio home page",
                            "actual_result": "",
                            "status": "",
                        },
                        {
                            "step_no": 3,
                            "user_action": "Verify the welcome banner",
                            "expected_result": "Welcome message shows the signed-in user name",
                            "actual_result": "",
                            "status": "",
                        },
                    ],
                }
            ],
        }

    monkeypatch.setattr(test_case_agent, "invoke_llm_json", fake_invoke_llm_json)

    state = {
        "requirement_text": "User Story 19775: Insight Studio access",
        "user_stories": [
            {
                "id": 19775,
                "title": "Insight Studio access",
                "description": "As a user, I want to access Insight Studio.",
                "acceptance_criteria": "Given valid credentials, user sees the home page.",
            }
        ],
        "etl_spec": {},
        "tests": [],
    }
    result = test_case_agent.generate_test_cases(state)
    assert len(result["test_cases"]) == 1
    assert result["test_cases"][0]["test_id"] == "TC-INS-001"
    assert result["test_cases"][0]["requirement_id"] == "US-19775"
    assert len(result["test_cases"][0]["execution_steps"]) == 3
    assert result["test_case_artifacts"]["requirement_traceability_matrix"]
