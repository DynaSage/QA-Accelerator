"""Dispatch mapping files to Word, CSV, or Excel parsers. Never send .docx to openpyxl."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_mapping_file(path: Path | str, *, sheet_name: str | None = None) -> dict[str, Any]:
    from src.parsers.excel_mapping_parser import parse_mapping_workbook
    from src.parsers.stm_extract import parse_stm_docx
    from src.parsers.tabular import coerce_path, is_word_document

    path = coerce_path(path)
    if is_word_document(path):
        return parse_stm_docx(path, write_excel=True)
    return parse_mapping_workbook(path, sheet_name=sheet_name)


def install_mapping_parser() -> None:
    """Patch live Streamlit modules so a stale Word parser cannot keep running."""
    from src.parsers.stm_extract import parse_stm_docx

    def _parse(path, sheet_name=None):
        return parse_mapping_file(path, sheet_name=sheet_name)

    def _parse_docx(path, *args, **kwargs):
        return parse_stm_docx(path, write_excel=True)

    targets = [
        "src.services.qa_workflow",
        "src.parsers.excel_mapping_parser",
        "src.parsers.docx_mapping_parser",
        "src.parsers.document_parser",
    ]
    import sys

    for name in targets:
        module = sys.modules.get(name)
        if module is None:
            continue
        if hasattr(module, "parse_mapping_workbook"):
            module.parse_mapping_workbook = _parse
        if hasattr(module, "parse_mapping_file"):
            module.parse_mapping_file = _parse
        if hasattr(module, "parse_mapping_docx"):
            module.parse_mapping_docx = _parse_docx
        if hasattr(module, "parse_stm_docx"):
            module.parse_stm_docx = _parse_docx
        if hasattr(module, "_resolve_stm_headers"):
            from src.parsers.docx_mapping_parser import _resolve_stm_headers

            module._resolve_stm_headers = _resolve_stm_headers
