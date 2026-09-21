from pathlib import Path

import streamlit as st

from app.state.session import UPLOADS


def save_upload(upload, target_dir: Path | None = None) -> Path | None:
    if upload is None:
        return None
    directory = target_dir or UPLOADS
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / upload.name
    path.write_bytes(upload.getbuffer())
    return path


def save_uploads(uploads, target_dir: Path | None = None) -> list[Path]:
    saved: list[Path] = []
    for upload in uploads or []:
        path = save_upload(upload, target_dir)
        if path:
            saved.append(path)
    return saved


def ui_context_from_uploads(uploads) -> str:
    paths = save_uploads(uploads)
    if not paths:
        return ""
    lines = ["UI screenshots / mockups provided:"]
    lines.extend(f"- {path.name}" for path in paths)
    lines.append(
        "Analyze visible controls, labels, buttons, fields, navigation, layout, and validation messages "
        "based on the filenames and any textual references in the user story."
    )
    return "\n".join(lines)
