# Guia de Operação 100% na Nuvem — `ScientificApex-Compartilhavel`
> **Para Agentes de IA (Antigravity Cloud, OpenAI Codex Cloud, xAI Grokbot, Claude Code & GitHub Codespaces)**

Este arquivo (`.agents/CLOUD_GUIDE.md`) ensina qualquer agente autônomo ou desenvolvedor na nuvem a operar, compilar, testar e localizar arquivos de suporte deste projeto **sem depender do computador local**.

---

## 1. Identidade e Arquitetura
- **Repositório GitHub:** `https://github.com/pngjaico/ScientificApex-Compartilhavel`
- **Stack Principal:** Python 3 / R — Versão compartilhável e higienizada do framework ScientificApex para colaboradores.
- **Branch Padrão:** `main`

### Mapa de Branches & Variantes Disponíveis
- **`main`** (Branch Padrão)

> **Atenção Agentes:** Se existir a branch `sync-pc-2026-11-08` ou branches de variantes listadas acima, verifique-as com `git branch -a` / `git checkout <branch>` caso procure experimentos específicos ou o último snapshot incremental do PC.

---

## 2. Referenciação Cruzada no Google Drive (`pngjaico@gmail.com`)

Todo material que **não é código** (datasets, PDFs, pacotes mínimos de assets, dumps e backups) e todos os **segredos/credenciais** vivem no Google Drive estruturado:

1. **Pasta do Projeto no Drive (`Projetos/ScientificApex-Compartilhavel/`):**
   - **Link Direto:** https://drive.google.com/drive/folders/1u0oiPf1uVC10uBP7sCIhi-66q3lIWK_S
   - **Subpastas padrão:** `docs/`, `dados/`, `assets/`, `backups/`
2. **Pasta Restrita de Segredos e Dados Sensíveis (`Projetos/_Restrito/ScientificApex-Compartilhavel/`):**
   - **Link Direto:** https://drive.google.com/drive/folders/1OpCGq67uYpJbxjiaILsZ9b27CVysWtQ7
   - **Itens Restritos / Segredos Mapeados:**
  - `Veja Projetos/_Restrito/ScientificApex-AI`
3. **Pasta Raiz `Projetos/` no Drive:**
   - **Link Direto:** https://drive.google.com/drive/folders/11nh7YZ7hJ0xYaKB18po5QJYuKgWrcM3R

---

## 3. Comandos de Execução no Ambiente Cloud (Codespaces / Antigravity / Codex / Grokbot)

- **Instalação de dependências:**
  ```bash
  python -m pip install -r requirements.txt
  ```
- **Ambiente de Desenvolvimento (Dev Server / CLI):**
  ```bash
  python -m article_machine.cli --help
  ```
- **Build / Empacotamento:**
  ```bash
  python -m pytest tests -q
  ```
- **Testes / Verificação:**
  ```bash
  python -m pytest tests -q
  ```

---

## 4. Variáveis de Ambiente e Regras de Segurança
- **Variáveis mapeadas (`.env.example`):** `SCOPUS_API_KEY`, `NCBI_API_KEY`, `CROSSREF_MAILTO`, `UNPAYWALL_EMAIL`
- **Regra de Ouro:** Nunca faça commit de arquivos `.env` reais, chaves `.json` de Service Accounts do Firebase/GCP, chaves `.key` ou dados identificáveis de pacientes no GitHub. Injete-os apenas como **Secrets** do ambiente cloud (GitHub Codespaces Secrets / Codex Environment Variables) buscando os valores em `Projetos/_Restrito/ScientificApex-Compartilhavel/`.
