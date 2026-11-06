"""Tests for OSF API v2 client and registration evidence bridge."""

import io
import json
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pytest

from article_machine.projects import init_project
from article_machine.services.osf import (
    fetch_and_save_osf_evidence,
    fetch_osf_registration,
    get_osf_token,
    verify_osf_connection,
)
from article_machine.services.protocol_registration import registration_gate, verify_protocol_registration
from article_machine.zero_trust import validate_provider_specs


def test_osf_provider_spec_is_valid() -> None:
    report = validate_provider_specs()
    assert report["status"] == "pass"
    assert "osf" in report["providers"]


def test_get_osf_token_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OSF_TOKEN", "mock_token_123")
    assert get_osf_token(tmp_path) == "mock_token_123"


def test_get_osf_token_from_env_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OSF_TOKEN", raising=False)
    monkeypatch.delenv("OSF_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("SOME_VAR=xyz\nOSF_TOKEN='mock_file_token_456'\n", encoding="utf-8")
    assert get_osf_token(tmp_path) == "mock_file_token_456"


def test_verify_osf_connection_success() -> None:
    mock_payload = {
        "data": {
            "id": "mock_user",
            "type": "users",
            "attributes": {
                "full_name": "Test Researcher",
                "date_registered": "2026-01-01T00:00:00Z",
            },
        }
    }
    mock_resp = io.BytesIO(json.dumps(mock_payload).encode("utf-8"))

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = verify_osf_connection(token="test_token")
        assert res["status"] == "pass"
        assert res["user_id"] == "mock_user"
        assert res["full_name"] == "Test Researcher"
        assert res["authenticated"] is True


def test_verify_osf_connection_unauthorized() -> None:
    http_error = urllib.error.HTTPError("https://api.osf.io/v2/users/me/", 401, "Unauthorized", {}, None)
    with patch("urllib.request.urlopen", side_effect=http_error):
        res = verify_osf_connection(token="bad_token")
        assert res["status"] == "blocked"
        assert any("401 Unauthorized" in issue for issue in res["issues"])


def test_fetch_osf_registration_rejects_malformed_id() -> None:
    res = fetch_osf_registration("inv!d")
    assert res["status"] == "blocked"
    assert any("Invalid OSF registration identifier" in issue for issue in res["issues"])


def test_fetch_osf_registration_rejects_non_registration_type() -> None:
    mock_payload = {
        "data": {
            "id": "abc12",
            "type": "nodes",  # project, not registration
            "attributes": {"title": "Test Project"},
        }
    }
    mock_resp = io.BytesIO(json.dumps(mock_payload).encode("utf-8"))
    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = fetch_osf_registration("abc12", token="test_token")
        assert res["status"] == "blocked"
        msg = "requires a finalized OSF registration, not an OSF project or node"
        assert any(msg in issue for issue in res["issues"])


def test_fetch_osf_registration_rejects_pending_or_withdrawn() -> None:
    mock_payload = {
        "data": {
            "id": "abc12",
            "type": "registrations",
            "attributes": {
                "title": "Pending Study",
                "date_registered": "2026-01-01T00:00:00Z",
                "pending_registration_approval": True,
                "withdrawn": False,
            },
        }
    }
    mock_resp = io.BytesIO(json.dumps(mock_payload).encode("utf-8"))
    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = fetch_osf_registration("abc12", token="test_token")
        assert res["status"] == "blocked"
        assert res["is_final"] is False
        assert any("pending registration approval" in issue for issue in res["issues"])


def test_fetch_and_save_osf_evidence_end_to_end(tmp_path: Path) -> None:
    project = init_project(tmp_path, "OSF Pipeline Test", "systematic-review")
    from article_machine.serialization import load_structured_file, save_structured_file

    protocol = load_structured_file(project / "protocol.yaml")
    protocol["status"] = "frozen"
    save_structured_file(project / "protocol.yaml", protocol)

    mock_payload = {
        "data": {
            "id": "osfreg123",
            "type": "registrations",
            "attributes": {
                "title": "Clinical Systematic Review on Preoperative Fasting",
                "description": "Preregistration of protocol and search strategy",
                "date_registered": "2025-06-01T12:00:00.000000Z",
                "public": True,
                "pending_registration_approval": False,
                "pending_embargo_approval": False,
                "withdrawn": False,
                "article_doi": "10.17605/OSF.IO/OSFREG123",
            },
            "links": {"html": "https://osf.io/osfreg123/"},
        }
    }
    mock_resp = io.BytesIO(json.dumps(mock_payload).encode("utf-8"))

    with patch("urllib.request.urlopen", return_value=mock_resp):
        save_res = fetch_and_save_osf_evidence(
            project,
            registration_id="osfreg123",
            reviewer="Dr. Named Reviewer",
            token="test_token",
        )
        assert save_res["status"] == "pass"
        assert save_res["registration_id"] == "osfreg123"
        assert (project / save_res["snapshot_path"]).is_file()
        assert (project / save_res["scaffold_path"]).is_file()

    # Now verify the registration using the scaffold
    scaffold_path = project / save_res["scaffold_path"]
    verify_res = verify_protocol_registration(project, scaffold_path)
    assert verify_res["status"] == "pass"

    # Gate should now pass!
    gate_res = registration_gate(project, "analysis", mark_started=True)
    assert gate_res["status"] == "pass"
