from pathlib import Path

from article_machine.projects import init_project
from article_machine.services.prospero_assistant import compile_prospero_40_fields
from article_machine.services.clinical_datasets import CANONICAL_RSCRIPT
from scripts.generate_workspace_graph import build_extraction


def test_contact_fields_do_not_inherit_an_author(tmp_path, monkeypatch):
    monkeypatch.delenv("USER_EMAIL", raising=False)
    project = init_project(tmp_path, "Example review", "systematic-review")
    packet = compile_prospero_40_fields(project)
    fields = packet["fields"]
    assert fields, "Compiler must persist its field packet"
    for field in fields:
        if field["key"] in {"named_contact", "named_contact_email", "organisational_affiliation"}:
            assert field["value"] == ""


def test_graph_of_minimal_clone_has_no_dangling_edges():
    extraction, communities, _, _ = build_extraction()
    identifiers = {node["id"] for node in extraction["nodes"]}
    assert identifiers
    assert all(edge["source"] in identifiers and edge["target"] in identifiers for edge in extraction["edges"])
    assert {node for members in communities.values() for node in members} == identifiers


def test_rscript_default_is_portable(monkeypatch):
    import os
    if not os.environ.get("ARTICLE_MACHINE_RSCRIPT"):
        assert CANONICAL_RSCRIPT == Path("Rscript")
