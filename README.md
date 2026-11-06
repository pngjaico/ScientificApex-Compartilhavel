# ScientificApex: máquina científica para Antigravity

Distribuição independente da Article Machine 0.3.0. Inclui o runtime, skills,
modelos de trabalho, locks de dependências e instruções. Não inclui estudos,
coortes, manuscritos, credenciais, perfil de pesquisador ou histórico do workspace
de origem. Os modelos são exemplos vazios ou demonstrações, não estudos aprovados.

## Instalação no Windows

1. Instale Git e uv. Consulte as instruções oficiais: https://git-scm.com/install/windows
   e https://docs.astral.sh/uv/getting-started/installation/ .
2. Clone este repositório em uma pasta sua e abra essa pasta no Antigravity.
3. No terminal PowerShell da pasta clonada, execute:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\instalar.ps1
```

O instalador baixa Python 3.13 e dependências travadas pelo uv, cria somente a
`.venv` deste clone e verifica o runtime e a auditoria operacional. Não instala
R, modelos de IA, navegadores ou extensões; não configura credenciais nem consulta
bases científicas. Requer internet para instalar dependências. Depois, o núcleo
funciona sem uma API de IA própria; o agente do Antigravity usa a sua configuração.

Para desenvolvimento e testes, use `-Development`. Para auditar sem baixar pacotes,
use `-VerifyOnly` depois da instalação. Leia [o guia](docs/portugues/guia_de_uso.md).

## Pedido para colar no Antigravity

> Leia GEMINI.md, AGENTS.md e docs/portugues/guia_de_uso.md. Instale esta máquina
> usando instalar.ps1 e confira a auditoria. Pergunte meu tema e desenho do estudo,
> crie um projeto novo e prepare o protocolo. Não invente autoria, dados ou registro.
> Não execute trabalho científico antes dos gates de registro e protocolo.

## Limites

O núcleo instala organização, protocolos, roteamento, controle de evidências e
CLI. Análises R, ML/DL, Zotero, navegadores, catálogos externos e plugins têm
dependências próprias, configuradas por projeto. Uma skill instalada não instala
o software que descreve. `compute.yaml` deve refletir o computador do usuário.
Nenhum PASS operacional aprova um estudo ou garante aceitação editorial.

As licenças e origens de componentes terceiros constam de `skills/registry.json`
e dos avisos incluídos. Não se concede licença nova a material de terceiros.

English instructions: [usage guide](docs/ingles/guia_de_uso.md).
