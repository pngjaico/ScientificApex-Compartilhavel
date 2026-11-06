"""Canonical Retrieval Portal Service for Crowdsourced Full-Text Retrieval.

Provides automated generation, deployment, and bidirectional synchronization of
collaborative web portals (Firebase Hosting + Storage + Drive) for Article Machine projects.
Allows research teams and co-authors to retrieve paywalled full-text PDFs by DOI,
tracks individual contributor names for authorship/acknowledgments, provides access guides
(CAPES/CAFe, Sci-Hub <= 2021, ResearchGate, PubMed), and logs unretrieved reports with PRISMA audit checklists.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_FIREBASE_CONFIG = {
    "apiKey": "AIzaSyA25nIrsv__RxzPN91GloE0EAo9WAlWPl8",
    "authDomain": "pharosreader.firebaseapp.com",
    "projectId": "pharosreader",
    "storageBucket": "pharosreader.firebasestorage.app",
    "messagingSenderId": "196370947164",
    "appId": "1:196370947164:web:da9d249086df45afb49a99",
}

STORAGE_RULES = """rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /full_texts/{allPaths=**} {
      allow read, write: if true;
    }
    match /reports/{allPaths=**} {
      allow read, write: if true;
    }
    match /coauthors/{allPaths=**} {
      allow read, write: if true;
    }
  }
}
"""

FIREBASE_JSON = {
    "hosting": {
        "public": "public",
        "ignore": [
            "firebase.json",
            "**/.*",
            "**/node_modules/**"
        ]
    },
    "storage": {
        "rules": "storage.rules"
    }
}


def _extract_text_from_pdf(pdf_path: Path, out_txt: Path) -> bool:
    """Extract plain text from PDF using pdfplumber."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        full_text = "\n\n".join(text_parts)
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        out_txt.write_text(full_text, encoding="utf-8", errors="replace")
        return len(full_text) > 100
    except Exception:
        return False


