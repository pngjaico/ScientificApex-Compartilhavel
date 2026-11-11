import os
import json
import argparse
from typing import List, Dict
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

# Personas
PERSONA_1 = """Você é o Revisor A: Um Metodologista Rigoroso. 
Seu foco é a qualidade do desenho do estudo, viés e rigor estatístico. 
Seja extremamente estrito com os critérios de inclusão/exclusão."""

PERSONA_2 = """Você é o Revisor B: Um Especialista Clínico Sénior. 
Seu foco é a relevância clínica, a população do estudo e a aplicabilidade dos resultados. 
Avalie se o estudo realmente responde à pergunta clínica."""

PERSONA_3 = """Você é o Adjudicador: Um Diretor de Investigação. 
Seu papel é analisar as discrepâncias entre o Revisor A e o Revisor B e tomar a decisão final baseada na evidência e nos critérios."""

def screen_study(study: Dict, criteria: str, model="gemini/gemini-3-flash-lite-preview") -> Dict:
    title = study.get("title", "No Title")
    abstract = study.get("abstract", "No Abstract")
    
    prompt = f"""
    ESTUDO: {title}
    ABSTRACT: {abstract}
    
    CRITÉRIOS DE INCLUSÃO/EXCLUSÃO:
    {criteria}
    
    Responda apenas em JSON com:
    {{
        "decision": "INCLUDE" ou "EXCLUDE",
        "reason": "Sua explicação curta baseada nos critérios"
    }}
    """
    
    # Reviewer 1
    resp1 = completion(model=model, messages=[{"role": "system", "content": PERSONA_1}, {"role": "user", "content": prompt}])
    r1 = json.loads(resp1.choices[0].message.content)
    
    # Reviewer 2
    resp2 = completion(model=model, messages=[{"role": "system", "content": PERSONA_2}, {"role": "user", "content": prompt}])
    r2 = json.loads(resp2.choices[0].message.content)
    
    final_decision = ""
    if r1["decision"] == r2["decision"]:
        final_decision = r1["decision"]
        justification = "Consenso entre Revisores A e B."
    else:
        # Adjudication
        adj_prompt = f"""
        Houve discrepância no screening deste estudo.
        Revisor A decidiu: {r1['decision']} ({r1['reason']})
        Revisor B decidiu: {r2['decision']} ({r2['reason']})
        
        Tome a decisão final baseada nos critérios:
        {criteria}
        
        Responda em JSON:
        {{
            "decision": "INCLUDE" ou "EXCLUDE",
            "reason": "Justificação final do Adjudicador"
        }}
        """
        resp3 = completion(model="gemini/gemini-3-flash-preview", messages=[{"role": "system", "content": PERSONA_3}, {"role": "user", "content": adj_prompt}])
        r3 = json.loads(resp3.choices[0].message.content)
        final_decision = r3["decision"]
        justification = r3["reason"]
        
    return {
        "title": title,
        "reviewer_a": r1,
        "reviewer_b": r2,
        "final_decision": final_decision,
        "justification": justification
    }

def main():
    parser = argparse.ArgumentParser(description="Trinity Systematic Screening")
    parser.add_argument("--input", required=True, help="JSON file with search results")
    parser.add_argument("--criteria", required=True, help="Markdown file with inclusion/exclusion criteria")
    parser.add_argument("-o", "--output", required=True, help="Output JSON results")
    args = parser.parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        studies = json.load(f)
        # Handle different search result formats (Scopus/PubMed)
        if isinstance(studies, dict):
            studies = studies.get("search-results", {}).get("entry", [])
            
    with open(args.criteria, "r", encoding="utf-8") as f:
        criteria_text = f.read()
        
    results = []
    print(f"Iniciando Screening Trinity para {len(studies)} estudos...")
    
    for study in studies:
        res = screen_study(study, criteria_text)
        results.append(res)
        print(f"[{res['final_decision']}] {res['title'][:50]}...")
        
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    print(f"Screening concluído. Resultados em {args.output}")

if __name__ == "__main__":
    main()
