from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict

UNKNOWN = "UNKNOWN"

TransformationType = Literal[
    "DIRECT",
    "STRING_TRANSFORMATION",
    "DATE_TRANSFORMATION",
    "DEFAULT_VALUE",
    "CONDITIONAL",
    "CALCULATION",
    "DATATYPE_CONVERSION",
    "LOOKUP",
    "JOIN",
    "AGGREGATION",
    "SCD",
    "FILTER",
    "COMPLEX_SQL",
]

RiskLevel = Literal["Low", "Medium", "High", "Very High"]


class MappingEndpoint(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    database: str = UNKNOWN
    schema_name: str = Field(default=UNKNOWN, alias="schema")
    table: str = UNKNOWN
    column: str = UNKNOWN
    data_type: str = UNKNOWN
    nullable: str = UNKNOWN
    primary_key: str = UNKNOWN


class TransformationDetail(BaseModel):
    type: str = "DIRECT"
    logic: str = UNKNOWN


class ValidationRule(BaseModel):
    rule_id: str
    type: str
    description: str
    priority: str = "Medium"


class MappingAnalysisRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    mapping_id: str
    source: MappingEndpoint
    target: MappingEndpoint
    transformation: TransformationDetail
    business_rule: str = UNKNOWN
    notes: str = ""
    risk: str = "Low"
    gaps: list[str] = Field(default_factory=list)
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    requires_review: bool = False

    def to_agent_dict(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True)


class MappingAnalysisResult(BaseModel):
    mappings: list[MappingAnalysisRecord] = Field(default_factory=list)
    load_type_rules: list[ValidationRule] = Field(default_factory=list)
    high_risk_count: int = 0
    gap_count: int = 0
    requires_review: bool = False
    summary_gaps: list[str] = Field(default_factory=list)

    def to_agent_dict(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True)
