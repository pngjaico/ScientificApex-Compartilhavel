from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

from .benchmarks import validate_benchmark_report
from .evidence import validate_evidence_lock
from .projects import MODE_ORDER, MACHINE_GOVERNANCE_MODE_ORDER
from .policy.gates import canonical_gate
from .serialization import load_structured_file, save_structured_file


QUERY_PLAN_PATH = Path("context") / "query_plan.yaml"
COMPILED_QUERY_PATH = Path("context") / "retrieval" / "compiled_queries.json"
RETRIEVAL_PLAN_PATH = Path("context") / "retrieval" / "retrieval_plan.json"
IDEA_INPUT_PATH = Path("context") / "ideas" / "idea_candidates.json"
IDEA_REPORT_PATH = Path("analysis") / "idea_tournament_report.json"
STAGE_AUDIT_PATH = Path("reviews") / "stage_audit_report.json"
GUARDRAIL_PATH = Path("reviews") / "guardrail_report.json"
MACHINE_AUDIT_PATH = Path("reviews") / "machine_audit_report.json"

CURRENT_MACHINE_UPGRADE_REQUEST = (
    "vamos melhorar a máquina, agora com o 5.6 sol ultra, ainda não mexi nela depois de ser lançado esse modelo, "
    "veja oq podemos melhorar, aprimorar, revisar, organizar e afins"
)

ROUTING_CANARIES: tuple[dict[str, Any], ...] = (
    {
        "id": "current_sol_ultra_machine_upgrade",
        "query": CURRENT_MACHINE_UPGRADE_REQUEST,
        "required_skills": ("skill-upgrade-governor", "agent-benchmark-harness"),
    },
    {
        "id": "graph_first_workspace_navigation",
        "query": "Como um agente novo deve navegar o workspace usando o grafo operacional Graphify?",
        "required_skills": ("workspace-graph-navigator",),
    },
    {
        "id": "reviewer_response_integrity",
        "query": "Responder pareceristas com rebuttal e checar a integridade das referências do manuscrito.",
        "required_skills": ("manuscript-integrity-response-governor",),
    },
)

QUERY_CONTRACT_VERSION = 1

CANONICAL_FIELDS = {
    "title_abstract",
    "title",
    "abstract",
    "mesh",
    "author",
    "journal",
    "doi",
    "pmid",
    "orcid",
    "affiliation",
    "institution",
}

