import json
from pathlib import Path

from src.inputs.json_loader import load_etl_spec_from_json
from src.metadata.store import MetadataStore


def test_metadata_store_saves_and_loads_spec(tmp_path: Path):
    db_path = tmp_path / "qa.db"
    store = MetadataStore(db_path)
    spec = load_etl_spec_from_json(Path("samples/specs/sample_etl_spec.json"))
    saved = store.save_spec(spec, name="customer_dim")
    loaded = store.get_spec(saved["id"])

    assert loaded is not None
    assert loaded["name"] == "customer_dim"
    assert loaded["version"] == 1
    assert loaded["content"]["source_table"] == spec.source_table


def test_metadata_store_versions_specs(tmp_path: Path):
    store = MetadataStore(tmp_path / "qa.db")
    spec = load_etl_spec_from_json(Path("samples/specs/sample_etl_spec.json"))
    first = store.save_spec(spec, name="customer_dim")
    second = store.save_spec(spec, name="customer_dim")

    assert first["version"] == 1
    assert second["version"] == 2
    latest = store.get_latest_spec_by_name("customer_dim")
    assert latest is not None
    assert latest["version"] == 2
