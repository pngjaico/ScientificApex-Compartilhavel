"""Fail on unscoped bundled skills; do not confuse this with a legal audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"Apache-2.0", "MIT", "BSD-3-Clause", "CC-BY-4.0", "Apache-2.0 AND CC-BY-4.0"}


def audit(root: Path = ROOT) -> dict:
    policy_path = root / "third_party/politica_licencas.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    registry = json.loads((root / "skills/registry.json").read_text(encoding="utf-8"))["skills"]
    issues = []
    installed = {item.parent.name for item in (root / "skills").glob("*/SKILL.md")}
    if set(policy["skills"]) != installed:
        issues.append("License policy and installed skill set differ.")
    for name in sorted(installed):
        record = policy["skills"].get(name, {})
        if record.get("license") not in ALLOWED:
            issues.append(f"{name}: unsupported or unresolved license.")
        if record.get("classification") not in {"first-party", "third-party"}:
            issues.append(f"{name}: missing origin classification.")
        if not record.get("origin", {}).get("url", "").startswith("https://github.com/"):
            issues.append(f"{name}: missing public source reference.")
        if not record.get("evidence"):
            issues.append(f"{name}: missing documentary evidence.")
        if registry.get(name, {}).get("license") != record.get("license"):
            issues.append(f"{name}: registry and policy license differ.")
        license_path = record.get("evidence", {}).get("license_text")
        if record.get("classification") == "third-party" and not license_path:
            issues.append(f"{name}: third-party license evidence is missing.")
        if license_path and not (root / license_path).is_file():
            issues.append(f"{name}: upstream license text is missing.")
    for record in policy.get("embedded_sources", []):
        if record.get("license") not in ALLOWED or not (root / record["license_text"]).is_file():
            issues.append(f"{record.get('path')}: embedded source license missing.")
    for required in ("LICENSE", "NOTICE", "LICENSE_SCOPE.md", "THIRD_PARTY_NOTICES.md"):
        if not (root / required).is_file():
            issues.append(f"{required}: required license document missing.")
    if any("CC-BY-4.0" in record.get("license", "") for record in policy["skills"].values()):
        if not (root / "third_party/licenses/CC-BY-4.0.txt").is_file():
            issues.append("CC-BY-4.0 legal text is missing.")
    return {
        "status": "pass" if not issues else "block",
        "checked_skills": len(installed),
        "scope": "Current bundled source; documentary checks only, not legal certification",
        "issues": issues,
    }


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["status"] == "pass" else 1)
