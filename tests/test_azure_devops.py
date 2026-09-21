import json

from src.config import AzureDevOpsSettings, get_azure_devops_settings
from src.integrations.ado_importer import AdoImporter, _strip_html
from src.integrations.azure_devops_client import AzureDevOpsClient


def test_strip_html():
    html = "<p>Load <strong>customer</strong> data<br/>into dim table.</p>"
    text = _strip_html(html)
    assert "customer" in text
    assert "dim table" in text


def test_build_wiql_with_area_and_iteration():
    settings = AzureDevOpsSettings(
        organization="contoso",
        project="QA Project",
        pat="token",
        area_path="QA Project\\ETL",
        iteration_path="QA Project\\Sprint 1",
        work_item_ids=(),
        work_item_types=("User Story",),
        max_stories=10,
        timeout_seconds=30,
    )
    wiql = settings.build_wiql()
    assert "[System.AreaPath] UNDER 'QA Project\\ETL'" in wiql
    assert "[System.IterationPath] UNDER 'QA Project\\Sprint 1'" in wiql
    assert "User Story" in wiql


def test_format_requirement_document():
    settings = AzureDevOpsSettings(
        organization="contoso",
        project="QA Project",
        pat="token",
        area_path="",
        iteration_path="",
        work_item_ids=(),
        work_item_types=("User Story",),
        max_stories=10,
        timeout_seconds=30,
    )
    importer = AdoImporter(AzureDevOpsClient(settings))
    text = importer._format_requirement_document(
        [
            {
                "id": 101,
                "title": "Validate customer ETL",
                "work_item_type": "User Story",
                "state": "Active",
                "description": "Source is stg.customer_raw",
                "acceptance_criteria": "Generate SQL tests",
                "tags": "ETL",
                "area_path": "QA\\ETL",
                "iteration_path": "QA\\Sprint 1",
            }
        ]
    )
    assert "Validate customer ETL" in text
    assert "stg.customer_raw" in text
    assert "Generate SQL tests" in text


def test_ui_empty_work_item_ids_do_not_use_env_default(monkeypatch):
    monkeypatch.setenv("AZURE_DEVOPS_ORG", "contoso")
    monkeypatch.setenv("AZURE_DEVOPS_PROJECT", "QA Project")
    monkeypatch.setenv("AZURE_DEVOPS_PAT", "token")
    monkeypatch.setenv("AZURE_DEVOPS_WORK_ITEM_IDS", "19775")

    from_ui = get_azure_devops_settings(work_item_ids=[])
    assert from_ui.work_item_ids == ()

    from_cli = get_azure_devops_settings()
    assert from_cli.work_item_ids == (19775,)

    from_override = get_azure_devops_settings(work_item_ids=[101, 102])
    assert from_override.work_item_ids == (101, 102)


def test_replace_imported_stories_removes_one(tmp_path, monkeypatch):
    monkeypatch.setattr(AdoImporter, "IMPORT_ROOT", tmp_path / "ado")
    import_id = "20260101_keep"
    import_dir = AdoImporter.IMPORT_ROOT / import_id
    import_dir.mkdir(parents=True)
    stories = [
        {
            "id": 101,
            "title": "Keep me",
            "work_item_type": "User Story",
            "state": "Active",
            "description": "keep description",
            "acceptance_criteria": "keep ac",
            "tags": "",
            "area_path": "",
            "iteration_path": "",
        },
        {
            "id": 102,
            "title": "Drop me",
            "work_item_type": "User Story",
            "state": "Active",
            "description": "drop description",
            "acceptance_criteria": "drop ac",
            "tags": "",
            "area_path": "",
            "iteration_path": "",
        },
    ]
    stories_path = import_dir / "user_stories.json"
    requirements_path = import_dir / "requirements_from_ado.txt"
    stories_path.write_text("[]", encoding="utf-8")
    requirements_path.write_text("", encoding="utf-8")
    metadata = {
        "import_id": import_id,
        "organization": "contoso",
        "project": "QA Project",
        "story_count": 2,
        "story_ids": [101, 102],
        "requirements_path": str(requirements_path),
        "stories_json_path": str(stories_path),
    }

    updated = AdoImporter.replace_imported_stories(metadata, [stories[0]])

    assert updated["story_count"] == 1
    assert updated["story_ids"] == [101]
    saved = json.loads(stories_path.read_text(encoding="utf-8"))
    assert [story["id"] for story in saved] == [101]
    requirement_text = requirements_path.read_text(encoding="utf-8")
    assert "Keep me" in requirement_text
    assert "Drop me" not in requirement_text
    latest = json.loads((AdoImporter.IMPORT_ROOT / "latest.json").read_text(encoding="utf-8"))
    assert latest["story_ids"] == [101]
