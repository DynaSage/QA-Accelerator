import io
import json
import zipfile
from pathlib import Path
from typing import Any


def export_qa_pack_zip(
    *,
    run_id: str,
    result: dict[str, Any],
    report_path: Path | None = None,
    test_cases_path: Path | None = None,
    extra_files: dict[str, str | bytes] | None = None,
) -> bytes:
    buffer = io.BytesIO()
    prefix = f"qa_pack_{run_id[:8]}"

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        summary = {
            "run_id": run_id,
            "spec_name": result.get("spec_name"),
            "test_count": len(result.get("tests") or []),
            "test_case_count": len(result.get("test_cases") or []),
            "execution_summary": result.get("execution_summary") or {},
            "report_path": str(report_path) if report_path else "",
            "test_cases_path": str(test_cases_path) if test_cases_path else "",
        }
        archive.writestr(f"{prefix}/run_summary.json", json.dumps(summary, indent=2))

        if report_path and report_path.exists():
            archive.write(report_path, arcname=f"{prefix}/{report_path.name}")

        if test_cases_path and test_cases_path.exists():
            archive.write(test_cases_path, arcname=f"{prefix}/{test_cases_path.name}")

        if result.get("etl_spec"):
            archive.writestr(
                f"{prefix}/etl_spec.json",
                json.dumps(result["etl_spec"], indent=2),
            )

        if result.get("test_case_artifacts"):
            archive.writestr(
                f"{prefix}/test_case_artifacts.json",
                json.dumps(result["test_case_artifacts"], indent=2),
            )

        if result.get("execution_results"):
            archive.writestr(
                f"{prefix}/sql_execution_results.json",
                json.dumps(result["execution_results"], indent=2, default=str),
            )

        for name, content in (extra_files or {}).items():
            if isinstance(content, bytes):
                archive.writestr(f"{prefix}/{name}", content)
            else:
                archive.writestr(f"{prefix}/{name}", content)

    return buffer.getvalue()
