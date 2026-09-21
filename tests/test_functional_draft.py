import json
from pathlib import Path

from src.services.qa_workflow import QAWorkflowService


def test_build_functional_draft_keeps_ado_stories_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    imports_dir = tmp_path / "imports" / "ado" / "import123"
    imports_dir.mkdir(parents=True)
    stories = [{"id": 19775, "title": "Insight Studio", "description": "UI story", "acceptance_criteria": "AC"}]
    stories_path = imports_dir / "user_stories.json"
    stories_path.write_text(json.dumps(stories), encoding="utf-8")

    service = QAWorkflowService(
        review_store=__import__("src.review.review_store", fromlist=["ReviewStore"]).ReviewStore(
            review_dir=tmp_path / "review"
        )
    )

    draft = service.build_functional_draft(
        requirement_text="Insight Studio user story",
        requirement_analysis={"requirement_summary": "UI story", "business_rules": [], "missing_information": [], "assumptions": []},
        user_stories=stories,
        spec_name="ado_import123",
        source_files={
            "ado_import_id": "import123",
            "stories_json_path": str(stories_path),
            "requirements_path": str(imports_dir / "requirements_from_ado.txt"),
        },
    )

    saved_path = draft["source_files"]["stories_json_path"]
    assert Path(saved_path).exists()
    assert "uploads" not in saved_path.replace("\\", "/")


def test_load_user_stories_falls_back_to_ado_import(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    imports_dir = tmp_path / "imports" / "ado" / "import456"
    imports_dir.mkdir(parents=True)
    stories = [{"id": 1, "title": "Story"}]
    (imports_dir / "user_stories.json").write_text(json.dumps(stories), encoding="utf-8")

    service = QAWorkflowService()
    loaded = service._load_user_stories(
        {
            "stories_json_path": str(tmp_path / "uploads" / "missing_user_stories.json"),
            "ado_import_id": "import456",
        }
    )
    assert loaded == stories


def test_approve_functional_draft_with_empty_spec(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from src.review.review_store import ReviewStore

    service = QAWorkflowService(review_store=ReviewStore(review_dir=tmp_path / "review"))
    draft = service.build_functional_draft(
        requirement_text="Login page should submit the form.",
        requirement_analysis={
            "requirement_summary": "UI login",
            "business_rules": [],
            "missing_information": [],
            "assumptions": [],
        },
        user_stories=[{"id": 1, "title": "Login", "description": "UI", "acceptance_criteria": "AC"}],
        spec_name="ui_login",
    )
    approved = service.approve_draft(draft["draft_id"])
    assert approved["saved_spec"] is None
    assert approved["etl_spec_draft"] == {}


def test_analyze_requirements_empty_does_not_block_mapping_only():
    from src.agents.requirement_agent import analyze_requirements

    analysis = analyze_requirements("   ")
    assert analysis["missing_information"] == []
    assert "mapping document" in analysis["requirement_summary"].lower()


def test_build_draft_from_ado_without_import_does_not_call_ado(monkeypatch):
    from src.integrations.ado_importer import AdoImporter
    from src.services.qa_workflow import QAWorkflowService

    monkeypatch.setattr(AdoImporter, "load_latest_import", classmethod(lambda cls: None))

    def _should_not_import(self, **kwargs):
        raise AssertionError("ADO import should stay optional")

    monkeypatch.setattr(QAWorkflowService, "import_from_azure_devops", _should_not_import)
    service = QAWorkflowService()
    try:
        service.build_draft_from_ado()
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError as exc:
        assert "mapping document" in str(exc).lower() or "devOps" in str(exc).lower() or "Azure DevOps" in str(exc)
