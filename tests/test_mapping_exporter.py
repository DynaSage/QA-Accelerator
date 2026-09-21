import json

from src.exporters.mapping_exporter import mapping_excel_bytes, mapping_json_bytes


def test_mapping_export_json_and_excel():
    draft = {
        "draft_id": "abc-123",
        "source_files": {"spec_name": "person_account", "workflow_mode": "etl"},
        "etl_spec_draft": {
            "source_table": "stg.account",
            "target_table": "gold.person_account",
            "primary_key": "account_number",
            "source_to_target_mapping": [
                {"source_column": "account_number", "target_column": "account_number", "transformation": "DIRECT"}
            ],
        },
        "mapping_rows": [
            {
                "source_table": "stg.account",
                "source_column": "account_number",
                "target_table": "person_account",
                "target_column": "account_number",
                "transformation": "DIRECT",
            }
        ],
        "canonical_mappings": [
            {
                "mapping_id": "MAP-001",
                "source": {"table": "account", "column": "account_number"},
                "target": {"table": "person_account", "column": "account_number"},
                "transformation": {"type": "DIRECT", "logic": "DIRECT"},
            }
        ],
        "mapping_analysis": {
            "mappings": [
                {
                    "mapping_id": "MAP-001",
                    "source": {"table": "account", "column": "account_number"},
                    "target": {"table": "person_account", "column": "account_number"},
                    "transformation": {"type": "DIRECT", "logic": "DIRECT"},
                    "risk": "Low",
                    "gaps": [],
                    "validation_rules": [{"rule_id": "VR01"}],
                    "requires_review": False,
                }
            ],
            "summary_gaps": [],
            "high_risk_count": 0,
            "gap_count": 0,
        },
        "entity_logic": [{"target_table": "person_account", "pseudo_code": "Join on account_number."}],
    }

    payload = json.loads(mapping_json_bytes(draft).decode("utf-8"))
    assert payload["etl_spec"]["target_table"] == "gold.person_account"
    assert payload["mapping_rows"][0]["source_column"] == "account_number"
    assert payload["canonical_mappings"][0]["mapping_id"] == "MAP-001"

    excel = mapping_excel_bytes(draft)
    assert excel[:2] == b"PK"
    assert len(excel) > 1000
