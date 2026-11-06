# Guia operacional de registro e verificação local

## Limite de início

Preparar a pergunta, preencher este questionário e congelar o protocolo em **bootstrap/protocol-freeze** é permitido. Para projeto científico, a política local exige registro final PROSPERO ou OSF revisado **antes** de construir o corpus, iniciar busca/triagem formal, extração, análise, descoberta ou redação científica. A política é mais estrita que os prazos mínimos aceitos por alguns registros.

Registro final significa uma submissão que chegou ao estado final aceito/publicado ou, no OSF, estado final aprovado (público ou embargo conforme as opções vigentes). Rascunho, projeto OSF, submissão pendente, manuscrito de protocolo, número reservado/fictício ou repositório institucional não substituem o registro final. Em pesquisa de ensaio clínico, o registro aplicável de ensaio e as aprovações éticas/regulatórias são obrigações adicionais.

## Antes do registro externo

1. Responda o questionário com a equipe e resolva perguntas pendentes que alterem pergunta, elegibilidade, desfechos, coleta, amostra, estimando, análise, privacidade ou ética.
2. Escolha a via de registro conforme o fluxo. A elegibilidade PROSPERO muda e deve ser conferida no formulário/regra atuais; não conclua que é elegível apenas por ser pesquisa em saúde.
3. Congele a versão completa do protocolo, busca, formulário de extração, plano estatístico, métodos de avaliação crítica e materiais/anexos. Confira consistência entre conteúdo do protocolo e respostas do formulário de registro.
4. Registre autoria, contribuições, financiamento, conflitos, ética, compartilhamento e data prevista; não invente respostas para campos obrigatórios.
5. O envio ao PROSPERO/OSF é uma ação externa. Faça-o apenas quando o responsável pelo estudo tiver autorizado e revisado o pacote final. Nunca inclua dados identificáveis de participantes.
6. Confirme estado final no próprio registro. No OSF, projeto e registro são objetos distintos; um projeto público não transforma um registro draft/pending em registro final. O embargo, se escolhido, deve ser entendido como estado final privado conforme regra corrente do OSF, não como ausência de registro.

## Evidência local do registro

1. Salve dentro do projeto uma cópia datada e legível do registro final (por exemplo, impressão/PDF da página oficial) e os anexos relevantes. Guarde URL canônica, identificador, timestamp de registro, versão do protocolo e trilha de alterações.
2. Calcule SHA-256 do snapshot guardado. Não use hash de um link, tela não salva ou protocolo apenas local como se fosse hash do registro externo.
3. Um revisor nomeado compara registro, URL/ID, estado final, protocolo, anexos e data; registra nome, data da revisão e correspondência.
4. Declare metadados já existentes no registro externo:

```text
python -m article_machine registry register <projeto> --registry PROSPERO --id <ID-real> --url <URL-canônica-do-registro-final> --registered-at <ISO-8601-real>
```

Substitua todos os marcadores por dados reais após a confirmação externa. Para OSF, use `--registry OSF`, o identificador real de registro e URL canônica OSF. Esse comando **não submete** protocolo: apenas grava em `protocol.yaml` status `declared-unverified`; gates continuam bloqueados.

5. Preencha uma cópia do JSON em branco com metadados idênticos aos declarados no `protocol.yaml`, caminho relativo do snapshot local, hash SHA-256 do snapshot, fingerprint do protocolo congelado, confirmação verdadeira do revisor, método literal `reviewed-hashed-registry-record` e horários ISO 8601 reais. O `protocol_sha256` é o fingerprint calculado pelo serviço a partir de `protocol.yaml`, excluindo os campos `registration` e `status`; não o invente.
6. O revisor só pode preencher `scientific_work_not_started_before_registration: true` após reconciliar o histórico do projeto, incluindo arquivos legados e trabalho fora do pipeline. O serviço também confronta `sources/registry.jsonl`, `.machine/runs/*/manifest.json` e `.machine/scientific_start.json`; a ausência desses arquivos não prova que nada ocorreu. O campo é atestado humano, não inferência automática. Se houver trabalho científico anterior ao registro, marque false e não use a porta como se o estudo fosse prospectivo; resolva a situação conforme a política e reporte desvios.
7. Salve o JSON revisado dentro do projeto e execute:

```text
python -m article_machine registry verify <projeto> --record <caminho-local-do-json-revisado>
```

8. Continue somente se o comando retornar `status: pass` e a equipe confirmar a revisão. O serviço importa o arquivo, verifica consistência local, datas, identidade sintática da URL/ID e hashes; grava `evidence/protocol_registration/verification.json` e atualiza os metadados no protocolo.

As datas legadas encontradas pela CLI podem bloquear a verificação, mas ausência de ledger/manifests não cobre arquivos ou trabalho externo ao pipeline. A declaração humana sobre todo o histórico não é validada automaticamente.

## O que a verificação prova e não prova

- O serviço rejeita identificadores/hosts fora dos formatos previstos, URL de projeto ou draft onde exige registro específico, divergência de campos, protocolo modificado após conferência, datas impossíveis, registro posterior ao início científico anotado, revisor vazio, arquivo ausente ou hash divergente.
- A checagem compara URL e ID localmente; não consulta o provedor para autenticar a página, estado, autoria ou conteúdo atual. Um hash comprova que o arquivo local não mudou desde o cálculo, não que o arquivo veio do registro.
- Um parecer local não prova elegibilidade PROSPERO, validade metodológica, conformidade ética, suficiência de amostra nem fidelidade semântica.
- Arquive captura datada de fonte oficial e mantenha protocolo e registro sob controle de versão. Reconfira fonte externa se surgir dúvida; não faça acesso ou envio externo através deste modelo.

## Emendas e início de atividades

Se a versão congelada mudar, o fingerprint muda. Pare a etapa científica afetada; registre alteração, data, versão, motivo, quem decidiu, impacto sobre desfechos/elegibilidade/análise, atividades já iniciadas, necessidade de alterar o registro externo e aprovação ética. Preserve versões antigas e relate desvios. Refaça conferência e verificação antes de retomar. Não edite a história para parecer prospectiva.

## Referências oficiais

- [Orientações PROSPERO](https://www.crd.york.ac.uk/prospero/documents/Registering%20a%20review%20on%20PROSPERO.pdf)
- [Ajuda OSF Registrations](https://help.osf.io/article/330-welcome-to-registrations)
- [PRISMA-P](https://www.prisma-statement.org/protocols)
- [Política local implementada](../../../article_machine/services/protocol_registration.py)
