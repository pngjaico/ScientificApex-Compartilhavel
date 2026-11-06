"""Portable checksums for the tracked source distribution (not local research)."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "manifesto_distribuicao.json"
POLICY = "SHA-256; valid UTF-8 without NUL: CRLF normalized to LF; binary: exact bytes"


def digest(path: Path) -> str:
    content = path.read_bytes()
    if b"\0" not in content:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Refresh manifest from the Git index path list")
    args = parser.parse_args()
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    paths = sorted(path for path in paths if path and path != MANIFEST)
    forbidden = [path for path in paths if path.startswith(("projects/", "sources/", ".machine/", ".venv/"))]
    if forbidden:
        print(json.dumps({"status": "block", "issue": "Private workspace areas are tracked", "paths": forbidden}))
        return 1
    manifest_path = ROOT / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    actual = [{"path": path, "sha256": digest(ROOT / path)} for path in paths]
    if args.write:
        manifest["contract"] = "PortableDistributionV2"
        manifest["hash_policy"] = POLICY
        manifest["files"] = actual
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    valid = manifest.get("hash_policy") == POLICY and manifest.get("files") == actual
    print(
        json.dumps(
            {
                "status": "pass" if valid else "block",
                "source_files": len(actual),
                "hash_policy": POLICY,
                "private_source_paths": len(forbidden),
            }
        )
    )
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
