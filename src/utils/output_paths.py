from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def unique_output_path(
    directory: Path,
    prefix: str,
    suffix: str,
    *,
    run_id: str | None = None,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    token = (run_id or uuid4().hex)[:8]
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return directory / f"{prefix}_{timestamp}_{token}{suffix}"


def safe_write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
