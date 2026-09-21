from pathlib import Path

from scripts.create_samples import write_mapping_workbook
from src.parsers.excel_mapping_parser import parse_mapping_workbook


def test_parse_mapping_workbook(tmp_path: Path):
    workbook_path = tmp_path / "mapping.xlsx"
    write_mapping_workbook(workbook_path)
    payload = parse_mapping_workbook(workbook_path)

    assert payload["source_table"] == "main.stg.customer_raw"
    assert payload["target_table"] == "main.dw.dim_customer"
    assert len(payload["mapping_rows"]) == 5
    assert payload["mapping_rows"][0]["source_column"] == "cust_id"


def test_parse_mapping_csv(tmp_path: Path):
    csv_path = tmp_path / "mapping.csv"
    csv_path.write_text(
        "Source Database,Source Schema,Source Table,Source Column,Source Data Type,"
        "Transformation,Target Database,Target Schema,Target Table,Target Column,"
        "Target Data Type,Business Rule,Nullable,Primary Key,Notes\n"
        "main,stg,customer_raw,cust_id,INT,CAST(cust_id AS BIGINT),"
        "main,dw,dim_customer,customer_id,BIGINT,Must be unique,N,Y,Business key\n",
        encoding="utf-8",
    )
    payload = parse_mapping_workbook(csv_path)

    assert payload["source_table"] == "main.stg.customer_raw"
    assert payload["target_table"] == "main.dw.dim_customer"
    assert payload["mapping_rows"][0]["source_column"] == "cust_id"
    assert payload["mapping_rows"][0]["target_column"] == "customer_id"


def test_parse_mapping_csv_uppercase_extension(tmp_path: Path):
    csv_path = tmp_path / "mapping.CSV"
    csv_path.write_text(
        "Source Column,Target Column\n"
        "cust_id,customer_id\n",
        encoding="utf-8",
    )
    payload = parse_mapping_workbook(str(csv_path))
    assert payload["mapping_rows"][0]["source_column"] == "cust_id"


def test_parse_mapping_csv_misnamed_as_xlsx(tmp_path: Path):
    path = tmp_path / "mapping.xlsx"
    path.write_text(
        "Source Column,Target Column\n"
        "cust_id,customer_id\n",
        encoding="utf-8",
    )
    payload = parse_mapping_workbook(path)
    assert payload["mapping_rows"][0]["target_column"] == "customer_id"
