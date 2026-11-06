# Instalar e operar no seu computador

Abra a raiz deste clone no Antigravity e leia `GEMINI.md`. No Windows, instale Git
e uv, clone o repositório e execute `instalar.ps1`. O script usa sua própria pasta,
baixa Python 3.13 se necessário e instala o núcleo com o `uv.lock` incluído.
Não há necessidade de copiar pastas, credenciais ou ambientes de outro computador.

## Começar um projeto

No terminal da pasta clonada:

```powershell
.\.venv\Scripts\python.exe -m article_machine init "Meu estudo" --type systematic-review
.\.venv\Scripts\python.exe -m article_machine skills route --query "planejar protocolo de revisão sistemática"
.\.venv\Scripts\python.exe -m article_machine preflight projects/meu-estudo
```

Outros tipos incluem `prediction-model` e `network-meta-analysis`. Leia os quatro
contratos gerados. O projeto começa em bootstrap, com pergunta/protocolo a preencher.
O preflight poderá bloquear se o ambiente exigido estiver ausente; corrija o contrato
e instale o ambiente adequado. Não desative gates para fazer um estudo parecer pronto.

Antes da execução científica, registre e documente o protocolo final PROSPERO/OSF,
conforme o desenho e as regras aplicáveis. `registry register` só declara metadados;
não registra um estudo no provedor. `registry verify` exige evidência revisada real.
O planejamento anterior ao registro continua permitido.

```powershell
.\.venv\Scripts\python.exe -m article_machine workflow plan projects/meu-estudo --query "preparar protocolo" --language pt-BR
.\.venv\Scripts\python.exe -m article_machine context build projects/meu-estudo --mode bootstrap --hypothesis "Pergunta a definir"
```

Depois dos gates, siga o desenho: fontes com proveniência, extração verificável,
análise reproduzível, claims e referências sincronizados, redação PT-BR/EN, revisão
e exportação. Use `--help` em cada subcomando. Nenhum dado real vem neste clone.

## Recursos adicionais

- R: instale a versão exigida pelo projeto e restaure o renv.lock apropriado.
  Configure o executável e o lock em compute.yaml. Bibliotecas R não vêm no Git.
- ML: os pyproject.toml e uv.lock em modelos/aprendizado_de_maquina_clinico
  definem ambientes próprios. Instale apenas o ambiente necessário com
  `uv sync --directory modelos/aprendizado_de_maquina_clinico`.
- Browser/Quarto/Zotero: instale e valide separadamente quando necessários.
- APIs e bases restritas: forneça suas próprias credenciais e autorizações;
  não coloque segredos no Git nem envie dados humanos sem autorização.
- Skills: `skills/registry.json` registra origem/licença/proveniência. Skills que
  mencionam catálogos externos exigem obtê-los separadamente; cópias desses
  repositórios e assinaturas comerciais não estão incluídas.

## Grafo operacional

```powershell
.\.venv\Scripts\python.exe scripts/generate_workspace_graph.py
.\.venv\Scripts\python.exe -m article_machine graph query "protocol evidence gates" --limit 5
```

O grafo gerado representa este clone. Não use o grafo de estudos de outra pessoa.

## Proteção dos seus arquivos

Projetos e arquivos pessoais são ignorados por padrão. Para compartilhar um estudo,
crie um repositório separado e revise dados, consentimento, licença e credenciais.
Templates e demonstrações em modelos/ não constituem evidência científica.
Declare as ferramentas de IA realmente usadas; não copie disclosure com modelo
ou autoria de outra pessoa. Leia o relatório de validação desta distribuição.

## Outros sistemas

O instalador foi preparado para Windows. Em Linux/macOS, use `uv sync --locked
--no-dev --python 3.13` e `.venv/bin/python -m article_machine --help`.
Ajuste compute.yaml para `.venv/bin/python` e caminhos locais. Essas plataformas
não foram executadas nesta entrega; recursos de navegador/exportação podem exigir
adaptação adicional. R, ML e integrações externas não foram validados neste clone.
