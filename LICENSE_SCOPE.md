# Escopo das licenças / License scope

## Português

A camada própria de ScientificApex / Article Machine é publicada sob
**Apache-2.0**, por autorização explícita do responsável pelo repositório em
2026-11-06. Isso abrange o runtime próprio, instaladores, testes, documentação
própria, modelos originais e contratos de workflow identificados como
`first-party` em [politica_licencas.json](third_party/politica_licencas.json).
Não reivindicamos autoria de material upstream nem o relicenciamos como próprio.

O inventário por skill diferencia:

- **K-Dense e autores de skills upstream:** termos MIT, BSD-3-Clause,
  Apache-2.0 ou CC-BY-4.0 conforme cada componente. Manifests fixados e
  entrypoints oficiais adicionais estão registrados na política.
- **ToolUniverse:** Apache-2.0. Os 14 entrypoints incluídos foram localizados
  no tag oficial `v1.3.1`; o texto da licença e as atribuições são preservados.
- **Google DeepMind Science Skills:** código Apache-2.0 e outros materiais
  CC-BY-4.0 conforme o README oficial de `v1.0.4`. Copyright 2026 Google LLC.
  Mantemos cabeçalhos do código e os termos de uso das fontes de dados.
- **renv:** o ativador incorporado mantém MIT, Copyright 2023 Posit Software,
  PBC; a licença foi obtida no tag oficial `v1.3.1`.
- **Dependências externas:** conservam suas próprias licenças. Um lock é
  metadado para instalação, não uma cópia dos binários dos pacotes.

As cópias podem conter adaptações locais de descrição, roteamento, credenciais,
gates e layout. Avisos nos entrypoints modificados e a política identificam a
origem. Localizar o entrypoint upstream não comprova identidade de toda a árvore
local; os hashes de árvore documentam a cópia efetivamente distribuída.

A política vale para a distribuição atual. Não concede nova licença a dados,
artigos, serviços externos, marcas ou a material de terceiros em commits antigos.
Novas contribuições precisam registrar origem e permissão; o CI bloqueia skills
sem escopo de licença. Isso é uma verificação documental, não certificação jurídica.

## English

The original ScientificApex / Article Machine layer is released under
**Apache-2.0**, expressly authorized by the repository owner on 2026-11-06.
The grant covers original runtime, installers, tests, documentation, templates
and workflow contracts classified as `first-party` in the linked policy.
Upstream authorship and terms are preserved, not replaced by this grant.

K-Dense and upstream skill authors retain their individual MIT, BSD-3-Clause,
Apache-2.0 or CC-BY-4.0 terms. ToolUniverse entrypoints were located at official
tag `v1.3.1` and retain Apache-2.0. Google DeepMind Science Skills uses Apache-2.0
for software and CC-BY-4.0 for other materials under its `v1.0.4` README,
Copyright 2026 Google LLC. The embedded renv activator retains MIT,
Copyright 2023 Posit Software, PBC, with license text from `v1.3.1`.

Local adaptations include routing descriptions, provider boundaries, gates and
formatting. Modified entrypoints and the policy record these changes. Upstream
entrypoint verification does not assert whole-tree identity; tree hashes identify
the actual bundled copy. External dependencies retain their own licenses and
their binaries are not bundled merely by including lock metadata.

This policy covers the current source distribution, not external research data,
articles, services, trademarks or blanket relicensing of earlier history. New
contributions must record origin and permission. CI checks documentary scope,
not legal authenticity or universal compliance.
