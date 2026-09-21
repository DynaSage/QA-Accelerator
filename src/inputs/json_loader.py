import json
from pathlib import Path

from src.models.etl_spec import ETLSpecModel


def load_etl_spec_from_json(path: Path) -> ETLSpecModel:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ETLSpecModel.model_validate(payload)
