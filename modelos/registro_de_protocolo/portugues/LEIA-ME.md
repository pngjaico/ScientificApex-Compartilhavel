# Modelos de protocolo e registro

Preencha questionario.md com a equipe, use fluxo_de_decisao.md para escolher método/registro e siga guia_de_registro_e_verificacao.md. Os nomes são iguais no diretório ingles; nomes de arquivo permanecem em português. Os documentos estão escritos nativamente em cada língua.

O modelo_registro_em_branco.json é deliberadamente inválido para verificação: não contém ID, URL, datas, hash, revisor ou confirmação, e `scientific_work_not_started_before_registration` está `false`. Ele não é registro real, não deve ser submetido e deve continuar bloqueado até que uma equipe conclua o registro externo e revise evidências reais. Nunca copie um ID de exemplo para protocolo. O revisor só pode atestar ausência de início científico anterior depois de reconciliar fontes legadas e atividades fora do pipeline; ausência de marker/manifests não prova ausência de trabalho.

Preparação e congelamento podem ocorrer em bootstrap/protocol-freeze. Para projeto científico, a política local exige registro final PROSPERO/OSF revisado antes de corpus, busca/triagem formal, extração, análise, descoberta ou redação. O comando local registry register só declara dados de registro já concluído; registry verify verifica a evidência guardada localmente. Nenhum dos comandos cria registro externo.

O serviço checa consistência local e hash, não autentica automaticamente com o provedor. Mantenha snapshot datado, protocolo congelado, fingerprint, autoria, ética, versão e emendas. A elegibilidade PROSPERO e as opções OSF devem ser conferidas diretamente nas fontes oficiais vigentes.

