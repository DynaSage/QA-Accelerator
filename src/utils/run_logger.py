import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RunLogger:
    def __init__(self, runs_dir: Path | None = None) -> None:
        self.runs_dir = runs_dir or Path("runs")
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        *,
        run_id: str,
        spec_id: str | None,
        spec_name: str,
        result: dict[str, Any],
        report_path: str,
        test_cases_path: str | None = None,
    ) -> Path:
        executions = result.get("execution_results") or []
        status_counts: dict[str, int] = {}
        for item in executions:
            status = item.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        payload = {
            "run_id": run_id,
            "run_at": datetime.now(UTC).isoformat(),
            "spec_id": spec_id,
            "spec_name": spec_name,
            "source_table": (result.get("etl_spec") or {}).get("source_table"),
            "target_table": (result.get("etl_spec") or {}).get("target_table"),
            "test_count": len(result.get("tests") or []),
            "test_case_count": len(result.get("test_cases") or []),
            "execution_summary": status_counts,
            "report_path": report_path,
            "test_cases_path": test_cases_path,
            "rejected_queries": result.get("rejected_queries") or [],
        }
        path = self.runs_dir / f"{run_id}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def list_runs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        runs: list[dict[str, Any]] = []
        for path in sorted(self.runs_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            payload = json.loads(path.read_text(encoding="utf-8"))
            runs.append(payload)
            if len(runs) >= limit:
                break
        return runs

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        path = self.runs_dir / f"{run_id}.json"
        if not path.exists():
            matches = sorted(self.runs_dir.glob(f"{run_id}*.json"))
            if not matches:
                return None
            path = matches[0]
        return json.loads(path.read_text(encoding="utf-8"))
