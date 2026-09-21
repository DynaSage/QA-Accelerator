from pathlib import Path

import pytest
from openpyxl import Workbook

from src.parsers.kpi_logic_parser import parse_kpi_logic_document, parse_kpi_logic_sql


def _write_kpi_workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["KPI ID", "KPI Name", "Module", "SQL Query", "Expected Result", "Priority"])
    sheet.append(
        [
            "KPI-001",
            "Null customer keys",
            "Dashboard",
            "SELECT customer_id FROM main.dw.dim_customer WHERE customer_id IS NULL",
            "0 rows",
            "High",
        ]
    )
    sheet.append(
        [
            "KPI-002",
            "Duplicate orders",
            "Orders",
            "SELECT order_id, COUNT(*) AS cnt FROM main.app.orders GROUP BY order_id HAVING COUNT(*) > 1",
            "0 rows",
            "Medium",
        ]
    )
    workbook.save(path)


def test_parse_kpi_logic_excel(tmp_path: Path):
    workbook_path = tmp_path / "kpi_logic.xlsx"
    _write_kpi_workbook(workbook_path)

    entries = parse_kpi_logic_document(workbook_path)

    assert len(entries) == 2
    assert entries[0]["kpi_id"] == "KPI-001"
    assert "SELECT customer_id" in entries[0]["sql_query"]
    assert entries[1]["module"] == "Orders"


def test_parse_kpi_logic_csv(tmp_path: Path):
    csv_path = tmp_path / "kpi_logic.csv"
    csv_path.write_text(
        "KPI ID,KPI Name,Module,SQL Query,Expected Result,Priority\n"
        "KPI-001,Null customer keys,Dashboard,"
        '"SELECT customer_id FROM main.dw.dim_customer WHERE customer_id IS NULL",0 rows,High\n',
        encoding="utf-8",
    )
    entries = parse_kpi_logic_document(csv_path)
    assert len(entries) == 1
    assert entries[0]["kpi_id"] == "KPI-001"
    assert "SELECT customer_id" in entries[0]["sql_query"]


def test_parse_kpi_logic_sql_file(tmp_path: Path):
    sql_path = tmp_path / "kpi.sql"
    sql_path.write_text(
        "-- KPI: Active Users\nSELECT COUNT(*) FROM main.analytics.users WHERE active = true\n",
        encoding="utf-8",
    )

    entries = parse_kpi_logic_sql(sql_path)

    assert len(entries) == 1
    assert entries[0]["kpi_name"] == "Active Users"
    assert "SELECT COUNT(*)" in entries[0]["sql_query"]


def test_parse_kpi_logic_document_rejects_empty_excel(tmp_path: Path):
    workbook_path = tmp_path / "empty.xlsx"
    workbook = Workbook()
    workbook.active.append(["SQL Query"])
    workbook.save(workbook_path)

    with pytest.raises(ValueError, match="No KPI SQL rows"):
        parse_kpi_logic_document(workbook_path)
