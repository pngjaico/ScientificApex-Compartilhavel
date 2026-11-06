import json

from scripts.auditar_licencas import audit


def _distribution(tmp_path):
    (tmp_path / "skills/example").mkdir(parents=True)
    (tmp_path / "skills/example/SKILL.md").write_text("# Example\n", encoding="utf-8")
    (tmp_path / "third_party").mkdir()
    for name in ("LICENSE", "NOTICE", "LICENSE_SCOPE.md", "THIRD_PARTY_NOTICES.md"):
        (tmp_path / name).write_text("Example fixture\n", encoding="utf-8")
    record = {
        "license": "Apache-2.0",
        "classification": "first-party",
        "origin": {"url": "https://github.com/example/project"},
        "evidence": {"basis": "Example owner grant"},
    }
    policy = {"skills": {"example": record}}
    (tmp_path / "third_party/politica_licencas.json").write_text(json.dumps(policy), encoding="utf-8")
    (tmp_path / "skills/registry.json").write_text(
        json.dumps({"skills": {"example": {"license": "Apache-2.0"}}}), encoding="utf-8"
    )
    return policy


def test_release_blocks_new_skill_without_license_scope(tmp_path):
    _distribution(tmp_path)
    assert audit(tmp_path)["status"] == "pass"
    (tmp_path / "skills/unreviewed").mkdir()
    (tmp_path / "skills/unreviewed/SKILL.md").write_text("# New dependency\n", encoding="utf-8")
    assert audit(tmp_path)["status"] == "block"


def test_release_blocks_third_party_without_license_evidence(tmp_path):
    policy = _distribution(tmp_path)
    policy["skills"]["example"]["classification"] = "third-party"
    (tmp_path / "third_party/politica_licencas.json").write_text(json.dumps(policy), encoding="utf-8")
    report = audit(tmp_path)
    assert report["status"] == "block"
    assert any("third-party license evidence" in issue for issue in report["issues"])


def test_release_blocks_license_drift_between_registry_and_policy(tmp_path):
    _distribution(tmp_path)
    (tmp_path / "skills/registry.json").write_text(
        json.dumps({"skills": {"example": {"license": "MIT"}}}), encoding="utf-8"
    )
    assert audit(tmp_path)["status"] == "block"
