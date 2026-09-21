from typing import Any

from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    step_no: int = 1
    user_action: str = ""
    expected_result: str = ""
    actual_result: str = ""
    status: str = ""

    def to_table_row(self) -> str:
        return (
            f"| {self.step_no} | {self.user_action} | {self.expected_result} | "
            f"{self.actual_result} | {self.status} |"
        )


class StructuredTestCase(BaseModel):
    test_id: str
    title: str = ""
    validation_type: str = ""
    priority: str = "Medium"
    preconditions: list[str] = Field(default_factory=list)
    test_steps: list[str] = Field(default_factory=list)
    expected_result: str = ""
    sql_query: str = ""
    traceability: dict[str, str] = Field(default_factory=dict)

    requirement_id: str = ""
    module: str = ""
    feature: str = ""
    test_scenario: str = ""
    test_case_description: str = ""
    test_data: str = ""
    severity: str = ""
    test_type: str = ""
    positive_negative: str = ""
    automation_candidate: str = ""
    automation_reason: str = ""
    execution_steps: list[ExecutionStep] = Field(default_factory=list)

    @classmethod
    def from_validation_test(
        cls,
        test: dict[str, Any],
        *,
        source_table: str = "",
        target_table: str = "",
        spec_version: str = "",
    ) -> "StructuredTestCase":
        test_id = test.get("test_id", "UNASSIGNED")
        scenario = test.get("test_scenario", "")
        validation_type = test.get("validation_type", "")
        return cls(
            test_id=test_id,
            title=f"{validation_type}: {scenario}"[:250],
            validation_type=validation_type,
            test_type="Data Validation",
            priority=test.get("priority", "Medium"),
            severity="Major",
            positive_negative="Positive",
            automation_candidate="Yes",
            automation_reason="SQL validation is suitable for automated execution on Databricks.",
            test_scenario=scenario,
            test_case_description=f"Validate {validation_type.lower()} between source and target tables.",
            preconditions=[
                f"Source table available: {source_table or 'N/A'}",
                f"Target table available: {target_table or 'N/A'}",
                "Validation SQL reviewed and approved by QA",
            ],
            test_steps=[
                "Execute the validation SQL on Azure Databricks SQL Warehouse.",
                "Review returned rows or counts against the expected result.",
                "Log pass/fail in the QA test management tool.",
            ],
            execution_steps=[
                ExecutionStep(
                    step_no=1,
                    user_action="Execute the validation SQL on Azure Databricks SQL Warehouse.",
                    expected_result="Query runs without error and returns a result set or count.",
                ),
                ExecutionStep(
                    step_no=2,
                    user_action="Compare the query output against the documented expected result.",
                    expected_result=test.get("expected_result", ""),
                ),
                ExecutionStep(
                    step_no=3,
                    user_action="Record pass/fail in the QA test management tool.",
                    expected_result="Test result is logged with evidence attached.",
                ),
            ],
            expected_result=test.get("expected_result", ""),
            sql_query=(test.get("sql_query") or "").strip(),
            traceability={
                "source_table": source_table,
                "target_table": target_table,
                "spec_version": spec_version,
                "validation_type": validation_type,
                "mapping_id": test.get("mapping_id", ""),
                "rule_id": test.get("rule_id", ""),
            },
        )

    @classmethod
    def from_functional_payload(cls, payload: dict[str, Any]) -> "StructuredTestCase":
        steps = [
            ExecutionStep.model_validate(step)
            for step in (payload.get("execution_steps") or [])
        ]
        test_id = payload.get("test_case_id") or payload.get("test_id") or "UNASSIGNED"
        scenario = payload.get("test_scenario") or payload.get("title") or ""
        description = payload.get("test_case_description") or scenario
        return cls(
            test_id=test_id,
            title=scenario[:250] if scenario else description[:250],
            requirement_id=payload.get("requirement_id", ""),
            module=payload.get("module", ""),
            feature=payload.get("feature", ""),
            test_scenario=scenario,
            test_case_description=description,
            preconditions=list(payload.get("preconditions") or []),
            test_data=payload.get("test_data", ""),
            priority=payload.get("priority", "Medium"),
            severity=payload.get("severity", "Major"),
            test_type=payload.get("test_type", "Functional"),
            positive_negative=payload.get("positive_negative", ""),
            automation_candidate=payload.get("automation_candidate", ""),
            automation_reason=payload.get("automation_reason", ""),
            validation_type=payload.get("test_type", "Functional"),
            test_steps=[step.user_action for step in steps if step.user_action],
            execution_steps=steps,
            expected_result=steps[-1].expected_result if steps else payload.get("expected_result", ""),
            traceability={
                "requirement_id": payload.get("requirement_id", ""),
                "module": payload.get("module", ""),
                "feature": payload.get("feature", ""),
            },
        )

    def format_execution_steps_table(self) -> str:
        if not self.execution_steps:
            return "\n".join(self.test_steps)
        header = "| Step No | User Action / Execution Step | Expected Result | Actual Result | Status |"
        separator = "|---|---|---|---|---|"
        rows = [step.to_table_row() for step in self.execution_steps]
        return "\n".join([header, separator, *rows])

    def to_row(self) -> dict[str, Any]:
        return {
            "Test Case ID": self.test_id,
            "Requirement ID": self.requirement_id,
            "Module": self.module,
            "Feature": self.feature,
            "Test Scenario": self.test_scenario or self.title,
            "Test Case Description": self.test_case_description,
            "Preconditions": "\n".join(self.preconditions),
            "Test Data": self.test_data,
            "Priority": self.priority,
            "Severity": self.severity,
            "Test Type": self.test_type or self.validation_type,
            "Positive/Negative": self.positive_negative,
            "Automation Candidate": self.automation_candidate,
            "Automation Reason": self.automation_reason,
            "Execution Steps": self.format_execution_steps_table(),
            "Expected Result": self.expected_result,
            "SQL Query": self.sql_query,
            "Source Table": self.traceability.get("source_table", ""),
            "Target Table": self.traceability.get("target_table", ""),
            "Spec Version": self.traceability.get("spec_version", ""),
            "Mapping ID": self.traceability.get("mapping_id", ""),
            "Rule ID": self.traceability.get("rule_id", ""),
        }
