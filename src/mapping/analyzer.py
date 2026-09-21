from __future__ import annotations

from typing import Any

from src.mapping.classifier import classify_transformation
from src.mapping.fabric_enrichment import enrich_mappings
from src.mapping.gap_detector import detect_gaps
from src.mapping.normalizer import normalize_mapping_rows
from src.mapping.risk_scoring import requires_review, score_risk
from src.mapping.vr_library import load_type_rules, rules_for_mapping
from src.models.mapping_analysis import MappingAnalysisRecord, MappingAnalysisResult


def analyze_mappings(
    mapping_payload: dict[str, Any],
    *,
    load_type: str = "",
    incremental_column: str = "",
    platform_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deterministic mapping analysis: classify, score risk, detect gaps, assign VR01–VR26."""
    canonical = normalize_mapping_rows(mapping_payload.get("mapping_rows") or [])
    canonical = enrich_mappings(canonical, platform_metadata)

    records: list[MappingAnalysisRecord] = []
    summary_gaps: list[str] = []

    for item in canonical:
        source = item["source"]
        target = item["target"]
        logic = item["transformation"]["logic"]
        transform_type = classify_transformation("" if logic == "UNKNOWN" else logic)
        item["transformation"]["type"] = transform_type

        extra_flags = list(item.get("enrichment_flags") or [])
        gaps = detect_gaps(
            source_table=source.get("table", ""),
            source_column=source.get("column", ""),
            target_table=target.get("table", ""),
            target_column=target.get("column", ""),
            transformation=logic,
            transform_type=transform_type,
            business_rule=item.get("business_rule", ""),
            source_data_type=source.get("data_type", ""),
            target_data_type=target.get("data_type", ""),
            load_type=load_type,
            incremental_column=incremental_column,
        ) + extra_flags

        risk = score_risk(
            transform_type,
            gaps=gaps,
            business_rule=item.get("business_rule", ""),
            primary_key=target.get("primary_key", "") or source.get("primary_key", ""),
        )
        rules = rules_for_mapping(
            mapping_id=item["mapping_id"],
            transform_type=transform_type,
            logic=logic,
            source_column=source.get("column", ""),
            target_column=target.get("column", ""),
            source_type=source.get("data_type", ""),
            target_type=target.get("data_type", ""),
            nullable=target.get("nullable", "") or source.get("nullable", ""),
            primary_key=target.get("primary_key", "") or source.get("primary_key", ""),
            business_rule=item.get("business_rule", ""),
        )
        record = MappingAnalysisRecord.model_validate(
            {
                **item,
                "risk": risk,
                "gaps": gaps,
                "validation_rules": rules,
                "requires_review": requires_review(risk, gaps),
            }
        )
        records.append(record)
        summary_gaps.extend(f"{record.mapping_id}: {gap}" for gap in gaps)

    load_rules = load_type_rules(load_type, incremental_column)
    high_risk_count = sum(1 for record in records if record.risk in {"High", "Very High"})
    result = MappingAnalysisResult(
        mappings=records,
        load_type_rules=load_rules,
        high_risk_count=high_risk_count,
        gap_count=len(summary_gaps),
        requires_review=any(record.requires_review for record in records) or high_risk_count > 0,
        summary_gaps=list(dict.fromkeys(summary_gaps)),
    )
    return result.to_agent_dict()
