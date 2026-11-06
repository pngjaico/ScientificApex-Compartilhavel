# LEIA-ME — modelo de estatística e figuras

The shared source is scripts/gerar_demonstracoes.R. Run it with R 4.6.1 and the packages listed in ambiente/renv.lock, passing the project output directory as its argument. It does not read patient data or access the network.

The installed library is kept in ambiente/biblioteca and ignored by Git. The renv.lock file and sessao_r_2026-11-02.txt record the technical environment. Code, seeds, and technical CSV files are not duplicated by language.

Results can be generated in Portuguese and English output folders. Filenames are Portuguese in both folders. Technical parity preserves counts, estimates, intervals, and p-values (if a future scientific artifact contains them); this example does not calculate p-values. Human review must still check semantic correspondence, claim strength, and terminology translation.

External validation of any clinical model remains PENDING. This synthetic model does not produce a clinical finding or establish performance, safety, calibration, or utility.


