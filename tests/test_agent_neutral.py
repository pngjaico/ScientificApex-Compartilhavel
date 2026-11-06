from article_machine.services.publication_packager import prepare_publication_package


def test_publication_scaffold_does_not_attest_default_ai_provider(tmp_path):
    prepare_publication_package(tmp_path, "Example Journal", "example")
    drafts = list((tmp_path / "publicacoes").rglob("*.md"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in drafts)
    assert "PENDING AUTHOR VERIFICATION" in text
    assert "PENDENTE DE VERIFICAÇÃO PELOS AUTORES" in text
    assert "[AI tool and version actually used]" in text
    assert "[provider]" in text
    assert "Claude Opus" not in text
    assert "Anthropic" not in text
