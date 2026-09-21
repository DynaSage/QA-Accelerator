from src.utils.workflow_mode import detect_workflow_mode


def test_detect_functional_mode_for_ui_story():
    mode = detect_workflow_mode(
        requirement_text="As a user I want to login to Insight Studio dashboard and click the Save button.",
        user_stories=[{"id": 19775, "title": "Insight Studio access", "description": "UI screen", "acceptance_criteria": ""}],
        has_mapping=False,
    )
    assert mode == "functional"


def test_detect_etl_mode_with_mapping():
    mode = detect_workflow_mode(
        requirement_text="Load customer data from staging to warehouse.",
        requirement_summary={"source_table": "main.stg.customer", "target_table": "main.dw.customer"},
        has_mapping=True,
    )
    assert mode in {"etl", "hybrid"}


def test_detect_etl_mode_mapping_only_without_stories():
    mode = detect_workflow_mode(
        requirement_text="",
        user_stories=[],
        has_mapping=True,
    )
    assert mode == "etl"
