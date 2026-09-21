import os
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()


@dataclass(frozen=True)
class DatabricksSettings:
    server_hostname: str
    http_path: str
    access_token: str
    catalog: str
    source_schema: str
    target_schema: str
    query_timeout_seconds: int
    preview_rows: int

    @property
    def is_dummy(self) -> bool:
        token = self.access_token.lower()
        host = self.server_hostname.lower()
        return (
            not self.server_hostname
            or not self.http_path
            or not self.access_token
            or "dummy" in token
            or "xxxxxxxxxxxx" in host
        )


def get_azure_llm() -> AzureChatOpenAI:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.1").strip()
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview").strip()

    if not endpoint or not api_key or "dummy" in api_key.lower() or "your-resource-name" in endpoint:
        raise RuntimeError(
            "Azure OpenAI dummy values detected. Update AZURE_OPENAI_ENDPOINT and "
            "AZURE_OPENAI_API_KEY in .env with a real GPT-5.1 deployment."
        )

    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        azure_deployment=deployment,
        api_version=api_version,
        temperature=0,
        use_responses_api=True,
    )


def get_databricks_settings() -> DatabricksSettings:
    return DatabricksSettings(
        server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME", "").strip(),
        http_path=os.getenv("DATABRICKS_HTTP_PATH", "").strip(),
        access_token=os.getenv("DATABRICKS_ACCESS_TOKEN", "").strip(),
        catalog=os.getenv("DATABRICKS_CATALOG", "main").strip(),
        source_schema=os.getenv("DATABRICKS_SOURCE_SCHEMA", "stg").strip(),
        target_schema=os.getenv("DATABRICKS_TARGET_SCHEMA", "dw").strip(),
        query_timeout_seconds=int(os.getenv("DATABRICKS_QUERY_TIMEOUT_SECONDS", "120")),
        preview_rows=int(os.getenv("DATABRICKS_PREVIEW_ROWS", "20")),
    )


def adb_runtime_context() -> dict[str, str]:
    settings = get_databricks_settings()
    return {
        "platform": "Azure Databricks",
        "dialect": "Databricks SQL",
        "catalog": settings.catalog,
        "source_schema": settings.source_schema,
        "target_schema": settings.target_schema,
        "server_hostname": settings.server_hostname,
    }


@dataclass(frozen=True)
class AzureDevOpsSettings:
    organization: str
    project: str
    pat: str
    area_path: str
    iteration_path: str
    work_item_ids: tuple[int, ...]
    work_item_types: tuple[str, ...]
    max_stories: int
    timeout_seconds: int

    @property
    def base_url(self) -> str:
        return "https://dev.azure.com"

    def build_wiql(self) -> str:
        if self.work_item_ids:
            ids = ", ".join(str(item) for item in self.work_item_ids)
            return f"SELECT [System.Id] FROM WorkItems WHERE [System.Id] IN ({ids})"

        type_filters = " OR ".join(
            f"[System.WorkItemType] = '{work_item_type}'" for work_item_type in self.work_item_types
        )
        clauses = [
            f"[System.TeamProject] = '{self.project}'",
            f"({type_filters})",
            "[System.State] <> 'Removed'",
        ]
        if self.area_path:
            clauses.append(f"[System.AreaPath] UNDER '{self.area_path}'")
        if self.iteration_path:
            clauses.append(f"[System.IterationPath] UNDER '{self.iteration_path}'")

        where_clause = " AND ".join(clauses)
        return (
            "SELECT [System.Id], [System.Title], [System.ChangedDate] "
            f"FROM WorkItems WHERE {where_clause} "
            "ORDER BY [System.ChangedDate] DESC"
        )


def get_azure_devops_settings(
    *,
    organization: str | None = None,
    project: str | None = None,
    work_item_ids: list[int] | None = None,
) -> AzureDevOpsSettings:
    organization = (organization or os.getenv("AZURE_DEVOPS_ORG", "")).strip()
    project = (project or os.getenv("AZURE_DEVOPS_PROJECT", "")).strip()
    pat = os.getenv("AZURE_DEVOPS_PAT", "").strip()
    area_path = os.getenv("AZURE_DEVOPS_AREA_PATH", "").strip()
    iteration_path = os.getenv("AZURE_DEVOPS_ITERATION_PATH", "").strip()
    work_item_ids_raw = os.getenv("AZURE_DEVOPS_WORK_ITEM_IDS", "").strip()
    if work_item_ids is not None:
        work_item_ids_raw = ",".join(str(item) for item in work_item_ids)
    work_item_types_raw = os.getenv("AZURE_DEVOPS_WORK_ITEM_TYPES", "User Story").strip()
    max_stories = int(os.getenv("AZURE_DEVOPS_MAX_STORIES", "25"))
    timeout_seconds = int(os.getenv("AZURE_DEVOPS_TIMEOUT_SECONDS", "60"))

    if not organization or not project or not pat:
        raise RuntimeError(
            "Azure DevOps is not fully configured. Set AZURE_DEVOPS_ORG, "
            "AZURE_DEVOPS_PROJECT, and AZURE_DEVOPS_PAT in .env."
        )

    work_item_ids: tuple[int, ...] = tuple(
        int(item.strip()) for item in work_item_ids_raw.split(",") if item.strip()
    )
    work_item_types = tuple(
        item.strip() for item in work_item_types_raw.split(",") if item.strip()
    ) or ("User Story",)

    return AzureDevOpsSettings(
        organization=organization,
        project=project,
        pat=pat,
        area_path=area_path,
        iteration_path=iteration_path,
        work_item_ids=work_item_ids,
        work_item_types=work_item_types,
        max_stories=max_stories,
        timeout_seconds=timeout_seconds,
    )


def _env_present(name: str) -> bool:
    value = os.getenv(name, "").strip()
    if not value:
        return False
    lowered = value.lower()
    return "dummy" not in lowered and "your-" not in lowered and "xxxxxxxx" not in lowered


def get_connection_status() -> dict[str, dict[str, str]]:
    openai_ready = _env_present("AZURE_OPENAI_ENDPOINT") and _env_present("AZURE_OPENAI_API_KEY")
    ado_ready = _env_present("AZURE_DEVOPS_ORG") and _env_present("AZURE_DEVOPS_PROJECT") and _env_present(
        "AZURE_DEVOPS_PAT"
    )
    databricks = get_databricks_settings()
    databricks_ready = not databricks.is_dummy

    return {
        "azure_openai": {
            "label": "Azure OpenAI",
            "status": "ready" if openai_ready else "missing",
            "detail": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.1") if openai_ready else "Set endpoint and API key in .env",
        },
        "azure_devops": {
            "label": "Azure DevOps",
            "status": "ready" if ado_ready else "missing",
            "detail": f"{os.getenv('AZURE_DEVOPS_ORG', '')}/{os.getenv('AZURE_DEVOPS_PROJECT', '')}".strip("/")
            if ado_ready
            else "Set org, project, and PAT in .env",
        },
        "databricks": {
            "label": "Azure Databricks",
            "status": "ready" if databricks_ready else "missing",
            "detail": databricks.server_hostname if databricks_ready else "Set hostname, HTTP path, and token in .env",
        },
    }
