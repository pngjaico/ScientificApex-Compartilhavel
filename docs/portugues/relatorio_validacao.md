# Verificação da distribuição

Data: 2026-11-06. Escopo: núcleo Windows da Article Machine 0.3.0.

- Instalação por uv.lock em clone local limpo e em outra pasta: PASS.
- CLI e auditoria operacional estrita no clone limpo: PASS.
- Suíte selecionada do núcleo: 80 testes PASS, incluindo gates de modo,
  registro, contratos, evidência, revisão, métricas e regressões de portabilidade.
- Registro PROSPERO sem autor/contato/afiliação herdados: PASS no teste específico.
- Grafo operacional com documentos opcionais ausentes: PASS; relações para
  entidades ausentes são omitidas e contabilizadas no manifesto do grafo.
- Seleção por lista de arquivos versionados da máquina e modelos; nenhum projeto,
  dado de estudo, manuscrito, perfil, credencial ou histórico Git original incluído.
- Busca direcionada por identificadores pessoais: sem ocorrências remanescentes
  nos textos distribuídos. Os 24 modelos DOCX também tiveram XML textual revisado.
- Detector de segredos: 581 sinais em 32 arquivos. A revisão dos candidatos
  encontrou hashes, metadados upstream, IDs públicos, placeholders e fixtures.
  Não foram identificadas credenciais reais nos candidatos revistos. O detector
  não autentica chaves e não prova ausência universal de segredos.

Dados de teste sintéticos, modelos editoriais em branco e metadados bibliográficos
de terceiros são parte do software. Contatos públicos dos mantenedores upstream
e avisos de licença foram preservados.

Não executados: R, ML/DL, browser/Quarto, Zotero, APIs externas e catálogos remotos,
validação clínica, revisão humana de todos os modelos e layout no Antigravity.
Não houve instalação em computador de terceiro nem teste em Linux/macOS.
O clone limpo foi testado nesta mesma máquina, com cache uv existente. Isso não
comprova disponibilidade futura de todos os pacotes em outro ambiente.
