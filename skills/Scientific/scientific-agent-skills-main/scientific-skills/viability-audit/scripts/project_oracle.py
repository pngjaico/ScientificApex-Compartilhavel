import os
import json
import argparse
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """Você é o ORÁCULO DE VIABILIDADE CIENTÍFICA.
Sua missão é destruir ideias fracas ou saturadas e fortalecer ideias inovadoras.
Ao analisar uma proposta, você deve ser brutalmente honesto sobre:
1. NOVIDADE: Alguém já fez exatamente isso? (Check Scopus/PubMed keywords).
2. SATURAÇÃO: O campo está saturado? (Muitas revisões sistemáticas recentes indicam saturação).
3. VIABILIDADE IN SILICO: Existem ferramentas, constantes e modelos para realizar isso sem custos laboratoriais imensos?
4. RISCO RED TEAM: Onde este projeto vai falhar no peer-review?

Use um tom profissional, estratégico e de alto nível (Diretor de Pesquisa)."""

def analyze_idea(idea: str, context_data: str):
    prompt = f"""
    PROPOSTA DE PROJETO:
    {idea}
    
    CONTEXTO DE PESQUISA (Artigos Recentes/Tendências):
    {context_data}
    
    FORNEÇA UM AUDIT COMPLETO:
    1. [ESTADO DA ARTE]: O que já existe e quem são os líderes.
    2. [GAP ANALYTICS]: Onde está o buraco na literatura que este projeto preenche.
    3. [IN SILICO FEASIBILITY]: Hardware/Software necessários.
    4. [VERDICT]: GO, NO-GO ou PIVOT.
    """
    
    response = completion(
        model="gemini/gemini-3-flash-preview",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(description="Scientific Project Oracle")
    parser.add_argument("--idea", required=True, help="Your project idea")
    parser.add_argument("--research_file", help="Path to a research-lookup or scopus-search result file")
    args = parser.parse_args()
    
    context = ""
    if args.research_file and os.path.exists(args.research_file):
        with open(args.research_file, "r", encoding="utf-8") as f:
            context = f.read()[:10000] # Limite para o prompt
            
    print("Iniciando Auditoria do Oráculo...")
    verdict = analyze_idea(args.idea, context)
    print("\n" + "="*50)
    print("VEREDITO DO ORÁCULO")
    print("="*50 + "\n")
    print(verdict)

if __name__ == "__main__":
    main()
