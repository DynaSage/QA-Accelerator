"""Parse Word DWH / STM mapping documents into the same payload as Excel mappings.

This module is a thin wrapper. Streamlit may keep an old copy in memory; install_mapping_parser
patches any leftover names onto the live module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_mapping_docx(path: Path | str) -> dict[str, Any]:
    from src.parsers.stm_extract import parse_stm_docx

    return parse_stm_docx(path, write_excel=True)


def _resolve_stm_headers(headers: list[str]) -> dict[str, int]:
    from src.parsers.stm_extract import resolve_stm_headers

    resolved = resolve_stm_headers(list(headers), use_llm=True)
    if "source_column" not in resolved:
        for index, header in enumerate(headers):
            text = str(header or "").lower()
            if "source" in text and "column" in text:
                resolved["source_column"] = index
                break
    if "target_column" not in resolved:
        for index, header in enumerate(headers):
            text = str(header or "").lower()
            if "target" in text and "column" in text:
                resolved["target_column"] = index
                break
    return resolved
