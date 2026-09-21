from pathlib import Path

from src.parsers.document_parser import read_requirement_document


def test_read_requirement_txt(tmp_path: Path):
    path = tmp_path / "req.txt"
    path.write_text("Source table: main.stg.customer_raw", encoding="utf-8")
    text = read_requirement_document(path)
    assert "customer_raw" in text
