# Verificação da distribuição

Data: 2026-11-06. Escopo: núcleo da Article Machine 0.3.0 em Windows local e CI Windows/Ubuntu.

- Instalação por uv.lock em clone local limpo e em outra pasta: PASS.
- CLI e auditoria operacional estrita no clone limpo: PASS.
- Suíte selecionada do núcleo: 84 testes PASS, incluindo gates de modo,
  registro, contratos, evidência, revisão, métricas e regressões de portabilidade.
- Modelos de declaração de IA sem fornecedor presumido, com verificação dos
  autores explicitamente pendente: PASS no teste de regressão.
- Política documental de licença: PASS para 117 skills; 65 componentes da camada
  própria publicados sob Apache-2.0 e 52 de terceiros com termos preservados.
- Instalador de shell: sintaxe conferida com Bash; execução Unix/macOS ainda não
  foi feita localmente. O workflow CI cobre Windows e Linux; consulte Actions para
  o resultado remoto do commit em uso, sem inferir suporte a macOS.
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
validação clínica, revisão humana de todos os modelos e layout em agentes/editores.
Não houve instalação em computador pessoal de terceiro nem teste em macOS. O núcleo e o instalador em modo de verificação passaram no CI Ubuntu/Linux e Windows.
O clone limpo foi testado nesta mesma máquina, com cache uv existente. Isso não
comprova disponibilidade futura de todos os pacotes em outro ambiente.

Evidência remota: 84 testes e todas as verificações do núcleo passaram em cada job Windows/Ubuntu, commit `ac8ec81`. [GitHub Actions](https://github.com/pngjaico/ScientificApex-Compartilhavel/actions/runs/42286830255).