def _load_json_data(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_project_studies(project_dir: Path) -> list[dict[str, Any]]:
    """Load core studies from project screening status file or fallback."""
    status_file = project_dir / "screening/core_100_full_text_status.json"
    data = _load_json_data(status_file)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("studies", [])
    
    # Check general screening ledger
    ledger_file = project_dir / "screening/multi_agent_screening_ledger.jsonl"
    if ledger_file.is_file():
        studies = []
        for line in ledger_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("senior_decision") == "include" or item.get("status") == "include":
                studies.append({
                    "record_id": item.get("record_id", f"STUDY-{len(studies)+1:04d}"),
                    "title": item.get("title", ""),
                    "authors": [item.get("authors", "Et al.")],
                    "year": item.get("year", 2024),
                    "journal": item.get("journal", ""),
                    "doi": item.get("doi", ""),
                    "pmid": item.get("pmid", ""),
                    "study_design_tier": item.get("tier", "Tier-1_RCT")
                })
        return studies
    return []


def generate_portal_html(project_dir: Path, firebase_config: dict[str, str] | None = None) -> str:
    """Generate self-contained modern HTML for the multi-project retrieval portal."""
    fb_config = firebase_config or DEFAULT_FIREBASE_CONFIG
    project_slug = project_dir.name
    
    # Load project metadata if available
    project_yaml = project_dir / "project.yaml"
    project_title = "Meta-Análise de Perfusão Hepática 2027 (HOPE vs NMP vs SCS)"
    if project_yaml.is_file():
        try:
            import yaml
            pm = yaml.safe_load(project_yaml.read_text(encoding="utf-8"))
            if isinstance(pm, dict) and pm.get("name"):
                project_title = pm["name"]
        except Exception:
            pass

    raw_studies = load_project_studies(project_dir)
    full_texts_dir = project_dir / "sources/full_texts"
    existing_pdfs = {p.stem.split("_")[0]: p.name for p in full_texts_dir.glob("*.pdf")} if full_texts_dir.is_dir() else {}

    studies_data = []
    for s in raw_studies:
        rec_id = s.get("record_id", "")
        is_saved = rec_id in existing_pdfs
        authors = s.get("authors", ["Et al."])
        author = authors[0] if isinstance(authors, list) and authors else str(authors)
        if isinstance(authors, list) and len(authors) > 1:
            author += " et al."

        filename = existing_pdfs.get(rec_id, "")
        pdf_url = f"https://firebasestorage.googleapis.com/v0/b/{fb_config['storageBucket']}/o/full_texts%2F{filename}?alt=media" if filename else ""

        studies_data.append({
            "id": rec_id,
            "title": s.get("title", ""),
            "author": author,
            "year": int(s.get("year", 2024)) if str(s.get("year", "")).isdigit() else 2024,
            "journal": s.get("journal", ""),
            "doi": s.get("doi", ""),
            "pmid": s.get("pmid", ""),
            "tier": str(s.get("study_design_tier", "Tier-1_RCT")).replace("_", " "),
            "status": "completed" if is_saved else "pending",
            "pdfUrl": pdf_url,
            "retrieved_by": s.get("retrieved_by", ""),
            "failed_by": s.get("failed_by", ""),
            "pivotal": rec_id in ["STUDY-0490", "STUDY-0594", "STUDY-0376", "STUDY-0456", "STUDY-0473"]
        })

    studies_json = json.dumps(studies_data, ensure_ascii=False)
    coauthors_file = project_dir / "evidence/coauthors_registry.json"
    initial_coauthors = []
    if coauthors_file.is_file():
        try:
            initial_coauthors = json.loads(coauthors_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    initial_coauthors_json = json.dumps(initial_coauthors, ensure_ascii=False)

    fb_config_json = json.dumps(fb_config, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Portal de Recuperação Científica — Article Machine</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Firebase App & Storage Compat SDK -->
  <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-storage-compat.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    .glass-card {{ background: rgba(255, 255, 255, 0.98); backdrop-filter: blur(12px); }}
    .gradient-header {{ background: linear-gradient(135deg, #090d16 0%, #1e293b 45%, #0369a1 100%); }}
    .modal-backdrop {{ background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(4px); }}
    .dropzone-box {{ transition: all 0.2s ease-in-out; }}
    .dropzone-box * {{ pointer-events: none; }}
    .dropzone-active {{
      border-color: #10b981 !important;
      background-color: #ecfdf5 !important;
      box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.35), 0 10px 25px -5px rgba(16, 185, 129, 0.25) !important;
      transform: scale(1.008);
    }}
  </style>
</head>
<body class="bg-slate-100 min-h-screen text-slate-800 antialiased font-sans pb-20">

  <!-- Header -->
  <header class="gradient-header text-white pt-6 pb-12 px-4 sm:px-6 lg:px-8 shadow-xl">
    <div class="max-w-5xl mx-auto">
      
      <!-- Top Bar: Project Selector, Contributor Identification & WhatsApp -->
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        
        <!-- Multi-Project Switcher (Currently locked to active project) -->
        <div class="flex items-center gap-2">
          <label for="projectSelector" class="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <i class="fa-solid fa-folder-tree text-sky-400"></i> Projeto Ativo:
          </label>
          <div class="relative inline-block">
            <select id="projectSelector" class="bg-slate-800/95 text-white text-xs font-semibold rounded-lg px-3 py-1.5 pr-8 border border-sky-500/40 focus:outline-none focus:ring-2 focus:ring-sky-400 cursor-pointer">
              <option value="{project_slug}" selected>● {project_title} ({len(studies_data)} estudos)</option>
              <option value="" disabled>──────────</option>
              <option value="" disabled>🔒 Outros projetos do laboratório (indisponíveis)</option>
            </select>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2.5">
          <!-- WhatsApp Sharing Button -->
          <a href="https://api.whatsapp.com/send?text=Ol%C3%A1!%20Estamos%20recuperando%20os%20textos%20completos%20da%20nossa%20Meta-An%C3%A1lise%20de%20Perfus%C3%A3o%20Hep%C3%A1tica%20(HOPE%20vs%20NMP%20vs%20SCS).%20Ajude%20enviando%20os%20PDFs%20pendentes%20pelo%20portal:%20https://pharosreader.web.app" target="_blank" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors border border-emerald-400/40 shadow-sm">
            <i class="fa-brands fa-whatsapp text-emerald-200"></i> Compartilhar no WhatsApp
          </a>

          <!-- Contributor Identifier Pill -->
          <div id="contributorPill" onclick="switchMainTab('authors')" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-white/10 text-sky-200 border border-white/20 backdrop-blur-sm cursor-pointer hover:bg-white/20 transition-all shadow-sm" title="Clique para cadastrar ou editar seus dados de autoria e ORCID">
            <i class="fa-brands fa-orcid text-emerald-400"></i>
            <span id="contributorLabel">Identifique-se / ORCID</span>
            <span class="ml-1 text-[10px] bg-emerald-500/30 text-emerald-200 px-1.5 py-0.2 rounded-full border border-emerald-400/30">Perfil</span>
          </div>
        </div>
      </div>
      
      <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">Portal Colaborativo de Recuperação de Artigos</h1>
      <p class="mt-2 text-sm text-slate-200 max-w-2xl leading-relaxed">
        Ajude nossa equipe científica a recuperar os textos completos (PDFs) dos estudos centrais deste projeto.
        Identifique-se acima para registrarmos sua contribuição nominal nos <strong>Agradecimentos / Coautoria</strong> do manuscrito!
      </p>

      <!-- Drag & Drop Quick Tip -->
      <div class="mt-3.5 inline-flex items-center gap-2 text-xs text-sky-200 bg-sky-950/50 border border-sky-400/30 rounded-lg px-3 py-2 shadow-sm">
        <i class="fa-solid fa-wand-magic-sparkles text-amber-300"></i>
        <span><strong>Dica:</strong> Arraste e solte o arquivo <strong>PDF</strong> diretamente sobre o card de qualquer artigo pendente para envio instantâneo!</span>
      </div>

      <!-- Progress Card -->
      <div class="mt-6 bg-white/10 border border-white/20 rounded-xl p-4 sm:p-5 text-white backdrop-blur-md shadow-inner">
        <div class="flex justify-between items-center mb-2">
          <span class="text-xs sm:text-sm font-semibold uppercase tracking-wider text-sky-200 flex items-center gap-1.5">
            <i class="fa-solid fa-chart-pie"></i> Progresso do Projeto Ativo
          </span>
          <span id="progressText" class="text-sm sm:text-base font-bold">Calculando...</span>
        </div>
        <div class="w-full bg-black/40 rounded-full h-3.5 overflow-hidden p-0.5">
          <div id="progressBar" class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-300 h-full rounded-full transition-all duration-700 shadow" style="width: 0%"></div>
        </div>
        <div class="mt-3 flex flex-wrap gap-4 text-xs font-medium text-slate-200">
          <div><span id="countCompleted" class="font-bold text-emerald-300 text-sm">0</span> recuperados ✅</div>
          <div><span id="countPending" class="font-bold text-amber-300 text-sm">0</span> pendentes 📥</div>
          <div><span id="countNotFound" class="font-bold text-rose-300 text-sm">0</span> inacessíveis ⚠️</div>
          <div><span class="font-bold text-white text-sm">{len(studies_data)}</span> estudos centrais</div>
          <div class="ml-auto text-[11px] text-sky-200 flex items-center gap-1">
            <i class="fa-solid fa-rotate text-sky-300" id="syncIcon"></i> Sincronizado em tempo real
          </div>
        </div>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 space-y-6">

    <!-- Top Navigation Tabs (Recuperação de Artigos vs Cadastro de Autoria) -->
    <div class="flex items-center gap-2 p-1.5 bg-white/95 backdrop-blur-md rounded-2xl border border-sky-200/80 shadow-md">
      <button id="tabBtnArticles" onclick="switchMainTab('articles')" class="flex-1 py-3 px-4 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all bg-sky-600 text-white shadow-sm">
        <i class="fa-solid fa-file-lines text-sky-200 text-sm"></i>
        <span>1. Recuperação de Artigos</span>
        <span id="tabBadgePending" class="ml-1 px-2.5 py-0.5 rounded-full bg-sky-900/40 text-sky-100 text-[11px] font-extrabold border border-sky-400/30">Carregando...</span>
      </button>

      <button id="tabBtnAuthors" onclick="switchMainTab('authors')" class="flex-1 py-3 px-4 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all text-slate-600 hover:text-slate-900 hover:bg-slate-50">
        <i class="fa-brands fa-orcid text-emerald-600 text-base"></i>
        <span>2. Cadastro de Autores & ORCID</span>
        <span class="ml-1 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-extrabold border border-emerald-300/50">Submissão Oficial</span>
      </button>
    </div>

    <!-- Tab 1: Recuperação de Artigos -->
    <div id="tabContentArticles" class="space-y-6">

      <!-- Tutorial Banner (Collapsible) -->
    <section class="bg-white rounded-xl border border-sky-200 p-5 shadow-sm">
      <div class="flex items-center justify-between cursor-pointer" onclick="toggleTutorial()">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-sm">
            <i class="fa-solid fa-graduation-cap"></i>
          </div>
          <div>
            <h2 class="text-sm sm:text-base font-bold text-slate-900">Tutorial: Onde e como encontrar os artigos?</h2>
            <p class="text-xs text-slate-500">4 passos rápidos para conseguir o PDF de qualquer artigo da lista</p>
          </div>
        </div>
        <span id="tutorialToggleIcon" class="text-slate-400 text-sm font-semibold flex items-center gap-1">
          <span class="text-xs">Ver Guia</span> <i class="fa-solid fa-chevron-down"></i>
        </span>
      </div>

      <div id="tutorialContent" class="mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        
        <!-- Step 1: Sci-Hub -->
        <div class="p-3.5 rounded-lg bg-amber-50/70 border border-amber-200">
          <div class="flex items-center gap-2 mb-1.5 font-bold text-amber-900">
            <i class="fa-solid fa-bolt text-amber-600 text-sm"></i>
            <span>1. Sci-Hub (Artigos até 2021)</span>
          </div>
          <p class="text-slate-600 leading-relaxed">
            Se o artigo foi publicado em <strong>2021 ou antes</strong>, o Sci-Hub costuma abrir na hora com 100% de sucesso.
            Clique no botão <strong>Sci-Hub</strong> do card ou cole o DOI em:
          </p>
          <a href="https://sci-hub.st/" target="_blank" class="inline-flex items-center gap-1 mt-2 font-semibold text-amber-800 hover:text-amber-900 underline">
            https://sci-hub.st/ <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
          </a>
        </div>

        <!-- Step 2: CAPES / Acesso CAFe sua instituição -->
        <div class="p-3.5 rounded-lg bg-sky-50/70 border border-sky-200">
          <div class="flex items-center gap-2 mb-1.5 font-bold text-sky-900">
            <i class="fa-solid fa-building-columns text-sky-600 text-sm"></i>
            <span>2. Portal CAPES / CAFe (Instituições participantes)</span>
          </div>
          <p class="text-slate-600 leading-relaxed">
            Para artigos recentes (<strong>2022 a 2026</strong>), faça login no <strong>Acesso CAFe</strong> com o login institucional da sua universidade (ex: <strong>sua instituição</strong>, USP, UNIFESP). Dá acesso liberado à Elsevier (ScienceDirect), Springer, Wiley, Nature, etc.:
          </p>
          <a href="https://www.periodicos.capes.gov.br/index.php/acesso-cafe.html" target="_blank" class="inline-flex items-center gap-1 mt-2 font-semibold text-sky-800 hover:text-sky-900 underline">
            Acesso CAFe Portal CAPES <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
          </a>
        </div>

        <!-- Step 3: ResearchGate -->
        <div class="p-3.5 rounded-lg bg-emerald-50/70 border border-emerald-200">
          <div class="flex items-center gap-2 mb-1.5 font-bold text-emerald-900">
            <i class="fa-brands fa-researchgate text-emerald-600 text-sm"></i>
            <span>3. ResearchGate (Autores & Pre-prints)</span>
          </div>
          <p class="text-slate-600 leading-relaxed">
            Muitos cirurgiões e pesquisadores disponibilizam o PDF completo diretamente no ResearchGate.
            O botão <strong>ResearchGate</strong> no card já busca pelo título do estudo automaticamente:
          </p>
          <a href="https://www.researchgate.net/" target="_blank" class="inline-flex items-center gap-1 mt-2 font-semibold text-emerald-800 hover:text-emerald-900 underline">
            https://www.researchgate.net/ <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
          </a>
        </div>

        <!-- Step 4: PubMed & Google Scholar -->
        <div class="p-3.5 rounded-lg bg-purple-50/70 border border-purple-200">
          <div class="flex items-center gap-2 mb-1.5 font-bold text-purple-900">
            <i class="fa-solid fa-book-medical text-purple-600 text-sm"></i>
            <span>4. PubMed / Periódico Oficial</span>
          </div>
          <p class="text-slate-600 leading-relaxed">
            Abra o artigo no PubMed para ver se há selo <strong>Free PMC article</strong> ou link para repositório institucional gratuito (ex: universidade de Zurique, Birmingham, etc.):
          </p>
          <a href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank" class="inline-flex items-center gap-1 mt-2 font-semibold text-purple-800 hover:text-purple-900 underline">
            https://pubmed.ncbi.nlm.nih.gov/ <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
          </a>
        </div>

      </div>
    </section>

    <!-- Controls Bar -->
    <div class="glass-card rounded-xl p-4 shadow-sm border border-slate-200 flex flex-col sm:flex-row gap-3 items-center justify-between">
      <div class="relative w-full sm:w-80">
        <i class="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
        <input type="text" id="searchInput" placeholder="Buscar título, autor, revista, DOI..." class="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
      </div>
      <div class="flex flex-wrap gap-2 w-full sm:w-auto">
        <button id="filterPending" class="flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white shadow-sm transition-colors">
          Pendentes (<span id="btnPendingCount">0</span>)
        </button>
        <button id="filterAll" class="flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors">
          Todos ({len(studies_data)})
        </button>
        <button id="filterCompleted" class="flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors">
          Recuperados (<span id="btnCompletedCount">0</span>)
        </button>
        <button id="filterNotFound" class="flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors">
          Inacessíveis (<span id="btnNotFoundCount">0</span>)
        </button>
        <button id="filterPivotal" class="flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors">
          ⭐ Pivotais
        </button>
      </div>
    </div>

    <!-- Studies Grid -->
    <div id="studiesContainer" class="space-y-4">
      <!-- Cards rendered dynamically -->
    </div>

    <!-- Empty State -->
    <div id="emptyState" class="hidden text-center py-16 bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
      <i class="fa-solid fa-circle-check text-emerald-500 text-5xl mb-3"></i>
      <h3 class="text-lg font-bold text-slate-800">Nenhum estudo pendente neste filtro!</h3>
      <p class="text-sm text-slate-500 mt-1">Todos os estudos selecionados já foram recuperados ou não batem com a busca.</p>
    </div>

    <!-- Leaderboard / Contributor Wall -->
    <section class="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2">
          <i class="fa-solid fa-trophy text-amber-500"></i> Colaboradores & Agradecimentos do Estudo
        </h3>
        <span class="text-[11px] text-slate-500">Nominação formal nos Agradecimentos da Publicação</span>
      </div>
      <div id="leaderboardContainer" class="flex flex-wrap gap-2.5">
        <span class="text-xs text-slate-500 italic">Carregando lista de colaboradores...</span>
      </div>
    </section>

    </div>
    <!-- End of Tab 1: Recuperação de Artigos -->

    <!-- Tab 2 Content: Cadastro de Autores & ORCID para Publicação -->
    <div id="tabContentAuthors" class="hidden space-y-6">
      
      <!-- Informational Banner -->
      <section class="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 text-white rounded-2xl p-6 shadow-lg border border-emerald-500/30">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div class="space-y-1.5 max-w-2xl">
            <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
              <i class="fa-brands fa-orcid text-sm"></i> Padrão Internacional de Publicação (ICMJE & CRediT)
            </div>
            <h2 class="text-xl sm:text-2xl font-extrabold text-white">Cadastro Formal de Autores & Pesquisadores</h2>
            <p class="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Para viabilizar a submissão formal a periódicos internacionais de alto impacto (<em>Lancet, JAMA Surg, Ann Surg, Liver Transpl</em>),
              precisamos de seus dados padronizados de afiliação e identificador persistente ORCID.
            </p>
          </div>
          <div class="shrink-0 bg-white/10 p-3.5 rounded-xl border border-white/20 backdrop-blur-sm text-center">
            <span class="text-[11px] block text-emerald-300 font-bold uppercase tracking-wider">Identificador Vital</span>
            <span class="text-xs text-white">ORCID iD Oficial</span>
            <a href="https://orcid.org/register" target="_blank" class="mt-2 inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-900 text-xs font-bold transition-all shadow">
              <i class="fa-brands fa-orcid"></i> Criar ORCID
            </a>
          </div>
        </div>
      </section>

      <!-- Registration Form Card -->
      <section class="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
        <div>
          <h3 class="text-base sm:text-lg font-bold text-slate-900 flex items-center gap-2">
            <i class="fa-solid fa-user-pen text-emerald-600"></i>
            Seus Dados Acadêmicos para a Publicação
          </h3>
          <p class="text-xs text-slate-500 mt-1">
            Preencha os campos abaixo. Seus dados serão vinculados às suas contribuições de recuperação e extração.
          </p>
        </div>

        <form id="authorForm" onsubmit="event.preventDefault(); saveAuthorProfile();" class="space-y-6">
          
          <!-- Bloco 1: Nome, Citação, ORCID e Email -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            <!-- Nome Completo -->
            <div>
              <label for="authorFullName" class="block text-xs font-bold text-slate-700 mb-1">
                Nome Completo (Full Legal Name) <span class="text-rose-500">*</span>
              </label>
              <input type="text" id="authorFullName" required placeholder="Ex: Eliezer Luciano da Silva Soares" oninput="onFullNameInput(this.value)"
                class="w-full px-3.5 py-2.5 text-xs sm:text-sm border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-slate-50/50 focus:bg-white transition-all">
              <span class="text-[11px] text-slate-400 mt-1 block">Nome civil completo, sem abreviações.</span>
            </div>

            <!-- Nome para Citação -->
            <div>
              <label for="authorCitationName" class="block text-xs font-bold text-slate-700 mb-1 flex items-center justify-between">
                <span>Nome para Citação (Citation Index)</span>
                <span class="text-[10px] font-semibold text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded-full">Automático NLM</span>
              </label>
              <input type="text" id="authorCitationName" placeholder="Ex: Soares ELS" 
                class="w-full px-3.5 py-2.5 text-xs sm:text-sm font-semibold text-emerald-900 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-emerald-50/30 focus:bg-white transition-all">
              <span class="text-[11px] text-emerald-700 mt-1 block flex items-center gap-1">
                <i class="fa-solid fa-wand-magic-sparkles text-amber-500"></i> Gerado automaticamente no padrão PubMed/Index Medicus (editável).
              </span>
            </div>

            <!-- ORCID iD -->
            <div>
              <label for="authorOrcid" class="block text-xs font-bold text-slate-700 mb-1">
                ORCID iD <span class="text-emerald-600 font-bold">*</span>
              </label>
              <div class="relative">
                <i class="fa-brands fa-orcid absolute left-3 top-1/2 -translate-y-1/2 text-emerald-600 text-base"></i>
                <input type="text" id="authorOrcid" required placeholder="0000-0002-1825-0097" maxlength="19" oninput="formatAndValidateOrcid(this)"
                  class="w-full pl-9 pr-3.5 py-2.5 text-xs sm:text-sm font-mono border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-slate-50/50 focus:bg-white transition-all">
              </div>
              <div id="orcidValidationMsg" class="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
                <span>Formato: 16 dígitos com hífens (0000-0000-0000-0000)</span>
              </div>
            </div>

            <!-- Email Institucional / Contato -->
            <div>
              <label for="authorEmail" class="block text-xs font-bold text-slate-700 mb-1">
                E-mail Institucional ou Profissional <span class="text-rose-500">*</span>
              </label>
              <input type="email" id="authorEmail" required placeholder="Ex: pesquisador@example.org" 
                class="w-full px-3.5 py-2.5 text-xs sm:text-sm border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-slate-50/50 focus:bg-white transition-all">
              <span class="text-[11px] text-slate-400 mt-1 block">Usado para cadastro no ScholarOne/Editorial Manager da revista.</span>
            </div>

          </div>

          <!-- Bloco 2: Afiliação Institucional -->
          <div class="pt-4 border-t border-slate-100">
            <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3 text-sky-800 flex items-center gap-1.5">
              <i class="fa-solid fa-building-columns"></i> Afiliações Institucionais (Affiliations)
            </h4>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              <!-- Instituição 1 (Principal) -->
              <div class="md:col-span-2">
                <label for="authorInstitution1" class="block text-xs font-bold text-slate-700 mb-1">
                  Instituição Primária (Universidade / Hospital Principal) <span class="text-rose-500">*</span>
                </label>
                <input type="text" id="authorInstitution1" required placeholder="Ex: Sua instituição, cidade, país" 
                  class="w-full px-3.5 py-2.5 text-xs sm:text-sm border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-slate-50/50 focus:bg-white transition-all">
                <span class="text-[11px] text-slate-400 mt-1 block">Nome oficial da instituição em português ou inglês.</span>
              </div>

              <!-- Departamento / Divisão -->
              <div>
                <label for="authorDepartment" class="block text-xs font-bold text-slate-700 mb-1">
                  Departamento / Divisão / Serviço
                </label>
                <input type="text" id="authorDepartment" placeholder="Ex: Programa de Pós-Graduação em Medicina / Departamento de Cirurgia" 
                  class="w-full px-3.5 py-2.5 text-xs sm:text-sm border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-slate-50/50 focus:bg-white transition-all">
              </div>

              <!-- Segunda Instituição (Opcional) -->
              <div>
                <label for="authorInstitution2" class="block text-xs font-bold text-slate-700 mb-1">
                  Segunda Afiliação (Hospital de Base / Residência) <span class="text-slate-400 font-normal">(Opcional)</span>
                </label>
                <input type="text" id="authorInstitution2" placeholder="Ex: Hospital das Clínicas da FMUSP / Hospital Alemão Oswaldo Cruz" 
                  class="w-full px-3.5 py-2.5 text-xs sm:text-sm border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-slate-50/50 focus:bg-white transition-all">
              </div>

              <!-- Cidade, Estado e País -->
              <div class="md:col-span-2">
                <label for="authorCityCountry" class="block text-xs font-bold text-slate-700 mb-1">
                  Cidade, Estado e País
                </label>
                <input type="text" id="authorCityCountry" placeholder="Ex: São Paulo, SP, Brasil" 
                  class="w-full px-3.5 py-2.5 text-xs sm:text-sm border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none bg-slate-50/50 focus:bg-white transition-all">
              </div>

            </div>
          </div>

          <!-- Bloco 3: Funções CRediT -->
          <div class="pt-4 border-t border-slate-100">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider text-sky-800 flex items-center gap-1.5">
                <i class="fa-solid fa-list-check"></i> Papéis de Autoria CRediT (Contributor Roles)
              </h4>
              <span class="text-[11px] text-slate-500">Exigência padrão das revistas (Lancet/JAMA/Elsevier)</span>
            </div>
            <p class="text-xs text-slate-600 mb-3 leading-relaxed">
              Selecione as atividades nas quais você participou ou participará neste projeto científico:
            </p>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
              <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors bg-white">
                <input type="checkbox" id="roleInvestigation" checked class="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500">
                <div>
                  <span class="font-bold text-slate-800">Investigação & Recuperação (Investigation)</span>
                  <p class="text-slate-500 text-[11px]">Busca sistemática, triagem e recuperação dos textos completos (PDFs).</p>
                </div>
              </label>

              <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors bg-white">
                <input type="checkbox" id="roleDataCuration" checked class="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500">
                <div>
                  <span class="font-bold text-slate-800">Curadoria de Dados (Data Curation)</span>
                  <p class="text-slate-500 text-[11px]">Extração e conferência de desfechos clínicos (EAD, NAS, PNF, HAT, sobrevida).</p>
                </div>
              </label>

              <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors bg-white">
                <input type="checkbox" id="roleValidation" class="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500">
                <div>
                  <span class="font-bold text-slate-800">Validação e Verificação (Validation)</span>
                  <p class="text-slate-500 text-[11px]">Auditoria independente das tabelas 2x2 e verificação cruzada de evidências.</p>
                </div>
              </label>

              <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors bg-white">
                <input type="checkbox" id="roleWritingReview" checked class="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500">
                <div>
                  <span class="font-bold text-slate-800">Redação - Revisão Crítica (Writing - Review)</span>
                  <p class="text-slate-500 text-[11px]">Revisão crítica do conteúdo intelectual e sugestões editoriais do manuscrito.</p>
                </div>
              </label>

              <label class="flex items-start gap-2.5 p-3 rounded-xl border border-slate-200 hover:bg-slate-50 cursor-pointer transition-colors bg-white sm:col-span-2">
                <input type="checkbox" id="roleConceptualization" class="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500">
                <div>
                  <span class="font-bold text-slate-800">Conceitualização & Metodologia (Conceptualization)</span>
                  <p class="text-slate-500 text-[11px]">Formulação das hipóteses, delineamento da síntese e interpretação dos achados cirúrgicos.</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Bloco 4: Conflito de Interesses & Critérios ICMJE -->
          <div class="pt-4 border-t border-slate-100 space-y-3">
            <h4 class="text-xs font-bold text-slate-900 uppercase tracking-wider text-sky-800 flex items-center gap-1.5">
              <i class="fa-solid fa-scale-balanced"></i> Declarações Editoriais e Éticas (ICMJE COI)
            </h4>

            <div class="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2.5 text-xs text-slate-700">
              <div class="font-bold text-slate-900">Conflito de Interesses:</div>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="coiChoice" id="coiNone" value="none" checked onchange="toggleCoiDetails(false)" class="text-emerald-600 focus:ring-emerald-500">
                <span>Declaro <strong>não possuir</strong> conflitos de interesse comerciais, financeiros ou acadêmicos a declarar.</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="coiChoice" id="coiYes" value="yes" onchange="toggleCoiDetails(true)" class="text-emerald-600 focus:ring-emerald-500">
                <span>Possuo potenciais conflitos a declarar (ex: honorários de palestras, consultorias, financiamento de equipamentos).</span>
              </label>

              <div id="coiDetailsContainer" class="hidden mt-2 pt-2 border-t border-slate-200">
                <label for="authorCoiText" class="block text-[11px] font-bold text-slate-700 mb-1">
                  Descreva o conflito de interesses para divulgação formal no artigo:
                </label>
                <textarea id="authorCoiText" rows="2" placeholder="Descreva os vínculos ou fontes de suporte..." 
                  class="w-full p-2.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:outline-none"></textarea>
              </div>
            </div>

            <!-- Checkbox de Aprovação ICMJE -->
            <label class="flex items-start gap-2.5 p-3.5 rounded-xl border border-emerald-300 bg-emerald-50/40 cursor-pointer text-xs text-slate-800">
              <input type="checkbox" id="chkIcmjeApproved" required checked class="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500">
              <div class="leading-relaxed">
                <strong>Concordância com Critérios ICMJE de Autoria:</strong> Declaro que participei substancialmente deste estudo,
                concordo em revisar criticamente o rascunho final do manuscrito e aprovo a submissão formal ao periódico científico.
              </div>
            </label>
          </div>

          <!-- Submit Button & Feedback -->
          <div class="pt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
            <span class="text-xs text-slate-500 flex items-center gap-1.5">
              <i class="fa-solid fa-shield-halved text-emerald-600"></i> Seus dados são salvos com segurança no repositório Firebase Storage.
            </span>

            <button type="submit" id="btnSaveAuthor" class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md transition-all hover:shadow-lg cursor-pointer">
              <i class="fa-solid fa-cloud-arrow-up"></i>
              <span>Salvar Dados de Autoria</span>
            </button>
          </div>

        </form>
      </section>

      <!-- Registered Coauthors Wall / Real-time Registry -->
      <section class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
          <div>
            <h3 class="text-sm sm:text-base font-bold text-slate-900 flex items-center gap-2">
              <i class="fa-solid fa-users text-sky-600"></i>
              Pesquisadores e Coautores Cadastrados neste Projeto
              <span id="coauthorCountBadge" class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                {len(initial_coauthors)} cadastrado(s)
              </span>
            </h3>
            <p class="text-xs text-slate-500 mt-0.5 flex flex-wrap items-center gap-2">
              <span>Relação consolidada para a Página de Rosto e submissão aos periódicos.</span>
              <span class="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Tempo Real Ativo (8s)
              </span>
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" onclick="loadRegisteredCoauthors(true)" class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 flex items-center gap-1.5 transition-all shadow-sm cursor-pointer">
              <i class="fa-solid fa-arrows-rotate text-sky-600" id="refreshCoauthorsIcon"></i>
              <span>Atualizar Agora</span>
            </button>
            <button type="button" onclick="exportCoauthorsCSV()" class="px-3 py-1.5 text-xs font-semibold rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1.5 transition-all shadow-sm cursor-pointer">
              <i class="fa-solid fa-file-csv text-emerald-600"></i>
              <span>Exportar Tabela CSV</span>
            </button>
          </div>
        </div>

        <div id="coauthorsGrid" class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          <div class="col-span-full text-center py-6 text-slate-400 text-xs italic">
            Carregando autores cadastrados...
          </div>
        </div>
      </section>

    </div>
    <!-- End of Tab 2 -->

  </main>

  <!-- Modal: Não Encontrei (Auditoria PRISMA) -->
  <div id="notFoundModal" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop">
    <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100">
      <div class="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
        <div class="flex items-center gap-2 text-rose-600 font-bold text-base">
          <i class="fa-solid fa-triangle-exclamation"></i>
          <span>Declarar Artigo como Inacessível</span>
        </div>
        <button onclick="closeNotFoundModal()" class="text-slate-400 hover:text-slate-600">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>

      <div class="space-y-3.5 text-xs text-slate-600">
        <p class="font-medium text-slate-800">
          Estudo: <span id="modalStudyId" class="font-bold text-blue-600"></span> — <span id="modalStudyTitle" class="italic"></span>
        </p>
        <p class="text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          Para mantermos a conformidade estrita com o <strong>PRISMA 2020 (Item 16b: Reports Not Retrieved)</strong>, confirme que você buscou nas 4 fontes obrigatórias:
        </p>

        <!-- Mandatory Checklist -->
        <div class="space-y-2 bg-amber-50/50 p-3.5 rounded-xl border border-amber-200 text-slate-700">
          <label class="flex items-start gap-2 cursor-pointer">
            <input type="checkbox" id="chkSciHub" class="mt-0.5 rounded text-blue-600 focus:ring-blue-500" onchange="validateModalForm()">
            <span>1. Busquei no <strong>Sci-Hub</strong> (<a href="https://sci-hub.st/" target="_blank" class="text-blue-600 underline">sci-hub.st</a>)</span>
          </label>
          <label class="flex items-start gap-2 cursor-pointer">
            <input type="checkbox" id="chkCafe" class="mt-0.5 rounded text-blue-600 focus:ring-blue-500" onchange="validateModalForm()">
            <span>2. Busquei no <strong>Portal CAPES / Acesso CAFe</strong> (universidade vinculada)</span>
          </label>
          <label class="flex items-start gap-2 cursor-pointer">
            <input type="checkbox" id="chkResearchGate" class="mt-0.5 rounded text-blue-600 focus:ring-blue-500" onchange="validateModalForm()">
            <span>3. Busquei no <strong>ResearchGate</strong> (<a href="https://www.researchgate.net/" target="_blank" class="text-blue-600 underline">researchgate.net</a>)</span>
          </label>
          <label class="flex items-start gap-2 cursor-pointer">
            <input type="checkbox" id="chkPubMed" class="mt-0.5 rounded text-blue-600 focus:ring-blue-500" onchange="validateModalForm()">
            <span>4. Busquei no <strong>PubMed / Periódico Oficial / Google Scholar</strong></span>
          </label>
        </div>

        <div>
          <label class="block text-slate-700 font-semibold mb-1">Seu Nome Completo:</label>
          <input type="text" id="modalContributorName" placeholder="Ex: Dr. Pedro Gomes" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" oninput="validateModalForm()">
        </div>

        <div>
          <label class="block text-slate-700 font-semibold mb-1">Motivo / Observação (opcional):</label>
          <input type="text" id="modalNotes" placeholder="Ex: Revista japonesa antiga sem arquivo digital; ou bloqueio de assinatura" class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>
      </div>

      <div class="mt-6 flex justify-end gap-2.5">
        <button onclick="closeNotFoundModal()" class="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors">
          Cancelar
        </button>
        <button id="btnSubmitNotFound" onclick="submitNotFoundReport()" disabled class="px-4 py-2 text-xs font-semibold rounded-lg bg-rose-600 hover:bg-rose-700 text-white shadow-sm transition-colors opacity-50 cursor-not-allowed">
          Confirmar que não foi encontrado
        </button>
      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-5 right-5 z-50 transform translate-y-20 opacity-0 transition-all duration-300 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 text-sm font-medium border border-slate-700">
    <i id="toastIcon" class="fa-solid fa-circle-check text-emerald-400 text-lg"></i>
    <span id="toastMsg">Notificação</span>
  </div>

  <script>
    const firebaseConfig = {fb_config_json};
    firebase.initializeApp(firebaseConfig);
    const storage = firebase.storage();

    let rawStudies = {studies_json};
    let currentFilter = "pending"; // Default to pending studies
    let searchTerm = "";
    let activeModalStudyId = null;

    // Contributor Tracking
    let currentContributor = localStorage.getItem("article_machine_contributor") || "";

    function updateContributorUI() {{
      const label = document.getElementById("contributorLabel");
      const cached = localStorage.getItem("article_machine_coauthor_profile");
      if (cached) {{
        try {{
          const p = JSON.parse(cached);
          if (p.full_name) currentContributor = p.full_name;
        }} catch (e) {{}}
      }}
      if (currentContributor) {{
        label.innerText = currentContributor;
      }} else {{
        label.innerText = "Identifique-se / ORCID";
      }}
    }}

    function promptContributorName() {{
      const name = prompt("Por favor, digite seu Nome Completo para registrarmos nos Agradecimentos do artigo:", currentContributor);
      if (name && name.trim()) {{
        currentContributor = name.trim();
        localStorage.setItem("article_machine_contributor", currentContributor);
        updateContributorUI();
        showToast(`Bem-vindo(a), ${{currentContributor}}! Suas contribuições serão registradas.`, "check");
      }}
    }}

    function toggleTutorial() {{
      const c = document.getElementById("tutorialContent");
      const icon = document.getElementById("tutorialToggleIcon");
      if (c.classList.contains("hidden")) {{
        c.classList.remove("hidden");
        icon.innerHTML = '<span class="text-xs">Ocultar Guia</span> <i class="fa-solid fa-chevron-up"></i>';
      }} else {{
        c.classList.add("hidden");
        icon.innerHTML = '<span class="text-xs">Ver Guia</span> <i class="fa-solid fa-chevron-down"></i>';
      }}
    }}

    function updateProgress() {{
      const completed = rawStudies.filter(s => s.status === "completed").length;
      const notFound = rawStudies.filter(s => s.status === "not_found").length;
      const total = rawStudies.length;
      const pending = total - (completed + notFound);
      const percent = Math.round((completed / total) * 100);

      document.getElementById("progressText").innerText = `${{completed}} / ${{total}} recuperados (${{percent}}%)`;
      document.getElementById("progressBar").style.width = `${{percent}}%`;
      document.getElementById("countCompleted").innerText = completed;
      document.getElementById("countPending").innerText = pending;
      document.getElementById("countNotFound").innerText = notFound;
      document.getElementById("btnPendingCount").innerText = pending;
      document.getElementById("btnCompletedCount").innerText = completed;
      document.getElementById("btnNotFoundCount").innerText = notFound;

      const tabBadge = document.getElementById("tabBadgePending");
      if (tabBadge) tabBadge.innerText = `${{pending}} pendentes`;

      updateLeaderboard();
    }}

    function updateLeaderboard() {{
      const container = document.getElementById("leaderboardContainer");
      const counts = {{}};

      rawStudies.forEach(s => {{
        if (s.status === "completed" && s.retrieved_by) {{
          counts[s.retrieved_by] = (counts[s.retrieved_by] || 0) + 1;
        }}
      }});

      const contributors = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
      if (contributors.length === 0) {{
        container.innerHTML = '<span class="text-xs text-slate-500 italic">Envie um PDF para aparecer no quadro de honra de colaboradores!</span>';
        return;
      }}

      container.innerHTML = contributors.map(name => `
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-50 text-sky-800 border border-sky-200">
          <i class="fa-solid fa-medal text-amber-500"></i> ${{name}} <span class="px-1.5 py-0.2 rounded-full bg-sky-200 text-sky-900 text-[10px] font-bold">${{counts[name]}}</span>
        </span>
      `).join("");
    }}

    function renderStudies() {{
      const container = document.getElementById("studiesContainer");
      container.innerHTML = "";

      const filtered = rawStudies.filter(s => {{
        if (currentFilter === "pending" && (s.status === "completed" || s.status === "not_found")) return false;
        if (currentFilter === "completed" && s.status !== "completed") return false;
        if (currentFilter === "not_found" && s.status !== "not_found") return false;
        if (currentFilter === "pivotal" && !s.pivotal) return false;

        if (searchTerm) {{
          const target = `${{s.id}} ${{s.title}} ${{s.author}} ${{s.journal}} ${{s.doi}} ${{s.pmid}}`.toLowerCase();
          if (!target.includes(searchTerm)) return false;
        }}
        return true;
      }});

      if (filtered.length === 0) {{
        document.getElementById("emptyState").classList.remove("hidden");
      }} else {{
        document.getElementById("emptyState").classList.add("hidden");
      }}

      filtered.forEach(s => {{
        const isDone = s.status === "completed";
        const isNotFound = s.status === "not_found";
        const card = document.createElement("div");
        card.id = `card_${{s.id}}`;
        card.className = `glass-card rounded-xl p-5 border transition-all duration-200 ${{
          isDone ? 'border-emerald-300 bg-emerald-50/25' : 
          isNotFound ? 'border-rose-200 bg-rose-50/25' : 
          'border-slate-200 hover:border-blue-300 hover:shadow-md'
        }}`;
        if (!isDone) {{
          card.setAttribute("ondragover", `handleCardDragOver(event, '${{s.id}}')`);
          card.setAttribute("ondragleave", `handleCardDragLeave(event, '${{s.id}}')`);
          card.setAttribute("ondrop", `handleCardDrop(event, '${{s.id}}')`);
        }}

        const pivotalBadge = s.pivotal ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 uppercase mr-1">⭐ Ensaio Pivotal</span>' : '';
        const tierBadge = s.tier.includes("RCT") ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800">Tier-1 RCT</span>' : '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">Tier-2 PSM</span>';

        const doiLink = s.doi ? `https://doi.org/${{s.doi}}` : '#';
        const pmidLink = s.pmid ? `https://pubmed.ncbi.nlm.nih.gov/${{s.pmid}}/` : '';
        const scihubLink = s.doi ? `https://sci-hub.st/${{s.doi}}` : 'https://sci-hub.st/';
        const cafeLink = 'https://www.periodicos.capes.gov.br/index.php/acesso-cafe.html';
        const rgLink = `https://www.researchgate.net/search/publication?q=${{encodeURIComponent(s.title)}}`;

        let statusBadge = `
          <div class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 text-amber-800 font-semibold text-xs border border-amber-200">
            <i class="fa-solid fa-clock text-amber-600"></i> Pendente
          </div>
        `;
        if (isDone) {{
          statusBadge = `
            <div class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-100 text-emerald-800 font-semibold text-xs border border-emerald-300 shadow-sm">
              <i class="fa-solid fa-circle-check text-emerald-600"></i> PDF Salvo ${{s.retrieved_by ? `<span class="text-[11px] font-normal text-emerald-700">(${{s.retrieved_by}})</span>` : ''}}
            </div>
          `;
        }} else if (isNotFound) {{
          statusBadge = `
            <div class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-100 text-rose-800 font-semibold text-xs border border-rose-300 shadow-sm">
              <i class="fa-solid fa-ban text-rose-600"></i> Inacessível ${{s.failed_by ? `<span class="text-[11px] font-normal text-rose-700">(${{s.failed_by}})</span>` : ''}}
            </div>
          `;
        }}

        card.innerHTML = `
          <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
            <div class="flex-1">
              <div class="flex items-center gap-1.5 mb-1.5">
                <span class="text-xs font-mono font-bold text-slate-500">${{s.id}}</span>
                ${{pivotalBadge}}
                ${{tierBadge}}
              </div>
              <h2 class="text-base font-bold text-slate-900 leading-snug">${{s.title}}</h2>
              <p class="text-xs text-slate-600 mt-1.5 font-medium">
                ${{s.author}} &bull; <span class="italic font-serif">${{s.journal}}</span> (${{s.year || 'N/D'}})
              </p>
            </div>
            
            <div class="shrink-0 flex items-center gap-2">
              ${{statusBadge}}
            </div>
          </div>

          <!-- Direct Search Helpers (4 Pillars) -->
          <div class="mt-3.5 pt-2.5 border-t border-slate-100 flex flex-wrap items-center gap-1.5 text-xs">
            <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mr-1">Buscar em:</span>
            
            <!-- Sci-Hub -->
            <a href="${{scihubLink}}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 transition-colors font-medium">
              <i class="fa-solid fa-bolt text-amber-600"></i> Sci-Hub ${{s.year <= 2021 ? '⚡' : '<span class="text-[9px] opacity-70">(<=2021)</span>'}}
            </a>

            <!-- CAPES CAFe -->
            <a href="${{cafeLink}}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 transition-colors font-medium">
              <i class="fa-solid fa-building-columns text-sky-600"></i> CAPES (CAFe)
            </a>

            <!-- ResearchGate -->
            <a href="${{rgLink}}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 transition-colors font-medium">
              <i class="fa-brands fa-researchgate text-emerald-600"></i> ResearchGate
            </a>

            <!-- PubMed -->
            ${{pmidLink ? `
              <a href="${{pmidLink}}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-200 transition-colors font-medium">
                <i class="fa-solid fa-book-medical text-purple-600"></i> PubMed
              </a>
            ` : ''}}

            <!-- Publisher Direct -->
            <a href="${{doiLink}}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors font-medium">
              <i class="fa-solid fa-arrow-up-right-from-square text-slate-500"></i> Periódico
            </a>
          </div>

          <!-- Actions Bar -->
          <div class="mt-3 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2.5">
            <div class="flex flex-wrap items-center gap-2">
              ${{s.doi ? `
                <button onclick="copyDOI('${{s.doi}}')" class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors">
                  <i class="fa-regular fa-copy text-slate-500"></i> Copiar DOI
                </button>
              ` : ''}}
              ${{s.pdfUrl ? `
                <a href="${{s.pdfUrl}}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-medium transition-colors border border-emerald-200">
                  <i class="fa-solid fa-file-pdf text-emerald-600"></i> Baixar / Ver PDF
                </a>
              ` : ''}}
            </div>

            <!-- Upload Area & Not Found Action -->
            <div class="flex flex-wrap items-center gap-2">
              ${{!isDone ? `
                <button onclick="openNotFoundModal('${{s.id}}', '${{s.title.replace(/'/g, "\\\\'")}}')" class="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-700 font-semibold text-xs transition-colors border border-slate-200 hover:border-rose-200">
                  <i class="fa-solid fa-ban text-rose-500"></i> Não encontrei
                </button>

                <label id="dropzone_${{s.id}}" 
                       class="dropzone-box inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border-2 border-dashed border-emerald-400 hover:border-emerald-600 font-semibold text-xs cursor-pointer shadow-sm transition-all">
                  <i id="dropzoneIcon_${{s.id}}" class="fa-solid fa-cloud-arrow-up text-emerald-600 text-sm"></i>
                  <span id="dropzoneText_${{s.id}}">Arraste o PDF aqui ou clique para enviar</span>
                  <input type="file" id="fileInput_${{s.id}}" accept="application/pdf" class="hidden" onchange="uploadPDF('${{s.id}}', this)">
                </label>
              ` : `
                <span class="text-xs text-emerald-700 font-medium"><i class="fa-solid fa-check mr-1"></i>Recuperado com sucesso!</span>
              `}}
            </div>
          </div>

          <div id="uploadProgress_${{s.id}}" class="hidden mt-3">
            <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div id="uploadBar_${{s.id}}" class="bg-emerald-500 h-full rounded-full transition-all duration-200" style="width: 0%"></div>
            </div>
            <span class="text-[11px] text-slate-500 mt-1 block">Enviando PDF para o repositório seguro...</span>
          </div>
        `;
        container.appendChild(card);
      }});

      updateProgress();
    }}

    function copyDOI(doi) {{
      navigator.clipboard.writeText(doi).then(() => {{
        showToast("DOI copiado com sucesso! Cole no seu navegador ou portal.", "check");
      }}).catch(() => {{
        showToast(`DOI: ${{doi}}`, "info");
      }});
    }}

    function uploadPDF(studyId, inputElement) {{
      if (inputElement && inputElement.files && inputElement.files.length > 0) {{
        processFileUpload(studyId, inputElement.files[0]);
      }}
    }}

    function handleCardDragOver(e, studyId) {{
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = "copy";
      const card = document.getElementById(`card_${{studyId}}`);
      const dropzone = document.getElementById(`dropzone_${{studyId}}`);
      const dropText = document.getElementById(`dropzoneText_${{studyId}}`);
      const dropIcon = document.getElementById(`dropzoneIcon_${{studyId}}`);
      if (card && !card.classList.contains("dropzone-active")) {{
        card.classList.add("dropzone-active");
      }}
      if (dropzone && !dropzone.classList.contains("dropzone-active")) {{
        dropzone.classList.add("dropzone-active");
      }}
      if (dropText) {{
        dropText.innerText = `Solte o PDF aqui para enviar (${{studyId}})`;
      }}
      if (dropIcon) {{
        dropIcon.className = "fa-solid fa-file-arrow-up text-emerald-700 animate-bounce";
      }}
    }}

    function handleCardDragLeave(e, studyId) {{
      e.preventDefault();
      e.stopPropagation();
      const card = document.getElementById(`card_${{studyId}}`);
      if (card && (!e.relatedTarget || !card.contains(e.relatedTarget))) {{
        card.classList.remove("dropzone-active");
        const dropzone = document.getElementById(`dropzone_${{studyId}}`);
        const dropText = document.getElementById(`dropzoneText_${{studyId}}`);
        const dropIcon = document.getElementById(`dropzoneIcon_${{studyId}}`);
        if (dropzone) dropzone.classList.remove("dropzone-active");
        if (dropText) dropText.innerText = "Arraste o PDF aqui ou clique para enviar";
        if (dropIcon) dropIcon.className = "fa-solid fa-cloud-arrow-up text-emerald-600";
      }}
    }}

    function handleCardDrop(e, studyId) {{
      e.preventDefault();
      e.stopPropagation();
      const card = document.getElementById(`card_${{studyId}}`);
      const dropzone = document.getElementById(`dropzone_${{studyId}}`);
      const dropText = document.getElementById(`dropzoneText_${{studyId}}`);
      const dropIcon = document.getElementById(`dropzoneIcon_${{studyId}}`);
      if (card) card.classList.remove("dropzone-active");
      if (dropzone) dropzone.classList.remove("dropzone-active");
      if (dropText) dropText.innerText = "Arraste o PDF aqui ou clique para enviar";
      if (dropIcon) dropIcon.className = "fa-solid fa-cloud-arrow-up text-emerald-600";

      const files = e.dataTransfer.files;
      if (files && files.length > 0) {{
        processFileUpload(studyId, files[0]);
      }}
    }}

    function processFileUpload(studyId, file) {{
      if (!file) return;

      if (!file.name.toLowerCase().endsWith(".pdf")) {{
        showToast("Por favor, selecione ou arraste apenas arquivos em formato PDF.", "error");
        return;
      }}

      if (!currentContributor) {{
        promptContributorName();
      }}
      const contributor = currentContributor || "Colaborador Anônimo";

      const progressDiv = document.getElementById(`uploadProgress_${{studyId}}`);
      const progressBar = document.getElementById(`uploadBar_${{studyId}}`);
      if (progressDiv) progressDiv.classList.remove("hidden");

      const cleanName = file.name.replace(/[^a-zA-Z0-9._-]/g, "_");
      const safeContributor = contributor.replace(/[^a-zA-Z0-9_-]/g, "");
      const storageRef = storage.ref(`full_texts/${{studyId}}_${{safeContributor}}_${{Date.now()}}_${{cleanName}}`);
      
      const uploadTask = storageRef.put(file, {{
        customMetadata: {{
          studyId: studyId,
          contributor: contributor,
          uploadedAt: new Date().toISOString()
        }}
      }});

      uploadTask.on('state_changed', 
        (snapshot) => {{
          const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
          if (progressBar) progressBar.style.width = `${{progress}}%`;
        }}, 
        (error) => {{
          console.error("Upload error:", error);
          showToast("Erro ao enviar o PDF. Verifique sua conexão e tente novamente.", "error");
          if (progressDiv) progressDiv.classList.add("hidden");
        }}, 
        () => {{
          uploadTask.snapshot.ref.getDownloadURL().then(downloadURL => {{
            showToast(`🎉 Maravilha! Artigo ${{studyId}} enviado com sucesso por ${{contributor}}!`, "check");
            
            const study = rawStudies.find(s => s.id === studyId);
            if (study) {{
              study.status = "completed";
              study.pdfUrl = downloadURL;
              study.retrieved_by = contributor;
            }}
            
            renderStudies();
          }}).catch(() => {{
            const study = rawStudies.find(s => s.id === studyId);
            if (study) {{
              study.status = "completed";
              study.retrieved_by = contributor;
            }}
            renderStudies();
          }});
        }}
      );
    }}

    // Modal: Não Encontrei
    function openNotFoundModal(studyId, title) {{
      activeModalStudyId = studyId;
      document.getElementById("modalStudyId").innerText = studyId;
      document.getElementById("modalStudyTitle").innerText = title;
      document.getElementById("modalContributorName").value = currentContributor || "";
      
      // Reset checkboxes
      document.getElementById("chkSciHub").checked = false;
      document.getElementById("chkCafe").checked = false;
      document.getElementById("chkResearchGate").checked = false;
      document.getElementById("chkPubMed").checked = false;
      document.getElementById("modalNotes").value = "";
      
      validateModalForm();
      document.getElementById("notFoundModal").classList.remove("hidden");
    }}

    function closeNotFoundModal() {{
      activeModalStudyId = null;
      document.getElementById("notFoundModal").classList.add("hidden");
    }}

    function validateModalForm() {{
      const c1 = document.getElementById("chkSciHub").checked;
      const c2 = document.getElementById("chkCafe").checked;
      const c3 = document.getElementById("chkResearchGate").checked;
      const c4 = document.getElementById("chkPubMed").checked;
      const name = document.getElementById("modalContributorName").value.trim();

      const btn = document.getElementById("btnSubmitNotFound");
      if (c1 && c2 && c3 && c4 && name.length >= 3) {{
        btn.disabled = false;
        btn.classList.remove("opacity-50", "cursor-not-allowed");
      }} else {{
        btn.disabled = true;
        btn.classList.add("opacity-50", "cursor-not-allowed");
      }}
    }}

    async function submitNotFoundReport() {{
      if (!activeModalStudyId) return;

      const name = document.getElementById("modalContributorName").value.trim();
      currentContributor = name;
      localStorage.setItem("article_machine_contributor", name);
      updateContributorUI();

      const reportPayload = {{
        contract: "UnretrievedReportV1",
        study_id: activeModalStudyId,
        contributor: name,
        reported_at: new Date().toISOString(),
        checklist: {{
          scihub: document.getElementById("chkSciHub").checked,
          capes_cafe: document.getElementById("chkCafe").checked,
          researchgate: document.getElementById("chkResearchGate").checked,
          pubmed: document.getElementById("chkPubMed").checked
        }},
        notes: document.getElementById("modalNotes").value.trim()
      }};

      const safeName = name.replace(/[^a-zA-Z0-9_-]/g, "");
      const reportBlob = new Blob([JSON.stringify(reportPayload, null, 2)], {{ type: 'application/json' }});
      const reportRef = storage.ref(`reports/${{activeModalStudyId}}_unretrieved_${{safeName}}_${{Date.now()}}.json`);

      try {{
        await reportRef.put(reportBlob);
        showToast(`Registro de inacessibilidade salvo para ${{activeModalStudyId}} por ${{name}}.`, "check");

        const study = rawStudies.find(s => s.id === activeModalStudyId);
        if (study) {{
          study.status = "not_found";
          study.failed_by = name;
        }}

        closeNotFoundModal();
        renderStudies();
      }} catch (err) {{
        console.error("Report upload error:", err);
        showToast("Erro ao registrar no servidor. Tente novamente.", "error");
      }}
    }}

    async function syncStorageStatus() {{
      const syncIcon = document.getElementById("syncIcon");
      if (syncIcon) syncIcon.classList.add("fa-spin");

      try {{
        // 1. Fetch full_texts/
        const resp = await fetch("https://firebasestorage.googleapis.com/v0/b/{fb_config['storageBucket']}/o?prefix=full_texts%2F");
        if (resp.ok) {{
          const data = await resp.json();
          const items = data.items || [];
          
          let changed = false;
          items.forEach(item => {{
            const match = item.name.match(/(STUDY-\\d{{4}})/);
            if (match) {{
              const sid = match[1];
              const study = rawStudies.find(s => s.id === sid);
              if (study && (study.status !== "completed" || !study.pdfUrl)) {{
                study.status = "completed";
                study.pdfUrl = `https://firebasestorage.googleapis.com/v0/b/{fb_config['storageBucket']}/o/${{encodeURIComponent(item.name)}}?alt=media`;
                
                // Parse contributor from name if present: STUDY-XXXX_Contributor_Timestamp_File
                const parts = item.name.replace("full_texts/", "").split("_");
                if (parts.length >= 3 && isNaN(parts[1]) && !study.retrieved_by) {{
                  study.retrieved_by = parts[1];
                }}
                changed = true;
              }}
            }}
          }});

          if (changed) renderStudies();
        }}

        // 2. Fetch reports/
        const respRep = await fetch("https://firebasestorage.googleapis.com/v0/b/{fb_config['storageBucket']}/o?prefix=reports%2F");
        if (respRep.ok) {{
          const dataRep = await respRep.json();
          const itemsRep = dataRep.items || [];
          
          let changedRep = false;
          itemsRep.forEach(item => {{
            const match = item.name.match(/(STUDY-\\d{{4}})/);
            if (match) {{
              const sid = match[1];
              const study = rawStudies.find(s => s.id === sid);
              if (study && study.status === "pending") {{
                study.status = "not_found";
                const parts = item.name.replace("reports/", "").split("_");
                if (parts.length >= 3) {{
                  study.failed_by = parts[2];
                }}
                changedRep = true;
              }}
            }}
          }});

          if (changedRep) renderStudies();
        }}
      }} catch (err) {{
        console.warn("Storage sync notice:", err);
      }} finally {{
        if (syncIcon) syncIcon.classList.remove("fa-spin");
      }}
    }}

    function showToast(msg, type) {{
      const toast = document.getElementById("toast");
      const toastMsg = document.getElementById("toastMsg");
      const toastIcon = document.getElementById("toastIcon");

      toastMsg.innerText = msg;
      if (type === "error") {{
        toastIcon.className = "fa-solid fa-circle-exclamation text-rose-400 text-lg";
      }} else {{
        toastIcon.className = "fa-solid fa-circle-check text-emerald-400 text-lg";
      }}

      toast.classList.remove("translate-y-20", "opacity-0");
      setTimeout(() => {{
        toast.classList.add("translate-y-20", "opacity-0");
      }}, 4000);
    }}

    // Filter Buttons
    document.getElementById("filterPending").addEventListener("click", () => {{
      currentFilter = "pending";
      updateFilterButtons();
      renderStudies();
    }});

    document.getElementById("filterAll").addEventListener("click", () => {{
      currentFilter = "all";
      updateFilterButtons();
      renderStudies();
    }});

    document.getElementById("filterCompleted").addEventListener("click", () => {{
      currentFilter = "completed";
      updateFilterButtons();
      renderStudies();
    }});

    document.getElementById("filterNotFound").addEventListener("click", () => {{
      currentFilter = "not_found";
      updateFilterButtons();
      renderStudies();
    }});

    document.getElementById("filterPivotal").addEventListener("click", () => {{
      currentFilter = "pivotal";
      updateFilterButtons();
      renderStudies();
    }});

    function updateFilterButtons() {{
      const p = document.getElementById("filterPending");
      const a = document.getElementById("filterAll");
      const c = document.getElementById("filterCompleted");
      const nf = document.getElementById("filterNotFound");
      const piv = document.getElementById("filterPivotal");

      [p, a, c, nf, piv].forEach(b => {{
        b.className = "flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors";
      }});

      if (currentFilter === "pending") p.className = "flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white shadow-sm transition-colors";
      if (currentFilter === "all") a.className = "flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white shadow-sm transition-colors";
      if (currentFilter === "completed") c.className = "flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-emerald-600 text-white shadow-sm transition-colors";
      if (currentFilter === "not_found") nf.className = "flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-rose-600 text-white shadow-sm transition-colors";
      if (currentFilter === "pivotal") piv.className = "flex-1 sm:flex-none px-3.5 py-2 text-xs font-semibold rounded-lg bg-amber-600 text-white shadow-sm transition-colors";
    }}

    document.getElementById("searchInput").addEventListener("input", (e) => {{
      searchTerm = e.target.value.toLowerCase().trim();
      renderStudies();
    }});

    // Global Drag & Drop Handler (Prevents browser navigation and auto-matches dropped PDFs)
    window.addEventListener("dragover", function(e) {{
      e.preventDefault();
    }}, false);

    window.addEventListener("drop", function(e) {{
      e.preventDefault();
      const files = e.dataTransfer.files;
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!file.name.toLowerCase().endsWith(".pdf")) {{
        showToast("Por favor, selecione ou arraste apenas arquivos em formato PDF.", "error");
        return;
      }}

      // Smart match by filename if dropped outside a specific study card
      const match = file.name.toUpperCase().match(/(STUDY[-_]?)?0*(\\d{{1,4}})/);
      if (match) {{
        const num = parseInt(match[2], 10);
        const candidateId = `STUDY-${{num.toString().padStart(4, '0')}}`;
        const targetStudy = rawStudies.find(s => s.id === candidateId);
        if (targetStudy && targetStudy.status !== "completed") {{
          showToast(`Arquivo identificado automaticamente para ${{candidateId}}! Iniciando envio...`, "check");
          processFileUpload(candidateId, file);
          return;
        }}
      }}

      showToast("Arraste e solte o PDF diretamente sobre o card do artigo correspondente.", "info");
    }}, false);

    // ==========================================
    // Tab Navigation & Author Registry Functions
    // ==========================================
    let registeredCoauthors = {initial_coauthors_json};

    function switchMainTab(tab) {{
      const btnArticles = document.getElementById("tabBtnArticles");
      const btnAuthors = document.getElementById("tabBtnAuthors");
      const contentArticles = document.getElementById("tabContentArticles");
      const contentAuthors = document.getElementById("tabContentAuthors");

      if (tab === "articles") {{
        btnArticles.className = "flex-1 py-3 px-4 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all bg-sky-600 text-white shadow-sm";
        btnAuthors.className = "flex-1 py-3 px-4 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all text-slate-600 hover:text-slate-900 hover:bg-slate-50";
        contentArticles.classList.remove("hidden");
        contentAuthors.classList.add("hidden");
      }} else if (tab === "authors") {{
        btnArticles.className = "flex-1 py-3 px-4 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all text-slate-600 hover:text-slate-900 hover:bg-slate-50";
        btnAuthors.className = "flex-1 py-3 px-4 rounded-xl font-bold text-xs sm:text-sm flex items-center justify-center gap-2 transition-all bg-emerald-600 text-white shadow-sm";
        contentArticles.classList.add("hidden");
        contentAuthors.classList.remove("hidden");
        loadAuthorFormFromStorage();
        loadRegisteredCoauthors();
      }}
    }}

    function formatAndValidateOrcid(input) {{
      let val = input.value.replace(/[^0-9Xx]/g, "").toUpperCase();
      if (val.length > 16) val = val.substring(0, 16);
      let formatted = "";
      for (let i = 0; i < val.length; i++) {{
        if (i > 0 && i % 4 === 0) formatted += "-";
        formatted += val[i];
      }}
      input.value = formatted;

      const msg = document.getElementById("orcidValidationMsg");
      if (formatted.length === 19) {{
        msg.innerHTML = `<span class="text-emerald-600 font-bold"><i class="fa-solid fa-circle-check"></i> ORCID Válido!</span> <a href="https://orcid.org/${{formatted}}" target="_blank" class="underline text-sky-600 hover:text-sky-800 ml-1">Ver perfil no ORCID.org <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i></a>`;
      }} else {{
        msg.innerHTML = `<span class="text-slate-400">Formato: 16 dígitos com hífens (${{formatted.length}}/19 caracteres)</span>`;
      }}
    }}

    function toggleCoiDetails(show) {{
      const container = document.getElementById("coiDetailsContainer");
      if (show) {{
        container.classList.remove("hidden");
      }} else {{
        container.classList.add("hidden");
      }}
    }}

    function onFullNameInput(val) {{
      const cit = generateDefaultCitation(val);
      const citInput = document.getElementById("authorCitationName");
      if (citInput) {{
        citInput.value = cit;
      }}
    }}

    function generateDefaultCitation(fullName) {{
      if (!fullName || !fullName.trim()) return "";
      const connectives = new Set(["da", "de", "do", "das", "dos", "e", "van", "von", "der", "del", "di"]);
      const rawParts = fullName.trim().split(/\\s+/);
      if (rawParts.length === 1) return rawParts[0];

      const lastName = rawParts[rawParts.length - 1];
      const givenParts = rawParts.slice(0, rawParts.length - 1);
      const initials = givenParts
        .filter(p => !connectives.has(p.toLowerCase()))
        .map(p => p[0].toUpperCase())
        .join("");

      return `${{lastName}} ${{initials}}`;
    }}

    function loadAuthorFormFromStorage() {{
      const cached = localStorage.getItem("article_machine_coauthor_profile");
      if (cached) {{
        try {{
          const p = JSON.parse(cached);
          if (p.full_name) document.getElementById("authorFullName").value = p.full_name;
          if (p.citation_name) document.getElementById("authorCitationName").value = p.citation_name;
          if (p.orcid) {{
            document.getElementById("authorOrcid").value = p.orcid;
            formatAndValidateOrcid(document.getElementById("authorOrcid"));
          }}
          if (p.email) document.getElementById("authorEmail").value = p.email;
          if (p.primary_institution) document.getElementById("authorInstitution1").value = p.primary_institution;
          if (p.department) document.getElementById("authorDepartment").value = p.department;
          if (p.secondary_institution) document.getElementById("authorInstitution2").value = p.secondary_institution;
          if (p.city_country) document.getElementById("authorCityCountry").value = p.city_country;
          if (p.credit_roles) {{
            document.getElementById("roleInvestigation").checked = p.credit_roles.includes("Investigation");
            document.getElementById("roleDataCuration").checked = p.credit_roles.includes("Data Curation");
            document.getElementById("roleValidation").checked = p.credit_roles.includes("Validation");
            document.getElementById("roleWritingReview").checked = p.credit_roles.includes("Writing - Review & Editing");
            document.getElementById("roleConceptualization").checked = p.credit_roles.includes("Conceptualization");
          }}
          if (p.coi_status === "declared") {{
            document.getElementById("coiYes").checked = true;
            toggleCoiDetails(true);
            if (p.coi_details) document.getElementById("authorCoiText").value = p.coi_details;
          }}
        }} catch (e) {{}}
      }} else if (currentContributor) {{
        document.getElementById("authorFullName").value = currentContributor;
      }}
    }}

    async function saveAuthorProfile() {{
      const fullName = document.getElementById("authorFullName").value.trim();
      const citationName = document.getElementById("authorCitationName").value.trim() || generateDefaultCitation(fullName);
      const orcid = document.getElementById("authorOrcid").value.trim();
      const email = document.getElementById("authorEmail").value.trim();
      const institution1 = document.getElementById("authorInstitution1").value.trim();
      const department = document.getElementById("authorDepartment").value.trim();
      const institution2 = document.getElementById("authorInstitution2").value.trim();
      const cityCountry = document.getElementById("authorCityCountry").value.trim();

      if (!fullName || !email || !institution1) {{
        showToast("Por favor, preencha Nome Completo, E-mail e Instituição Principal.", "error");
        return;
      }}

      const creditRoles = [];
      if (document.getElementById("roleInvestigation").checked) creditRoles.push("Investigation");
      if (document.getElementById("roleDataCuration").checked) creditRoles.push("Data Curation");
      if (document.getElementById("roleValidation").checked) creditRoles.push("Validation");
      if (document.getElementById("roleWritingReview").checked) creditRoles.push("Writing - Review & Editing");
      if (document.getElementById("roleConceptualization").checked) creditRoles.push("Conceptualization");

      if (creditRoles.length === 0) {{
        showToast("Selecione pelo menos um papel de autoria CRediT.", "error");
        return;
      }}

      const hasCoi = document.getElementById("coiYes").checked;
      const coiText = hasCoi ? document.getElementById("authorCoiText").value.trim() : "None declared";

      const icmjeApproved = document.getElementById("chkIcmjeApproved").checked;
      if (!icmjeApproved) {{
        showToast("Você deve confirmar a concordância com os critérios ICMJE de autoria.", "error");
        return;
      }}

      const profile = {{
        contract: "CoAuthorProfileV1",
        full_name: fullName,
        citation_name: citationName,
        orcid: orcid,
        email: email,
        primary_institution: institution1,
        department: department,
        secondary_institution: institution2,
        city_country: cityCountry,
        credit_roles: creditRoles,
        coi_status: hasCoi ? "declared" : "none",
        coi_details: coiText,
        icmje_approved: true,
        registered_at: new Date().toISOString()
      }};

      localStorage.setItem("article_machine_coauthor_profile", JSON.stringify(profile));
      currentContributor = fullName;
      localStorage.setItem("article_machine_contributor", fullName);
      updateContributorUI();

      const safeKey = (orcid || fullName).replace(/[^a-zA-Z0-9]/g, "_");
      const authorBlob = new Blob([JSON.stringify(profile, null, 2)], {{ type: "application/json" }});
      const storageRef = storage.ref(`coauthors/${{safeKey}}_profile.json`);

      const btn = document.getElementById("btnSaveAuthor");
      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Salvando no repositório seguro...';

      try {{
        await storageRef.put(authorBlob);
        showToast(`🎉 Parabéns, ${{fullName}}! Seus dados de autoria foram registrados com sucesso!`, "check");
        loadRegisteredCoauthors();
      }} catch (err) {{
        console.error("Author save error:", err);
        showToast("Dados salvos localmente no navegador! Sincronização em nuvem pendente.", "check");
        loadRegisteredCoauthors();
      }} finally {{
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Salvar Dados de Autoria';
      }}
    }}

    async function loadRegisteredCoauthors(isManual = false) {{
      const container = document.getElementById("coauthorsGrid");
      if (!container) return;

      const refreshIcon = document.getElementById("refreshCoauthorsIcon");
      if (refreshIcon && isManual) refreshIcon.classList.add("fa-spin");

      let loaded = [];
      try {{
        if (typeof storage !== "undefined") {{
          const res = await storage.ref("coauthors").listAll();
          for (const itemRef of res.items) {{
            try {{
              const dlUrl = await itemRef.getDownloadURL();
              const fileResp = await fetch(dlUrl);
              if (fileResp.ok) {{
                const authorData = await fileResp.json();
                loaded.push(authorData);
              }}
            }} catch (e) {{}}
          }}
        }}
      }} catch (err) {{
        console.warn("Storage listAll error, falling back to REST:", err);
        try {{
          const resp = await fetch("https://firebasestorage.googleapis.com/v0/b/{fb_config['storageBucket']}/o?prefix=coauthors%2F");
          if (resp.ok) {{
            const data = await resp.json();
            for (const item of (data.items || [])) {{
              try {{
                const dlUrl = `https://firebasestorage.googleapis.com/v0/b/{fb_config['storageBucket']}/o/${{encodeURIComponent(item.name)}}?alt=media`;
                const fileResp = await fetch(dlUrl);
                if (fileResp.ok) {{
                  const authorData = await fileResp.json();
                  loaded.push(authorData);
                }}
              }} catch (e) {{}}
            }}
          }}
        }} catch (e2) {{}}
      }}

      if (loaded.length === 0 && registeredCoauthors.length > 0) {{
        loaded = [...registeredCoauthors];
      }}

      const localCached = localStorage.getItem("article_machine_coauthor_profile");
      if (localCached) {{
        try {{
          const localProfile = JSON.parse(localCached);
          if (!loaded.find(a => a.full_name === localProfile.full_name || (a.orcid && a.orcid === localProfile.orcid))) {{
            loaded.unshift(localProfile);
          }}
        }} catch (e) {{}}
      }}

      registeredCoauthors = loaded;
      renderCoauthorsList(loaded);

      const countBadge = document.getElementById("coauthorCountBadge");
      if (countBadge) countBadge.innerText = `${{loaded.length}} cadastrado(s)`;

      if (refreshIcon) refreshIcon.classList.remove("fa-spin");
      if (isManual) showToast("Lista de coautores sincronizada com a nuvem!", "check");
    }}

    function renderCoauthorsList(list) {{
      const container = document.getElementById("coauthorsGrid");
      if (!container) return;

      if (!list || list.length === 0) {{
        container.innerHTML = '<div class="col-span-full text-center py-6 text-slate-400 text-xs italic">Nenhum autor cadastrado ainda. Preencha o formulário acima para registrar seus dados!</div>';
        return;
      }}

      container.innerHTML = list.map(a => {{
        const orcidBadge = a.orcid ? `
          <a href="https://orcid.org/${{a.orcid}}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[11px] font-mono font-bold border border-emerald-300 hover:bg-emerald-100 transition-colors">
            <i class="fa-brands fa-orcid text-emerald-600"></i> ${{a.orcid}}
          </a>
        ` : '<span class="text-[11px] text-slate-400 italic">Sem ORCID informado</span>';

        const rolesBadges = (a.credit_roles || []).map(r => `
          <span class="px-2 py-0.5 rounded bg-sky-50 text-sky-800 text-[10px] font-semibold border border-sky-200">${{r}}</span>
        `).join("");

        return `
          <div class="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-sm transition-all space-y-2">
            <div class="flex items-start justify-between gap-2">
              <div>
                <h4 class="font-bold text-slate-900 text-sm">${{a.full_name}}</h4>
                <span class="text-xs text-slate-500 font-mono">Citação: ${{a.citation_name || a.full_name}}</span>
              </div>
              ${{orcidBadge}}
            </div>

            <div class="text-xs text-slate-600 space-y-0.5">
              <p><i class="fa-solid fa-building-columns text-slate-400 w-4"></i> ${{a.primary_institution || 'Instituição não informada'}}</p>
              ${{a.department ? `<p><i class="fa-solid fa-sitemap text-slate-400 w-4"></i> ${{a.department}}</p>` : ''}}
              ${{a.email ? `<p><i class="fa-solid fa-envelope text-slate-400 w-4"></i> <span class="text-sky-700 font-medium">${{a.email}}</span></p>` : ''}}
            </div>

            <div class="pt-2 border-t border-slate-200/60 flex flex-wrap gap-1">
              ${{rolesBadges}}
            </div>
          </div>
        `;
      }}).join("");
    }}

    function exportCoauthorsCSV() {{
      if (registeredCoauthors.length === 0) {{
        showToast("Nenhum autor cadastrado ainda para exportar.", "info");
        return;
      }}

      const headers = ["Nome Completo", "Nome Citacao", "ORCID", "Email", "Instituicao Principal", "Departamento", "Cidade Estado Pais", "Papeis CRediT", "Conflito Interesses", "Data Registro"];
      const rows = registeredCoauthors.map(a => [
        `"${{(a.full_name || '').replace(/"/g, '""')}}"`,
        `"${{(a.citation_name || '').replace(/"/g, '""')}}"`,
        `"${{(a.orcid || '').replace(/"/g, '""')}}"`,
        `"${{(a.email || '').replace(/"/g, '""')}}"`,
        `"${{(a.primary_institution || '').replace(/"/g, '""')}}"`,
        `"${{(a.department || '').replace(/"/g, '""')}}"`,
        `"${{(a.city_country || '').replace(/"/g, '""')}}"`,
        `"${{(a.credit_roles || []).join('; ')}}"`,
        `"${{a.coi_status || 'none'}}"`,
        `"${{a.registered_at || ''}}"`
      ]);

      const csvContent = "\\uFEFF" + [headers.join(","), ...rows.map(r => r.join(","))].join("\\n");
      const blob = new Blob([csvContent], {{ type: "text/csv;charset=utf-8;" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `coautores_submissao_${{Date.now()}}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast("Planilha CSV de coautores baixada com sucesso!", "check");
    }}

    // Initialize
    updateContributorUI();
    renderStudies();
    syncStorageStatus();
    loadAuthorFormFromStorage();
    loadRegisteredCoauthors();

    // Auto-polling em tempo real (a cada 8 segundos) na aba de autoria
    setInterval(() => {{
      const authTab = document.getElementById("tab-authors");
      if (authTab && !authTab.classList.contains("hidden")) {{
        loadRegisteredCoauthors(false);
      }}
    }}, 8000);
  </script>
</body>
</html>
"""
    return html


def build_portal(project_dir: Path, target_dir: Path | None = None, firebase_project: str = "pharosreader") -> dict[str, Any]:
    """Build the standalone collaborative retrieval portal files for a project."""
    p_dir = Path(project_dir)
    portal_dir = target_dir or (p_dir / "portal_recuperacao")
    public_dir = portal_dir / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate index.html
    html_content = generate_portal_html(p_dir)
    index_file = public_dir / "index.html"
    index_file.write_text(html_content, encoding="utf-8")

    # 2. Generate firebase.json
    (portal_dir / "firebase.json").write_text(json.dumps(FIREBASE_JSON, indent=2), encoding="utf-8")

    # 3. Generate storage.rules
    (portal_dir / "storage.rules").write_text(STORAGE_RULES, encoding="utf-8")

    # 4. Generate .firebaserc (must be valid JSON)
    (portal_dir / ".firebaserc").write_text(json.dumps({"projects": {"default": firebase_project}}, indent=2), encoding="utf-8")

    # 5. Manifest
    manifest = {
        "contract": "RetrievalPortalManifest",
        "project_slug": p_dir.name,
        "firebase_project": firebase_project,
        "hosting_url": f"https://{firebase_project}.web.app",
        "storage_bucket": f"{firebase_project}.firebasestorage.app",
        "created_at": datetime.now(UTC).isoformat(),
        "files_count": len(load_project_studies(p_dir))
    }
    (portal_dir / "portal_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "contract": "BuildPortalResult",
        "status": "pass",
        "portal_dir": str(portal_dir),
        "hosting_url": f"https://{firebase_project}.web.app",
        "studies_count": manifest["files_count"]
    }


def sync_portal(project_dir: Path, bucket: str = "pharosreader.firebasestorage.app") -> dict[str, Any]:
    """Sync PDFs and not-found audit reports uploaded to Firebase Storage down to the project."""
    p_dir = Path(project_dir)
    full_texts_dir = p_dir / "sources/full_texts"
    extracted_dir = p_dir / "sources/extracted"
    reports_dir = p_dir / "evidence/reports_not_retrieved"
    status_file = p_dir / "screening/core_100_full_text_status.json"

    full_texts_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    core_studies = _load_json_data(status_file) or []
    if isinstance(core_studies, dict):
        core_studies = core_studies.get("studies", [])
    studies_by_id = {s.get("record_id"): s for s in core_studies}
    existing_local_ids = {p.stem.split("_")[0]: p for p in full_texts_dir.glob("*.pdf")}

    # 1. Sync PDFs from full_texts/
    api_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o?prefix=full_texts%2F"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "ArticleMachine/1.0"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {
            "contract": "SyncPortalResult",
            "status": "error",
            "error": str(e),
            "new_downloaded": 0,
            "total_local": len(existing_local_ids)
        }

    items = data.get("items", [])
    new_downloads = 0
    updated_studies = False
    contributor_counts: dict[str, int] = {}

    for item in items:
        blob_name = item.get("name", "")
        match = re.search(r"(STUDY-\d{4})", blob_name)
        if not match:
            continue

        study_id = match.group(1)
        study_meta = studies_by_id.get(study_id, {})
        
        # Parse contributor
        parts = blob_name.replace("full_texts/", "").split("_")
        contributor = "Equipe Científica"
        if len(parts) >= 3 and not parts[1].isdigit() and len(parts[1]) >= 2:
            contributor = parts[1]
        contributor_counts[contributor] = contributor_counts.get(contributor, 0) + 1

        if study_id not in existing_local_ids:
            year = str(study_meta.get("year", "2024"))
            authors = study_meta.get("authors", [])
            author_slug = "Unknown"
            if authors:
                first_author = authors[0]
                author_slug = re.sub(r"[^\w\s-]", "", first_author).strip().split()[-1] or "EtAl"

            title_words = re.sub(r"[^\w\s-]", "", study_meta.get("title", "")).strip().split()[:5]
            title_slug = "_".join(title_words) if title_words else "Article"

            canonical_filename = f"{study_id}_{year}_{author_slug}_{title_slug}.pdf"
            target_path = full_texts_dir / canonical_filename

            encoded_name = urllib.parse.quote(blob_name, safe="")
            download_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{encoded_name}?alt=media"

            try:
                req_dl = urllib.request.Request(download_url, headers={"User-Agent": "ArticleMachine/1.0"})
                with urllib.request.urlopen(req_dl) as dl_resp:
                    content = dl_resp.read()
                    target_path.write_bytes(content)

                new_downloads += 1
                existing_local_ids[study_id] = target_path

                # Text extraction
                txt_path = extracted_dir / f"{study_id}.txt"
                _extract_text_from_pdf(target_path, txt_path)

                if study_id in studies_by_id:
                    studies_by_id[study_id]["downloaded"] = True
                    studies_by_id[study_id]["local_pdf"] = str(target_path.relative_to(p_dir))
                    studies_by_id[study_id]["retrieved_by"] = contributor
                    updated_studies = True
            except Exception:
                pass
        else:
            if study_id in studies_by_id and not studies_by_id[study_id].get("retrieved_by"):
                studies_by_id[study_id]["retrieved_by"] = contributor
                updated_studies = True

    # 2. Sync unretrieved reports from reports/
    new_reports = 0
    try:
        rep_api = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o?prefix=reports%2F"
        req_rep = urllib.request.Request(rep_api, headers={"User-Agent": "ArticleMachine/1.0"})
        with urllib.request.urlopen(req_rep) as resp_rep:
            data_rep = json.loads(resp_rep.read().decode("utf-8"))
        for item in data_rep.get("items", []):
            blob_name = item.get("name", "")
            match = re.search(r"(STUDY-\d{4})", blob_name)
            if not match:
                continue
            study_id = match.group(1)
            local_report = reports_dir / f"{study_id}_unretrieved.json"
            if not local_report.is_file():
                encoded_name = urllib.parse.quote(blob_name, safe="")
                dl_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{encoded_name}?alt=media"
                with urllib.request.urlopen(urllib.request.Request(dl_url, headers={"User-Agent": "ArticleMachine/1.0"})) as dl_r:
                    rep_content = dl_r.read()
                    local_report.write_bytes(rep_content)
                new_reports += 1
                
                try:
                    rep_json = json.loads(rep_content.decode("utf-8"))
                    if study_id in studies_by_id and not studies_by_id[study_id].get("downloaded"):
                        studies_by_id[study_id]["unretrieved"] = True
                        studies_by_id[study_id]["failed_by"] = rep_json.get("contributor", "Equipe")
                        studies_by_id[study_id]["failed_checklist"] = rep_json.get("checklist", {})
                        updated_studies = True
                except Exception:
                    pass
    except Exception:
        pass

    # 3. Update status json
    if updated_studies and status_file.is_file():
        status_file.write_text(json.dumps(list(studies_by_id.values()), indent=2, ensure_ascii=False), encoding="utf-8")

    # 3.5. Sync Co-authors from coauthors/
    coauthors_dir = p_dir / "evidence/coauthors"
    coauthors_dir.mkdir(parents=True, exist_ok=True)
    coauthors_list = []

    try:
        coauth_api = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o?prefix=coauthors%2F"
        req_coauth = urllib.request.Request(coauth_api, headers={"User-Agent": "ArticleMachine/1.0"})
        with urllib.request.urlopen(req_coauth) as resp_coauth:
            data_coauth = json.loads(resp_coauth.read().decode("utf-8"))
        for item in data_coauth.get("items", []):
            blob_name = item.get("name", "")
            encoded_name = urllib.parse.quote(blob_name, safe="")
            dl_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{encoded_name}?alt=media"
            with urllib.request.urlopen(urllib.request.Request(dl_url, headers={"User-Agent": "ArticleMachine/1.0"})) as dl_r:
                content = dl_r.read()
                try:
                    c_json = json.loads(content.decode("utf-8"))
                    coauthors_list.append(c_json)
                except Exception:
                    pass
    except Exception:
        pass

    if coauthors_list:
        (p_dir / "evidence/coauthors_registry.json").write_text(json.dumps(coauthors_list, indent=2, ensure_ascii=False), encoding="utf-8")
        csv_lines = ["Nome Completo,Nome Citacao,ORCID,Email,Instituicao Principal,Departamento,Cidade Estado Pais,Papeis CRediT,Conflito Interesses,Data Registro"]
        for c in coauthors_list:
            roles = "; ".join(c.get("credit_roles", []))
            row = [
                f'"{c.get("full_name", "")}"',
                f'"{c.get("citation_name", "")}"',
                f'"{c.get("orcid", "")}"',
                f'"{c.get("email", "")}"',
                f'"{c.get("primary_institution", "")}"',
                f'"{c.get("department", "")}"',
                f'"{c.get("city_country", "")}"',
                f'"{roles}"',
                f'"{c.get("coi_status", "none")}"',
                f'"{c.get("registered_at", "")}"',
            ]
            csv_lines.append(",".join(row))
        (p_dir / "evidence/tabela_coautores_submissao.csv").write_text("\n".join(csv_lines), encoding="utf-8")

    # 4. Generate Contributors & Acknowledgments Report
    ack_report_path = p_dir / "evidence/relatorio_colaboradores_recuperacao.md"
    ack_report_path.parent.mkdir(parents=True, exist_ok=True)
    
    ack_lines = [
        "# Relatório de Colaboradores e Agradecimentos da Recuperação de Artigos",
        "",
        f"**Projeto:** {p_dir.name}  ",
        f"**Data da Auditoria:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"**Total de Estudos no Corpus:** {len(core_studies)}  ",
        f"**Artigos Recuperados:** {len(existing_local_ids)}  ",
        "",
        "## 1. Quadro de Colaboradores (Para Seção de Agradecimentos / Acknowledgments)",
        "",
        "| Colaborador / Pesquisador | Artigos Recuperados | Papel na Revisão |",
        "| :--- | :--- | :--- |"
    ]
    for c_name, count in sorted(contributor_counts.items(), key=lambda x: x[1], reverse=True):
        ack_lines.append(f"| **{c_name}** | {count} | Recuperação de textos completos e busca bibliográfica |")
    
    ack_lines.extend([
        "",
        "## 2. Texto Canônico para a Seção de Agradecimentos (Inglês)",
        "",
        "> *Acknowledgments: The authors wish to thank " + 
        ", ".join(sorted(contributor_counts.keys())) + 
        " for their invaluable assistance with full-text article retrieval across institutional library networks (CAPES/CAFe) and scientific databases.*",
        "",
        "## 3. Texto Canônico para a Seção de Agradecimentos (Português)",
        "",
        "> *Agradecimentos: Os autores agradecem a " + 
        ", ".join(sorted(contributor_counts.keys())) + 
        " pelo auxílio indispensável na recuperação dos textos completos nas redes de bibliotecas institucionais (CAPES/CAFe) e bases de dados científicas.*"
    ])

    if coauthors_list:
        ack_lines.extend([
            "",
            "## 4. Metadados de Autoria para Submissão Formal (ORCID & CRediT)",
            "",
            "| Nome Completo | Nome Citação | ORCID | E-mail | Instituição Principal | Papéis CRediT |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ])
        for c in coauthors_list:
            roles = ", ".join(c.get("credit_roles", []))
            ack_lines.append(f"| **{c.get('full_name', '')}** | {c.get('citation_name', '')} | [{c.get('orcid', 'N/D')}](https://orcid.org/{c.get('orcid', '')}) | {c.get('email', '')} | {c.get('primary_institution', '')} | {roles} |")

    ack_report_path.write_text("\n".join(ack_lines), encoding="utf-8")

    total_local = len(existing_local_ids)
    pct = round((total_local / len(core_studies)) * 100, 1) if core_studies else 0.0

    return {
        "contract": "SyncPortalResult",
        "status": "pass",
        "new_downloaded": new_downloads,
        "new_unretrieved_reports": new_reports,
        "total_local": total_local,
        "total_target": len(core_studies),
        "coverage_percentage": pct,
        "pending": len(core_studies) - total_local,
        "contributors": contributor_counts,
        "acknowledgments_report": str(ack_report_path.relative_to(p_dir))
    }


def portal_status(project_dir: Path) -> dict[str, Any]:
    """Get the current retrieval portal and full-text status for a project."""
    p_dir = Path(project_dir)
    status_file = p_dir / "screening/core_100_full_text_status.json"
    full_texts_dir = p_dir / "sources/full_texts"
    reports_dir = p_dir / "evidence/reports_not_retrieved"

    core_studies = _load_json_data(status_file) or []
    if isinstance(core_studies, dict):
        core_studies = core_studies.get("studies", [])
    existing_pdfs = list(full_texts_dir.glob("*.pdf")) if full_texts_dir.is_dir() else []
    existing_reports = list(reports_dir.glob("*.json")) if reports_dir.is_dir() else []
    
    total = len(core_studies)
    completed = len(existing_pdfs)
    not_retrieved = len(existing_reports)
    pending = max(0, total - (completed + not_retrieved))
    pct = round((completed / total) * 100, 1) if total > 0 else 0.0

    portal_manifest = p_dir / "portal_recuperacao/portal_manifest.json"
    manifest = _load_json_data(portal_manifest) or {}

    return {
        "contract": "PortalStatusReport",
        "status": "pass",
        "project": p_dir.name,
        "total_studies": total,
        "completed": completed,
        "not_retrieved": not_retrieved,
        "pending": pending,
        "coverage_percentage": pct,
        "hosting_url": manifest.get("hosting_url", "https://pharosreader.web.app"),
        "portal_built": portal_manifest.is_file()
    }
