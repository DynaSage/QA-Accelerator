from src.mapping.analyzer import analyze_mappings
from src.mapping.classifier import classify_transformation
from src.mapping.fabric_enrichment import enrich_mappings
from src.mapping.gap_detector import detect_gaps
from src.mapping.normalizer import normalize_mapping_rows
from src.mapping.risk_scoring import score_risk
from src.parsers.excel_mapping_parser import parse_mapping_workbook


def test_classify_transformation_types():
    assert classify_transformation("DIRECT") == "DIRECT"
    assert classify_transformation("UPPER(CUST_NAME)") == "STRING_TRANSFORMATION"
    assert classify_transformation("COALESCE(COUNTRY,'UNKNOWN')") == "DEFAULT_VALUE"
    assert classify_transformation("CASE WHEN status_cd = 'A' THEN 1 ELSE 0 END") == "CONDITIONAL"
    assert classify_transformation("CAST(cust_id AS BIGINT)") == "DATATYPE_CONVERSION"
    assert classify_transformation("lookup customer_ref on cust_id") == "LOOKUP"
    assert classify_transformation("left join orders o on o.id = c.id join items i on i.oid = o.id") == "COMPLEX_SQL"
    assert classify_transformation("SCD Type 2 effective_from") == "SCD"


def test_normalize_and_analyze_rows():
    rows = [
        {
            "source_table": "main.stg.customer_raw",
            "target_table": "main.dw.dim_customer",
            "source_column": "cust_name",
            "target_column": "customer_name",
            "source_data_type": "VARCHAR(100)",
            "target_data_type": "VARCHAR(100)",
            "transformation": "UPPER(CUST_NAME)",
            "business_rule": "Mandatory",
            "nullable": "N",
            "primary_key": "N",
            "notes": "",
        }
    ]
    canonical = normalize_mapping_rows(rows)
    assert canonical[0]["mapping_id"] == "MAP-001"
    assert canonical[0]["transformation"]["type"] == "STRING_TRANSFORMATION"
    assert canonical[0]["source"]["table"] == "customer_raw"

    analysis = analyze_mappings({"mapping_rows": rows}, load_type="incremental", incremental_column="updated_at")
    record = analysis["mappings"][0]
    rule_ids = {rule["rule_id"] for rule in record["validation_rules"]}
    assert "VR12" in rule_ids
    assert "VR02" in rule_ids
    assert record["risk"] in {"Low", "Medium"}
    assert any(rule["rule_id"] == "VR21" for rule in analysis["load_type_rules"])


def test_gap_and_risk_for_mismatch():
    gaps = detect_gaps(
        source_table="CUSTOMER",
        source_column="CUST_ID",
        target_table="DIM_CUSTOMER",
        target_column="CUSTOMER_ID",
        transformation="DIRECT",
        transform_type="DIRECT",
        business_rule="",
        source_data_type="BIGINT",
        target_data_type="VARCHAR(50)",
    )
    assert any("datatype mismatch" in gap for gap in gaps)
    assert "missing business rule" in gaps
    assert score_risk("COMPLEX_SQL") == "Very High"
    assert score_risk("LOOKUP") == "High"


def test_fabric_enrichment_flags_mismatch():
    mappings = [
        {
            "mapping_id": "MAP-001",
            "source": {"database": "main", "schema": "stg", "table": "customer_raw", "column": "cust_id", "data_type": "INT"},
            "target": {
                "database": "main",
                "schema": "dw",
                "table": "dim_customer",
                "column": "customer_id",
                "data_type": "VARCHAR(50)",
            },
            "transformation": {"type": "DIRECT", "logic": "DIRECT"},
            "business_rule": "Must be unique",
        }
    ]
    metadata = {
        "tables": {
            "main.dw.dim_customer": {
                "columns": {"customer_id": {"data_type": "BIGINT", "nullable": False, "primary_key": True}}
            }
        }
    }
    enriched = enrich_mappings(mappings, metadata)
    flags = enriched[0].get("enrichment_flags") or []
    assert flags
    assert "BIGINT" in flags[0]


def test_parser_canonical_aliases(tmp_path):
    from openpyxl import Workbook

    path = tmp_path / "map.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Src Table", "SOURCE_COLUMN", "Tgt Col", "Transform", "Business Rule"])
    sheet.append(["stg.customer", "cust_id", "customer_id", "DIRECT", "Must be unique"])
    workbook.save(path)

    payload = parse_mapping_workbook(path)
    row = payload["mapping_rows"][0]
    assert row["source_table"] == "stg.customer"
    assert row["source_column"] == "cust_id"
    assert row["target_column"] == "customer_id"
    assert row["business_rule"] == "Must be unique"
