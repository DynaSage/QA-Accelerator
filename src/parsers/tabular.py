"""Read CSV/TSV tables without sending them to openpyxl."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

CSV_SUFFIXES = {".csv", ".tsv"}
EXCEL_SUFFIXES = {".xlsx", ".xlsm", ".xltx", ".xltm"}
WORD_SUFFIXES = {".docx", ".docm"}


def coerce_path(path: str | Path) -> Path:
    return Path(path)


def is_office_zip(path: Path) -> bool:
    try:
        header = path.read_bytes()[:4]
    except OSError:
        return False
    return header.startswith(b"PK")


def is_excel_zip(path: Path) -> bool:
    return is_office_zip(path)


def zip_has_entry_prefix(path: Path, prefix: str) -> bool:
    import zipfile

    try:
        with zipfile.ZipFile(path) as archive:
            return any(name.replace("\\", "/").startswith(prefix) for name in archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return False


def is_word_document(path: str | Path) -> bool:
    path = coerce_path(path)
    suffix = path.suffix.lower()
    if suffix in WORD_SUFFIXES:
        return True
    if suffix in EXCEL_SUFFIXES or suffix in CSV_SUFFIXES:
        return zip_has_entry_prefix(path, "word/")
    if not path.exists() or not is_office_zip(path):
        return False
    return zip_has_entry_prefix(path, "word/")


def is_excel_workbook(path: str | Path) -> bool:
    path = coerce_path(path)
    suffix = path.suffix.lower()
    if is_word_document(path):
        return False
    if suffix in EXCEL_SUFFIXES:
        return True
    return path.exists() and zip_has_entry_prefix(path, "xl/")


def should_read_as_csv(path: str | Path) -> bool:
    path = coerce_path(path)
    suffix = path.suffix.lower()
    if suffix in CSV_SUFFIXES:
        return True
    if suffix in EXCEL_SUFFIXES:
        return path.exists() and not is_excel_zip(path)
    if suffix:
        return False
    return path.exists() and not is_excel_zip(path)


def _decode_table_bytes(raw: bytes) -> str:
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def read_csv_rows(path: str | Path) -> list[list[Any]]:
    path = coerce_path(path)
    text = _decode_table_bytes(path.read_bytes())
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
        if "\t" in sample and sample.count("\t") > sample.count(","):
            dialect = csv.excel_tab
    return list(csv.reader(io.StringIO(text), dialect))
