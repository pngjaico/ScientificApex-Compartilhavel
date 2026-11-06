"""Render skill documentation from ``skills/registry.json`` deterministically."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- ARTICLE_MACHINE_REGISTRY_START -->"
END = "<!-- ARTICLE_MACHINE_REGISTRY_END -->"


def render(registry: dict) -> dict[str, str]:
    skills = registry["skills"]
    rows = ["# Skill Registry", "", "Generated from `skills/registry.json`; do not edit this section manually.", ""]
    for name, entry in sorted(skills.items()):
        rows.append(f"- `{name}` — {entry['status']} — {entry['origin']['provider']} — `{entry['pinned_revision']}`")
    index = "\n".join(rows) + "\n"
    canon = "# Skills Canon\n\nGenerated from `skills/registry.json`.\n\n" + "\n".join(
        f"- `{name}`: `{entry['tree_hash']}`" for name, entry in sorted(skills.items())
    ) + "\n"
    manifest = "## Skill registry (generated)\n\n" + "\n".join(
        f"- `{name}` ({entry['status']})" for name, entry in sorted(skills.items()) if entry["status"] == "active"
    ) + "\n"
    return {"SKILL_INDEX.md": index, "SKILLS_CANON.md": canon, "AGENT_MANIFEST.skills.md": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=ROOT / "skills" / "registry.json")
    parser.add_argument("--out-dir", type=Path, default=ROOT / ".machine" / "generated-skill-docs")
    parser.add_argument("--write-workspace", action="store_true")
    parser.add_argument("--check-workspace", action="store_true")
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    rendered = render(registry)
    if args.write_workspace or args.check_workspace:
        drift = []
        for source, destination in (("SKILL_INDEX.md", "SKILL_INDEX.md"), ("SKILLS_CANON.md", "SKILLS_CANON.md"), ("AGENT_MANIFEST.skills.md", "AGENT_MANIFEST.md")):
            path = ROOT / destination
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            block = START + "\n" + rendered[source] + END
            if START in current and END in current:
                before, rest = current.split(START, 1)
                _, after = rest.split(END, 1)
                expected = before + block + after
            else:
                expected = current.rstrip() + "\n\n" + block + "\n"
            if current != expected:
                drift.append(destination)
                if args.write_workspace:
                    path.write_text(expected, encoding="utf-8", newline="\n")
        print(json.dumps({"status": "block" if drift and args.check_workspace else "pass", "drift": drift}))
        return 1 if drift and args.check_workspace else 0
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in rendered.items():
        (args.out_dir / name).write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "written", "out_dir": str(args.out_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
