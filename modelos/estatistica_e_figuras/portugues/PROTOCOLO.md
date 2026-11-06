# Protocolo — demonstração estatística bilíngue

## Finalidade
Demonstrar uma estrutura técnica mínima para estatística, visualização, tabelas e exportação em R. O exemplo não representa pacientes, estudos publicados, estimativas clínicas ou inferência sobre uma população real.

## Fontes de dados e unidade
A base é criada inteiramente no script, com semente fixa. A unidade da tabela descritiva é uma observação simulada; a unidade do forest plot é um estudo artificial. Não há importação nem acesso a dados externos.

## Desfechos e parâmetros
São gerados uma medida contínua arbitrária e um indicador binário artificial para a Tabela 1; seis estimativas e erros-padrão artificiais para ilustrar REML com ajuste Hartung–Knapp; e um modelo logístico simples sobre dados gerados para mostrar uma curva de calibração em partição sintética treino/teste.

## Procedimentos
Tabela 1 exibe mediana e intervalo interquartil para a medida e n (%) para o indicador. Não são calculados testes de hipótese nem p-valores. A medida contém ausências artificiais, exibidas como categoria própria. O forest plot usa intervalos normais de 95% para efeitos individuais e o intervalo retornado pelo modelo aleatório com ajuste Hartung–Knapp. A curva de calibração agrupa predições em decis e exibe intervalos binomiais exatos por grupo.

## Replicabilidade e idiomas
Uma semente única governa os dados, e um segundo valor fixado deriva a demonstração de predição. Código e CSV técnico permanecem compartilhados; manuscritos, tabelas, gráficos, legendas e textos alternativos têm versão nativa em português e inglês, com mesmo nome de arquivo em português e números idênticos.

## Limites
Tamanho de amostra, proporções e efeitos são escolhas pedagógicas arbitrárias. A calibração por bins pode ser instável e perde informação; a validação sintética não avalia transportabilidade, desempenho clínico ou utilidade decisória. Seis estudos não sustentam diagnóstico confiável de viés de publicação, metarregressão ou conclusões sobre heterogeneidade. Nada neste modelo substitui protocolo registrado, plano de análise, especialista em método, revisão clínica ou Evidence Lock.
