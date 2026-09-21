"""Fetch Unity Catalog columns from Azure Databricks and write a mapping Excel."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from src.config import get_databricks_settings

OUTPUT = ROOT / "samples" / "mappings" / "databricks_catalog_mapping.xlsx"

SKIP_CATALOGS = {"system", "samples", "hive_metastore"}
SKIP_SCHEMAS = {"information_schema"}

LAYER_TOKENS: dict[str, frozenset[str]] = {
    "bronze": frozenset({"bronze", "brz", "raw", "stg", "staging", "ml_raw"}),
    "silver": frozenset({"silver", "slv", "cleansed", "ml_silver"}),
    "gold": frozenset({"gold", "gld", "dw", "curated", "serving", "ml_output"}),
}

MAPPING_HEADERS = [
    "Source Database",
    "Source Schema",
    "Source Table",
    "Source Column",
    "Source Data Type",
    "Transformation",
    "Target Database",
    "Target Schema",
    "Target Table",
    "Target Column",
    "Target Data Type",
    "Business Rule",
    "Nullable",
    "Primary Key",
    "Notes",
]

INVENTORY_HEADERS = [
    "Catalog",
    "Schema",
    "Table",
    "Column",
    "Data Type",
    "Nullable",
    "Primary Key",
    "Ordinal",
    "Layer",
    "Full Name",
]


def _connect():
    from databricks import sql

    settings = get_databricks_settings()
    if settings.is_dummy:
        raise RuntimeError("Databricks credentials in .env are dummy. Update DATABRICKS_* first.")
    return sql.connect(
        server_hostname=settings.server_hostname,
        http_path=settings.http_path,
        access_token=settings.access_token,
        _socket_timeout=max(settings.query_timeout_seconds, 180),
    ), settings


def _fetch_all(cursor, query: str) -> list[tuple[Any, ...]]:
    cursor.execute(query)
    rows: list[tuple[Any, ...]] = []
    while True:
        batch = cursor.fetchmany(5000)
        if not batch:
            break
        rows.extend(batch)
    return rows


def classify_layer(schema: str) -> str:
    token = (schema or "").strip().lower().replace("-", "_")
    for layer, aliases in LAYER_TOKENS.items():
        if token in aliases:
            return layer
    return "other"


SNAPSHOT_TABLE_RE = re.compile(r"_\d{4}_\d{2}_\d{2}(_\d{2}_\d{2}_\d{2})?$")


def is_snapshot_table(name: str) -> bool:
    return bool(SNAPSHOT_TABLE_RE.search(name or ""))


def normalize_table(name: str) -> str:
    value = (name or "").strip().lower()
    value = re.sub(
        r"(^|_)(bronze|silver|gold|brz|slv|gld|raw|stg|staging)(_|$)",
        r"\1\3",
        value,
    )
    value = re.sub(r"^(dim|fact|stg|raw|vw|v)_", "", value)
    return re.sub(r"_+", "_", value).strip("_")


def table_match_keys(name: str) -> set[str]:
    value = normalize_table(name)
    if not value:
        return set()
    keys = {value}
    if value.endswith("ies") and len(value) > 3:
        keys.add(value[:-3] + "y")
    elif value.endswith("s") and not value.endswith(("ss", "us", "status")):
        keys.add(value[:-1])
    else:
        keys.add(value + "s")
    return keys


def normalize_column(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").strip().lower())


def yn(value: Any) -> str:
    if value is True or str(value).strip().upper() in {"Y", "YES", "TRUE", "1"}:
        return "Y"
    if value is False or str(value).strip().upper() in {"N", "NO", "FALSE", "0"}:
        return "N"
    text = str(value or "").strip().upper()
    if text in {"YES", "Y"}:
        return "Y"
    if text in {"NO", "N"}:
        return "N"
    return "Y" if text == "YES" else ("N" if text else "")


def fetch_catalog(cursor) -> tuple[list[dict[str, Any]], set[tuple[str, str, str, str]]]:
    column_rows = _fetch_all(
        cursor,
        """
        SELECT
            table_catalog,
            table_schema,
            table_name,
            column_name,
            full_data_type,
            is_nullable,
            ordinal_position
        FROM system.information_schema.columns
        WHERE table_catalog NOT IN ('system', 'samples', 'hive_metastore')
          AND table_schema NOT IN ('information_schema')
        ORDER BY table_catalog, table_schema, table_name, ordinal_position
        """,
    )

    pk_keys: set[tuple[str, str, str, str]] = set()
    try:
        pk_rows = _fetch_all(
            cursor,
            """
            SELECT
                kcu.table_catalog,
                kcu.table_schema,
                kcu.table_name,
                kcu.column_name
            FROM system.information_schema.key_column_usage kcu
            JOIN system.information_schema.table_constraints tc
              ON kcu.constraint_catalog = tc.constraint_catalog
             AND kcu.constraint_schema = tc.constraint_schema
             AND kcu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND kcu.table_catalog NOT IN ('system', 'samples', 'hive_metastore')
            """,
        )
        pk_keys = {
            (str(row[0]), str(row[1]), str(row[2]), str(row[3]))
            for row in pk_rows
        }
    except Exception:
        pk_keys = set()

    columns: list[dict[str, Any]] = []
    for catalog, schema, table, column, data_type, nullable, ordinal in column_rows:
        if catalog in SKIP_CATALOGS or schema in SKIP_SCHEMAS:
            continue
        columns.append(
            {
                "catalog": str(catalog or ""),
                "schema": str(schema or ""),
                "table": str(table or ""),
                "column": str(column or ""),
                "data_type": str(data_type or ""),
                "nullable": "Y" if str(nullable).upper() in {"YES", "Y", "TRUE"} else "N",
                "primary_key": "Y"
                if (str(catalog), str(schema), str(table), str(column)) in pk_keys
                else "N",
                "ordinal": int(ordinal or 0),
                "layer": classify_layer(str(schema or "")),
            }
        )
    return columns, pk_keys


def _index_tables(tables: list[tuple[str, str]]) -> dict[str, list[tuple[str, str]]]:
    index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for schema, table in tables:
        if is_snapshot_table(table):
            continue
        for key in table_match_keys(table):
            index[key].append((schema, table))
    return index


def _choose_target(
    source_table: str,
    candidates: list[tuple[str, str]],
) -> tuple[str, str] | None:
    if not candidates:
        return None
    unique = list(dict.fromkeys(candidates))
    source_norm = normalize_table(source_table)
    exact = [item for item in unique if normalize_table(item[1]) == source_norm]
    if exact:
        return exact[0]
    if len(unique) == 1:
        return unique[0]
    return None


def _pair_layers(
    source_tables: list[tuple[str, str]],
    target_tables: list[tuple[str, str]],
) -> tuple[list[tuple[tuple[str, str], tuple[str, str]]], set[tuple[str, str]], set[tuple[str, str]]]:
    target_index = _index_tables(target_tables)
    pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
    used_sources: set[tuple[str, str]] = set()
    used_targets: set[tuple[str, str]] = set()

    for source in sorted(source_tables, key=lambda item: item[1].lower()):
        source_schema, source_table = source
        if is_snapshot_table(source_table):
            continue
        candidates: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for key in table_match_keys(source_table):
            for candidate in target_index.get(key, []):
                if candidate not in seen:
                    seen.add(candidate)
                    candidates.append(candidate)
        chosen = _choose_target(source_table, candidates)
        if not chosen:
            continue
        pairs.append((source, chosen))
        used_sources.add(source)
        used_targets.add(chosen)
    return pairs, used_sources, used_targets


def _mapping_row(
    catalog: str,
    source: dict[str, Any] | None,
    target: dict[str, Any] | None,
    transformation: str,
    notes: str,
) -> list[Any]:
    return [
        catalog,
        (source or {}).get("schema", ""),
        (source or {}).get("table", ""),
        (source or {}).get("column", ""),
        (source or {}).get("data_type", ""),
        transformation,
        catalog if target else "",
        (target or {}).get("schema", ""),
        (target or {}).get("table", ""),
        (target or {}).get("column", ""),
        (target or {}).get("data_type", ""),
        "",
        (target or source or {}).get("nullable", ""),
        (target or source or {}).get("primary_key", ""),
        notes,
    ]


def build_mapping_rows(columns: list[dict[str, Any]]) -> tuple[list[list[Any]], list[list[Any]]]:
    by_table: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for col in columns:
        by_table[(col["catalog"], col["schema"], col["table"])].append(col)

    tables_by_catalog: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for catalog, schema, table in by_table:
        tables_by_catalog[catalog][classify_layer(schema)].append((schema, table))

    mapping_rows: list[list[Any]] = []
    unmapped_rows: list[list[Any]] = []

    for catalog, layers in sorted(tables_by_catalog.items()):
        hops: list[tuple[str, str]] = []
        if layers.get("bronze") and layers.get("silver"):
            hops.append(("bronze", "silver"))
        if layers.get("silver") and layers.get("gold"):
            hops.append(("silver", "gold"))
        if layers.get("bronze") and layers.get("gold") and not layers.get("silver"):
            hops.append(("bronze", "gold"))

        for source_layer, target_layer in hops:
            pairs, used_sources, used_targets = _pair_layers(layers[source_layer], layers[target_layer])
            hop_note = f"{source_layer} → {target_layer}"

            for (source_schema, source_table), (target_schema, target_table) in pairs:
                source_cols = by_table[(catalog, source_schema, source_table)]
                target_cols = by_table[(catalog, target_schema, target_table)]
                target_by_name = {col["column"].lower(): col for col in target_cols}
                target_by_norm = {normalize_column(col["column"]): col for col in target_cols}
                matched_target_cols: set[str] = set()

                for col in source_cols:
                    match = target_by_name.get(col["column"].lower()) or target_by_norm.get(
                        normalize_column(col["column"])
                    )
                    if match:
                        matched_target_cols.add(match["column"])
                        same_type = (col["data_type"] or "").lower() == (match["data_type"] or "").lower()
                        mapping_rows.append(
                            _mapping_row(
                                catalog,
                                col,
                                match,
                                "DIRECT" if same_type else f"CAST({col['column']} AS {match['data_type']})",
                                hop_note,
                            )
                        )
                    else:
                        unmapped_rows.append(
                            _mapping_row(
                                catalog,
                                col,
                                {
                                    "schema": target_schema,
                                    "table": target_table,
                                    "column": "",
                                    "data_type": "",
                                    "nullable": col["nullable"],
                                    "primary_key": col["primary_key"],
                                },
                                "",
                                f"No matching {target_layer} column",
                            )
                        )

                for col in target_cols:
                    if col["column"] in matched_target_cols:
                        continue
                    unmapped_rows.append(
                        _mapping_row(catalog, None, col, "", f"Target-only {target_layer} column")
                    )

            for schema, table in layers[source_layer]:
                if is_snapshot_table(table) or (schema, table) in used_sources:
                    continue
                count = len(by_table[(catalog, schema, table)])
                first = by_table[(catalog, schema, table)][0]
                unmapped_rows.append(
                    _mapping_row(
                        catalog,
                        {**first, "column": "", "data_type": ""},
                        None,
                        "",
                        f"No {target_layer} table matched ({count} columns)",
                    )
                )

            for schema, table in layers[target_layer]:
                if is_snapshot_table(table) or (schema, table) in used_targets:
                    continue
                count = len(by_table[(catalog, schema, table)])
                first = by_table[(catalog, schema, table)][0]
                unmapped_rows.append(
                    _mapping_row(
                        catalog,
                        None,
                        {**first, "column": "", "data_type": ""},
                        "",
                        f"No {source_layer} table matched ({count} columns)",
                    )
                )

    return mapping_rows, unmapped_rows


def _style_header(sheet: Worksheet, headers: list[str], fill_hex: str) -> None:
    fill = PatternFill("solid", fgColor=fill_hex)
    font = Font(bold=True, color="FFFFFF")
    sheet.append(headers)
    for cell in sheet[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(vertical="center")
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions


def _autosize(sheet: Worksheet, max_width: int = 36) -> None:
    for index, column_cells in enumerate(sheet.columns, start=1):
        width = min(max((len(str(cell.value or "")) for cell in column_cells), default=8) + 2, max_width)
        sheet.column_dimensions[get_column_letter(index)].width = max(width, 12)


def write_workbook(
    path: Path,
    *,
    settings_catalog: str,
    columns: list[dict[str, Any]],
    mapping_rows: list[list[Any]],
    unmapped_rows: list[list[Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()

    summary = workbook.active
    summary.title = "Summary"
    summary.append(["SpecQA mapping document generated from Azure Databricks Unity Catalog"])
    summary["A1"].font = Font(bold=True, size=14)
    summary.append([])
    summary.append(["Generated at (UTC)", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")])
    summary.append(["Configured DATABRICKS_CATALOG", settings_catalog or "(empty)"])
    summary.append(["Note", "Configured catalog 'main' was not found. This file uses live Unity Catalog metadata."])
    summary.append(["Catalogs included", ", ".join(sorted({col["catalog"] for col in columns}))])
    summary.append(["Tables", len({(c["catalog"], c["schema"], c["table"]) for c in columns})])
    summary.append(["Columns", len(columns)])
    summary.append(["Inferred mapping rows", len(mapping_rows)])
    summary.append(["Unmapped / gap rows", len(unmapped_rows)])
    summary.append([])
    summary.append(["How mapping was inferred"])
    summary.append(["1. Pair bronze → silver and silver → gold inside each catalog (skip dated snapshot tables)."])
    summary.append(["2. Match tables by name after stripping dim_/fact_/bronze/silver/gold prefixes (and simple plurals)."])
    summary.append(["3. Pair columns by name (case-insensitive, then ignoring punctuation)."])
    summary.append(["4. DIRECT if types match; otherwise CAST(source AS target type). Review before use."])
    summary.append([])
    summary.append(["Catalog", "Schemas", "Tables", "Columns", "Source layer", "Target layer", "Mapped columns"])

    by_catalog: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for col in columns:
        by_catalog[col["catalog"]].append(col)
    mapped_by_catalog: dict[str, int] = defaultdict(int)
    for row in mapping_rows:
        mapped_by_catalog[str(row[0])] += 1

    for catalog in sorted(by_catalog):
        cols = by_catalog[catalog]
        layers = sorted({c["layer"] for c in cols if c["layer"] != "other"})
        source = "bronze" if "bronze" in layers else ("silver" if "silver" in layers else "")
        target = "gold" if "gold" in layers else ("silver" if source == "bronze" and "silver" in layers else "")
        summary.append(
            [
                catalog,
                len({c["schema"] for c in cols}),
                len({(c["schema"], c["table"]) for c in cols}),
                len(cols),
                source,
                target,
                mapped_by_catalog.get(catalog, 0),
            ]
        )
    _autosize(summary, 80)

    mapping = workbook.create_sheet("Mapping")
    _style_header(mapping, MAPPING_HEADERS, "0C6F9E")
    for row in mapping_rows:
        mapping.append(row)
    _autosize(mapping)

    inventory = workbook.create_sheet("Inventory")
    _style_header(inventory, INVENTORY_HEADERS, "1A2836")
    for col in columns:
        inventory.append(
            [
                col["catalog"],
                col["schema"],
                col["table"],
                col["column"],
                col["data_type"],
                col["nullable"],
                col["primary_key"],
                col["ordinal"],
                col["layer"],
                f"{col['catalog']}.{col['schema']}.{col['table']}.{col['column']}",
            ]
        )
    _autosize(inventory)

    gaps = workbook.create_sheet("Gaps")
    _style_header(gaps, MAPPING_HEADERS, "8A1538")
    for row in unmapped_rows:
        gaps.append(row)
    _autosize(gaps)

    workbook.save(path)


def main() -> None:
    connection, settings = _connect()
    try:
        cursor = connection.cursor()
        print("Fetching Unity Catalog columns...")
        columns, _pk = fetch_catalog(cursor)
        print(f"Fetched {len(columns)} columns.")
        mapping_rows, unmapped_rows = build_mapping_rows(columns)
        print(f"Inferred {len(mapping_rows)} mapping rows, {len(unmapped_rows)} gap rows.")
        write_workbook(
            OUTPUT,
            settings_catalog=settings.catalog,
            columns=columns,
            mapping_rows=mapping_rows,
            unmapped_rows=unmapped_rows,
        )
        print(f"Wrote {OUTPUT}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
