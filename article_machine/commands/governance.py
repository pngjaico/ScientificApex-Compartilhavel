from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..benchmarks import aggregate_benchmark_payload, validate_benchmark_payload


def record_blocked_attempt(project_dir: Path, command: str, payload: dict[str, Any]) -> Path:
    """Persist a blocked intent without creating a gate-eligible Task Packet."""

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = Path(project_dir) / ".machine" / "attempts" / f"{timestamp}_{command}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "contract": "BlockedAttemptV1",
        "gate_eligible": False,
        "recorded_at": datetime.now(UTC).isoformat(),
        "command": command,
        "payload": payload,
    }
    output.write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def aggregate_benchmark_file(
    project_dir: Path,
    *,
    input_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    project_dir = Path(project_dir)
    source = input_path or project_dir / "benchmarks" / "cases.json"
    destination = output_path or project_dir / "analysis" / "benchmark_report.json"
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            "contract": "AgentBenchmarkAggregateCommandV2",
            "status": "block",
            "gate_eligible": False,
            "issues": [f"Benchmark case input is unreadable: {exc}."],
            "input": str(source),
        }
    if not isinstance(payload, dict):
        return {
            "contract": "AgentBenchmarkAggregateCommandV2",
            "status": "block",
            "gate_eligible": False,
            "issues": ["Benchmark case input must be a JSON object."],
            "input": str(source),
        }
    report = aggregate_benchmark_payload(payload)
    validation = validate_benchmark_payload(report, source_path=destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "contract": "AgentBenchmarkAggregateCommandV2",
        "status": validation["status"],
        "gate_eligible": validation["gate_eligible"],
        "input": str(source),
        "output": str(destination),
        "validation": validation,
    }
