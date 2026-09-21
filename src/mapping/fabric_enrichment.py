"""Optional Fabric / Data Nexus metadata enrichment onto canonical mappings."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.models.mapping_analysis import UNKNOWN


def _qualified(endpoint: dict[str, Any]) -> str:
    parts = [
        endpoint.get("database") or "",
        endpoint.get("schema") or "",
        endpoint.get("table") or "",
    ]
    cleaned = [part for part in parts if part and part != UNKNOWN]
    return ".".join(cleaned).lower()


def _column_meta(catalog: dict[str, Any], endpoint: dict[str, Any]) -> dict[str, Any]:
    tables = catalog.get("tables") or catalog
    table_key = _qualified(endpoint)
    table = tables.get(table_key) or tables.get((endpoint.get("table") or "").lower()) or {}
    columns = table.get("columns") or {}
    column = (endpoint.get("column") or "").lower()
    return columns.get(column) or columns.get(endpoint.get("column") or "") or {}


def load_platform_metadata(path: str | Path | None = None) -> dict[str, Any]:
    candidate = Path(path or os.getenv("FABRIC_METADATA_PATH", "") or "samples/metadata/fabric_columns.json")
    if not candidate.exists():
        return {}
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def enrich_mappings(mappings: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    catalog = metadata if metadata is not None else load_platform_metadata()
    if not catalog:
        return mappings

    enriched: list[dict[str, Any]] = []
    for mapping in mappings:
        item = json.loads(json.dumps(mapping))
        for side in ("source", "target"):
            endpoint = item.get(side) or {}
            meta = _column_meta(catalog, endpoint)
            if not meta:
                continue
            if (endpoint.get("data_type") in {"", UNKNOWN}) and meta.get("data_type"):
                endpoint["data_type"] = str(meta["data_type"])
                endpoint["data_type_source"] = "fabric_metadata"
            elif meta.get("data_type") and str(meta["data_type"]).lower() != str(endpoint.get("data_type") or "").lower():
                endpoint["metadata_data_type"] = str(meta["data_type"])
                item.setdefault("enrichment_flags", []).append(
                    f"{side} datatype mismatch vs platform metadata "
                    f"({endpoint.get('data_type')} vs {meta['data_type']})"
                )
            if (endpoint.get("nullable") in {"", UNKNOWN}) and meta.get("nullable") is not None:
                endpoint["nullable"] = "Y" if meta["nullable"] else "N"
            if (endpoint.get("primary_key") in {"", UNKNOWN}) and meta.get("primary_key") is not None:
                endpoint["primary_key"] = "Y" if meta["primary_key"] else "N"
            item[side] = endpoint
        enriched.append(item)
    return enriched
