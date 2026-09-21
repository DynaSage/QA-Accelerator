import json
import re
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.integrations.azure_devops_client import AzureDevOpsClient


def _strip_html(value: str) -> str:
    if not value:
        return ""
    text = unescape(value)
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(?:p|div|li|tr|h[1-6])\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class AdoImporter:
    IMPORT_ROOT = Path("imports") / "ado"

    def __init__(self, client: AzureDevOpsClient | None = None) -> None:
        self.client = client or AzureDevOpsClient()

    def import_user_stories(self) -> dict[str, Any]:
        self.client.test_connection()
        story_ids = self.client.query_user_stories()
        work_items = self.client.get_work_items(story_ids)

        import_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
        import_dir = self.IMPORT_ROOT / import_id
        import_dir.mkdir(parents=True, exist_ok=True)

        normalized_stories = [self._normalize_work_item(item) for item in work_items]
        requirement_text = self.format_requirement_document(
            normalized_stories,
            organization=self.client.settings.organization,
            project=self.client.settings.project,
        )

        requirements_path = import_dir / "requirements_from_ado.txt"
        stories_json_path = import_dir / "user_stories.json"
        metadata_path = import_dir / "import_metadata.json"

        requirements_path.write_text(requirement_text, encoding="utf-8")
        stories_json_path.write_text(json.dumps(normalized_stories, indent=2), encoding="utf-8")

        mapping_path = self._download_mapping_attachment(work_items, import_dir)
        metadata = {
            "import_id": import_id,
            "imported_at": datetime.now(UTC).isoformat(),
            "organization": self.client.settings.organization,
            "project": self.client.settings.project,
            "story_count": len(normalized_stories),
            "story_ids": [story["id"] for story in normalized_stories],
            "requirements_path": str(requirements_path),
            "stories_json_path": str(stories_json_path),
            "mapping_path": str(mapping_path) if mapping_path else "",
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        latest_pointer = self.IMPORT_ROOT / "latest.json"
        latest_pointer.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        return metadata

    @classmethod
    def load_latest_import(cls) -> dict[str, Any] | None:
        latest_pointer = cls.IMPORT_ROOT / "latest.json"
        if not latest_pointer.exists():
            return None
        return json.loads(latest_pointer.read_text(encoding="utf-8"))

    @classmethod
    def load_import(cls, import_id: str) -> dict[str, Any]:
        metadata_path = cls.IMPORT_ROOT / import_id / "import_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"ADO import not found: {import_id}")
        return json.loads(metadata_path.read_text(encoding="utf-8"))

    @classmethod
    def format_requirement_document(
        cls,
        stories: list[dict[str, Any]],
        *,
        organization: str = "",
        project: str = "",
    ) -> str:
        lines = [
            "ETL QA Requirements imported from Azure DevOps User Stories",
            f"Organization: {organization}",
            f"Project: {project}",
            f"Imported at: {datetime.now(UTC).isoformat()}",
            "",
        ]
        for index, story in enumerate(stories, start=1):
            lines.extend(
                [
                    f"## User Story {index}: {story['id']} - {story['title']}",
                    f"Type: {story['work_item_type']}",
                    f"State: {story['state']}",
                    f"Area Path: {story.get('area_path', '')}",
                    f"Iteration Path: {story.get('iteration_path', '')}",
                    f"Tags: {story.get('tags') or 'None'}",
                    "",
                    "### Description",
                    story.get("description") or "No description provided.",
                    "",
                    "### Acceptance Criteria",
                    story.get("acceptance_criteria") or "No acceptance criteria provided.",
                    "",
                    "---",
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n"

    @classmethod
    def replace_imported_stories(
        cls,
        metadata: dict[str, Any],
        stories: list[dict[str, Any]],
    ) -> dict[str, Any]:
        stories_json_path = Path(metadata["stories_json_path"])
        requirements_path = Path(metadata["requirements_path"])
        import_id = metadata["import_id"]
        metadata_path = cls.IMPORT_ROOT / import_id / "import_metadata.json"

        stories_json_path.parent.mkdir(parents=True, exist_ok=True)
        stories_json_path.write_text(json.dumps(stories, indent=2), encoding="utf-8")
        requirements_path.write_text(
            cls.format_requirement_document(
                stories,
                organization=str(metadata.get("organization") or ""),
                project=str(metadata.get("project") or ""),
            ),
            encoding="utf-8",
        )
        updated = {
            **metadata,
            "story_count": len(stories),
            "story_ids": [story.get("id") for story in stories],
        }
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")
        latest_pointer = cls.IMPORT_ROOT / "latest.json"
        latest_pointer.write_text(json.dumps(updated, indent=2), encoding="utf-8")
        return updated

    def _normalize_work_item(self, item: dict[str, Any]) -> dict[str, Any]:
        fields = item.get("fields", {})
        return {
            "id": item.get("id"),
            "title": fields.get("System.Title", ""),
            "work_item_type": fields.get("System.WorkItemType", ""),
            "state": fields.get("System.State", ""),
            "description": _strip_html(fields.get("System.Description", "")),
            "acceptance_criteria": _strip_html(fields.get("Microsoft.VSTS.Common.AcceptanceCriteria", "")),
            "tags": fields.get("System.Tags", ""),
            "area_path": fields.get("System.AreaPath", ""),
            "iteration_path": fields.get("System.IterationPath", ""),
            "url": item.get("url", ""),
        }

    def _format_requirement_document(self, stories: list[dict[str, Any]]) -> str:
        return self.format_requirement_document(
            stories,
            organization=self.client.settings.organization,
            project=self.client.settings.project,
        )

    def _download_mapping_attachment(self, work_items: list[dict[str, Any]], import_dir: Path) -> Path | None:
        for item in work_items:
            for relation in item.get("relations", []) or []:
                if relation.get("rel") != "AttachedFile":
                    continue
                name = relation.get("attributes", {}).get("name", "")
                lower_name = name.lower()
                if not lower_name.endswith((".xlsx", ".xlsm", ".csv", ".docx")):
                    continue
                content = self.client.download_attachment(relation["url"])
                mapping_path = import_dir / name
                mapping_path.write_bytes(content)
                return mapping_path
        return None
