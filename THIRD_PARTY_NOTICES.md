# Créditos de terceiros / Third-party acknowledgements

Esta máquina depende do trabalho de muitas comunidades. Agradecemos aos autores,
mantenedores e colaboradores. Não reivindicamos como próprias as bibliotecas,
skills, métodos ou documentações dessas fontes.

This machine builds on many communities. We thank their authors, maintainers and
contributors and do not claim their libraries, skills, methods or documentation
as our original work.

- **[Inventário completo em português](docs/portugues/creditos_opensource.md)**
- **[Full inventory in English](docs/ingles/creditos_opensource.md)**
- [Inventário estruturado / machine-readable inventory](third_party/inventario_creditos.json)
- [Textos de licença e avisos preservados / license and notice texts](third_party/licenses/)

| Projeto / Project | Crédito / Credit | Papel / Role |
| --- | --- | --- |
| [K-Dense scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | K-Dense Inc. e colaboradores / contributors | Skills científicas e referências; termos por skill / scientific skills and references; per-skill terms |
| [ToolUniverse](https://github.com/mims-harvard/ToolUniverse) | MIMS Lab e colaboradores / contributors | Integrações científicas e skills / scientific integrations and skills |
| [Google DeepMind Science Skills](https://github.com/google-deepmind/science-skills) | Google LLC / Google DeepMind e colaboradores / contributors | Clientes de bases e helpers; código Apache-2.0, outros materiais CC-BY-4.0 / database clients and helpers; Apache-2.0 code, CC-BY-4.0 other materials |
| [BIDS](https://bids.neuroimaging.io/) | Yaroslav Halchenko e colaboradores / contributors | Documentação da skill BIDS em CC-BY-4.0 / BIDS skill documentation under CC-BY-4.0 |
| [Exa](https://exa.ai/) | Exa e colaboradores / contributors | Skill de busca MIT / MIT search skill |
| [Graphify](https://pypi.org/project/graphifyy/0.9.23/) | Safi Shamsi e colaboradores / contributors, conforme metadados da versão / per version metadata | Grafo operacional / operational graph |
| [Python](https://www.python.org/) | Python Software Foundation e comunidade / community | Runtime |
| [R](https://www.r-project.org/) | R Foundation, R Core Team e comunidade / community | Estatística opcional / optional statistical runtime |
| [uv](https://github.com/astral-sh/uv) | Astral e colaboradores / contributors | Ambientes e locks / environments and locks |
| [Git](https://git-scm.com/) | Projeto Git e colaboradores / contributors | Versionamento / version control |
| [Playwright](https://github.com/microsoft/playwright) | Microsoft e colaboradores / contributors | Automação de navegador opcional / optional browser automation |
| [Node.js](https://nodejs.org/) | OpenJS Foundation e colaboradores / contributors | Runtime opcional do navegador / optional browser-tool runtime |
| [renv](https://github.com/rstudio/renv) | Autores e colaboradores do renv / renv authors and contributors | Reprodutibilidade em R / R reproducibility |
| [Quarto](https://github.com/quarto-dev/quarto-cli) | Posit e colaboradores / contributors | Renderização opcional / optional rendering |
| [Zotero](https://github.com/zotero/zotero) | Corporation for Digital Scholarship e colaboradores / contributors | Integração bibliográfica opcional / optional bibliography integration |

O inventário detalha também PyYAML, NetworkX, tree-sitter e gramáticas, NumPy,
pytest e ferramentas de desenvolvimento, bem como os ambientes opcionais de
scikit-learn, PyTorch, XGBoost, LightGBM, MAPIE, SHAP, pandas, SciPy, matplotlib,
metafor, meta, netmeta, tidymodels, ggplot2, Quarto/R e suas dependências transitivas.
Cada linha mantém a versão e o lock correspondente; presença no lock não comprova
execução. Não há afirmação de que todas essas bibliotecas estejam instaladas.

The inventory also identifies the scientific and development dependencies above,
including transitive dependencies, with their versions and lock evidence. Lock
presence does not establish installation or execution.

## Fontes e limites / Sources and limits

Os textos em `third_party/licenses/python/` são copiados dos metadados das versões
exatas instaladas neste clone. Os demais registros vêm dos locks e das skills.
As licenças de pacotes não instalados podem constar como `NOASSERTION`; não foram
inferidas de versões atuais. Avisos já existentes dentro das skills são preservados.

Texts under `third_party/licenses/python/` come from exact installed distributions.
Other records come from locks and skill metadata. Missing licenses are marked
`NOASSERTION`, not inferred from current releases. Existing skill notices remain.

Também foram preservados os textos oficiais da licença raiz do K-Dense no commit
`a1043ef544e3a100c28e70a736b6cf32554d0677` (MIT; hash igual ao manifesto de origem)
e do ToolUniverse no tag `v1.3.1` (Apache-2.0). As URLs e hashes desses snapshots
estão em [fontes_licencas.json](third_party/fontes_licencas.json). A licença raiz
do upstream não substitui termos específicos de arquivos ou skills.

Official root-license texts are included for the pinned K-Dense commit and
ToolUniverse tag above. Snapshot URLs and hashes are recorded separately; root
upstream terms do not override file-specific or skill-specific terms.

O responsável autorizou a publicação da camada própria em Apache-2.0. A revisão
da distribuição atual substituiu rótulos locais/indefinidos por uma política
documentada por skill, corrigindo atribuições a K-Dense e Google. As fontes
oficiais e licenças foram conferidas; isso não afirma identidade de toda a árvore
local com uma revisão upstream. Leia [LICENSE_SCOPE.md](LICENSE_SCOPE.md).
Dar crédito não relicencia dados, artigos ou material histórico de terceiros.

The owner authorized Apache-2.0 publication of the original layer. Current-source
review replaces local/undefined labels with a documented per-skill policy and
corrects K-Dense and Google attribution. Official sources and terms were checked;
this does not assert whole-tree identity to upstream revisions. See the license
scope. Acknowledgement does not relicense research data, papers or older history.

Catálogos externos apenas mencionados, sem árvores incorporadas nesta distribuição:
DenDen047, Orchestra-Research, Imbad0202 e InternScience. A menção não significa
instalação, execução ou licença comum. Antigravity, serviços de modelos e APIs são
produtos/serviços externos; não são classificados aqui como software livre.

External catalogs only mentioned, without their trees bundled: DenDen047,
Orchestra-Research, Imbad0202 and InternScience. Mention does not establish
installation, execution or shared licensing. Antigravity and model/API services
are external products/services, not classified here as open-source software.

Para atualizar / regenerate: `.venv/Scripts/python.exe scripts/gerar_creditos.py`.
