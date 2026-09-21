import json
from collections import Counter

from src.config import adb_runtime_context
from src.graph.state import AgentState


def _execution_summary(state: AgentState) -> dict[str, int]:
    counts = Counter(item.get("status", "UNKNOWN") for item in (state.get("execution_results") or []))
    return dict(sorted(counts.items()))


def format_qa_report(state: AgentState) -> AgentState:
    spec = state.get("etl_spec") or {}
    summary = _execution_summary(state)
    lines = [
        "# QA ETL SQL Validation Pack",
        "",
        "## Run Summary",
        f"- Spec ID: {state.get('spec_id') or 'N/A'}",
        f"- Spec name: {state.get('spec_name') or 'N/A'}",
        f"- Spec version: {state.get('spec_version') or 'N/A'}",
        f"- Validation tests generated: {len(state.get('tests') or [])}",
        f"- Structured test cases: {len(state.get('test_cases') or [])}",
    ]
    if summary:
        lines.append(f"- Execution summary: {', '.join(f'{k}: {v}' for k, v in summary.items())}")
    lines.extend(
        [
            "",
            "## Scope",
            f"- Source table: {spec.get('source_table') or 'MISSING'}",
            f"- Target table: {spec.get('target_table') or 'MISSING'}",
            f"- Primary key: {spec.get('primary_key') or 'MISSING'}",
            f"- Load type: {spec.get('load_type') or 'MISSING'}",
            f"- Dialect: {spec.get('database_dialect') or 'Databricks SQL'}",
            f"- Execution platform: Azure Databricks ({adb_runtime_context().get('server_hostname') or 'MISSING HOST'})",
            f"- Catalog: {spec.get('catalog') or adb_runtime_context().get('catalog') or 'MISSING'}",
            "",
            "## Analyst Notes",
            state.get("analyst_notes") or "None",
            "",
            "## Missing Information",
        ]
    )

    missing = state.get("missing_information") or []
    lines.extend([f"- {item}" for item in missing] or ["- None identified"])
    lines.extend(["", "## Assumptions"])
    assumptions = state.get("assumptions") or []
    lines.extend([f"- {item}" for item in assumptions] or ["- None listed"])

    kpi_normalization = state.get("kpi_normalization") or {}
    if kpi_normalization:
        lines.extend(
            [
                "",
                "## KPI Logic Normalization",
                f"- Total developer queries: {kpi_normalization.get('total_count', 0)}",
                f"- Databricks-ready queries: {kpi_normalization.get('runnable_count', 0)}",
                f"- Rejected during normalization: {len(kpi_normalization.get('rejected_queries') or [])}",
            ]
        )
        if kpi_normalization.get("global_notes"):
            lines.append("- Global notes:")
            lines.extend([f"  - {note}" for note in kpi_normalization["global_notes"]])
        for entry in kpi_normalization.get("queries") or []:
            if not entry.get("fixes_applied"):
                continue
            lines.append(
                f"- {entry.get('kpi_id', '')} ({entry.get('kpi_name', '')}): "
                + "; ".join(entry["fixes_applied"])
            )

    mapping_analysis = state.get("mapping_analysis") or {}
    if mapping_analysis.get("mappings"):
        lines.extend(
            [
                "",
                "## Mapping Analysis (VR Coverage)",
                f"- Column mappings: {len(mapping_analysis.get('mappings') or [])}",
                f"- High / very high risk: {mapping_analysis.get('high_risk_count', 0)}",
                f"- Gaps: {mapping_analysis.get('gap_count', 0)}",
                f"- Requires QA review: {'Yes' if mapping_analysis.get('requires_review') else 'No'}",
            ]
        )
        for item in mapping_analysis.get("mappings") or []:
            source = item.get("source") or {}
            target = item.get("target") or {}
            transform = item.get("transformation") or {}
            rule_ids = ", ".join(rule.get("rule_id", "") for rule in (item.get("validation_rules") or []))
            gaps = "; ".join(item.get("gaps") or []) or "None"
            lines.append(
                f"- {item.get('mapping_id')}: {source.get('column')} → {target.get('column')} "
                f"({transform.get('type')}, risk {item.get('risk')}) | rules {rule_ids or 'n/a'} | gaps: {gaps}"
            )

    rejected = state.get("rejected_queries") or []
    if rejected:
        lines.extend(["", "## Blocked Queries"])
        lines.extend([f"- {item}" for item in rejected])

    artifacts = state.get("test_case_artifacts") or {}
    if artifacts.get("test_scenario_summary"):
        lines.extend(["", "## Test Scenario Summary"])
        for item in artifacts["test_scenario_summary"]:
            lines.append(
                f"- {item.get('scenario_id', '')}: {item.get('scenario_name', '')} "
                f"({item.get('test_type', '')}, {item.get('priority', '')})"
            )

    if artifacts.get("requirement_traceability_matrix"):
        lines.extend(["", "## Requirement Traceability Matrix"])
        for item in artifacts["requirement_traceability_matrix"]:
            test_ids = ", ".join(item.get("test_case_ids") or [])
            lines.append(
                f"- {item.get('requirement_id', '')}: {item.get('coverage_status', '')} "
                f"→ {test_ids or 'No linked tests'}"
            )

    if artifacts.get("test_coverage_matrix"):
        lines.extend(["", "## Test Coverage Matrix"])
        for item in artifacts["test_coverage_matrix"]:
            lines.append(
                f"- {item.get('test_type', '')}: {item.get('total_cases', 0)} cases "
                f"({item.get('high_priority_cases', 0)} high priority)"
            )

    if artifacts.get("automation_recommendations"):
        lines.extend(["", "## Automation Recommendations"])
        for item in artifacts["automation_recommendations"]:
            lines.append(
                f"- {item.get('test_case_id', '')}: {item.get('automation_candidate', '')} — "
                f"{item.get('reason', '')}"
            )

    lines.extend(["", "## Structured Test Cases"])
    for case in state.get("test_cases") or []:
        test_type = case.get("test_type") or case.get("validation_type", "")
        lines.extend(
            [
                "",
                f"### {case.get('test_id')} | {test_type}",
                f"- Requirement ID: {case.get('requirement_id') or 'N/A'}",
                f"- Module / Feature: {case.get('module') or 'N/A'} / {case.get('feature') or 'N/A'}",
                f"- Scenario: {case.get('test_scenario') or case.get('title', '')}",
                f"- Description: {case.get('test_case_description') or 'N/A'}",
                f"- Priority / Severity: {case.get('priority', '')} / {case.get('severity') or 'N/A'}",
                f"- Type: {test_type} ({case.get('positive_negative') or 'N/A'})",
                f"- Automation: {case.get('automation_candidate') or 'N/A'}",
                f"- Expected Result: {case.get('expected_result', '')}",
                "- Preconditions:",
                *[f"  - {item}" for item in (case.get("preconditions") or [])],
            ]
        )
        execution_steps = case.get("execution_steps") or []
        if execution_steps:
            lines.append("- Execution Steps:")
            lines.append("")
            lines.append("| Step No | User Action | Expected Result | Actual Result | Status |")
            lines.append("|---|---|---|---|---|")
            for step in execution_steps:
                lines.append(
                    f"| {step.get('step_no', '')} | {step.get('user_action', '')} | "
                    f"{step.get('expected_result', '')} | {step.get('actual_result', '')} | "
                    f"{step.get('status', '')} |"
                )
        else:
            lines.append("- Test Steps:")
            lines.extend([f"  - {item}" for item in (case.get("test_steps") or [])])

    executions = {item.get("test_id"): item for item in (state.get("execution_results") or [])}
    lines.extend(["", "## Validation SQL Tests"])
    for test in state.get("tests") or []:
        test_id = test.get("test_id", "UNASSIGNED")
        execution = executions.get(test_id, {})
        lines.extend(
            [
                "",
                f"### {test_id} | {test.get('validation_type', '')}",
                f"- Test Scenario: {test.get('test_scenario', '')}",
                f"- Mapping ID: {test.get('mapping_id') or 'N/A'}",
                f"- Rule ID: {test.get('rule_id') or 'N/A'}",
                f"- Priority: {test.get('priority', '')}",
                f"- Expected Result: {test.get('expected_result', '')}",
                f"- ADB Execution Status: {execution.get('status', 'NOT RUN')}",
                "- SQL Query:",
                "```sql",
                (test.get("sql_query") or "").strip(),
                "```",
            ]
        )
        if execution.get("error"):
            label = "ADB Note" if execution.get("status") == "SKIPPED" else "ADB Error"
            lines.append(f"- {label}: {execution['error']}")
        elif execution.get("preview") is not None:
            lines.append(f"- Preview row count: {execution.get('row_count_preview', 0)}")
            if execution.get("truncated"):
                lines.append("- Preview truncated: yes (more rows exist on ADB)")
            lines.append("- Preview:")
            lines.append("```json")
            lines.append(json.dumps(execution.get("preview") or [], indent=2, default=str))
            lines.append("```")

    if not state.get("tests"):
        lines.append("\nNo SELECT validation tests were generated. Resolve missing information and rerun.")

    return {"qa_report": "\n".join(lines), "execution_summary": summary}
