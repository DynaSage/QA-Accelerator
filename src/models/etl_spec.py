from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ColumnMapping(BaseModel):
    source_column: str
    target_column: str
    transformation: str = ""


class ETLSpecModel(BaseModel):
    database_dialect: str = "Databricks SQL"
    catalog: str = "main"
    source_table: str
    target_table: str
    primary_key: str
    load_type: Literal["full", "incremental", "snapshot", "cdc"] | str = "full"
    incremental_column: str | None = None
    watermark_column: str | None = None
    source_to_target_mapping: list[ColumnMapping] = Field(default_factory=list)
    transformation_rules: list[str] = Field(default_factory=list)
    business_rules: list[str] = Field(default_factory=list)
    not_null_columns: list[str] = Field(default_factory=list)
    additional_notes: str = ""

    @field_validator("source_table", "target_table", "primary_key")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Required ETL spec field cannot be empty.")
        return cleaned

    def to_agent_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class ValidationTestModel(BaseModel):
    test_id: str
    test_scenario: str
    validation_type: str
    sql_query: str
    expected_result: str
    priority: str = "Medium"

    def to_agent_dict(self) -> dict[str, Any]:
        return self.model_dump()
