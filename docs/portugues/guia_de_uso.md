# Guia de uso

ScientificApex / Article Machine é uma máquina científica de código aberto, composta por CLI Python, contratos de projeto, gates de evidência e revisão, documentação e skills. Pode ser usada no terminal, com qualquer agente que consiga ler os arquivos do repositório, ou em fluxo combinado. O núcleo não exige provedor, modelo, conta ou agente específico de IA.

## Instalação do clone completo

Instale Git e [uv](https://docs.astral.sh/uv/), clone o repositório e entre na pasta. O clone é necessário para usar a máquina completa: skills, modelos, documentação e arquivos operacionais não são entregues por um wheel Python isolado.

### Windows (PowerShell)

```powershell
git clone https://github.com/pngjaico/ScientificApex-Compartilhavel.git
cd ScientificApex-Compartilhavel
powershell -NoProfile -ExecutionPolicy Bypass -File .\instalar.ps1
```

Use `-Development` para instalar dependências de desenvolvimento. Use `-VerifyOnly` para verificar uma instalação existente sem sincronizar pacotes. O script cria e usa `.venv` neste clone.

### Linux ou macOS (Bash)

```sh
git clone https://github.com/pngjaico/ScientificApex-Compartilhavel.git
cd ScientificApex-Compartilhavel
bash instalar.sh
```

Use `--development` para dependências de desenvolvimento ou `--verify-only` para verificar uma instalação existente. O núcleo e o instalador em modo de verificação passaram no CI Ubuntu/Linux. macOS não foi testado; integrações opcionais precisam de validação específica.

Os instaladores sincronizam dependências travadas com `uv.lock` e verificam CLI e auditoria operacional estrita. Precisam de acesso à internet durante a instalação de pacotes. Não instalam R, ML/DL, navegador, Zotero, Quarto, provedores externos ou modelo de IA; também não configuram conta ou credenciais de agente.

## Criar e preparar um projeto

Use o interpretador do clone:

```powershell
.\.venv\Scripts\python.exe -m article_machine --help
.\.venv\Scripts\python.exe -m article_machine init "Meu estudo" --type systematic-review
.\.venv\Scripts\python.exe -m article_machine preflight projects/meu-estudo
```

Em Linux/macOS, substitua o caminho do interpretador por `.venv/bin/python`. Tipos adicionais incluem `prediction-model` e `network-meta-analysis`. Leia `project.yaml`, `protocol.yaml`, `standards.yaml` e `compute.yaml`; preencha-os com informações verificadas e prepare um Task Packet antes do trabalho científico. Use `skills route --query "..."` para localizar orientações relevantes, sem supor que a ferramenta externa descrita pela skill esteja instalada.

Comece com planejamento e protocolo. Antes de corpus, triagem, extração, análise, descoberta ou redação científica, cumpra o gate aplicável de protocolo e registro final PROSPERO/OSF, conforme desenho e regras vigentes. Planejar e preparar o protocolo antes do registro é permitido. Comandos locais podem compilar ou revisar metadados e evidências, mas não registram um estudo no serviço externo. Não invente IDs, aprovação ética, autoria ou declaração de registro prospectivo.

Depois de liberados os gates, preserve proveniência das fontes e decisões de extração, faça análises reproduzíveis, sincronize `evidence/claim_map.jsonl` e `drafts/references.bib`, e use Evidence Lock e Review Trinity nos pontos exigidos. Entregas científicas novas devem ter versões em português e inglês, com números, citações, incerteza e disclosure verdadeiro das ferramentas utilizados preservados. PASS operacional não valida método, segurança clínica ou prontidão de publicação.

## Ambientes opcionais

Configure somente o que o projeto exige e registre a configuração real em `compute.yaml`.

- **R:** instale a versão do projeto e restaure o `renv.lock` correspondente. R e bibliotecas não são instalados pelo instalador principal.
- **ML/DL:** os ambientes separados em `modelos/aprendizado_de_maquina_clinico/` e subpastas têm seus próprios `pyproject.toml`/locks. Exemplo: `uv sync --directory modelos/aprendizado_de_maquina_clinico`.
- **Navegador:** siga os arquivos de lock e instruções do ambiente Playwright local; perfis autenticados não são distribuídos.
- **Quarto, Zotero, catálogos, plugins e APIs:** instale ou configure separadamente quando necessários. Use credenciais próprias, não as registre no Git, e confira permissões e termos do serviço.

Uma skill é orientação textual, não uma integração ativa nem validação da disponibilidade do serviço descrito.

## Dados, privacidade e limites

Use dados sintéticos ou cujo processamento esteja autorizado. Não versione dados pessoais, dados em nível de paciente, manuscritos privados, credenciais ou perfis de conta. Não envie dados humanos a serviços externos sem autorização e salvaguardas aplicáveis. Projetos novos ficam sob `projects/<id>/`; revise o conteúdo antes de criar um repositório separado para compartilhamento. Modelos e demonstrações são exemplos de software, não estudos aprovados nem evidência.

O relatório de validação documenta escopo e limitações dos checks executados. O núcleo foi validado localmente em Windows e no CI Windows/Ubuntu. macOS, ambientes R e ML/DL, integrações externas e validade clínica não foram verificados. A camada própria usa Apache-2.0; terceiros mantêm seus termos. Consulte LICENSE_SCOPE.md e a política por skill para o escopo atual e as adaptações.

## Grafo operacional

Quando disponível, gere ou atualize o grafo deste clone e use-o para navegação:

```powershell
.\.venv\Scripts\python.exe scripts/generate_workspace_graph.py
.\.venv\Scripts\python.exe -m article_machine graph query "protocol evidence gates" --limit 5
```

No Unix, use `.venv/bin/python`. O grafo serve para localizar componentes, não para provar claims científicos.

Veja também [AGENTS.md](../../AGENTS.md), [como contribuir](../../CONTRIBUTING.md), [guia em inglês](../ingles/guia_de_uso.md), [créditos](creditos_opensource.md), [avisos de terceiros](../../THIRD_PARTY_NOTICES.md) e [relatório de validação](relatorio_validacao.md).
