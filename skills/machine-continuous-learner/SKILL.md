---
name: machine-continuous-learner
description: Use when an agent needs to extract, distill, and persist reusable workflows, debugging fixes, laboratory protocols, or scientific best practices into the Article Machine from recent user sessions or corrections (equivalent to /learn).
---

# Machine Continuous Learner

Use esta skill sempre que uma sessão produzir um avanço metodológico, correção de bug, refinamento de protocolo ou nova demanda do usuário que deva se tornar parte permanente da Article Machine.

## Quando Acionar
- O usuário invocar `/learn` ou pedir para a máquina "aprender com o que fizemos".
- Um erro complexo foi superado e a causa-raiz identificada (para não reincidir em sessões futuras).
- Um novo tipo de protocolo, ensaio de bancada ou análise foi desenhado e deve ser reutilizável.
- Regras de formatação, escrita anti-IA ou novos periódicos forem consolidados.

## Workflow de Aprendizado (Ciclo em 5 Etapas)

1. **Dissecação da Causa-Raiz e do Valor Aprendido:**
   - O que falhou inicialmente? O que causou o sucesso?
   - O aprendizado é uma *Regra Invariante* (comportamento estrito) ou uma *Skill* (ferramenta/procedimento sob demanda)?
   
2. **Aplicação do Princípio de Divulgação Progressiva (Progressive Disclosure):**
   - Para evitar saturar a janela de contexto de conversas futuras (anti-context-rot), mantenha as regras mestras em formato de ponteiros curtos e objetivos.
   - Detalhes extensos, scripts e tabelas devem residir dentro da pasta da skill (`skills/<name>/`) ou em módulos Python/R de `article_machine/services/`, nunca soltos no contexto inicial.

3. **Geração de Proposta Auditável (`learning_proposal.md`):**
   - Antes de modificar qualquer arquivo de controle, apresente um resumo claro e os diffs exatos para aprovação do usuário.

4. **Implementação e Sincronização Estrita:**
   - Criar ou atualizar o arquivo da skill em `skills/<name>/SKILL.md`.
   - Espelhar a alteração em `.agents/skills/<name>/SKILL.md`.
   - Atualizar o hash determinístico (`tree_hash`) em `skills/registry.json`.

5. **Verificação Automática e Registro no Grafo:**
   - Executar `.\.venv\Scripts\python.exe -m pytest tests/`
   - Executar `.\.venv\Scripts\python.exe -m article_machine machine audit --workspace-root . --strict`
   - Atualizar o grafo operacional com `python scripts/generate_workspace_graph.py`.
