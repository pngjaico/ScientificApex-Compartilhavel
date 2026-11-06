# LEIA-ME — modelo de estatística e figuras

O script comum está em scripts/gerar_demonstracoes.R. Execute-o com R 4.6.1 e os pacotes listados em ambiente/renv.lock, passando como argumento a pasta de saída do projeto. O script não lê dados de pacientes nem acessa a rede.

A biblioteca instalada fica em ambiente/biblioteca e é ignorada pelo Git. O arquivo renv.lock e a captura sessao_r_2026-11-02.txt registram o ambiente técnico. Não há duas cópias do código, das sementes ou dos CSVs técnicos por idioma.

Os resultados podem ser gerados em diretórios portugueses e ingleses. Os nomes de arquivos são em português nos dois diretórios. A paridade técnica mantém contagens, estimativas, intervalos e valores p (se algum artefato científico futuro os tiver); este exemplo não calcula p-valores. A revisão humana ainda deve verificar correspondência semântica, força das afirmações e tradução dos termos.

A validação externa de qualquer modelo clínico permanece PENDENTE. Este modelo sintético não produz achado clínico nem comprova desempenho, segurança, calibração ou utilidade.


