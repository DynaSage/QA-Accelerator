import base64
from typing import Any

import httpx

from src.config import AzureDevOpsSettings, get_azure_devops_settings


class AzureDevOpsClient:
    def __init__(self, settings: AzureDevOpsSettings | None = None) -> None:
        self.settings = settings or get_azure_devops_settings()
        token = base64.b64encode(f":{self.settings.pat}".encode("utf-8")).decode("ascii")
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.settings.base_url}/{self.settings.organization}/{path.lstrip('/')}"

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = httpx.get(
            self._url(path),
            headers=self._headers,
            params=params,
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: dict[str, Any], *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = httpx.post(
            self._url(path),
            headers=self._headers,
            params=params,
            json=payload,
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def test_connection(self) -> dict[str, Any]:
        projects = self._get("_apis/projects", params={"api-version": "7.1"})
        project_names = [item["name"] for item in projects.get("value", [])]
        if self.settings.project not in project_names:
            raise RuntimeError(
                f"Project '{self.settings.project}' was not found in organization "
                f"'{self.settings.organization}'. Available projects: {', '.join(project_names)}"
            )
        return {
            "organization": self.settings.organization,
            "project": self.settings.project,
            "project_count": len(project_names),
            "projects": project_names,
        }

    def query_user_stories(self) -> list[int]:
        wiql = self.settings.build_wiql()
        payload = self._post(
            f"{self.settings.project}/_apis/wit/wiql",
            {"query": wiql},
            params={"api-version": "7.1"},
        )
        ids = [item["id"] for item in payload.get("workItems", [])]
        if not ids:
            return []
        return ids[: self.settings.max_stories]

    def get_work_items(self, ids: list[int]) -> list[dict[str, Any]]:
        if not ids:
            return []
        # ADO rejects using $expand together with fields; fetch details first, then relations.
        fields = [
            "System.Id",
            "System.Title",
            "System.WorkItemType",
            "System.State",
            "System.Description",
            "Microsoft.VSTS.Common.AcceptanceCriteria",
            "System.Tags",
            "System.AreaPath",
            "System.IterationPath",
        ]
        payload = self._get(
            f"{self.settings.project}/_apis/wit/workitems",
            params={
                "ids": ",".join(str(item) for item in ids),
                "fields": ",".join(fields),
                "api-version": "7.1",
            },
        )
        items = payload.get("value", [])
        enriched: list[dict[str, Any]] = []
        for item in items:
            item_id = item.get("id")
            if not item_id:
                enriched.append(item)
                continue
            relations_payload = self._get(
                f"{self.settings.project}/_apis/wit/workitems/{item_id}",
                params={"$expand": "relations", "api-version": "7.1"},
            )
            item["relations"] = relations_payload.get("relations", [])
            enriched.append(item)
        return enriched

    def download_attachment(self, url: str) -> bytes:
        response = httpx.get(url, headers=self._headers, timeout=self.settings.timeout_seconds)
        response.raise_for_status()
        return response.content
