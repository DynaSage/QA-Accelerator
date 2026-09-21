from typing import Any, TypedDict


class QueryExecution(TypedDict, total=False):
    test_id: str
    status: str
    row_count_preview: int
    truncated: bool
    columns: list[str]
    preview: list[dict[str, Any]]
    error: str


class ETLSpec(TypedDict, total=False):
    database_dialect: str
    catalog: str
    source_table: str
    target_table: str
    primary_key: str
    load_type: str
    incremental_column: str
    watermark_column: str
    source_to_target_mapping: list[dict[str, Any]]
    transformation_rules: list[str]
    business_rules: list[str]
    not_null_columns: list[str]
    additional_notes: str


class ValidationTest(TypedDict):
    test_id: str
    test_scenario: str
    validation_type: str
    sql_query: str
    expected_result: str
    priority: str
    mapping_id: str
    rule_id: str


class StructuredTestCase(TypedDict, total=False):
    test_id: str
    title: str
    validation_type: str
    priority: str
    preconditions: list[str]
    test_steps: list[str]
    expected_result: str
    sql_query: str
    traceability: dict[str, str]


class AgentState(TypedDict, total=False):
    etl_spec: ETLSpec
    execute_queries: bool
    requirement_text: str
    requirement_summary: dict[str, Any]
    user_stories: list[dict[str, Any]]
    ui_context: str
    requirement_analysis: dict[str, Any]
    mapping_payload: dict[str, Any]
    mapping_analysis: dict[str, Any]
    draft_id: str
    spec_id: str
    spec_name: str
    spec_version: str
    run_id: str
    analyst_notes: str
    missing_information: list[str]
    assumptions: list[str]
    validation_plan: list[str]
    tests: list[ValidationTest]
    test_cases: list[StructuredTestCase]
    test_case_artifacts: dict[str, Any]
    kpi_logic_entries: list[dict[str, Any]]
    kpi_normalization: dict[str, Any]
    rejected_queries: list[str]
    execution_results: list[QueryExecution]
    execution_summary: dict[str, int]
    qa_report: str
    error: str
