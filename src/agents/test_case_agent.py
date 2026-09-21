import json
from typing import Any

from src.models.test_case import StructuredTestCase
from src.prompts.test_case_prompts import TEST_CASE_AGENT_SYSTEM_PROMPT, TEST_CASE_GENERATION_PROMPT
from src.graph.state import AgentState
from src.utils.llm_json import invoke_llm_json


def _has_requirement_context(state: AgentState) -> bool:
    if (state.get("requirement_text") or "").strip():
        return True
    if state.get("user_stories"):
        return True
    summary = state.get("requirement_summary") or {}
    return bool((summary.get("requirement_summary") or "").strip())


def _format_user_story(state: AgentState) -> str:
    if (state.get("requirement_text") or "").strip():
        return state["requirement_text"].strip()

    stories = state.get("user_stories") or []
    if not stories:
        summary = state.get("requirement_summary") or {}
        return (summary.get("requirement_summary") or "").strip()

    lines: list[str] = []
    for story in stories:
        lines.extend(
            [
                f"User Story ID: {story.get('id', 'N/A')}",
                f"Title: {story.get('title', '')}",
                f"Type: {story.get('work_item_type', '')}",
                f"State: {story.get('state', '')}",
                "",
                "Description:",
                story.get("description") or "No description provided.",
                "",
            ]
        )
    return "\n".join(lines).strip()


def _format_acceptance_criteria(state: AgentState) -> str:
    stories = state.get("user_stories") or []
    if stories:
        blocks: list[str] = []
        for story in stories:
            ac = (story.get("acceptance_criteria") or "").strip()
            blocks.append(
                f"Story {story.get('id', 'N/A')} — {story.get('title', '')}\n{ac or 'No acceptance criteria provided.'}"
            )
        return "\n\n".join(blocks)

    text = (state.get("requirement_text") or "").strip()
    if "### Acceptance Criteria" in text:
        return text.split("### Acceptance Criteria", 1)[1].strip()
    return "No explicit acceptance criteria provided. Derive test scope from the user story description."


def _format_business_rules(state: AgentState) -> str:
    summary = state.get("requirement_summary") or {}
    spec = state.get("etl_spec") or {}
    rules = list(summary.get("business_rules") or []) + list(spec.get("business_rules") or [])
    if not rules:
        return "No business rules explicitly provided."
    return "\n".join(f"- {rule}" for rule in rules)


def _format_ui_context(state: AgentState) -> str:
    ui_context = (state.get("ui_context") or "").strip()
    if ui_context:
        return ui_context
    return (
        "No UI screenshots or mockups were provided. "
        "Derive UI-related test cases from textual descriptions in the user story and acceptance criteria. "
        "List any UI assumptions in missing_information."
    )


def _format_technical_context(state: AgentState) -> str:
    spec = state.get("etl_spec") or {}
    tests = state.get("tests") or []
    if not spec and not tests:
        return "No additional technical or ETL context provided."

    lines = ["ETL / Technical Context:"]
    if spec:
        lines.extend(
            [
                f"- Source table: {spec.get('source_table') or 'N/A'}",
                f"- Target table: {spec.get('target_table') or 'N/A'}",
                f"- Primary key: {spec.get('primary_key') or 'N/A'}",
                f"- Load type: {spec.get('load_type') or 'N/A'}",
            ]
        )
    if tests:
        lines.append("")
        lines.append("Existing SQL validation tests (reference only — do not duplicate):")
        for test in tests[:10]:
            lines.append(
                f"- {test.get('test_id')}: {test.get('test_scenario')} ({test.get('validation_type')})"
            )
        if len(tests) > 10:
            lines.append(f"- ... and {len(tests) - 10} more SQL tests")
    return "\n".join(lines)


def _format_traceability_hints(state: AgentState) -> str:
    hints: list[str] = []
    for story in state.get("user_stories") or []:
        hints.append(f"US-{story.get('id')}: {story.get('title', '')}")
    if not hints and state.get("spec_id"):
        hints.append(f"Spec ID: {state.get('spec_id')}")
    if not hints and state.get("spec_name"):
        hints.append(f"Spec name: {state.get('spec_name')}")
    return "\n".join(hints) if hints else "Use requirement IDs from the user story document."


def _generate_functional_test_cases(state: AgentState) -> dict[str, Any]:
    prompt = TEST_CASE_GENERATION_PROMPT.format(
        user_story=_format_user_story(state),
        acceptance_criteria=_format_acceptance_criteria(state),
        business_rules=_format_business_rules(state),
        ui_context=_format_ui_context(state),
        technical_context=_format_technical_context(state),
        traceability_hints=_format_traceability_hints(state),
    )
    payload = invoke_llm_json(prompt, system_prompt=TEST_CASE_AGENT_SYSTEM_PROMPT)
    test_cases = [
        StructuredTestCase.from_functional_payload(case).model_dump()
        for case in (payload.get("test_cases") or [])
    ]
    return {
        "test_cases": test_cases,
        "test_case_artifacts": {
            "test_scenario_summary": payload.get("test_scenario_summary") or [],
            "requirement_traceability_matrix": payload.get("requirement_traceability_matrix") or [],
            "test_coverage_matrix": payload.get("test_coverage_matrix") or [],
            "automation_recommendations": payload.get("automation_recommendations") or [],
            "missing_information": payload.get("missing_information") or [],
            "assumptions": payload.get("assumptions") or [],
        },
    }


def _generate_etl_test_cases(state: AgentState) -> list[dict[str, Any]]:
    spec = state.get("etl_spec") or {}
    spec_version = state.get("spec_version") or ""
    source_table = spec.get("source_table", "")
    target_table = spec.get("target_table", "")

    return [
        StructuredTestCase.from_validation_test(
            test,
            source_table=source_table,
            target_table=target_table,
            spec_version=spec_version,
        ).model_dump()
        for test in (state.get("tests") or [])
    ]


def generate_test_cases(state: AgentState) -> AgentState:
    result: dict[str, Any] = {}

    if _has_requirement_context(state):
        generated = _generate_functional_test_cases(state)
        result["test_cases"] = generated["test_cases"]
        result["test_case_artifacts"] = generated["test_case_artifacts"]
        artifacts = generated["test_case_artifacts"]
        if artifacts.get("missing_information"):
            existing = list(state.get("missing_information") or [])
            result["missing_information"] = existing + artifacts["missing_information"]
        if artifacts.get("assumptions"):
            existing = list(state.get("assumptions") or [])
            result["assumptions"] = existing + artifacts["assumptions"]
    else:
        result["test_cases"] = _generate_etl_test_cases(state)

    etl_cases = _generate_etl_test_cases(state)
    if _has_requirement_context(state) and etl_cases:
        existing_ids = {case["test_id"] for case in result.get("test_cases") or []}
        result["test_cases"] = (result.get("test_cases") or []) + [
            case for case in etl_cases if case["test_id"] not in existing_ids
        ]

    return result
