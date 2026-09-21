from src.agents import mapping_agent


def test_merge_llm_mapping_rows_overlays_logic_without_dropping_columns():
    parsed = [
        {
            "target_table": "Person_Account",
            "target_column": "account_number",
            "source_column": "account_number",
            "transformation": "DIRECT",
        },
        {
            "target_table": "Person_Account",
            "target_column": "combined_key",
            "source_column": "CONCAT_WS(' ', account_number, ibd_number)",
            "transformation": "CONCAT_WS(' ', account_number, ibd_number)",
        },
    ]
    llm_rows = [
        {
            "target_column": "account_number",
            "source_column": "account_number",
            "transformation": "DIRECT copy from hldu_hldr_j.account_number",
            "primary_key": "Y",
        },
        {
            "target_column": "combined_key",
            "source_column": "",
            "transformation": "CONCAT_WS(' ', account_number, ibd_number)",
            "primary_key": "N",
        },
        {"target_column": "invented_column", "transformation": "should be ignored"},
    ]
    merged = mapping_agent.merge_llm_mapping_rows(parsed, llm_rows)
    assert len(merged) == 2
    assert merged[0]["transformation"] == "DIRECT copy from hldu_hldr_j.account_number"
    assert merged[0]["primary_key"] == "Y"
    assert merged[1]["target_column"] == "combined_key"


def test_enrich_mapping_output_with_llm(monkeypatch):
    monkeypatch.setattr(
        mapping_agent,
        "_llm_mapping_for_entity",
        lambda target_table, rows, entity_logic: {
            "target_table": target_table,
            "primary_key": "account_number",
            "load_type": "full",
            "mapping_rows": [
                {
                    "target_column": "account_number",
                    "source_column": "account_number",
                    "transformation": "DIRECT from source account_number",
                    "primary_key": "Y",
                }
            ],
            "transformation_rules": ["Copy account_number as-is."],
            "business_rules": [],
            "not_null_columns": ["account_number"],
            "missing_information": [],
        },
    )
    payload = mapping_agent.enrich_mapping_output_with_llm(
        {
            "mapping_rows": [
                {
                    "target_table": "Person_Account",
                    "target_column": "account_number",
                    "source_column": "account_number",
                    "transformation": "DIRECT",
                }
            ],
            "entity_logic": [{"target_table": "Person_Account", "pseudo_code": "Join on account_number."}],
        }
    )
    assert payload["mapping_rows"][0]["transformation"] == "DIRECT from source account_number"
    assert payload["llm_mapping_output"]["entities"][0]["primary_key"] == "account_number"
    assert payload["llm_mapping_output"]["transformation_rules"] == ["Copy account_number as-is."]


def test_apply_canonical_spec_defaults_and_backfills_truncated_mapping():
    payload = {
        "source_table": "",
        "target_table": "",
        "primary_key": "",
        "source_to_target_mapping": [
            {"source_column": "account_number", "target_column": "account_number", "transformation": "DIRECT"}
        ],
    }
    mapping_payload = {
        "source_table": "hldu_hldr_j",
        "target_table": "Person_Account",
        "llm_mapping_output": {"entities": [{"target_table": "Person_Account", "primary_key": "account_number"}]},
    }
    canonical = [
        {
            "source": {"column": "account_number"},
            "target": {"column": "account_number"},
            "transformation": {"logic": "DIRECT"},
        },
        {
            "source": {"column": "ibd_number"},
            "target": {"column": "ibd_number"},
            "transformation": {"logic": "DIRECT"},
        },
    ]
    filled = mapping_agent.apply_canonical_spec(payload, mapping_payload, canonical)
    assert filled["source_table"] == "hldu_hldr_j"
    assert filled["target_table"] == "Person_Account"
    assert filled["primary_key"] == "account_number"
    assert len(filled["source_to_target_mapping"]) == 2


def test_mappings_for_prompt_compacts_large_word_stm():
    rows = [
        {
            "source": {"table": "src", "column": f"c{index}"},
            "target": {"table": f"gold_{index % 17}", "column": f"c{index}"},
            "transformation": {"logic": "DIRECT"},
        }
        for index in range(90)
    ]
    compacted = mapping_agent._mappings_for_prompt(rows, {"stm_entities": [{"target_table": "gold_0", "row_count": 6}]})
    assert isinstance(compacted, dict)
    assert compacted["total_mappings"] == 90
    assert len(compacted["sample_rows_per_entity"]) < 90


def test_build_etl_spec_backfills_truncated_word_stm(monkeypatch):
    monkeypatch.setattr(mapping_agent, "adb_runtime_context", lambda: {"catalog": "main"})
    monkeypatch.setattr(mapping_agent, "enrich_mapping_output_with_llm", lambda payload: payload)
    monkeypatch.setattr(
        mapping_agent,
        "invoke_llm_json",
        lambda *args, **kwargs: {
            "source_table": "",
            "target_table": "",
            "primary_key": "",
            "load_type": "full",
            "source_to_target_mapping": [
                {"source_column": "account_number", "target_column": "account_number", "transformation": "DIRECT"}
            ],
            "missing_information": [],
            "assumptions": [],
        },
    )
    mapping_payload = {
        "source_table": "hldu_hldr_j",
        "target_table": "Person_Account",
        "document_kind": "word_stm",
        "stm_entities": [{"target_table": "Person_Account", "row_count": 2}],
        "mapping_rows": [
            {
                "source_table": "hldu_hldr_j",
                "source_column": "account_number",
                "target_table": "Person_Account",
                "target_column": "account_number",
                "transformation": "DIRECT",
            },
            {
                "source_table": "hldu_hldr_j",
                "source_column": "ibd_number",
                "target_table": "Person_Account",
                "target_column": "ibd_number",
                "transformation": "DIRECT",
            },
        ],
        "entity_logic": [{"target_table": "Person_Account", "pseudo_code": "Join on account_number."}],
    }
    built = mapping_agent.build_etl_spec({}, mapping_payload)
    spec = built["etl_spec"]
    assert spec["source_table"] == "hldu_hldr_j"
    assert spec["target_table"] == "Person_Account"
    assert spec["primary_key"] == "UNKNOWN"
    assert len(spec["source_to_target_mapping"]) == 2
    assert built["canonical_mappings"]
    assert built["mapping_rows"]
