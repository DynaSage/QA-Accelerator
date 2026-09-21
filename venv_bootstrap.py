"""Re-launch the current script with the project virtual environment when needed."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def ensure_project_venv(project_root: Path | None = None) -> None:
    if sys.prefix != sys.base_prefix:
        return

    root = project_root or Path(__file__).resolve().parent
    venv_dir = root / ".venv"
    if os.name == "nt":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    if not venv_python.exists():
        print(f"Virtual environment not found at {venv_dir}")
        print("Run setup first:")
        print("  .\\setup.ps1   (Windows)")
        print("  python -m venv .venv && pip install -r requirements.txt")
        sys.exit(1)

    result = subprocess.call([str(venv_python), *sys.argv])
    sys.exit(result)