PROVIDER_SPECS: dict[str, dict[str, Any]] = {
    "pubmed": {
        "contract": "ProviderSpec",
        "provider": "pubmed",
        "display_name": "PubMed / NCBI E-utilities",
        "source_url": "https://eutilities.github.io/site/API_Key/usageandkey/",
        "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
        "requires_live_calls": False,
        "authentication": {"api_key_optional": True, "tool_email_required_for_block_recovery": True},
        "rate_limit": {
            "policy": "no more than 3 requests/second without API key; up to 10 requests/second with API key by default",
            "requests_per_second_without_key": 3,
            "requests_per_second_with_key": 10,
        },
        "supported_fields": ["title_abstract", "title", "abstract", "mesh", "author", "journal", "doi", "pmid"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "europe_pmc": {
        "contract": "ProviderSpec",
        "provider": "europe_pmc",
        "display_name": "Europe PMC",
        "source_url": "https://dev.europepmc.org/RestfulWebService",
        "base_url": "https://www.ebi.ac.uk/europepmc/webservices/rest/",
        "requires_live_calls": False,
        "authentication": {"api_key_optional": False, "tool_email_required_for_block_recovery": False},
        "rate_limit": {
            "policy": "public REST API; local contract uses conservative throttling and requires fresh policy review before live use",
            "requests_per_second_without_key": 5,
            "requests_per_second_with_key": None,
        },
        "supported_fields": ["title_abstract", "title", "abstract", "mesh", "author", "journal", "doi", "pmid"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "openalex": {
        "contract": "ProviderSpec",
        "provider": "openalex",
        "display_name": "OpenAlex",
        "source_url": "https://docs.openalex.org/how-to-use-the-api/api-overview",
        "base_url": "https://api.openalex.org/",
        "requires_live_calls": False,
        "authentication": {"api_key_required": True, "api_key_cost": "free"},
        "rate_limit": {
            "policy": "API key required for current API; check credits/rate status before live use",
            "requests_per_second_without_key": 0,
            "requests_per_second_with_key": None,
        },
        "supported_fields": ["title_abstract", "title", "author", "journal", "doi", "pmid", "orcid", "institution"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "crossref": {
        "contract": "ProviderSpec",
        "provider": "crossref",
        "display_name": "Crossref REST",
        "source_url": "https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
        "base_url": "https://api.crossref.org/",
        "requires_live_calls": False,
        "authentication": {"mailto_required_for_polite_pool": True},
        "rate_limit": {
            "policy": "responsible use with mailto/tool identification; backoff on 429/503",
            "requests_per_second_without_key": None,
            "requests_per_second_with_key": None,
        },
        "supported_fields": ["title", "author", "journal", "doi"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "orcid": {
        "contract": "ProviderSpec",
        "provider": "orcid",
        "display_name": "ORCID",
        "source_url": "https://info.orcid.org/documentation/integration-and-api-faq/",
        "base_url": "https://pub.orcid.org/",
        "requires_live_calls": False,
        "authentication": {"public_api_available": True},
        "rate_limit": {
            "policy": "public API contract; live use must add client identification, cache, and replay manifest",
            "requests_per_second_without_key": None,
            "requests_per_second_with_key": None,
        },
        "supported_fields": ["author", "orcid", "affiliation"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "ror": {
        "contract": "ProviderSpec",
        "provider": "ror",
        "display_name": "ROR",
        "source_url": "https://ror.readme.io/",
        "base_url": "https://api.ror.org/",
        "requires_live_calls": False,
        "authentication": {"public_api_available": True},
        "rate_limit": {
            "policy": "public API contract; live use must add cache, throttle, and replay manifest",
            "requests_per_second_without_key": None,
            "requests_per_second_with_key": None,
        },
        "supported_fields": ["affiliation", "institution"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "crossref_retractions": {
        "contract": "ProviderSpec",
        "provider": "crossref_retractions",
        "display_name": "Retraction metadata via Crossref/Crossmark when available",
        "source_url": "https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
        "base_url": "https://api.crossref.org/",
        "requires_live_calls": False,
        "authentication": {"mailto_required_for_polite_pool": True},
        "rate_limit": {
            "policy": "responsible Crossref use with mailto/tool identification; retraction coverage is incomplete",
            "requests_per_second_without_key": None,
            "requests_per_second_with_key": None,
        },
        "supported_fields": ["title", "doi"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "osf": {
        "contract": "ProviderSpec",
        "provider": "osf",
        "display_name": "Open Science Framework (OSF) API v2",
        "source_url": "https://developer.osf.io/",
        "base_url": "https://api.osf.io/v2/",
        "requires_live_calls": False,
        "authentication": {
            "api_key_optional": True,
            "token_env_var": "OSF_TOKEN",
            "token_cost": "free",
        },
        "rate_limit": {
            "policy": "OSF API v2 rate limiting (100 req/min authenticated, 30 req/min unauthenticated); exponential backoff on 429",
            "requests_per_second_without_key": 0.5,
            "requests_per_second_with_key": 1.6,
        },
        "supported_fields": ["title", "abstract", "author", "doi", "affiliation", "institution"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "scopus": {
        "contract": "ProviderSpec",
        "provider": "scopus",
        "display_name": "Elsevier Scopus Search API / Export",
        "source_url": "https://dev.elsevier.com/sc_search_tips.html",
        "base_url": "https://api.elsevier.com/content/search/scopus",
        "requires_live_calls": False,
        "authentication": {
            "api_key_optional": True,
            "token_env_var": "SCOPUS_API_KEY",
            "manual_export_drop_folder": "sources/manual_imports/scopus",
        },
        "rate_limit": {
            "policy": "Elsevier API quota (2 to 9 req/sec depending on endpoint); supports manual RIS/CSV drop-folder import",
            "requests_per_second_without_key": 0,
            "requests_per_second_with_key": 2,
        },
        "supported_fields": ["title_abstract", "title", "abstract", "mesh", "author", "journal", "doi", "pmid", "affiliation"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "embase": {
        "contract": "ProviderSpec",
        "provider": "embase",
        "display_name": "Elsevier Embase (Emtree / TiAbKw)",
        "source_url": "https://www.embase.com/",
        "base_url": "https://www.embase.com/",
        "requires_live_calls": False,
        "authentication": {
            "api_key_optional": True,
            "manual_export_drop_folder": "sources/manual_imports/embase",
        },
        "rate_limit": {
            "policy": "Compiled Embase query string for institutional export (RIS/CSV) into sources/manual_imports/embase",
            "requests_per_second_without_key": None,
            "requests_per_second_with_key": None,
        },
        "supported_fields": ["title_abstract", "title", "abstract", "mesh", "author", "journal", "doi", "pmid"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "cochrane_central": {
        "contract": "ProviderSpec",
        "provider": "cochrane_central",
        "display_name": "Cochrane CENTRAL Register of Controlled Trials",
        "source_url": "https://www.cochranelibrary.com/advanced-search",
        "base_url": "https://www.cochranelibrary.com/",
        "requires_live_calls": False,
        "authentication": {
            "api_key_optional": True,
            "manual_export_drop_folder": "sources/manual_imports/cochrane_central",
        },
        "rate_limit": {
            "policy": "Compiled CENTRAL query string for RIS/CSV export into sources/manual_imports/cochrane_central",
            "requests_per_second_without_key": None,
            "requests_per_second_with_key": None,
        },
        "supported_fields": ["title_abstract", "title", "abstract", "mesh", "author", "journal", "doi"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
    "lilacs_bvs": {
        "contract": "ProviderSpec",
        "provider": "lilacs_bvs",
        "display_name": "LILACS / BVS (BIREME)",
        "source_url": "https://pesquisa.bvsalud.org/",
        "base_url": "https://pesquisa.bvsalud.org/",
        "requires_live_calls": False,
        "authentication": {
            "api_key_optional": True,
            "manual_export_drop_folder": "sources/manual_imports/lilacs_bvs",
        },
        "rate_limit": {
            "policy": "Compiled BVS/LILACS query string for RIS/CSV export into sources/manual_imports/lilacs_bvs",
            "requests_per_second_without_key": None,
            "requests_per_second_with_key": None,
        },
        "supported_fields": ["title_abstract", "title", "abstract", "mesh", "author", "journal", "doi"],
        "requires_manifest_fields": ["provider", "query_hash", "retrieved_at", "record_count", "records_sha256"],
    },
}

GUIDELINE_ROUTES: dict[str, dict[str, str]] = {
    "systematic-review": {
        "primary_guideline": "PRISMA 2020",
        "source_url": "https://www.prisma-statement.org/prisma-2020",
    },
    "network-meta-analysis": {
        "primary_guideline": "PRISMA 2020 plus network meta-analysis extension when applicable",
        "source_url": "https://www.prisma-statement.org/prisma-2020",
    },
    "clinical-trial": {
        "primary_guideline": "CONSORT 2025",
        "source_url": "https://www.consort-spirit.org/",
    },
    "observational-study": {
        "primary_guideline": "EQUATOR-indexed design-specific guideline, commonly STROBE",
        "source_url": "https://www.equator-network.org/reporting-guidelines/",
    },
}

FIELD_RENDERERS: dict[str, dict[str, str]] = {
    "pubmed": {
        "title_abstract": "Title/Abstract",
        "title": "Title",
        "abstract": "Abstract",
        "mesh": "MeSH Terms",
        "author": "Author",
        "journal": "Journal",
        "doi": "AID",
        "pmid": "PMID",
    },
    "europe_pmc": {
        "title_abstract": "TITLE_ABS",
        "title": "TITLE",
        "abstract": "ABSTRACT",
        "mesh": "MESH",
        "author": "AUTH",
        "journal": "JOURNAL",
        "doi": "DOI",
        "pmid": "EXT_ID",
    },
    "openalex": {
        "title_abstract": "search",
        "title": "title.search",
        "author": "authorships.author.display_name.search",
        "journal": "primary_location.source.display_name.search",
        "doi": "doi",
        "pmid": "ids.pmid",
        "orcid": "authorships.author.orcid",
        "institution": "institutions.ror",
    },
    "crossref": {
        "title": "query.title",
        "author": "query.author",
        "journal": "query.container-title",
        "doi": "doi",
    },
    "orcid": {
        "author": "given-names/family-name",
        "orcid": "orcid",
        "affiliation": "affiliation-org-name",
    },
    "ror": {
        "affiliation": "query",
        "institution": "query",
    },
    "crossref_retractions": {
        "title": "query.title",
        "doi": "doi",
    },
    "osf": {
        "title": "title",
        "abstract": "description",
        "author": "contributors",
        "doi": "doi",
        "affiliation": "affiliated_institutions",
        "institution": "affiliated_institutions",
    },
    "scopus": {
        "title_abstract": "TITLE-ABS-KEY",
        "title": "TITLE",
        "abstract": "ABS",
        "mesh": "INDEXTERMS",
        "author": "AUTH",
        "journal": "SRCTITLE",
        "doi": "DOI",
        "pmid": "PMID",
        "affiliation": "AFFIL",
    },
    "embase": {
        "title_abstract": ":ti,ab,kw",
        "title": ":ti",
        "abstract": ":ab",
        "mesh": "/exp",
        "author": ":au",
        "journal": ":jt",
        "doi": ":doi",
        "pmid": ":ui",
    },
    "cochrane_central": {
        "title_abstract": ":ti,ab,kw",
        "title": ":ti",
        "abstract": ":ab",
        "mesh": "mh",
        "author": ":au",
        "journal": ":so",
        "doi": ":doi",
    },
    "lilacs_bvs": {
        "title_abstract": "tw",
        "title": "ti",
        "abstract": "ab",
        "mesh": "mh",
        "author": "au",
        "journal": "ta",
        "doi": "doi",
    },
}

FACTUAL_GUIDELINE_SOURCES = [
    "https://www.prisma-statement.org/prisma-2020",
    "https://www.consort-spirit.org/",
    "https://www.equator-network.org/reporting-guidelines/",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_from_issues(issues: list[str]) -> str:
    return "pass" if not issues else "block"


def _sha256_payload(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_provider_spec(provider_id: str, spec: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    label = provider_id or str(spec.get("provider") or "<unknown>")
    for field in ["contract", "provider", "source_url", "base_url", "rate_limit", "supported_fields"]:
        if not spec.get(field):
            issues.append(f"{label}: ProviderSpec missing '{field}'.")
    if spec.get("contract") != "ProviderSpec":
        issues.append(f"{label}: contract must be ProviderSpec.")
    rate_limit = spec.get("rate_limit")
    if not isinstance(rate_limit, dict) or not rate_limit.get("policy"):
        issues.append(f"{label}: ProviderSpec requires declared rate_limit.policy.")
    supported_fields = spec.get("supported_fields")
    if not isinstance(supported_fields, list) or not supported_fields:
        issues.append(f"{label}: ProviderSpec requires non-empty supported_fields.")
    else:
        invalid = [field for field in supported_fields if field not in CANONICAL_FIELDS]
        if invalid:
            issues.append(f"{label}: unsupported canonical fields {invalid}.")
    manifest_fields = spec.get("requires_manifest_fields")
    required_manifest = {"provider", "query_hash", "retrieved_at", "record_count", "records_sha256"}
    if not isinstance(manifest_fields, list) or not required_manifest.issubset(set(manifest_fields)):
        issues.append(f"{label}: ProviderSpec requires manifest fields {sorted(required_manifest)}.")
    return issues


def validate_provider_specs(provider_specs: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    specs = provider_specs or PROVIDER_SPECS
    issues: list[str] = []
    for provider_id, spec in specs.items():
        issues.extend(validate_provider_spec(provider_id, spec))
    return {
        "contract": "ProviderSpecAudit",
        "status": _status_from_issues(issues),
        "provider_count": len(specs),
        "providers": sorted(specs),
        "issues": issues,
    }


def _load_query_plan(project_dir: Path) -> tuple[dict[str, Any], Path]:
    path = Path(project_dir) / QUERY_PLAN_PATH
    return load_structured_file(path), path


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _balanced(value: str, opener: str, closer: str) -> bool:
    depth = 0
    for char in value:
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
        if depth < 0:
            return False
    return depth == 0


def _term_issues(term: str, context: str) -> list[str]:
    issues: list[str] = []
    term = str(term or "").strip()
    if not term:
        issues.append(f"{context}: empty term.")
        return issues
    if not _balanced(term, "(", ")"):
        issues.append(f"{context}: broken parentheses in term '{term}'.")
    if term.count('"') % 2 != 0:
        issues.append(f"{context}: unbalanced quotes in term '{term}'.")
    if re.search(r"\b(AND|OR|NOT)\b|&&|\|\|", term, flags=re.IGNORECASE):
        issues.append(f"{context}: term '{term}' contains raw boolean logic; put booleans in the plan, not inside terms.")
    if re.search(r"(^|[^A-Za-z0-9])([A-Za-z0-9]{0,2})\*", term):
        issues.append(f"{context}: term '{term}' uses dangerous wildcard; require at least 3 leading characters.")
    return issues


def _validate_date_range(date_range: Any) -> list[str]:
    if not date_range:
        return []
    if not isinstance(date_range, dict):
        return ["date_range must be an object with from/to."]
    issues: list[str] = []
    start = str(date_range.get("from") or "")
    end = str(date_range.get("to") or "")
    for label, value in [("from", start), ("to", end)]:
        if value and not re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", value):
            issues.append(f"date_range.{label} must be YYYY, YYYY-MM, or YYYY-MM-DD.")
    if start and end and start > end:
        issues.append("date_range.from must not be after date_range.to.")
    return issues


def validate_query_plan(project_dir: Path) -> dict[str, Any]:
    project_dir = Path(project_dir)
    query_plan, query_path = _load_query_plan(project_dir)
    issues: list[str] = []
    warnings: list[str] = []

    if not query_path.exists():
        issues.append("context/query_plan.yaml is missing.")
        query_plan = {}
    if not isinstance(query_plan, dict):
        issues.append("QueryPlan must be an object.")
        query_plan = {}

    provider_audit = validate_provider_specs()
    if provider_audit["status"] != "pass":
        issues.extend(provider_audit["issues"])

    if query_plan:
        if query_plan.get("contract") not in {None, "QueryPlan"}:
            issues.append("QueryPlan contract must be 'QueryPlan' when declared.")
        if not query_plan.get("topic"):
            issues.append("QueryPlan.topic is required.")

        providers = [str(item) for item in _as_list(query_plan.get("providers") or ["pubmed"])]
        if not providers:
            issues.append("QueryPlan.providers must include at least one provider.")
        unknown_providers = [provider for provider in providers if provider not in PROVIDER_SPECS]
        if unknown_providers:
            issues.append(f"Unknown providers: {unknown_providers}.")

        boolean = str(query_plan.get("boolean") or "AND").upper()
        if boolean not in {"AND", "OR"}:
            issues.append("QueryPlan.boolean must be AND or OR; nested logic belongs in structured concepts.")

        concepts = query_plan.get("concepts")
        if not isinstance(concepts, list) or not concepts:
            issues.append("QueryPlan.concepts must be a non-empty list.")
        else:
            for index, concept in enumerate(concepts, start=1):
                label = f"concept[{index}]"
                if not isinstance(concept, dict):
                    issues.append(f"{label}: must be an object.")
                    continue
                if not concept.get("id"):
                    issues.append(f"{label}: id is required.")
                field = str(concept.get("field") or "title_abstract")
                if field not in CANONICAL_FIELDS:
                    issues.append(f"{label}: unknown field '{field}'.")
                terms = [str(item) for item in _as_list(concept.get("terms")) + _as_list(concept.get("synonyms"))]
                if not terms:
                    issues.append(f"{label}: terms or synonyms are required.")
                for term in terms:
                    issues.extend(_term_issues(term, label))
                for provider in providers:
                    spec = PROVIDER_SPECS.get(provider)
                    if spec and field not in spec.get("supported_fields", []):
                        issues.append(f"{label}: field '{field}' is incompatible with provider '{provider}'.")

        exclusions = query_plan.get("exclusions", [])
        if exclusions and not isinstance(exclusions, list):
            issues.append("QueryPlan.exclusions must be a list.")
        for index, exclusion in enumerate(exclusions if isinstance(exclusions, list) else [], start=1):
            label = f"exclusion[{index}]"
            if not isinstance(exclusion, dict):
                issues.append(f"{label}: must be an object.")
                continue
            field = str(exclusion.get("field") or "title_abstract")
            if field not in CANONICAL_FIELDS:
                issues.append(f"{label}: unknown field '{field}'.")
            terms = [str(item) for item in _as_list(exclusion.get("terms"))]
            if not terms:
                issues.append(f"{label}: terms are required.")
            for term in terms:
                issues.extend(_term_issues(term, label))
            for provider in providers:
                spec = PROVIDER_SPECS.get(provider)
                if spec and field not in spec.get("supported_fields", []):
                    issues.append(f"{label}: field '{field}' is incompatible with provider '{provider}'.")

        issues.extend(_validate_date_range(query_plan.get("date_range")))
        if not query_plan.get("rationale"):
            warnings.append("QueryPlan.rationale is recommended for auditability.")
        if "limits" not in query_plan:
            warnings.append("QueryPlan.limits is recommended before live retrieval.")

    report = {
        "contract": "QueryPlanValidation",
        "status": _status_from_issues(issues),
        "project_dir": str(project_dir),
        "query_plan_path": str(query_path),
        "providers": query_plan.get("providers", []) if isinstance(query_plan, dict) else [],
        "issues": issues,
        "warnings": warnings,
    }
    save_structured_file(project_dir / "context" / "retrieval" / "query_validation_report.json", report)
    return report


def _clean_term(term: str) -> str:
    return re.sub(r"\s+", " ", str(term).strip())


def _quote_term(term: str) -> str:
    cleaned = _clean_term(term).replace('"', '\\"')
    return f'"{cleaned}"'


def _compile_term(provider: str, field: str, term: str) -> str:
    renderer = FIELD_RENDERERS[provider][field]
    quoted = _quote_term(term)
    if provider == "pubmed":
        return f"{quoted}[{renderer}]"
    if provider == "europe_pmc":
        return f'{renderer}:{quoted}'
    if provider == "openalex":
        if renderer in {"doi", "ids.pmid", "authorships.author.orcid", "institutions.ror"}:
            return f"{renderer}:{_clean_term(term)}"
        return f"{renderer}:{quoted}"
    if provider == "scopus":
        return f"{renderer}({quoted})"
    if provider == "embase":
        escaped = _clean_term(term).replace("'", "")
        return f"'{escaped}'{renderer}"
    if provider == "cochrane_central":
        if field == "mesh":
            return f"[mh {quoted}]"
        return f"({quoted}){renderer}"
    if provider == "lilacs_bvs":
        return f"{renderer}:({quoted})"
    if provider in {"crossref", "crossref_retractions", "orcid", "ror", "osf"}:
        if field in {"doi", "orcid"}:
            return f"{renderer}:{_clean_term(term)}"
        return f"{renderer}:{quoted}"
    return f"{field}:{quoted}"


def _compile_clause(provider: str, item: dict[str, Any]) -> str:
    field = str(item.get("field") or "title_abstract")
    terms = [_clean_term(term) for term in _as_list(item.get("terms")) + _as_list(item.get("synonyms"))]
    rendered_terms = [_compile_term(provider, field, term) for term in terms if term]
    if not rendered_terms:
        return ""
    if len(rendered_terms) == 1:
        return rendered_terms[0]
    return "(" + " OR ".join(rendered_terms) + ")"


def _date_filter(provider: str, date_range: dict[str, Any] | None) -> str:
    if not date_range:
        return ""
    start = str(date_range.get("from") or "").replace("-", "/")
    end = str(date_range.get("to") or "").replace("-", "/")
    if not start and not end:
        return ""
    if provider == "pubmed":
        start = start or "1800/01/01"
        end = end or "3000/12/31"
        return f'("{start}"[Date - Publication] : "{end}"[Date - Publication])'
    if provider == "europe_pmc":
        start = str(date_range.get("from") or "1800-01-01")
        end = str(date_range.get("to") or "3000-12-31")
        return f"FIRST_PDATE:[{start} TO {end}]"
    if provider == "openalex":
        start = str(date_range.get("from") or "")
        end = str(date_range.get("to") or "")
        filters = []
        if start:
            filters.append(f"from_publication_date:{start}")
        if end:
            filters.append(f"to_publication_date:{end}")
        return "filter:" + ",".join(filters)
    if provider == "scopus":
        parts = []
        if date_range.get("from"):
            y_from = str(date_range["from"])[:4]
            parts.append(f"PUBYEAR > {int(y_from) - 1}")
        if date_range.get("to"):
            y_to = str(date_range["to"])[:4]
            parts.append(f"PUBYEAR < {int(y_to) + 1}")
        return "(" + " AND ".join(parts) + ")" if parts else ""
    if provider == "embase":
        y_from = str(date_range.get("from") or "1800")[:4]
        y_to = str(date_range.get("to") or "3000")[:4]
        return f"[{y_from}-{y_to}]/py"
    if provider in {"crossref", "crossref_retractions"}:
        filters = []
        if date_range.get("from"):
            filters.append(f"from-pub-date:{date_range['from']}")
        if date_range.get("to"):
            filters.append(f"until-pub-date:{date_range['to']}")
        return "filter:" + ",".join(filters)
    return ""


def _language_filter(provider: str, languages: list[Any]) -> str:
    if not languages:
        return ""
    cleaned = [str(language).strip().lower() for language in languages if str(language).strip()]
    if not cleaned:
        return ""
    if provider == "pubmed":
        return "(" + " OR ".join(f"{language}[Language]" for language in cleaned) + ")"
    if provider == "europe_pmc":
        return "(" + " OR ".join(f'LANG:"{language}"' for language in cleaned) + ")"
    if provider == "openalex":
        return "filter:language:" + "|".join(cleaned)
    return ""


def _compile_provider_query(query_plan: dict[str, Any], provider: str) -> dict[str, Any]:
    if isinstance(query_plan.get("provider_queries"), dict) and query_plan["provider_queries"].get(provider):
        query = re.sub(r"\s+", " ", str(query_plan["provider_queries"][provider])).strip()
        limits = dict(query_plan.get("limits") or {})
        provider_payload = {
            "contract": "CompiledQuery",
            "contract_version": QUERY_CONTRACT_VERSION,
            "provider": provider,
            "query": query,
            "syntax_errors": [],
            "limits": limits,
            "rationale": query_plan.get("rationale", ""),
            "compiled_at": _now_iso(),
        }
        provider_payload["query_hash"] = _sha256_payload(
            {
                "contract_version": QUERY_CONTRACT_VERSION,
                "provider": provider,
                "query": query,
                "limits": limits,
            }
        )
        return provider_payload

    concepts = [item for item in query_plan.get("concepts", []) if isinstance(item, dict)]
    boolean = str(query_plan.get("boolean") or "AND").upper()
    clauses = [_compile_clause(provider, concept) for concept in concepts]
    clauses = [clause for clause in clauses if clause]

    exclusions = []
    for exclusion in query_plan.get("exclusions", []) or []:
        if isinstance(exclusion, dict):
            clause = _compile_clause(provider, exclusion)
            if clause:
                exclusions.append(clause)

    filters = []
    date_clause = _date_filter(provider, query_plan.get("date_range"))
    if date_clause:
        filters.append(date_clause)
    language_clause = _language_filter(provider, _as_list(query_plan.get("languages")))
    if language_clause:
        filters.append(language_clause)

    query_parts = []
    if clauses:
        query_parts.append(f" {boolean} ".join(clauses))
    query_parts.extend(filters)
    query = " AND ".join(query_parts)
    for exclusion in exclusions:
        if provider in {"scopus", "embase", "cochrane_central"}:
            query += f" AND NOT {exclusion}"
        else:
            query += f" NOT {exclusion}"
    query = re.sub(r"\s+", " ", query).strip()

    limits = dict(query_plan.get("limits") or {})
    provider_payload = {
        "contract": "CompiledQuery",
        "contract_version": QUERY_CONTRACT_VERSION,
        "provider": provider,
        "query": query,
        "syntax_errors": [],
        "limits": limits,
        "rationale": query_plan.get("rationale", ""),
        "compiled_at": _now_iso(),
    }
    provider_payload["query_hash"] = _sha256_payload(
        {
            "contract_version": QUERY_CONTRACT_VERSION,
            "provider": provider,
            "query": query,
            "limits": limits,
        }
    )
    return provider_payload


def compile_query_plan(project_dir: Path) -> dict[str, Any]:
    project_dir = Path(project_dir)
    validation = validate_query_plan(project_dir)
    if validation["status"] != "pass":
        report = {
            "contract": "QueryCompileReport",
            "status": "block",
            "project_dir": str(project_dir),
            "validation": validation,
            "compiled_queries": [],
        }
        save_structured_file(project_dir / COMPILED_QUERY_PATH, report)
        return report

    query_plan, _ = _load_query_plan(project_dir)
    providers = [str(provider) for provider in _as_list(query_plan.get("providers") or ["pubmed"])]
    compiled = [_compile_provider_query(query_plan, provider) for provider in providers]
    report = {
        "contract": "QueryCompileReport",
        "status": "pass",
        "project_dir": str(project_dir),
        "compiled_queries": compiled,
        "query_plan_hash": _sha256_payload(query_plan),
        "provider_specs_hash": _sha256_payload(PROVIDER_SPECS),
    }
    save_structured_file(project_dir / COMPILED_QUERY_PATH, report)
    return report


def build_retrieval_plan(project_dir: Path) -> dict[str, Any]:
    project_dir = Path(project_dir)
    compiled_report = compile_query_plan(project_dir)
    if compiled_report["status"] != "pass":
        report = {
            "contract": "RetrievalPlan",
            "status": "block",
            "project_dir": str(project_dir),
            "execution_mode": "offline-contract",
            "issues": ["Query compilation failed."],
            "compiled_report": compiled_report,
        }
        save_structured_file(project_dir / RETRIEVAL_PLAN_PATH, report)
        return report

    providers = [item["provider"] for item in compiled_report["compiled_queries"]]
    report = {
        "contract": "RetrievalPlan",
        "status": "pass",
        "project_dir": str(project_dir),
        "execution_mode": "offline-contract",
        "generated_at": _now_iso(),
        "providers": {provider: PROVIDER_SPECS[provider] for provider in providers},
        "compiled_queries": compiled_report["compiled_queries"],
        "manifest_requirements": {
            provider: PROVIDER_SPECS[provider]["requires_manifest_fields"] for provider in providers
        },
        "future_online_gate": [
            "cache required",
            "rate limit required",
            "mailto/tool identification required when provider policy expects it",
            "retrieval manifest required",
            "offline replay required",
        ],
    }
    save_structured_file(project_dir / RETRIEVAL_PLAN_PATH, report)
    return report


def audit_retrieval(project_dir: Path) -> dict[str, Any]:
    project_dir = Path(project_dir)
    issues: list[str] = []
    compiled_report = load_structured_file(project_dir / COMPILED_QUERY_PATH)
    retrieval_plan = load_structured_file(project_dir / RETRIEVAL_PLAN_PATH)
    if not compiled_report or compiled_report.get("status") != "pass":
        issues.append("context/retrieval/compiled_queries.json is missing or not passing.")
    if not retrieval_plan or retrieval_plan.get("status") != "pass":
        issues.append("context/retrieval/retrieval_plan.json is missing or not passing.")

    manifest_dir = project_dir / "evidence" / "retrieval"
    manifest_files = sorted(manifest_dir.glob("*.json")) if manifest_dir.exists() else []
    manifest_reports: list[dict[str, Any]] = []
    if not manifest_files:
        issues.append("No retrieval manifests found under evidence/retrieval/*.json.")

    compiled_hashes = {
        item.get("query_hash"): item.get("provider")
        for item in compiled_report.get("compiled_queries", [])
        if isinstance(item, dict)
    }
    required_fields = {"provider", "query_hash", "retrieved_at", "record_count", "records_sha256"}
    for manifest_file in manifest_files:
        manifest = load_structured_file(manifest_file)
        manifest_issues: list[str] = []
        missing = sorted(field for field in required_fields if field not in manifest or manifest.get(field) in {None, ""})
        if missing:
            manifest_issues.append(f"{manifest_file.name}: missing fields {missing}.")
        provider = manifest.get("provider")
        query_hash = manifest.get("query_hash")
        if provider not in PROVIDER_SPECS:
            manifest_issues.append(f"{manifest_file.name}: unknown provider '{provider}'.")
        if query_hash not in compiled_hashes:
            manifest_issues.append(f"{manifest_file.name}: query_hash is not in compiled queries.")
        elif compiled_hashes.get(query_hash) != provider:
            manifest_issues.append(f"{manifest_file.name}: query_hash/provider mismatch.")
        if not isinstance(manifest.get("record_count"), int) or int(manifest.get("record_count", -1)) < 0:
            manifest_issues.append(f"{manifest_file.name}: record_count must be a non-negative integer.")
        if not re.match(r"^[a-f0-9]{64}$", str(manifest.get("records_sha256") or "")):
            manifest_issues.append(f"{manifest_file.name}: records_sha256 must be a SHA-256 hex digest.")
        issues.extend(manifest_issues)
        manifest_reports.append(
            {
                "manifest_path": str(manifest_file),
                "status": _status_from_issues(manifest_issues),
                "issues": manifest_issues,
            }
        )

    report = {
        "contract": "RetrievalManifestAudit",
        "status": _status_from_issues(issues),
        "project_dir": str(project_dir),
        "manifest_count": len(manifest_files),
        "manifests": manifest_reports,
        "issues": issues,
    }
    save_structured_file(project_dir / "reviews" / "retrieval_audit_report.json", report)
    return report


def _candidate_score(candidate: dict[str, Any]) -> tuple[int, dict[str, int]]:
    novelty = {"confirmed-novel": 20, "probably-novel": 16, "uncertain": 8, "not-novel": 0}.get(
        str(candidate.get("novelty_status") or "").lower(),
        0,
    )
    feasibility = int(candidate.get("feasibility", 0) or 0)
    database = 15 if candidate.get("database_plan") else 0
    journal_fit = int(candidate.get("journal_fit", 0) or 0)
    author_fit = min(10, int(candidate.get("author_fit", 0) or 0))
    ethics_risk = int(candidate.get("ethical_risk", 5) or 0)
    stats_risk = int(candidate.get("statistical_risk", 5) or 0)
    publishability = int(candidate.get("publication_chance", 0) or 0)
    components = {
        "novelty": max(0, min(20, novelty)),
        "feasibility": max(0, min(15, feasibility)),
        "database_availability": database,
        "journal_fit": max(0, min(15, journal_fit)),
        "author_fit": max(0, min(10, author_fit)),
        "ethical_risk": max(0, 10 - ethics_risk),
        "statistical_risk": max(0, 10 - stats_risk),
        "publication_chance": max(0, min(15, publishability)),
    }
    return sum(components.values()), components


def _default_idea_candidate(project_dir: Path) -> dict[str, Any]:
    project = load_structured_file(project_dir / "project.yaml")
    protocol = load_structured_file(project_dir / "protocol.yaml")
    title = protocol.get("research_question") or project.get("name") or "Untitled research idea"
    return {
        "contract": "IdeaCandidate",
        "idea_id": "idea-001",
        "title": title,
        "novelty_status": "",
        "database_plan": "",
        "red_team_notes": [],
        "feasibility": 0,
        "journal_fit": 0,
        "author_fit": 0,
        "ethical_risk": 5,
        "statistical_risk": 5,
        "publication_chance": 0,
    }


def run_idea_tournament(project_dir: Path) -> dict[str, Any]:
    project_dir = Path(project_dir)
    input_path = project_dir / IDEA_INPUT_PATH
    payload = load_structured_file(input_path)
    raw_candidates = payload.get("ideas") if isinstance(payload.get("ideas"), list) else payload.get("candidates")
    if not raw_candidates:
        raw_candidates = [_default_idea_candidate(project_dir)]

    issues: list[str] = []
    ranked: list[dict[str, Any]] = []
    for index, candidate in enumerate(raw_candidates, start=1):
        if not isinstance(candidate, dict):
            issues.append(f"idea[{index}]: must be an object.")
            continue
        idea_id = str(candidate.get("idea_id") or f"idea-{index:03d}")
        for required in ["novelty_status", "database_plan", "red_team_notes"]:
            value = candidate.get(required)
            if value is None or value == "" or value == []:
                issues.append(f"{idea_id}: missing required field '{required}'.")
        score, components = _candidate_score(candidate)
        enriched = dict(candidate)
        enriched.update(
            {
                "contract": "IdeaCandidate",
                "idea_id": idea_id,
                "score": score,
                "score_components": components,
                "can_be_promoted_to_project": not any(issue.startswith(f"{idea_id}:") for issue in issues),
            }
        )
        ranked.append(enriched)

    ranked.sort(key=lambda item: (-item.get("score", 0), item.get("idea_id", "")))
    report = {
        "contract": "IdeaTournamentReport",
        "status": _status_from_issues(issues),
        "project_dir": str(project_dir),
        "generated_at": _now_iso(),
        "ranked_ideas": ranked,
        "issues": issues,
        "gate": "No idea may become a project without novelty_status, database_plan, and red_team_notes.",
    }
    save_structured_file(project_dir / IDEA_REPORT_PATH, report)
    return report


def _file_nonempty(path: Path) -> bool:
    return path.exists() and path.read_text(encoding="utf-8", errors="replace").strip() != ""


def _journal_route_passed(project_dir: Path) -> bool:
    journal_report = load_structured_file(project_dir / "analysis" / "journal_strategy_report.json")
    if journal_report.get("status") == "routed":
        return True
    route_report = journal_report.get("route_report")
    return isinstance(route_report, dict) and route_report.get("status") == "routed"


def audit_stage(project_dir: Path, target_mode: str | None = None) -> dict[str, Any]:
    project_dir = Path(project_dir)
    project = load_structured_file(project_dir / "project.yaml")
    protocol = load_structured_file(project_dir / "protocol.yaml")
    governance = project.get("lane") == "machine-governance" and project.get("project_type") == "machine-governance"
    order = MACHINE_GOVERNANCE_MODE_ORDER if governance else MODE_ORDER
    target = target_mode or ("release" if governance else "submission")
    if target not in order:
        target = order[-1]

    target_index = order.index(target)
    checked_modes = order[: target_index + 1]
    checks: list[dict[str, Any]] = []
    issues: list[str] = []

    def add(mode: str, name: str, passed: bool, message: str) -> None:
        check = {
            "mode": mode,
            "check": name,
            "status": "pass" if passed else "block",
            "message": f"{name} passed." if passed else message,
        }
        checks.append(check)
        if not passed:
            issues.append(f"{mode}: {message}")

    if "bootstrap" in checked_modes:
        add("bootstrap", "project.yaml", bool(project), "project.yaml is missing or empty.")
        add("bootstrap", "protocol.yaml", bool(protocol), "protocol.yaml is missing or empty.")
        add("bootstrap", "standards.yaml", (project_dir / "standards.yaml").exists(), "standards.yaml is missing.")
        add("bootstrap", "compute.yaml", (project_dir / "compute.yaml").exists(), "compute.yaml is missing.")

    if governance:
        if "inventory" in checked_modes:
            add("inventory", "inventory_manifest", _file_nonempty(project_dir / "context" / "inventory_manifest.json"), "context/inventory_manifest.json is missing.")
        if "upgrade" in checked_modes:
            add("upgrade", "upgrade_record", _file_nonempty(project_dir / "context" / "upgrade_record.json"), "context/upgrade_record.json is missing.")
        if "verification" in checked_modes:
            add("verification", "verification_report", _file_nonempty(project_dir / "analysis" / "verification_report.json"), "analysis/verification_report.json is missing.")
        if "acceptance-benchmark" in checked_modes:
            benchmark_validation = validate_benchmark_report(project_dir)
            add("acceptance-benchmark", "benchmark", benchmark_validation.get("gate_eligible") is True, "AgentBenchmarkReportV2 is missing or blocked.")
        if "release" in checked_modes:
            add("release", "release_audit", _file_nonempty(project_dir / "analysis" / "release_audit.json"), "analysis/release_audit.json is missing.")
        stage_report = canonical_gate(project_dir, target, checks)
        stage_report["checked_modes"] = checked_modes
        save_structured_file(project_dir / STAGE_AUDIT_PATH, stage_report)
        return stage_report

    if "protocol-freeze" in checked_modes:
        add("protocol-freeze", "research_question", bool(protocol.get("research_question")), "protocol.yaml research_question is empty.")
        add("protocol-freeze", "objectives", bool(protocol.get("objectives")), "protocol.yaml objectives are empty.")
        add("protocol-freeze", "status", protocol.get("status") in {"frozen", "approved", "locked"}, "protocol.yaml is not frozen.")

    if any(mode not in {"bootstrap", "protocol-freeze"} for mode in checked_modes):
        from .services.protocol_registration import registration_gate
        registration = registration_gate(project_dir, target)
        add("corpus-build", "protocol_registration", registration["status"] == "pass", "; ".join(registration["issues"]))

    if "corpus-build" in checked_modes:
        query_validation = validate_query_plan(project_dir)
        add("corpus-build", "query_plan", query_validation["status"] == "pass", "context/query_plan.yaml is invalid or missing.")
        retrieval_plan = load_structured_file(project_dir / RETRIEVAL_PLAN_PATH)
        add("corpus-build", "retrieval_plan", retrieval_plan.get("status") == "pass", "retrieval plan is missing or not passing.")

    if "screening" in checked_modes:
        add("screening", "registry", _file_nonempty(project_dir / "sources" / "registry.jsonl"), "sources/registry.jsonl is empty.")

    if "extraction" in checked_modes:
        add(
            "extraction",
            "extraction_manifest",
            _file_nonempty(project_dir / "evidence" / "extraction_manifest.json"),
            "evidence/extraction_manifest.json is missing or empty.",
        )

    if "analysis" in checked_modes:
        add(
            "analysis",
            "analysis_manifest",
            _file_nonempty(project_dir / "analysis" / "manifest.json"),
            "analysis/manifest.json is missing or empty.",
        )

    if "discovery" in checked_modes and project.get("lane") == "computational-discovery":
        add(
            "discovery",
            "validation_governor",
            _file_nonempty(project_dir / "analysis" / "in_silico_validation_report.json"),
            "computational discovery requires in-silico validation report.",
        )

    if "drafting" in checked_modes:
        evidence_report = validate_evidence_lock(project_dir)
        add("drafting", "evidence_lock", evidence_report.get("gate_eligible") is True, "Evidence Lock V2 is not gate eligible.")

    if "review-trinity" in checked_modes:
        review_report = load_structured_file(project_dir / "reviews" / "review_report.json")
        from .policy.gates import file_sha256, workspace_snapshot
        review_current = review_report.get("review_snapshot") == workspace_snapshot(project_dir)
        red_team_current = review_report.get("red_team_sha256") == file_sha256(project_dir / "reviews" / "red_team_report.json")
        add(
            "review-trinity",
            "review_report",
            review_report.get("gate_eligible") is True and review_current and red_team_current,
            "Review Trinity is missing, blocked or stale; rerun after inputs or red-team changes.",
        )

    if "submission" in checked_modes:
        add("submission", "journal_route", _journal_route_passed(project_dir), "journal route/report is missing or blocked.")
        benchmark_validation = validate_benchmark_report(project_dir)
        add(
            "submission",
            "benchmark",
            benchmark_validation.get("gate_eligible") is True and benchmark_validation.get("eligibility_scope") == "scientific-acceptance",
            "agent-benchmark-harness benchmark is missing, invalid, reporting-only, or not gate eligible.",
        )
        checks[-1]["validation"] = benchmark_validation

    report = canonical_gate(project_dir, target, checks)
    report["checked_modes"] = checked_modes
    save_structured_file(project_dir / STAGE_AUDIT_PATH, report)
    return report


def run_guard_check(project_dir: Path) -> dict[str, Any]:
    project_dir = Path(project_dir)
    evidence = validate_evidence_lock(project_dir)
    query = validate_query_plan(project_dir)
    retrieval = audit_retrieval(project_dir)
    stage = audit_stage(project_dir)
    reports = {
        "evidence_lock": evidence,
        "query_validation": query,
        "retrieval_audit": retrieval,
        "stage_audit": stage,
    }
    issues = []
    for name, report in reports.items():
        if report.get("status") != "pass":
            issues.append(f"{name} status is {report.get('status')}.")
    guardrail = {
        "contract": "GuardrailReport",
        "status": _status_from_issues(issues),
        "project_dir": str(project_dir),
        "generated_at": _now_iso(),
        "reports": reports,
        "issues": issues,
        "gate": "Advancement is blocked until every zero-trust report passes.",
    }
    save_structured_file(project_dir / GUARDRAIL_PATH, guardrail)
    return guardrail


def audit_operational_graph(workspace_root: Path) -> dict[str, Any]:
    """Run the workspace graph validator without generating graph artifacts."""

    root = Path(workspace_root).resolve()
    try:
        from scripts.generate_workspace_graph import validate_operational_graph

        report = validate_operational_graph(root)
        if not isinstance(report, dict):
            raise TypeError("operational graph validator returned a non-object report")
        return report
    except Exception as exc:
        return {
            "contract": "OperationalGraphAuditReport",
            "status": "block",
            "workspace_root": str(root),
            "read_only": True,
            "checks": {},
            "issues": [f"operational graph audit could not run: {exc}"],
        }


def audit_routing_canaries(skills_dir: Path) -> dict[str, Any]:
    """Exercise fixed router regressions against the installed skill catalog."""

    from .agent_skills import route_workspace_skills

    canary_reports: list[dict[str, Any]] = []
    issues: list[str] = []
    for canary in ROUTING_CANARIES:
        route = route_workspace_skills(str(canary["query"]), Path(skills_dir), limit=16)
        selected = {
            item.get("skill")
            for item in route.get("selected_skills", [])
            if isinstance(item, dict) and isinstance(item.get("skill"), str)
        }
        required = set(canary["required_skills"])
        missing = sorted(required - selected)
        canary_reports.append(
            {
                "id": canary["id"],
                "status": "pass" if not missing else "block",
                "query": canary["query"],
                "required_skills": sorted(required),
                "selected_skills": sorted(selected),
                "missing_skills": missing,
            }
        )
        if missing:
            issues.append(f"routing canary {canary['id']} missed required skill(s): {', '.join(missing)}")

    return {
        "contract": "RoutingCanaryAuditReport",
        "status": _status_from_issues(issues),
        "skills_dir": str(Path(skills_dir)),
        "canaries": canary_reports,
        "issues": issues,
    }


def audit_git_skill_reproducibility(
    workspace_root: Path,
    required_skills: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Verify required skill entrypoints in both the Git index and ``HEAD``.

    The index alone is insufficient clean-clone evidence: a newly staged skill
    is still unavailable to another agent until it is committed.
    """

    root = Path(workspace_root).resolve()
    if required_skills is None:
        from .agent_skills import WORLD_CLASS_SKILLS

        required_skills = WORLD_CLASS_SKILLS
    required = tuple(dict.fromkeys(required_skills))
    git_marker = root / ".git"
    if not git_marker.exists():
        return {
            "contract": "GitSkillReproducibilityAuditReport",
            "status": "pass",
            "workspace_root": str(root),
            "applicable": False,
            "checked_skills": list(required),
            "tracked_skills": [],
            "untracked_skills": [],
            "committed_skills": [],
            "uncommitted_skills": [],
            "staged_only_skills": [],
            "issues": [],
        }

    git_env = os.environ.copy()
    git_env["GIT_CONFIG_NOSYSTEM"] = "1"
    git_env["GIT_CONFIG_GLOBAL"] = os.devnull
    try:
        index_result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "skills"],
            check=False,
            capture_output=True,
            env=git_env,
        )
        head_result = subprocess.run(
            ["git", "-C", str(root), "ls-tree", "-r", "-z", "--name-only", "HEAD", "--", "skills"],
            check=False,
            capture_output=True,
            env=git_env,
        )
    except OSError as exc:
        return {
            "contract": "GitSkillReproducibilityAuditReport",
            "status": "block",
            "workspace_root": str(root),
            "applicable": True,
            "checked_skills": list(required),
            "tracked_skills": [],
            "untracked_skills": list(required),
            "committed_skills": [],
            "uncommitted_skills": list(required),
            "staged_only_skills": [],
            "issues": [f"Git skill reproducibility audit could not run: {exc}"],
        }

    failed_result = next((result for result in (index_result, head_result) if result.returncode != 0), None)
    if failed_result is not None:
        stderr = failed_result.stderr.decode("utf-8", errors="replace").strip()
        return {
            "contract": "GitSkillReproducibilityAuditReport",
            "status": "block",
            "workspace_root": str(root),
            "applicable": True,
            "checked_skills": list(required),
            "tracked_skills": [],
            "untracked_skills": list(required),
            "committed_skills": [],
            "uncommitted_skills": list(required),
            "staged_only_skills": [],
            "issues": [
                f"Git skill reproducibility audit failed ({failed_result.returncode}): "
                f"{stderr or 'no error output'}"
            ],
        }

    indexed_paths = {
        path.replace("\\", "/")
        for path in index_result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
        if path
    }
    head_paths = {
        path.replace("\\", "/")
        for path in head_result.stdout.decode("utf-8", errors="surrogateescape").split("\0")
        if path
    }
    tracked_skills = [name for name in required if f"skills/{name}/SKILL.md" in indexed_paths]
    untracked_skills = [name for name in required if f"skills/{name}/SKILL.md" not in indexed_paths]
    committed_skills = [name for name in required if f"skills/{name}/SKILL.md" in head_paths]
    uncommitted_skills = [name for name in required if f"skills/{name}/SKILL.md" not in head_paths]
    staged_only_skills = [name for name in tracked_skills if name not in committed_skills]
    committed_but_removed_from_index = [name for name in committed_skills if name not in tracked_skills]
    issues = []
    if untracked_skills:
        issues.append(
            f"{len(untracked_skills)}/{len(required)} required skill entrypoints are absent from the Git index: "
            + ", ".join(untracked_skills)
        )
    if uncommitted_skills:
        issues.append(
            f"{len(uncommitted_skills)}/{len(required)} required skill entrypoints are absent from HEAD "
            "and therefore unavailable to a clean clone: "
            + ", ".join(uncommitted_skills)
        )
    if committed_but_removed_from_index:
        issues.append(
            "Required skill entrypoints exist in HEAD but are removed from the current index: "
            + ", ".join(committed_but_removed_from_index)
        )
    return {
        "contract": "GitSkillReproducibilityAuditReport",
        "status": _status_from_issues(issues),
        "workspace_root": str(root),
        "applicable": True,
        "checked_skills": list(required),
        "tracked_skills": tracked_skills,
        "untracked_skills": untracked_skills,
        "committed_skills": committed_skills,
        "uncommitted_skills": uncommitted_skills,
        "staged_only_skills": staged_only_skills,
        "committed_but_removed_from_index": committed_but_removed_from_index,
        "issues": issues,
    }


def run_machine_audit(workspace_root: Path | None = None, strict: bool = False) -> dict[str, Any]:
    root = Path(workspace_root or Path.cwd())
    provider_audit = validate_provider_specs()
    reports: dict[str, Any] = {"provider_specs": provider_audit}
    issues: list[str] = []
    if provider_audit["status"] != "pass":
        issues.extend(provider_audit["issues"])

    try:
        from .agent_skills import audit_workspace_skills

        skills_report = audit_workspace_skills(root / "skills")
        reports["skills"] = skills_report
        if skills_report.get("status") != "pass":
            issues.extend(skills_report.get("issues", []))
    except Exception as exc:  # pragma: no cover - defensive CLI hardening
        issues.append(f"skills audit failed: {exc}")

    try:
        from .journals import verify_journal_presets

        journal_report = verify_journal_presets()
        reports["journals"] = journal_report
        if journal_report.get("status") != "pass":
            issues.extend(journal_report.get("issues", []))
    except Exception as exc:  # pragma: no cover - defensive CLI hardening
        issues.append(f"journal preset audit failed: {exc}")

    if strict:
        strict_audits = (
            ("operational_graph", lambda: audit_operational_graph(root)),
            ("routing_canaries", lambda: audit_routing_canaries(root / "skills")),
            ("git_skill_reproducibility", lambda: audit_git_skill_reproducibility(root)),
        )
        for name, audit in strict_audits:
            try:
                strict_report = audit()
            except Exception as exc:  # pragma: no cover - defensive CLI hardening
                strict_report = {"status": "block", "issues": [f"{name} audit failed: {exc}"]}
            reports[name] = strict_report
            if strict_report.get("status") != "pass":
                report_issues = strict_report.get("issues") or [f"{name} status is {strict_report.get('status')}." ]
                issues.extend(str(item) for item in report_issues)

    report = {
        "contract": "MachineAuditReport",
        "status": _status_from_issues(issues),
        "workspace_root": str(root),
        "generated_at": _now_iso(),
        "reports": reports,
        "issues": issues,
    }
    if strict:
        report["strict"] = True
        report["read_only"] = True
    if not strict and (root / "reviews").exists():
        save_structured_file(root / MACHINE_AUDIT_PATH, report)
    return report
