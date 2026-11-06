# ruff: noqa: E501
"""Clinical & Healthcare ML Dataset Catalog, Automated Open API/HTTP/R Fetcher, and Governance Stage.

Catalogs 50+ gold-standard free/open-access and credentialed healthcare ML datasets
(covering ICU/EHR, Surgery, GI/Hepatology/CRC, Urology/Nephrology, Dermatology/Plastic Surgery,
Radiology, Pathology, Cardiology/Signals, Oncology/Omics, Brazilian DATASUS, and Evidence Synthesis).

Provides:
1. Immediate Open-Access alternatives while PhysioNet CITI/DUA credentialing is pending.
2. Automated downloading (`fetch_open_dataset` and `fetch_specialty_pack`) via:
   - Direct REST APIs (VitalDB API, cBioPortal API, NCI GDC API, ISIC v2 API, OpenFDA API, WHO GHO API)
   - Direct Open PhysioNet HTTP tables (`mimic-iv-demo-open`, `eicu-crd-demo-open`, `physionet-cinc-2012-icu`)
   - Direct Open UCI Clinical Cohort ZIP archives (`uci-support2-critical-care`, `uci-sepsis-survival-cohorts`,
     `uci-myocardial-infarction-complications`, `uci-thoracic-surgery-postop`, `uci-hcv-egypt-cirrhosis`,
     `uci-ckd-nephrology`, `uci-heart-disease-multicenter`, `uci-diabetes-130-us-hospitals`)
   - Direct R 4.6.1 Clinical Survival & Meta-Analysis Extractor (`r-clinical-survival-metadat-suite`:
     Moertel Colon Surgery n=929, Rotterdam Surgery Dev n=2982, GBSG ExtVal n=686, Mayo PBC Cirrhosis n=418,
     Wilms Renal Tumor Surgery n=4028, FLChain n=7874, plus `metadat` benchmarks)
3. Project dataset staging (`sources/datasets/<dataset_id>/`) with bilingual PT-BR/EN governance plans.
4. Zero-Trust SHA-256 dataset manifest generation (`evidence/datasets/<dataset_id>_manifest.json`).
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import subprocess
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..ingest import register_source
from ..serialization import save_structured_file
from .scientific_execution import scientific_execution_gate

CANONICAL_RSCRIPT = Path(os.environ.get("ARTICLE_MACHINE_RSCRIPT", "Rscript"))

CLINICAL_DATASETS_CATALOG: list[dict[str, Any]] = [
    # =========================================================================
    # 1. CRITICAL CARE, SEPSIS, EMERGENCY, PERIOPERATIVE & EHR
    # =========================================================================
    {
        "id": "vitaldb",
        "name": "VitalDB (Open Perioperative & Surgical Clinical Data + Biosignals API)",
        "domain": "surgery-perioperative",
        "modality": ["tabular-clinical", "intraoperative-waveforms", "labs", "surgical-outcomes"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-gzip",
        "auto_fetchable": True,
        "download_url": "https://api.vitaldb.net/cases",
        "provider": "Seoul National University College of Medicine / VitalDB Open API",
        "url": "https://vitaldb.net/",
        "sample_size": "6,388 surgical patients (general, GI, colorectal, hepatobiliary, thoracic, urology) with 74 clinical variables + lab panels",
        "license": "CC BY-NC-SA 4.0 (100% Open Direct REST API — NO PhysioNet CITI wait!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "perioperative mortality & ICU admission prediction",
            "emergency abdominal/GI surgical risk",
            "preop/postop lactate, CRP, albumin & coagulation modeling",
            "intraoperative hemodynamic instability",
        ],
    },
    {
        "id": "vanderbilt-rhc-icu-swan-ganz",
        "name": "SUPPORT Right Heart Catheterization (RHC) Multicenter ICU Cohort (5,735 ICU Patients)",
        "domain": "icu-emergency-ehr",
        "modality": ["tabular-icu", "hemodynamics-swan-ganz", "labs", "apache-iii", "causal-ml-benchmark"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-gzip",
        "auto_fetchable": True,
        "download_url": "https://hbiostat.org/data/repo/rhc.csv",
        "provider": "Vanderbilt University Department of Biostatistics (Prof. Frank Harrell)",
        "url": "https://hbiostat.org/data/",
        "sample_size": "5,735 critically ill adult ICU patients (ARF, MOSF, Sepsis, Coma, Cirrhosis, GI Bleed) with 62 clinical/lab/hemodynamic variables",
        "license": "Open Academic Biostatistics Repository (100% Direct CSV Download — Zero wait!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "ICU hemodynamic monitoring & 30/180-day mortality prediction",
            "propensity score / doubly-robust causal inference & TMLE benchmark",
            "sepsis, cirrhosis & acute organ failure risk stratification",
        ],
    },
    {
        "id": "uci-support2-critical-care",
        "name": "SUPPORT2 Multicenter Critical Care & Acute Organ Failure Study",
        "domain": "icu-emergency-ehr",
        "modality": ["tabular-icu", "physiology-labs", "apache-iii", "survival-6m"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-zip",
        "auto_fetchable": True,
        "download_url": "https://hbiostat.org/data/repo/support2csv.zip",
        "provider": "Vanderbilt Biostatistics / UCI ML Repository (ID 880)",
        "url": "https://archive.ics.uci.edu/dataset/880/support2",
        "sample_size": "9,105 critically ill hospitalized adults across 5 US medical centers (47 clinical/lab variables)",
        "license": "CC BY 4.0 (100% Open Direct ZIP Download — Zero wait!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "ICU mortality & 6-month survival modeling",
            "GI bleeding, cirrhosis, ARF/MOSF, sepsis & coma subphenotyping",
            "APACHE III vs ML calibration & Decision Curve Analysis",
        ],
    },
    {
        "id": "uci-sepsis-survival-cohorts",
        "name": "Hospitalized Sepsis Survival Primary & Norwegian External Validation Cohorts",
        "domain": "icu-emergency-ehr",
        "modality": ["tabular-clinical", "multi-cohort-external-validation", "survival"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-zip",
        "auto_fetchable": True,
        "download_url": "https://archive.ics.uci.edu/static/public/827/sepsis+survival+minimal+clinical+records.zip",
        "provider": "Chicco & Jurman (Scientific Reports) / UCI ML Repository (ID 827)",
        "url": "https://archive.ics.uci.edu/dataset/827/sepsis+survival+minimal+clinical+records",
        "sample_size": "110,204 primary admissions + 19,051 study admissions + 137 Norwegian external validation ICU sepsis patients",
        "license": "CC BY 4.0 (100% Open Direct ZIP Download — Ready for TRIPOD+AI external validation!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "sepsis short-term mortality prediction",
            "international multi-cohort external validation",
            "calibration drift & recalibration benchmarking",
        ],
    },
    {
        "id": "mimic-iv-demo-open",
        "methodological_limits": ["100-patient demo: pipeline engineering, not evidence of generalizable model performance"],
        "name": "MIMIC-IV Clinical Database Demo v2.2 (100 Patients Exact Schema Open Subset)",
        "domain": "icu-emergency-ehr",
        "modality": ["tabular-ehr", "labs", "icu-stays", "prescriptions", "diagnoses-icd"],
        "access_tier": "open-direct",
        "fetch_method": "physionet-open-http",
        "auto_fetchable": True,
        "download_url": "https://physionet.org/files/mimic-iv-demo/2.2/",
        "provider": "PhysioNet Open Access / MIT LCP",
        "url": "https://physionet.org/content/mimic-iv-demo/2.2/",
        "sample_size": "100 real de-identified MIMIC-IV patients with identical hosp/ and icu/ relational tables",
        "license": "Open Database License (ODbL) — Immediate download without CITI credentialing!",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "exact MIMIC-IV SQL/R/Python pipeline development before full DUA approval",
            "UGIB, pancreatitis & sepsis feature extraction verification",
        ],
    },
    {
        "id": "eicu-crd-demo-open",
        "name": "eICU Collaborative Research Database Demo v2.0.1 (2,520 ICU Stays Open Subset)",
        "domain": "icu-emergency-ehr",
        "modality": ["tabular-ehr", "multi-center-icu", "apache-results", "labs"],
        "access_tier": "open-direct",
        "fetch_method": "physionet-open-http",
        "auto_fetchable": True,
        "download_url": "https://physionet.org/files/eicu-crd-demo/2.0.1/",
        "provider": "PhysioNet Open Access / MIT LCP & Philips",
        "url": "https://physionet.org/content/eicu-crd-demo/2.0.1/",
        "sample_size": "Over 2,500 ICU stays selected from 20 hospitals; hospital and unit identifiers removed",
        "methodological_limits": [
            "Demo intended for feasibility and pipeline checks",
            "Hospital/unit identifiers removed: cannot assume center-held-out validation is feasible",
        ],
        "license": "Open Database License (ODbL) — Immediate download without CITI credentialing!",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "ICU relational pipeline and schema engineering",
            "Exploratory APACHE/ML comparison; cohort suitability and bias require separate review",
        ],
    },
    {
        "id": "physionet-cinc-2012-icu",
        "name": "PhysioNet CinC 2012 ICU Mortality Prediction Cohort (12,000 ICU Stays)",
        "domain": "icu-emergency-ehr",
        "modality": ["time-series-48h", "labs", "vitals", "sofa-saps", "mortality"],
        "access_tier": "open-direct",
        "fetch_method": "physionet-open-http",
        "auto_fetchable": True,
        "download_url": "https://physionet.org/files/challenge-2012/1.0.0/Outcomes-a.txt",
        "fetch_scope": "outcomes-only-not-the-48h-predictor-cohort",
        "provider": "PhysioNet Open Access",
        "url": "https://physionet.org/content/challenge-2012/1.0.0/",
        "sample_size": "4,000 (Set A) to 12,000 ICU admissions with 48h lactate, creatinine, bilirubin, WBC, GCS, SOFA, SAPS-I & death",
        "license": "Open PhysioNet Challenge License (No CITI credentialing required!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "48-hour dynamic ICU mortality prediction",
            "SOFA / SAPS-I vs machine learning comparison",
        ],
    },
    {
        "id": "physionet-sepsis-challenge",
        "name": "PhysioNet Computing in Cardiology Sepsis Early Prediction Dataset",
        "domain": "icu-emergency-ehr",
        "modality": ["hourly-vitals", "labs", "demographics", "sepsis-3"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "PhysioNet Open Access",
        "url": "https://physionet.org/content/challenge-2019/1.0.0/",
        "sample_size": "40,336 ICU patients from 3 hospital systems (40 clinical variables)",
        "license": "CC BY 4.0 (100% Open Access on PhysioNet — NO credentialing required!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["sepsis onset prediction", "dynamic SOFA/biomarker modeling", "multi-hospital validation"],
    },
    {
        "id": "mimic-iv",
        "name": "MIMIC-IV (v3.1 Full Credentialed Cohort)",
        "domain": "icu-emergency-ehr",
        "modality": ["tabular-ehr", "time-series", "labs", "medications", "icd-procedures"],
        "access_tier": "credentialed-dua",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "PhysioNet / MIT LCP",
        "url": "https://physionet.org/content/mimiciv/",
        "sample_size": "364,627 patients (~546k hospitalizations, ~94k ICU stays)",
        "license": "PhysioNet Credentialed Health Data License 1.5.0 (requires CITI training + DUA)",
        "open_alternative_while_waiting": "uci-support2-critical-care",
        "clinical_tasks": ["UGIB dynamic risk", "acute pancreatitis phenotyping", "sepsis prediction", "mortality/AKI"],
    },
    {
        "id": "mimic-iv-ed",
        "name": "MIMIC-IV-ED (Emergency Department)",
        "domain": "icu-emergency-ehr",
        "modality": ["tabular-ehr", "triage-vitals", "medications"],
        "access_tier": "credentialed-dua",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "PhysioNet / MIT LCP",
        "url": "https://physionet.org/content/mimic-iv-ed/",
        "sample_size": "425,087 ED stays",
        "license": "PhysioNet Credentialed Health Data License",
        "open_alternative_while_waiting": "uci-support2-critical-care",
        "clinical_tasks": ["emergency triage", "GI bleeding admission risk", "early deterioration"],
    },
    {
        "id": "eicu-crd",
        "name": "eICU Collaborative Research Database (Full Credentialed Cohort)",
        "domain": "icu-emergency-ehr",
        "modality": ["tabular-ehr", "multi-center-icu", "time-series", "labs"],
        "access_tier": "credentialed-dua",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "PhysioNet / Philips / MIT LCP",
        "url": "https://physionet.org/content/eicu-crd/",
        "sample_size": "200,859 ICU stays across 208 US hospitals",
        "license": "PhysioNet Credentialed Health Data License",
        "open_alternative_while_waiting": "eicu-crd-demo-open",
        "clinical_tasks": ["external multi-center validation", "sepsis", "organ failure", "UGIB/pancreatitis"],
    },
    {
        "id": "hirid",
        "name": "HiRID (High Time-Resolution ICU Dataset)",
        "domain": "icu-emergency-ehr",
        "modality": ["high-frequency-time-series", "labs", "hemodynamics"],
        "access_tier": "credentialed-dua",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "PhysioNet / ETH Zurich & Bern University Hospital",
        "url": "https://physionet.org/content/hirid/",
        "sample_size": "33,905 ICU admissions",
        "license": "PhysioNet Credentialed Health Data License",
        "open_alternative_while_waiting": "vitaldb",
        "clinical_tasks": ["circulatory shock prediction", "dynamic lactate/biomarker trajectories"],
    },
    {
        "id": "inspire-perioperative",
        "name": "INSPIRE Perioperative Dataset",
        "domain": "surgery-perioperative",
        "modality": ["tabular-ehr", "intraoperative-vitals", "labs", "surgical-outcomes"],
        "access_tier": "credentialed-dua",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "PhysioNet / Seoul National University Hospital",
        "url": "https://physionet.org/content/inspire/",
        "sample_size": "130,000+ surgical operations (2011-2020)",
        "license": "PhysioNet Credentialed Health Data License",
        "open_alternative_while_waiting": "vitaldb",
        "clinical_tasks": ["postoperative sepsis", "surgical complications", "30-day mortality", "AKI after surgery"],
    },
    # =========================================================================
    # 2. R 4.6.1 BUILT-IN CLINICAL TRIALS, SURGICAL COHORTS & META-ANALYSES
    # =========================================================================
    {
        "id": "r-clinical-survival-metadat-suite",
        "name": "R 4.6.1 Gold-Standard Clinical Cohorts & Meta-Analysis Datasets Suite (12 Cohorts)",
        "domain": "surgery-oncology-meta-analysis",
        "modality": ["tabular-clinical-trials", "surgical-oncology", "hepatology", "urology", "meta-analysis"],
        "access_tier": "open-direct",
        "fetch_method": "r-clinical-export",
        "auto_fetchable": True,
        "provider": "Local R 4.6.1 Scientific Stack (survival + metadat packages)",
        "url": "https://cran.r-project.org/package=survival",
        "sample_size": "12 complete clinical cohorts: Colon Cancer Surgery (n=929), Rotterdam Breast Surgery Dev (n=2,982), GBSG ExtVal (n=686), Mayo PBC Cirrhosis (n=418), Wilms Renal Tumor Surgery (n=4,028), FLChain (n=7,874), MGUS2 (n=1,384) + metadat RCTs",
        "license": "GPL / LGPL Open Scientific Data (Immediate offline extraction in <3 seconds!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "colorectal & breast surgical oncology survival prediction (Cox / RSF / XGBoost)",
            "TRIPOD+AI development (Rotterdam) + external validation (GBSG) benchmark",
            "hepatology MELD/Mayo PBC cirrhosis transplant-free survival",
            "pediatric/urological Wilms renal tumor surgical staging",
            "pairwise & network meta-analysis validation",
        ],
    },
    # =========================================================================
    # 3. CARDIOLOGY, INTERNAL MEDICINE & MULTICENTER HOSPITAL READMISSIONS
    # =========================================================================
    {
        "id": "uci-myocardial-infarction-complications",
        "name": "Acute Myocardial Infarction Clinical Complications & Mortality Cohort",
        "domain": "cardiology-signals",
        "modality": ["tabular-clinical", "ecg-features", "labs", "12-complication-endpoints"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-zip",
        "auto_fetchable": True,
        "download_url": "https://archive.ics.uci.edu/static/public/579/myocardial+infarction+complications.zip",
        "provider": "Krasnoyarsk Interdistrict Clinical Hospital / UCI ML Repository (ID 579)",
        "url": "https://archive.ics.uci.edu/dataset/579/myocardial+infarction+complications",
        "sample_size": "1,700 acute MI patients with 111 clinical/lab predictors and 12 complication/mortality targets",
        "license": "CC BY 4.0 (100% Open Direct ZIP Download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "cardiogenic shock, pulmonary edema & myocardial rupture prediction",
            "multi-label clinical complication modeling & SHAP explainability",
        ],
    },
    {
        "id": "uci-heart-disease-multicenter",
        "name": "Multicenter Coronary Artery Disease Clinical Cohorts (Cleveland, Hungary, Switzerland, VA)",
        "domain": "cardiology-signals",
        "modality": ["tabular-clinical", "multi-center-external-validation"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-zip",
        "auto_fetchable": True,
        "download_url": "https://archive.ics.uci.edu/static/public/45/heart+disease.zip",
        "provider": "UCI ML Repository (ID 45)",
        "url": "https://archive.ics.uci.edu/dataset/45/heart+disease",
        "sample_size": "920 patients across 4 international hospitals (Cleveland, Budapest, Zurich/Basel, Long Beach)",
        "license": "CC BY 4.0 (100% Open Direct ZIP Download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "4-center geographic external validation (Steyerberg / TRIPOD+AI)",
            "missing data multiple imputation (MICE) + clinical utility DCA",
        ],
    },
    {
        "id": "uci-diabetes-130-us-hospitals",
        "name": "130-US Hospitals Inpatient Clinical Care & 30-Day Readmission Cohort",
        "domain": "icu-emergency-ehr",
        "modality": ["tabular-ehr", "inpatient-encounters", "labs-medications", "readmission"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-zip",
        "auto_fetchable": True,
        "download_url": "https://archive.ics.uci.edu/static/public/296/diabetes+130-us+hospitals+for+years+1999-2008.zip",
        "provider": "Virginia Commonwealth University / UCI ML Repository (ID 296)",
        "url": "https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008",
        "sample_size": "101,766 hospital admissions across 130 US hospitals (50 clinical variables)",
        "license": "CC BY 4.0 (100% Open Direct ZIP Download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "30-day hospital readmission & length-of-stay prediction",
            "large-scale EHR fairness & subgroup calibration across 130 hospitals",
        ],
    },
    {
        "id": "uci-thoracic-surgery-postop",
        "name": "Thoracic Surgery Post-Operative Survival & Risk Cohort",
        "domain": "surgery-perioperative",
        "modality": ["tabular-clinical", "spirometry-fev1", "tnm-staging", "1yr-mortality"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-zip",
        "auto_fetchable": True,
        "download_url": "https://archive.ics.uci.edu/static/public/277/thoracic+surgery+data.zip",
        "provider": "Wroclaw Thoracic Surgery Centre / UCI ML Repository (ID 277)",
        "url": "https://archive.ics.uci.edu/dataset/277/thoracic+surgery+data",
        "sample_size": "470 patients undergoing major lung resection for primary lung cancer (17 clinical variables)",
        "license": "CC BY 4.0 (100% Open Direct ZIP Download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "post-operative 1-year mortality in thoracic/oncological surgery",
            "imbalanced surgical outcome calibration",
        ],
    },
    # =========================================================================
    # 4. GASTROENTEROLOGY, HEPATOLOGY, COLORECTAL & ABDOMINAL SURGERY
    # =========================================================================
    {
        "id": "uci-hcv-egypt-cirrhosis",
        "name": "Hepatitis C, Liver Fibrosis & Cirrhosis Laboratory Staging Cohort",
        "domain": "gastroenterology-surgery",
        "modality": ["tabular-clinical", "liver-enzymes-bilirubin-ast-alt", "fibrosis-cirrhosis"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-zip",
        "auto_fetchable": True,
        "download_url": "https://archive.ics.uci.edu/static/public/571/hcv+data.zip",
        "provider": "UCI ML Repository (ID 571)",
        "url": "https://archive.ics.uci.edu/dataset/571/hcv+data",
        "sample_size": "615 patients with complete hepatic laboratory panel (ALB, ALP, ALT, AST, BIL, CHE, CHOL, CREA, GGT, PROT) and histological staging",
        "license": "CC BY 4.0 (100% Open Direct ZIP Download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "non-invasive hepatic fibrosis & cirrhosis biomarker diagnostic accuracy",
            "multiclass disease progression modeling",
        ],
    },
    {
        "id": "cbioportal-crc-pancancer-api",
        "name": "cBioPortal Colorectal, Gastric, Hepatic & Pancreatic Cancer Clinical API",
        "domain": "oncology-gi",
        "modality": ["clinical-survival", "tnm-staging", "msi-status", "rest-api"],
        "access_tier": "open-direct",
        "fetch_method": "rest-api",
        "auto_fetchable": True,
        "cbioportal_studies": [
            "coadread_tcga_pan_can_atlas_2018",
            "stad_tcga_pan_can_atlas_2018",
            "lihc_tcga_pan_can_atlas_2018",
            "paad_tcga_pan_can_atlas_2018",
        ],
        "provider": "Memorial Sloan Kettering / cBioPortal Open REST API",
        "url": "https://www.cbioportal.org/api",
        "sample_size": "1,600+ GI surgical oncology patients (CRC n=594, Gastric n=440, HCC n=372, Pancreatic n=184) with OS/DFS/PFS & TNM",
        "license": "NIH / cBioPortal Open Access (Direct REST API — Zero credentials required!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "colorectal, gastric, hepatic & pancreatic cancer surgical survival modeling",
            "TNM + molecular biomarker prognostic nomograms",
        ],
    },
    {
        "id": "tcga-coad-read",
        "name": "TCGA-COAD & TCGA-READ (Colorectal Adenocarcinoma Clinical & Multi-Omics)",
        "domain": "oncology-gi",
        "modality": ["clinical-survival", "rna-seq", "somatic-mutations", "whole-slide-pathology"],
        "access_tier": "open-direct",
        "fetch_method": "rest-api",
        "auto_fetchable": True,
        "cbioportal_studies": ["coadread_tcga_pan_can_atlas_2018"],
        "provider": "NCI Genomic Data Commons (GDC) / cBioPortal",
        "url": "https://www.cbioportal.org/",
        "sample_size": "594 colorectal cancer patients with survival, TNM stage, MSI status, and multi-omics",
        "license": "NIH Open Access Tier",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["oncometabolic CRC survival modeling", "biomarker signature validation"],
    },
    {
        "id": "hyperkvasir-gi",
        "name": "HyperKvasir & Kvasir-GI Endoscopy Dataset",
        "domain": "gastroenterology-surgery",
        "modality": ["endoscopy-images", "segmentation-masks", "video"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "SimulaMet / Bærum Hospital Norway",
        "url": "https://datasets.simula.no/hyper-kvasir/",
        "sample_size": "110,079 GI endoscopy images and 374 videos",
        "license": "CC BY 4.0 (Open Direct Download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "GI bleeding detection",
            "polyp segmentation",
            "ulcerative colitis grading",
            "Barrett's esophagus",
        ],
    },
    {
        "id": "cholec80-surgical",
        "name": "Cholec80 & CholecSeg8k Laparoscopic Surgery Dataset",
        "domain": "gastroenterology-surgery",
        "modality": ["surgical-video", "phase-annotations", "organ-tool-segmentation"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "CAMMA / University of Strasbourg",
        "url": "http://camma.u-strasbg.fr/datasets",
        "sample_size": "80 laparoscopic cholecystectomy videos + 8,080 segmented frames",
        "license": "CC BY-NC-SA 4.0 (Open Academic Access)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["surgical phase recognition", "critical view of safety", "anatomical segmentation"],
    },
    {
        "id": "lits-liver-ct",
        "name": "LiTS (Liver Tumor Segmentation Benchmark)",
        "domain": "gastroenterology-surgery",
        "modality": ["abdominal-ct-3d", "segmentation"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "TUM / ISBI / MICCAI",
        "url": "https://competitions.codalab.org/competitions/17094",
        "sample_size": "201 contrast-enhanced 3D abdominal CT scans",
        "license": "CC BY-NC-SA 4.0",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["hepatic lesion segmentation", "surgical volume planning"],
    },
    {
        "id": "amos22-abdominal",
        "name": "AMOS22 (Multi-Modality Abdominal Multi-Organ Segmentation)",
        "domain": "gastroenterology-surgery",
        "modality": ["abdominal-ct-3d", "abdominal-mri-3d"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "Grand Challenge / Zenodo",
        "url": "https://zenodo.org/records/7262581",
        "sample_size": "500 CT and 100 MRI scans with 15 abdominal organ annotations (pancreas, duodenum, aorta, kidneys)",
        "license": "CC BY 4.0 (Open Direct Download on Zenodo)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["pancreas volumetry/radiomics", "intestinal/vascular anatomy", "multi-organ segmentation"],
    },
    # =========================================================================
    # 5. UROLOGY, NEPHROLOGY & UROLOGICAL ONCOLOGY
    # =========================================================================
    {
        "id": "uci-ckd-nephrology",
        "name": "UCI Chronic Kidney Disease & Clinical Nephrology Cohort",
        "domain": "urology-nephrology",
        "modality": ["tabular-clinical", "labs", "renal-function"],
        "access_tier": "open-direct",
        "fetch_method": "direct-http-zip",
        "auto_fetchable": True,
        "download_url": "https://archive.ics.uci.edu/static/public/336/chronic+kidney+disease.zip",
        "provider": "UCI Machine Learning Repository (ID 336)",
        "url": "https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease",
        "sample_size": "400 patients (24 clinical/lab predictors: creatinine, BUN, hemoglobin, albuminuria, HTN, DM)",
        "license": "CC BY 4.0 (100% Open Direct ZIP Download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["missing-data MICE imputation benchmarking", "renal dysfunction classification"],
    },
    {
        "id": "cbioportal-urology-kirc-blca-prad",
        "name": "cBioPortal Urological Oncology Clinical API (Kidney RCC, Bladder & Prostate)",
        "domain": "urology-nephrology",
        "modality": ["clinical-survival", "tnm-staging", "gleason-isup", "rest-api"],
        "access_tier": "open-direct",
        "fetch_method": "rest-api",
        "auto_fetchable": True,
        "cbioportal_studies": [
            "kirc_tcga_pan_can_atlas_2018",
            "blca_tcga_pan_can_atlas_2018",
            "prad_tcga_pan_can_atlas_2018",
        ],
        "provider": "cBioPortal Open REST API",
        "url": "https://www.cbioportal.org/api",
        "sample_size": "1,417 urological oncology surgical patients (Clear Cell RCC n=512, Bladder n=411, Prostate n=494)",
        "license": "NIH / cBioPortal Open Access (Direct REST API)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "nephrectomy, cystectomy & prostatectomy survival prediction",
            "urological oncology staging & recurrence modeling",
        ],
    },
    {
        "id": "kits23-kidney",
        "name": "KiTS23 (Kidney and Kidney Mass Segmentation Challenge)",
        "domain": "urology-nephrology",
        "modality": ["ct-3d", "clinical-metadata", "surgical-outcomes"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "University of Minnesota / MICCAI",
        "url": "https://kits-challenge.org/kits23/",
        "sample_size": "599 patients undergoing nephrectomy with clinical variables & CT scans",
        "license": "CC BY-NC-SA 4.0 (Open GitHub/Direct Download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["renal mass characterization", "nephrectomy outcomes", "urological radiomics"],
    },
    {
        "id": "panda-prostate-wsi",
        "name": "PANDA (Prostate cANcer graDe Assessment)",
        "domain": "urology-nephrology",
        "modality": ["whole-slide-histopathology", "isup-grade"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "Radboud UMC & Karolinska Institute",
        "url": "https://panda.grand-challenge.org/",
        "sample_size": "10,616 digitized prostate biopsies",
        "license": "CC BY-NC-SA 4.0",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["Gleason/ISUP grading", "multi-center pathology generalization"],
    },
    # =========================================================================
    # 6. DERMATOLOGY, PLASTIC SURGERY, COSMIATRY & WOUND CARE
    # =========================================================================
    {
        "id": "isic-archive-rest-api",
        "name": "ISIC Archive v2 Live REST API (Biopsy-Confirmed Cutaneous Lesions)",
        "domain": "dermatology-plastic-surgery",
        "modality": ["clinical-metadata", "histopathology-diagnosis", "dermoscopy-urls", "rest-api"],
        "access_tier": "open-direct",
        "fetch_method": "rest-api",
        "auto_fetchable": True,
        "download_url": "https://api.isic-archive.com/api/v2/images/?limit=500",
        "provider": "International Skin Imaging Collaboration (ISIC)",
        "url": "https://api.isic-archive.com/api/v2/ schema/",
        "sample_size": "80,000+ public skin lesions with age, sex, anatomical site, histopathology diagnosis & malignancy status",
        "license": "CC0 / CC BY-NC 4.0 (Direct Live REST API — Zero credentials required!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "melanoma, BCC & SCC surgical triage",
            "plastic surgery lesion excision & reconstruction risk",
        ],
    },
    {
        "id": "pad-ufes-20-brazil",
        "name": "PAD-UFES-20 (Brazilian Clinical Skin Lesion & Patient Metadata Dataset)",
        "domain": "dermatology-plastic-surgery",
        "modality": ["clinical-smartphone-images", "tabular-patient-metadata", "biopsy-confirmed"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "Universidade Federal do Espírito Santo (UFES, Brasil) / Mendeley Data",
        "url": "https://data.mendeley.com/datasets/zr7vgbcyr2/1",
        "sample_size": "2,298 lesions from 1,373 Brazilian patients with 21 clinical metadata features (Fitzpatrick, age, site, biopsy)",
        "license": "CC BY 4.0 (100% Open Direct Download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "multimodal image+clinical skin cancer triage",
            "Brazilian population validation",
            "plastic surgery reconstruction planning",
        ],
    },
    {
        "id": "isic-ham10000",
        "name": "ISIC Archive & HAM10000 Dermoscopy Dataset",
        "domain": "dermatology-plastic-surgery",
        "modality": ["dermoscopy-images", "clinical-metadata"],
        "access_tier": "open-direct",
        "fetch_method": "rest-api",
        "auto_fetchable": True,
        "download_url": "https://api.isic-archive.com/api/v2/images/?limit=500",
        "provider": "International Skin Imaging Collaboration (ISIC) / Harvard Dataverse",
        "url": "https://www.isic-archive.com/",
        "sample_size": "10,015 (HAM10000) to 500,000+ (ISIC Archive) images",
        "license": "CC BY-NC 4.0 / CC0",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["cutaneous lesion classification", "surgical margin/excision triage"],
    },
    {
        "id": "fitzpatrick17k-ddi",
        "name": "Fitzpatrick17k & Stanford DDI (Diverse Dermatology Images)",
        "domain": "dermatology-plastic-surgery",
        "modality": ["clinical-images", "fitzpatrick-skin-type-labels"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "Harvard / Stanford AIMI",
        "url": "https://github.com/mattgroh/fitzpatrick17k",
        "sample_size": "16,577 clinical images annotated with Fitzpatrick skin types I-VI",
        "license": "Open Academic Research",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["algorithmic fairness across skin tones", "cosmiatry/dermatology equity auditing"],
    },
    {
        "id": "azh-dfuc-wound-care",
        "name": "AZH Wound Care & Diabetic Foot Ulcer (DFUC) Segmentation Datasets",
        "domain": "dermatology-plastic-surgery",
        "modality": ["wound-images", "segmentation-masks"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "UWM / MICCAI DFUC",
        "url": "https://github.com/uwm-bigdata/wound-segmentation",
        "sample_size": "2,000 to 4,000+ annotated clinical wound photographs",
        "license": "MIT / Academic Open",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["plastic surgery wound healing quantification", "ischemic/necrotic tissue segmentation"],
    },
    # =========================================================================
    # 7. BRAZILIAN & GLOBAL PUBLIC HEALTH, EPIDEMIOLOGY & PHARMACOVIGILANCE APIs
    # =========================================================================
    {
        "id": "openfda-faers",
        "name": "OpenFDA FAERS (FDA Adverse Event Reporting System Live REST API)",
        "domain": "pharmacovigilance",
        "modality": ["tabular-adverse-events", "drug-safety", "rest-api"],
        "access_tier": "open-direct",
        "fetch_method": "rest-api",
        "auto_fetchable": True,
        "download_url": "https://api.fda.gov/drug/event.json?limit=100",
        "provider": "US FDA OpenFDA API",
        "url": "https://open.fda.gov/apis/drug/event/",
        "sample_size": "28M+ adverse event reports queryable live via REST API",
        "license": "CC0 1.0 Public Domain",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "pharmacovigilance disproportionality (PRR/ROR/IC)",
            "drug-induced pancreatitis, GI bleeding & surgical adverse events",
        ],
    },
    {
        "id": "world-bank-health-indicators",
        "name": "World Bank Global Health & Healthcare System Indicators Live API",
        "domain": "epidemiology-biomarkers",
        "modality": ["global-epidemiology", "healthcare-expenditure", "hospital-capacity", "rest-api"],
        "access_tier": "open-direct",
        "fetch_method": "world-bank-fetch",
        "auto_fetchable": True,
        "provider": "The World Bank Open Data API",
        "url": "https://data.worldbank.org/indicator",
        "sample_size": "Time series (2015-2023) across major global nations covering life expectancy, health exp % GDP, hospital beds per 1,000, and physicians per 1,000",
        "license": "CC BY 4.0 World Bank Open Data",
        "open_alternative_while_waiting": None,
        "clinical_tasks": [
            "macro-level healthcare capacity modeling",
            "international surgical and public health benchmarking",
        ],
    },
    {
        "id": "who-gho-odata-api",
        "name": "WHO Global Health Observatory (GHO) Live OData REST API",
        "domain": "epidemiology-biomarkers",
        "modality": ["global-epidemiology", "mortality-indicators", "rest-api"],
        "access_tier": "open-direct",
        "fetch_method": "rest-api",
        "auto_fetchable": True,
        "download_url": "https://ghoapi.azureedge.net/api/Indicator?$top=200",
        "provider": "World Health Organization (WHO)",
        "url": "https://www.who.int/data/gho/info/gho-odata-api",
        "sample_size": "2,000+ global health indicators across 194 WHO member states",
        "license": "CC BY 3.0 IGO (Open REST API)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["global surgical & infectious disease burden", "international ecological & trend modeling"],
    },
    {
        "id": "datasus-sih-sim-sinan",
        "name": "DATASUS Brasil & IBGE SIDRA API (SIH/SUS, SIM, SINAN, SIA)",
        "domain": "public-health-brazil",
        "modality": ["tabular-administrative", "surgical-procedures", "mortality", "rest-api"],
        "access_tier": "open-direct",
        "fetch_method": "rest-api",
        "auto_fetchable": True,
        "download_url": "https://servicodados.ibge.gov.br/api/v3/agregados?nivel=N1",
        "provider": "Ministério da Saúde do Brasil (DATASUS) / IBGE API",
        "url": "https://datasus.saude.gov.br/transferencia-de-arquivos/",
        "sample_size": "100M+ hospitalizations and national mortality records across all Brazilian states",
        "license": "Open Government Data Brazil (Dados Abertos SUS)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["Brazilian surgical outcomes", "urology RIRS/sepsis epidemiology", "GI ischemia mortality"],
    },
    {
        "id": "nhanes-cdc",
        "name": "CDC NHANES Continuous Cohort (Demographics + Biochemistry + CBC Laboratory Panel)",
        "domain": "epidemiology-biomarkers",
        "modality": ["tabular-clinical", "laboratory-biomarkers", "demographics", "cbc-biochemistry"],
        "access_tier": "open-direct",
        "fetch_method": "nhanes-r-fetch",
        "auto_fetchable": True,
        "provider": "US CDC / NCHS & Article Machine Automated Pipeline",
        "url": "https://wwwn.cdc.gov/nchs/nhanes/",
        "sample_size": "9,254 participants with demographics, 6,401 with standard biochemistry panel (ALT, AST, albumin, bilirubin, creatinine, BUN, glucose), 8,366 with complete blood count",
        "license": "US Public Domain (100% Open Direct R Fetch — Zero credentials required!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["metabolic/inflammatory biomarkers", "organ dysfunction", "survival & prediction models"],
    },
    {
        "id": "cdc-brfss",
        "name": "CDC BRFSS (Behavioral Risk Factor Surveillance System)",
        "domain": "epidemiology-biomarkers",
        "modality": ["tabular-survey", "chronic-disease", "comorbidities"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "US CDC",
        "url": "https://www.cdc.gov/brfss/annual_data/annual_data.htm",
        "sample_size": "400,000+ adults per year",
        "license": "US Public Domain (Open Direct Access)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["population risk modeling", "calibration at scale", "subgroup fairness"],
    },
    {
        "id": "synthea-ehr",
        "name": "Synthea Synthetic Patient Population EHR",
        "domain": "icu-emergency-ehr",
        "modality": ["fhir", "csv-ehr", "longitudinal-encounters"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "MITRE Corporation",
        "url": "https://synthea.mitre.org/downloads",
        "sample_size": "Configurable (1k to 1M+ synthetic longitudinal patients)",
        "license": "Apache-2.0",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["EHR pipeline stress-testing", "temporal leakage verification"],
    },
    # =========================================================================
    # 8. RADIOLOGY, CARDIOLOGY SIGNALS, ONCOLOGY OMICS & BIOMEDICAL NLP
    # =========================================================================
    {
        "id": "tcga-gdc-pancancer",
        "name": "TCGA Pan-Cancer Atlas (NCI Genomic Data Commons Live REST API)",
        "domain": "oncology-omics",
        "modality": ["clinical-survival", "rnaseq", "whole-exome", "rest-api"],
        "access_tier": "open-direct",
        "fetch_method": "rest-api",
        "auto_fetchable": True,
        "download_url": "https://api.gdc.cancer.gov/cases?size=200&expand=demographic,diagnoses&format=JSON",
        "provider": "NIH / NCI Genomic Data Commons (GDC)",
        "url": "https://portal.gdc.cancer.gov/",
        "sample_size": "11,000+ patients across 33 cancer types queryable via open GDC REST API",
        "license": "NIH Open Access Tier",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["Cox/survival ML", "multi-omics integration", "immunotherapy response"],
    },
    {
        "id": "medmnist-v2",
        "name": "MedMNIST v2 (18 Standardized 2D & 3D Biomedical Datasets)",
        "domain": "radiology-multimodal-imaging",
        "modality": ["2d-medical-images", "3d-ct-mri", "pathology", "dermatology", "oct", "ultrasound"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "MedMNIST Consortium / Zenodo",
        "url": "https://medmnist.com/",
        "sample_size": "708,069 2D images and 9,998 3D volumes across 18 datasets (PathMNIST, DermaMNIST, OrganAMNIST, etc.)",
        "license": "CC BY 4.0 (Direct Python pip/Zenodo download)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["rapid DL architecture benchmarking", "conformal prediction in medical imaging"],
    },
    {
        "id": "nih-chestxray14",
        "name": "NIH ChestX-ray14",
        "domain": "radiology-multimodal-imaging",
        "modality": ["chest-xray", "14-thoracic-pathology-labels"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "NIH Clinical Center",
        "url": "https://nihcc.app.box.com/v/ChestXray-NIHCC",
        "sample_size": "112,120 frontal-view X-rays from 30,805 unique patients",
        "license": "CC0 1.0 Public Domain",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["patient-grouped thoracic disease classification", "label noise robustness"],
    },
    {
        "id": "stanford-chexpert",
        "name": "Stanford CheXpert & AIMI Open Datasets",
        "domain": "radiology-multimodal-imaging",
        "modality": ["chest-xray", "radiology-reports", "uncertainty-labels"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "Stanford AIMI Center",
        "url": "https://stanfordaimi.azurewebsites.net/datasets",
        "sample_size": "224,316 chest radiographs from 65,240 patients",
        "license": "Stanford AIMI Research Use Agreement (Free online registration)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["uncertainty-aware thoracic diagnosis", "vision-language grounding"],
    },
    {
        "id": "rsna-abdominal-trauma-ct",
        "name": "RSNA 2023 Abdominal Trauma Detection CT Dataset",
        "domain": "gastroenterology-surgery",
        "modality": ["abdominal-ct-3d", "organ-injury-labels"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "RSNA (Radiological Society of North America)",
        "url": "https://www.rsna.org/rsnai/ai-image-challenge/abdominal-trauma-detection-ai-challenge",
        "sample_size": "4,000+ multi-phase abdominal CT exams annotated for bowel, mesenteric, liver, spleen, kidney injury & extravasation",
        "license": "RSNA Non-Commercial Research License",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["bowel/mesenteric ischemia & trauma CT detection", "active arterial extravasation"],
    },
    {
        "id": "brats-neuro-mri",
        "name": "BraTS (Brain Tumor Segmentation Challenge MRI)",
        "domain": "neuroimaging",
        "modality": ["multiparametric-mri-3d", "segmentation", "survival"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "CBICA UPenn / Synapse",
        "url": "http://braintumorsegmentation.org/",
        "sample_size": "2,000+ multiparametric 3D brain MRIs",
        "license": "CC BY-NC-SA 4.0",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["3D volumetric segmentation", "radiogenomic survival prediction"],
    },
    {
        "id": "nyu-fastmri",
        "name": "NYU fastMRI (Raw k-Space & DICOM MRI)",
        "domain": "radiology-multimodal-imaging",
        "modality": ["mri-kspace", "dicom-knee-brain-prostate"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "NYU Langone Health & Meta AI",
        "url": "https://fastmri.med.nyu.edu/",
        "sample_size": "8,500+ clinical knee, brain, and prostate MRI volumes",
        "license": "fastMRI Open Dataset License",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["accelerated MRI reconstruction", "prostate/musculoskeletal diagnostic AI"],
    },
    {
        "id": "ptb-xl-ecg",
        "name": "PTB-XL Clinical 12-Lead ECG Dataset",
        "domain": "cardiology-signals",
        "modality": ["12-lead-ecg-waveforms", "clinical-metadata"],
        "access_tier": "open-direct",
        "fetch_method": "physionet-open-http",
        "auto_fetchable": True,
        "download_url": "https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv",
        "provider": "PhysioNet Open Access / PTB Germany",
        "url": "https://physionet.org/content/ptb-xl/1.0.3/",
        "sample_size": "21,837 10-second 12-lead ECGs from 18,885 patients",
        "license": "CC BY 4.0 (100% Open Direct Download on PhysioNet — NO CITI wait!)",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["ECG arrhythmia & ischemia classification", "patient-stratified 10-fold benchmark"],
    },
    {
        "id": "echonet-dynamic",
        "name": "Stanford EchoNet-Dynamic Echocardiography Dataset",
        "domain": "cardiology-signals",
        "modality": ["echocardiogram-video", "ejection-fraction", "ventricular-tracings"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "Stanford AIMI",
        "url": "https://echonet.github.io/dynamic/",
        "sample_size": "10,030 apical-4-chamber echocardiogram videos",
        "license": "Stanford Research Use Agreement",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["LVEF regression", "beat-to-beat cardiac segmentation"],
    },
    {
        "id": "ncbi-geo-transcriptomics",
        "name": "NCBI Gene Expression Omnibus (GEO)",
        "domain": "oncology-omics",
        "modality": ["bulk-rnaseq", "microarray", "scrnaseq", "spatial-transcriptomics"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "NCBI / NIH",
        "url": "https://www.ncbi.nlm.nih.gov/geo/",
        "sample_size": "200,000+ public gene expression series (including human intestinal ischemia, sepsis, pancreatitis)",
        "license": "US Public Domain",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["differential expression", "external biomarker cohort validation", "pathway enrichment"],
    },
    {
        "id": "cz-cellxgene",
        "name": "CZ CELLxGENE Discover (Single-Cell Atlas)",
        "domain": "oncology-omics",
        "modality": ["single-cell-rnaseq", "spatial"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "Chan Zuckerberg Initiative",
        "url": "https://cellxgene.cziscience.com/",
        "sample_size": "90M+ standardized single cells across human tissues (gut, liver, kidney, skin, immune)",
        "license": "CC BY 4.0 / CC0",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["intestinal barrier cellular deconvolution", "target validation"],
    },
    {
        "id": "tdc-drug-discovery",
        "name": "Therapeutics Data Commons (TDC)",
        "domain": "drug-discovery",
        "modality": ["molecules-smiles", "proteins", "admet", "dti-binding", "clinical-trial-outcomes"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "Harvard Zitnik Lab",
        "url": "https://tdcommons.ai/",
        "sample_size": "66+ curated ML datasets across ADMET, DTI, drug synergy, and clinical trial phase outcomes",
        "license": "MIT",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["scaffold-split ADMET prediction", "drug repurposing", "target-ligand binding"],
    },
    {
        "id": "pubmedqa-medqa",
        "name": "PubMedQA & MedQA-USMLE Biomedical Reasoning Corpora",
        "domain": "biomedical-nlp",
        "modality": ["clinical-text", "question-answering", "evidence-abstracts"],
        "access_tier": "open-direct",
        "fetch_method": "manual-portal",
        "auto_fetchable": False,
        "provider": "MIT / Jin et al.",
        "url": "https://pubmedqa.github.io/",
        "sample_size": "273,500 PubMedQA instances + 61,097 MedQA clinical vignettes",
        "license": "MIT",
        "open_alternative_while_waiting": None,
        "clinical_tasks": ["evidence synthesis NLP benchmarking", "clinical reasoning evaluation"],
    },
]

DATASET_SPECIALTY_PACKS: dict[str, dict[str, Any]] = {
    "essential-core": {
        "name": "Pacote Essencial Completo (Cirurgia, UTI, Sepse, Gastro/CRC, Cardiologia, Nefro/Uro e Oncologia)",
        "description": "Baixa automaticamente as principais coortes clínicas abertas via API/HTTP/R (sem precisar de credenciamento PhysioNet).",
        "dataset_ids": [
            "r-clinical-survival-metadat-suite",
            "vitaldb",
            "uci-support2-critical-care",
            "vanderbilt-rhc-icu-swan-ganz",
            "uci-sepsis-survival-cohorts",
            "mimic-iv-demo-open",
            "eicu-crd-demo-open",
            "uci-myocardial-infarction-complications",
            "uci-heart-disease-multicenter",
            "uci-thoracic-surgery-postop",
            "uci-hcv-egypt-cirrhosis",
            "uci-ckd-nephrology",
            "cbioportal-crc-pancancer-api",
            "cbioportal-urology-kirc-blca-prad",
            "isic-archive-rest-api",
            "openfda-faers",
            "nhanes-cdc",
            "world-bank-health-indicators",
        ],
    },
    "icu-sepsis-surgery": {
        "name": "UTI, Sepse, Emergência e Cirurgia Perioperatória (Alternativas Abertas ao MIMIC-IV/eICU)",
        "description": "6.388 pacientes cirúrgicos (VitalDB), 9.105 pacientes críticos (SUPPORT2), 110.204 internações de sepse (UCI), 470 cirurgias torácicas, MIMIC-IV Demo e eICU Demo.",
        "dataset_ids": [
            "vitaldb",
            "uci-support2-critical-care",
            "vanderbilt-rhc-icu-swan-ganz",
            "uci-sepsis-survival-cohorts",
            "mimic-iv-demo-open",
            "eicu-crd-demo-open",
            "physionet-cinc-2012-icu",
            "uci-thoracic-surgery-postop",
        ],
    },
    "gastro-hepatology-crc": {
        "name": "Gastroenterologia, Cirurgia Digestiva/Colorretal, Hepatologia e Pâncreas",
        "description": "Coortes cirúrgicas de câncer colorretal (Moertel n=929, TCGA PanCancer CRC/Gástrico/HCC/Pâncreas), Cirrose Biliar Primária Mayo Clinic (n=418), Fibrose/HCV (n=615) e Cirurgia Geral (VitalDB).",
        "dataset_ids": [
            "r-clinical-survival-metadat-suite",
            "vitaldb",
            "uci-hcv-egypt-cirrhosis",
            "cbioportal-crc-pancancer-api",
            "uci-support2-critical-care",
        ],
    },
    "urology-nephrology": {
        "name": "Urologia, Nefrologia, Sepse Urinária e Oncologia Urológica",
        "description": "Tumor de Wilms (n=4.028), TCGA Rim/Bexiga/Próstata (n=1.417), Doença Renal Crônica (n=400) e Sepse Hospitalar (n=110.204).",
        "dataset_ids": [
            "r-clinical-survival-metadat-suite",
            "cbioportal-urology-kirc-blca-prad",
            "uci-ckd-nephrology",
            "uci-sepsis-survival-cohorts",
        ],
    },
    "plastic-dermatology-oncology": {
        "name": "Cirurgia Plástica, Dermatologia Oncológica e Reconstrução",
        "description": "ISIC Archive v2 REST API (lesões cutâneas biopsiadas), Rotterdam (n=2.982) & GBSG (n=686) cirurgia mamária/reconstrução.",
        "dataset_ids": [
            "isic-archive-rest-api",
            "r-clinical-survival-metadat-suite",
        ],
    },
}


def list_clinical_datasets(
    *,
    domain: str | None = None,
    access_tier: str | None = None,
    query: str | None = None,
    auto_fetchable_only: bool = False,
) -> list[dict[str, Any]]:
    """Filter curated clinical datasets by domain, access tier, auto-fetchable flag, or keyword."""
    results = list(CLINICAL_DATASETS_CATALOG)
    if domain:
        d_clean = domain.strip().lower()
        results = [item for item in results if d_clean in str(item["domain"]).lower()]
    if access_tier:
        a_clean = access_tier.strip().lower()
        results = [item for item in results if str(item["access_tier"]).lower() == a_clean]
    if auto_fetchable_only:
        results = [item for item in results if item.get("auto_fetchable") is True]
    if query:
        tokens = [t.lower() for t in query.strip().split() if t.strip()]
        filtered = []
        for item in results:
            blob = json.dumps(item, ensure_ascii=False).lower()
            if any(tok in blob for tok in tokens):
                filtered.append(item)
        results = filtered
    return results


def prepare_dataset_stage(project_dir: Path, dataset_ids: list[str] | None = None) -> dict[str, Any]:
    """Create the dataset staging tree (sources/datasets/<id>/) and bilingual PT-BR/EN governance guides."""
    root = Path(project_dir).resolve()
    catalog_by_id = {str(item["id"]): item for item in CLINICAL_DATASETS_CATALOG}

    if dataset_ids:
        selected = [catalog_by_id[did] for did in dataset_ids if did in catalog_by_id]
        unknown = [did for did in dataset_ids if did not in catalog_by_id]
        if unknown:
            return {
                "contract": "ClinicalDatasetStageV1",
                "status": "blocked",
                "issues": [f"Unknown dataset IDs: {unknown}. Run list_clinical_datasets() to inspect valid IDs."],
            }
    else:
        selected = list(CLINICAL_DATASETS_CATALOG)

    staged_folders: dict[str, str] = {}
    for ds in selected:
        did = str(ds["id"])
        folder = root / "sources" / "datasets" / did
        folder.mkdir(parents=True, exist_ok=True)
        staged_folders[did] = folder.relative_to(root).as_posix()

    plan_payload = {
        "contract": "ClinicalDatasetStageV1",
        "generated_at": datetime.now(UTC).isoformat(),
        "project_dir": str(root),
        "total_catalog_datasets": len(CLINICAL_DATASETS_CATALOG),
        "selected_count": len(selected),
        "open_direct_count": sum(1 for d in selected if d["access_tier"] == "open-direct"),
        "auto_fetchable_count": sum(1 for d in selected if d.get("auto_fetchable") is True),
        "credentialed_dua_count": sum(1 for d in selected if d["access_tier"] == "credentialed-dua"),
        "specialty_packs": DATASET_SPECIALTY_PACKS,
        "staged_folders": staged_folders,
        "governance_rules": [
            "Never commit or stage raw patient-level files to Git.",
            "Never upload credentialed human data (e.g., MIMIC-IV, eICU) to external cloud APIs without explicit DUA compliance.",
            "While PhysioNet credentialing is pending, use `datasets fetch` or `datasets fetch-pack` to download open-direct cohorts automatically.",
        ],
        "datasets": selected,
    }

    plan_path = root / "context" / "datasets" / "dataset_governance_plan.json"
    save_structured_file(plan_path, plan_payload)

    pt_dir = root / "context" / "datasets" / "portugues"
    en_dir = root / "context" / "datasets" / "ingles"
    pt_dir.mkdir(parents=True, exist_ok=True)
    en_dir.mkdir(parents=True, exist_ok=True)

    pt_lines = [
        "# Catálogo e Etapa de Bases de Dados Clínicas & Machine Learning (2026)\n",
        f"- **Total de bases catalogadas:** {len(CLINICAL_DATASETS_CATALOG)}",
        f"- **Bases selecionadas para este projeto:** {len(selected)} ({plan_payload['open_direct_count']} Acesso Direto Imediato / {plan_payload['auto_fetchable_count']} com Download Automático via CLI / {plan_payload['credentialed_dua_count']} Credenciadas DUA/PhysioNet)\n",
        "## Download Automático via API / HTTP / R 4.6.1 (Sem esperar pelo PhysioNet!)\n",
        "- Baixar uma base aberta específica: `python -m article_machine datasets fetch <project_dir> --id <dataset_id>`",
        "- Baixar um pacote completo por especialidade: `python -m article_machine datasets fetch-pack <project_dir> --pack essential-core`",
        "  - Pacotes disponíveis: `essential-core`, `icu-sepsis-surgery`, `gastro-hepatology-crc`, `urology-nephrology`, `plastic-dermatology-oncology`\n",
        "## Pastas Locais e Links Oficiais por Base\n",
    ]
    en_lines = [
        "# Clinical & Healthcare Machine Learning Datasets Stage & Catalog (2026)\n",
        f"- **Total cataloged datasets:** {len(CLINICAL_DATASETS_CATALOG)}",
        f"- **Selected datasets for this project:** {len(selected)} ({plan_payload['open_direct_count']} Open Direct Access / {plan_payload['auto_fetchable_count']} Automated CLI Fetch / {plan_payload['credentialed_dua_count']} Credentialed DUA/PhysioNet)\n",
        "## Automated CLI Fetch via API / HTTP / R 4.6.1 (Zero Wait While PhysioNet Is Pending)\n",
        "- Fetch a single open dataset: `python -m article_machine datasets fetch <project_dir> --id <dataset_id>`",
        "- Fetch a complete specialty pack: `python -m article_machine datasets fetch-pack <project_dir> --pack essential-core`\n",
        "## Local Drop-Folders and Official URLs by Dataset\n",
    ]

    for ds in selected:
        did = str(ds["id"])
        rel_folder = staged_folders[did]
        alt = ds.get("open_alternative_while_waiting")
        auto_tag = "Sim (`datasets fetch`)" if ds.get("auto_fetchable") else "Manual via Portal"
        alt_note_pt = f" | **Alternativa aberta imediata:** `{alt}`" if alt else ""
        alt_note_en = f" | **Immediate open alternative:** `{alt}`" if alt else ""

        pt_lines.extend(
            [
                f"### `{did}` — {ds['name']}",
                f"- **Domínio:** `{ds['domain']}` | **Acesso:** `{ds['access_tier']}` | **Download Automático:** {auto_tag}{alt_note_pt}",
                f"- **Amostra:** {ds['sample_size']}",
                f"- **Licença:** {ds['license']}",
                f"- **URL Oficial:** {ds['url']}",
                f"- **Pasta local:** `{rel_folder}/`\n",
            ]
        )
        en_lines.extend(
            [
                f"### `{did}` — {ds['name']}",
                f"- **Domain:** `{ds['domain']}` | **Access Tier:** `{ds['access_tier']}` | **Auto-Fetch:** `{ds.get('auto_fetchable', False)}`{alt_note_en}",
                f"- **Sample Size:** {ds['sample_size']}",
                f"- **License:** {ds['license']}",
                f"- **Official URL:** {ds['url']}",
                f"- **Local folder:** `{rel_folder}/`\n",
            ]
        )

    pt_file = pt_dir / "plano_bases_de_dados_clinicos.md"
    en_file = en_dir / "plano_bases_de_dados_clinicos.md"
    pt_file.write_text("\n".join(pt_lines), encoding="utf-8")
    en_file.write_text("\n".join(en_lines), encoding="utf-8")

    return {
        "contract": "ClinicalDatasetStageV1",
        "status": "pass",
        "selected_count": len(selected),
        "open_direct_count": plan_payload["open_direct_count"],
        "auto_fetchable_count": plan_payload["auto_fetchable_count"],
        "credentialed_dua_count": plan_payload["credentialed_dua_count"],
        "plan_path": plan_path.relative_to(root).as_posix(),
        "guides": {
            "portugues": pt_file.relative_to(root).as_posix(),
            "ingles": en_file.relative_to(root).as_posix(),
        },
        "staged_folders": staged_folders,
    }


def _http_get_bytes(url: str, timeout: int = 45) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ArticleMachine-ClinicalResearch/2026.11 (Doutorado Medicina; +https://osf.io/)",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
        limit = 256 * 1024 * 1024
        payload = bytes(resp.read(limit + 1))
        if len(payload) > limit:
            raise ValueError("Download exceeds the 256 MiB per-response limit; use a reviewed streaming plan.")
        content_type = str(resp.headers.get("Content-Type", "")).lower()
        if "text/html" in content_type or payload.lstrip().lower().startswith((b"<!doctype html", b"<html")):
            raise ValueError("Provider returned HTML rather than dataset content.")
        return payload


def _bounded_gzip(payload: bytes) -> bytes:
    """Bound expansion before allocating a full decompressed dataset."""
    with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:
        result = stream.read(512 * 1024 * 1024 + 1)
    if len(result) > 512 * 1024 * 1024:
        raise ValueError("GZIP expansion exceeds 512 MiB; explicit streaming ingestion is required.")
    return result


def _export_r_clinical_suite(target_dir: Path) -> list[str]:
    """Use local R 4.6.1 to export 12 canonical clinical trial, surgical oncology, cirrhosis & meta-analysis datasets."""
    target_dir.mkdir(parents=True, exist_ok=True)
    r_exe = str(CANONICAL_RSCRIPT) if CANONICAL_RSCRIPT.exists() else "Rscript"
    out_posix = target_dir.as_posix()
    r_code = f"""
    out_dir <- "{out_posix}"
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
    suppressPackageStartupMessages(library(survival))
    write.csv(survival::colon, file.path(out_dir, "colon_moertel_929_crc_surgery.csv"), row.names = FALSE)
    write.csv(survival::rotterdam, file.path(out_dir, "rotterdam_2982_breast_surgery_dev.csv"), row.names = FALSE)
    write.csv(survival::gbsg, file.path(out_dir, "gbsg_686_breast_surgery_extval.csv"), row.names = FALSE)
    write.csv(survival::pbc, file.path(out_dir, "pbc_mayo_418_cirrhosis_liver.csv"), row.names = FALSE)
    write.csv(survival::nwtco, file.path(out_dir, "nwtco_4028_wilms_renal_tumor.csv"), row.names = FALSE)
    write.csv(survival::veteran, file.path(out_dir, "veteran_137_lung_cancer_rct.csv"), row.names = FALSE)
    write.csv(survival::mgus2, file.path(out_dir, "mgus2_1384_hematology_survival.csv"), row.names = FALSE)
    write.csv(survival::flchain, file.path(out_dir, "flchain_7874_mortality_cohort.csv"), row.names = FALSE)
    if (requireNamespace("metadat", quietly = TRUE)) {{
      suppressPackageStartupMessages(library(metadat))
      write.csv(metadat::dat.bcg, file.path(out_dir, "metadat_bcg_13_rcts.csv"), row.names = FALSE)
      write.csv(metadat::dat.haddock2011, file.path(out_dir, "metadat_haddock2011_surgical_recovery_rcts.csv"), row.names = FALSE)
      write.csv(metadat::dat.gibson2002, file.path(out_dir, "metadat_gibson2002_clinical_trials.csv"), row.names = FALSE)
      write.csv(metadat::dat.hart1999, file.path(out_dir, "metadat_hart1999_warfarin_stroke_rcts.csv"), row.names = FALSE)
      write.csv(metadat::dat.normand1999, file.path(out_dir, "metadat_normand1999_stroke_los.csv"), row.names = FALSE)
    }}
    """
    subprocess.run([r_exe, "--vanilla", "-e", r_code], check=True, capture_output=True, text=True, timeout=60)
    return sorted(p.name for p in target_dir.glob("*.csv"))


def _fetch_cbioportal_studies(target_dir: Path, study_ids: list[str], timeout: int = 45) -> list[str]:
    """Fetch clinical patient-level attributes from cBioPortal public REST API and pivot into wide CSVs."""
    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for sid in study_ids:
        url = f"https://www.cbioportal.org/api/studies/{sid}/clinical-data?clinicalDataType=PATIENT&projection=SUMMARY"
        raw = _http_get_bytes(url, timeout=timeout)
        rows = json.loads(raw.decode("utf-8", errors="replace"))
        if not isinstance(rows, list) or not rows:
            continue
        by_patient: dict[str, dict[str, Any]] = {}
        all_cols: set[str] = {"patientId", "studyId"}
        for item in rows:
            if not isinstance(item, dict):
                continue
            pid = str(item.get("patientId") or "")
            attr = str(item.get("clinicalAttributeId") or "")
            val = item.get("value")
            if not pid or not attr:
                continue
            rec = by_patient.setdefault(pid, {"patientId": pid, "studyId": sid})
            rec[attr] = val
            all_cols.add(attr)
        ordered_cols = ["patientId", "studyId"] + sorted(all_cols - {"patientId", "studyId"})
        csv_path = target_dir / f"{sid}_clinical_patients.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=ordered_cols)
            writer.writeheader()
            for pid in sorted(by_patient):
                writer.writerow(by_patient[pid])
        written.append(csv_path.name)
    return written


def _fetch_nhanes_via_r(target_dir: Path, timeout: int = 60) -> list[str]:
    """Download official CDC NHANES 2017-2018 Demographics, Biochemistry, and CBC via R and merge into a cohort."""
    target_dir.mkdir(parents=True, exist_ok=True)
    r_exe = str(CANONICAL_RSCRIPT) if CANONICAL_RSCRIPT.exists() else "Rscript"
    out_posix = target_dir.as_posix()
    r_code = f"""
    suppressPackageStartupMessages(library(foreign))
    out_dir <- "{out_posix}"
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

    # 1. Demographics
    tf_demo <- tempfile(fileext=".xpt")
    download.file("https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.xpt", tf_demo, mode="wb", quiet=TRUE)
    d_demo <- foreign::read.xport(tf_demo)
    write.csv(d_demo, file.path(out_dir, "nhanes_2017_2018_demographics.csv"), row.names = FALSE)

    # 2. Standard Biochemistry Profile
    tf_bio <- tempfile(fileext=".xpt")
    download.file("https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/BIOPRO_J.xpt", tf_bio, mode="wb", quiet=TRUE)
    d_bio <- foreign::read.xport(tf_bio)
    write.csv(d_bio, file.path(out_dir, "nhanes_2017_2018_biochemistry.csv"), row.names = FALSE)

    # 3. Complete Blood Count
    tf_cbc <- tempfile(fileext=".xpt")
    download.file("https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/CBC_J.xpt", tf_cbc, mode="wb", quiet=TRUE)
    d_cbc <- foreign::read.xport(tf_cbc)
    write.csv(d_cbc, file.path(out_dir, "nhanes_2017_2018_complete_blood_count.csv"), row.names = FALSE)

    # 4. Merged Clinical Cohort
    m <- merge(d_demo, d_bio, by="SEQN", all.x=FALSE, all.y=FALSE)
    m <- merge(m, d_cbc, by="SEQN", all.x=TRUE, all.y=FALSE)
    write.csv(m, file.path(out_dir, "nhanes_2017_2018_merged_clinical_cohort.csv"), row.names = FALSE)
    """
    subprocess.run([r_exe, "--vanilla", "-e", r_code], check=True, capture_output=True, text=True, timeout=timeout)
    return sorted(p.name for p in target_dir.glob("*.csv"))


def _fetch_world_bank_health_indicators(target_dir: Path, timeout: int = 45) -> str:
    """Download World Bank Global Health Indicators (Life expectancy, Health exp % GDP, Beds, Physicians, Infant Mort)."""
    target_dir.mkdir(parents=True, exist_ok=True)
    indicators = [
        ("SP.DYN.LE00.IN", "life_expectancy_at_birth_years"),
        ("SH.XPD.CHEX.GD.ZS", "current_health_expenditure_pct_gdp"),
        ("SH.MED.BEDS.ZS", "hospital_beds_per_1000"),
        ("SH.MED.PHYS.ZS", "physicians_per_1000"),
        ("SP.DYN.IMRT.IN", "infant_mortality_rate_per_1000"),
    ]
    countries = "BRA;USA;GBR;DEU;FRA;ITA;ESP;CAN;JPN;AUS;CHN;IND;ZAF;ARG;CHL;COL;MEX"
    all_records: dict[tuple[str, str], dict[str, Any]] = {}
    for ind_code, ind_name in indicators:
        url = f"https://api.worldbank.org/v2/country/{countries}/indicator/{ind_code}?format=json&date=2015:2023&per_page=1000"
        raw = _http_get_bytes(url, timeout=timeout)
        data = json.loads(raw.decode("utf-8", errors="replace"))
        rows = data[1] if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list) else []
        for r in rows:
            if not isinstance(r, dict):
                continue
            cid = r.get("countryiso3code") or r.get("country", {}).get("id")
            cname = r.get("country", {}).get("value")
            year = r.get("date")
            val = r.get("value")
            if not cid or not year:
                continue
            key = (str(cid), str(year))
            entry = all_records.setdefault(key, {"country_code": cid, "country_name": cname, "year": year})
            entry[ind_name] = val

    csv_path = target_dir / "world_bank_global_health_indicators.csv"
    cols = [
        "country_code",
        "country_name",
        "year",
        "life_expectancy_at_birth_years",
        "current_health_expenditure_pct_gdp",
        "hospital_beds_per_1000",
        "physicians_per_1000",
        "infant_mortality_rate_per_1000",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=cols)
        writer.writeheader()
        for key in sorted(all_records):
            writer.writerow(all_records[key])
    return csv_path.name


def fetch_open_dataset(
    project_dir: Path,
    dataset_id: str,
    *,
    timeout: int = 45,
) -> dict[str, Any]:
    """Automatically download/extract an open-direct dataset via REST API, HTTP/ZIP/GZIP, or R 4.6.1 and verify its SHA-256 manifest."""
    root = Path(project_dir).resolve()
    gate = scientific_execution_gate(root, "dataset-fetch")
    if gate["status"] != "pass":
        return gate
    catalog_by_id = {str(item["id"]): item for item in CLINICAL_DATASETS_CATALOG}
    ds_meta = catalog_by_id.get(dataset_id)
    if not ds_meta:
        return {"status": "blocked", "issues": [f"Unknown dataset_id '{dataset_id}'."]}

    if not ds_meta.get("auto_fetchable"):
        return {
            "status": "blocked",
            "dataset_id": dataset_id,
            "issues": [
                f"Dataset '{dataset_id}' requires manual portal download or DUA credentialing ({ds_meta['url']}). "
                f"Open alternative: {ds_meta.get('open_alternative_while_waiting') or 'use `datasets catalog`'}."
            ],
        }

    gate = scientific_execution_gate(root, "dataset-fetch", mark_started=True)
    if gate["status"] != "pass":
        return gate
    ds_dir = root / "sources" / "datasets" / dataset_id
    if ds_dir.exists() and any(ds_dir.iterdir()):
        return {
            "status": "blocked",
            "dataset_id": dataset_id,
            "issues": ["Dataset destination is nonempty; preserve it and select a reviewed new release directory."],
        }
    ds_dir.mkdir(parents=True, exist_ok=True)
    method = str(ds_meta.get("fetch_method") or "")

    try:
        if method == "r-clinical-export":
            _export_r_clinical_suite(ds_dir)

        elif method == "nhanes-r-fetch":
            _fetch_nhanes_via_r(ds_dir, timeout=timeout)

        elif method == "world-bank-fetch":
            _fetch_world_bank_health_indicators(ds_dir, timeout=timeout)

        elif method == "direct-http-gzip":
            raw = _http_get_bytes(str(ds_meta["download_url"]), timeout=timeout)
            try:
                decompressed = _bounded_gzip(raw)
            except OSError:
                decompressed = raw
            out_file = ds_dir / f"{dataset_id}_clinical_cases.csv"
            out_file.write_bytes(decompressed)

        elif method == "direct-http-zip":
            raw = _http_get_bytes(str(ds_meta["download_url"]), timeout=timeout)
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                members = [m for m in zf.infolist() if not m.is_dir()]
                names = [Path(m.filename).name.casefold() for m in members]
                if len(members) > 512 or sum(m.file_size for m in members) > 512 * 1024 * 1024:
                    raise ValueError("ZIP exceeds reviewed member/expansion limits.")
                if len(names) != len(set(names)):
                    raise ValueError("ZIP has colliding flattened filenames; no files were extracted.")
                if any(m.file_size / max(1, m.compress_size) > 1000 for m in members):
                    raise ValueError("ZIP expansion ratio exceeds 1000; no files were extracted.")
                for member in zf.infolist():
                    if member.is_dir():
                        continue
                    safe_name = Path(member.filename).name
                    if not safe_name or safe_name.startswith("."):
                        continue
                    target_file = ds_dir / safe_name
                    target_file.write_bytes(zf.read(member))
                    # If inner file is .gz or nested .zip, unpack it for convenience
                    if target_file.suffix.lower() == ".gz":
                        try:
                            csv_target = ds_dir / target_file.stem
                            if csv_target.exists():
                                raise ValueError("Nested GZIP filename collides with a dataset file.")
                            csv_target.write_bytes(_bounded_gzip(target_file.read_bytes()))
                        except OSError:
                            pass

        elif method == "physionet-open-http":
            base_url = str(ds_meta["download_url"])
            if dataset_id == "mimic-iv-demo-open":
                tables = [
                    ("hosp/patients.csv.gz", "patients.csv"),
                    ("hosp/admissions.csv.gz", "admissions.csv"),
                    ("icu/icustays.csv.gz", "icustays.csv"),
                    ("hosp/diagnoses_icd.csv.gz", "diagnoses_icd.csv"),
                    ("hosp/procedures_icd.csv.gz", "procedures_icd.csv"),
                    ("hosp/d_labitems.csv.gz", "d_labitems.csv"),
                    ("hosp/labevents.csv.gz", "labevents.csv"),
                    ("hosp/prescriptions.csv.gz", "prescriptions.csv"),
                    ("hosp/services.csv.gz", "services.csv"),
                    ("hosp/transfers.csv.gz", "transfers.csv"),
                ]
                for rel_url, out_name in tables:
                    raw = _http_get_bytes(base_url.rstrip("/") + "/" + rel_url, timeout=timeout)
                    (ds_dir / out_name).write_bytes(_bounded_gzip(raw))
            elif dataset_id == "eicu-crd-demo-open":
                tables = [
                    ("patient.csv.gz", "patient.csv"),
                    ("hospital.csv.gz", "hospital.csv"),
                    ("apachePatientResult.csv.gz", "apachePatientResult.csv"),
                    ("apacheApsVar.csv.gz", "apacheApsVar.csv"),
                    ("apachePredVar.csv.gz", "apachePredVar.csv"),
                    ("diagnosis.csv.gz", "diagnosis.csv"),
                    ("lab.csv.gz", "lab.csv"),
                    ("medication.csv.gz", "medication.csv"),
                ]
                for rel_url, out_name in tables:
                    raw = _http_get_bytes(base_url.rstrip("/") + "/" + rel_url, timeout=timeout)
                    (ds_dir / out_name).write_bytes(_bounded_gzip(raw))
            else:
                out_name = Path(base_url).name or f"{dataset_id}.csv"
                raw = _http_get_bytes(base_url, timeout=timeout)
                (ds_dir / out_name).write_bytes(raw)

        elif method == "rest-api":
            if "cbioportal_studies" in ds_meta:
                _fetch_cbioportal_studies(ds_dir, list(ds_meta["cbioportal_studies"]), timeout=timeout)
            elif dataset_id == "isic-archive-rest-api" or dataset_id == "isic-ham10000":
                raw = _http_get_bytes(str(ds_meta["download_url"]), timeout=timeout)
                data = json.loads(raw.decode("utf-8", errors="replace"))
                results = data.get("results", []) if isinstance(data, dict) else []
                csv_path = ds_dir / "isic_clinical_lesions.csv"
                cols = [
                    "isic_id",
                    "age_approx",
                    "sex",
                    "anatom_site_general",
                    "benign_malignant",
                    "diagnosis",
                    "melanocytic",
                ]
                with csv_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=cols)
                    writer.writeheader()
                    for item in results:
                        if not isinstance(item, dict):
                            continue
                        clin = (
                            item.get("metadata", {}).get("clinical", {})
                            if isinstance(item.get("metadata"), dict)
                            else {}
                        )
                        writer.writerow(
                            {
                                "isic_id": item.get("isic_id"),
                                "age_approx": clin.get("age_approx"),
                                "sex": clin.get("sex"),
                                "anatom_site_general": clin.get("anatom_site_general"),
                                "benign_malignant": clin.get("benign_malignant"),
                                "diagnosis": clin.get("diagnosis"),
                                "melanocytic": clin.get("melanocytic"),
                            }
                        )
            elif dataset_id == "tcga-gdc-pancancer":
                raw = _http_get_bytes(str(ds_meta["download_url"]), timeout=timeout)
                data = json.loads(raw.decode("utf-8", errors="replace"))
                hits = data.get("data", {}).get("hits", []) if isinstance(data, dict) else []
                csv_path = ds_dir / "tcga_gdc_clinical_cases.csv"
                cols = [
                    "case_id",
                    "submitter_id",
                    "primary_site",
                    "disease_type",
                    "gender",
                    "vital_status",
                    "days_to_death",
                    "age_at_diagnosis",
                    "tumor_stage",
                ]
                with csv_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=cols)
                    writer.writeheader()
                    for h in hits:
                        if not isinstance(h, dict):
                            continue
                        raw_demo = h.get("demographic")
                        demo: dict[str, Any] = raw_demo if isinstance(raw_demo, dict) else {}
                        raw_diags = h.get("diagnoses")
                        diags: list[Any] = raw_diags if isinstance(raw_diags, list) and raw_diags else [{}]
                        d0: dict[str, Any] = diags[0] if isinstance(diags[0], dict) else {}
                        writer.writerow(
                            {
                                "case_id": h.get("case_id") or h.get("id"),
                                "submitter_id": h.get("submitter_id"),
                                "primary_site": h.get("primary_site"),
                                "disease_type": h.get("disease_type"),
                                "gender": demo.get("gender"),
                                "vital_status": demo.get("vital_status"),
                                "days_to_death": demo.get("days_to_death"),
                                "age_at_diagnosis": d0.get("age_at_diagnosis"),
                                "tumor_stage": d0.get("tumor_stage") or d0.get("ajcc_pathologic_stage"),
                            }
                        )
            elif dataset_id == "openfda-faers":
                raw = _http_get_bytes(str(ds_meta["download_url"]), timeout=timeout)
                (ds_dir / "openfda_adverse_events.json").write_bytes(raw)
                data = json.loads(raw.decode("utf-8", errors="replace"))
                results = data.get("results", []) if isinstance(data, dict) else []
                csv_path = ds_dir / "openfda_adverse_events_summary.csv"
                cols = [
                    "safetyreportid",
                    "serious",
                    "seriousnessdeath",
                    "seriousnesshospitalization",
                    "patientsex",
                    "patientonsetage",
                    "primary_reaction",
                    "primary_drug",
                ]
                with csv_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=cols)
                    writer.writeheader()
                    for r in results:
                        if not isinstance(r, dict):
                            continue
                        pat = r.get("patient", {}) if isinstance(r.get("patient"), dict) else {}
                        rx = pat.get("reaction", [{}])
                        dr = pat.get("drug", [{}])
                        writer.writerow(
                            {
                                "safetyreportid": r.get("safetyreportid"),
                                "serious": r.get("serious"),
                                "seriousnessdeath": r.get("seriousnessdeath"),
                                "seriousnesshospitalization": r.get("seriousnesshospitalization"),
                                "patientsex": pat.get("patientsex"),
                                "patientonsetage": pat.get("patientonsetage"),
                                "primary_reaction": rx[0].get("reactionmeddrapt")
                                if rx and isinstance(rx[0], dict)
                                else "",
                                "primary_drug": dr[0].get("medicinalproduct") if dr and isinstance(dr[0], dict) else "",
                            }
                        )
            else:
                raw = _http_get_bytes(str(ds_meta["download_url"]), timeout=timeout)
                (ds_dir / f"{dataset_id}_api_snapshot.json").write_bytes(raw)
    except Exception as exc:
        return {
            "contract": "ClinicalDatasetFetchV1",
            "status": "blocked",
            "dataset_id": dataset_id,
            "fetch_method": method,
            "issues": [f"Failed to fetch '{dataset_id}' ({method}): {exc}"],
        }

    verified = ingest_and_verify_dataset(root, dataset_id)
    verified["fetch_method"] = method
    return verified


def fetch_specialty_pack(
    project_dir: Path,
    pack_id: str = "essential-core",
    *,
    timeout: int = 45,
) -> dict[str, Any]:
    """Stage and automatically download all open datasets in a specialty pack."""
    root = Path(project_dir).resolve()
    gate = scientific_execution_gate(root, "dataset-pack-fetch")
    if gate["status"] != "pass":
        return gate
    pack = DATASET_SPECIALTY_PACKS.get(pack_id)
    if not pack:
        return {
            "contract": "ClinicalDatasetPackFetchV1",
            "status": "blocked",
            "issues": [f"Unknown pack '{pack_id}'. Valid packs: {sorted(DATASET_SPECIALTY_PACKS)}"],
        }

    dataset_ids = list(pack["dataset_ids"])
    prepare_dataset_stage(root, dataset_ids=dataset_ids)
    results: dict[str, Any] = {}
    succeeded: list[str] = []
    failed: list[str] = []
    for did in dataset_ids:
        res = fetch_open_dataset(root, did, timeout=timeout)
        results[did] = res
        if res.get("status") == "pass":
            succeeded.append(did)
        else:
            failed.append(did)

    summary_path = root / "evidence" / "datasets" / f"pack_{pack_id}_summary.json"
    summary_payload = {
        "contract": "ClinicalDatasetPackFetchV1",
        "status": "pass" if succeeded and not failed else "partial" if succeeded else "blocked",
        "pack_id": pack_id,
        "pack_name": pack["name"],
        "fetched_at": datetime.now(UTC).isoformat(),
        "requested_count": len(dataset_ids),
        "succeeded_count": len(succeeded),
        "failed_count": len(failed),
        "succeeded_ids": succeeded,
        "failed_ids": failed,
        "results": results,
    }
    save_structured_file(summary_path, summary_payload)
    return summary_payload


def ingest_and_verify_dataset(
    project_dir: Path,
    dataset_id: str,
    *,
    enforce_registration_gate: bool = True,
) -> dict[str, Any]:
    """Verify local dataset files in sources/datasets/<dataset_id>/, compute hashes, and write manifest."""
    root = Path(project_dir).resolve()
    # Legacy callers cannot disable the user-mandated policy with a flag.
    gate = scientific_execution_gate(root, "dataset-ingest")
    if gate["status"] != "pass":
        return gate

    catalog_by_id = {str(item["id"]): item for item in CLINICAL_DATASETS_CATALOG}
    ds_meta = catalog_by_id.get(dataset_id)
    if not ds_meta:
        return {"status": "blocked", "issues": [f"Unknown dataset_id '{dataset_id}'."]}

    ds_dir = root / "sources" / "datasets" / dataset_id
    if not ds_dir.is_dir():
        return {"status": "blocked", "issues": [f"Dataset folder 'sources/datasets/{dataset_id}' does not exist."]}

    files = sorted(p for p in ds_dir.rglob("*") if p.is_file())
    if not files:
        return {
            "status": "blocked",
            "issues": [
                f"No data files found in 'sources/datasets/{dataset_id}/'. Drop or fetch the dataset files first."
            ],
        }

    file_manifests: list[dict[str, Any]] = []
    gate = scientific_execution_gate(root, "dataset-ingest", mark_started=True)
    if gate["status"] != "pass":
        return gate
    for fpath in files:
        register_source(root, str(fpath), "file")
        sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        columns: list[str] = []
        row_count: int | None = None
        if fpath.suffix.lower() in {".csv", ".tsv", ".data"}:
            delim = "\t" if fpath.suffix.lower() == ".tsv" else ","
            try:
                with fpath.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
                    reader = csv.reader(handle, delimiter=delim)
                    header = next(reader, None)
                    if header:
                        columns = [str(c).strip() for c in header[:80]]
                        row_count = sum(1 for _ in reader)
            except OSError:
                pass
        file_manifests.append(
            {
                "relative_path": fpath.relative_to(root).as_posix(),
                "size_bytes": fpath.stat().st_size,
                "sha256": sha,
                "columns": columns,
                "row_count": row_count,
            }
        )

    manifest_dir = root / "evidence" / "datasets"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{dataset_id}_manifest.json"
    manifest_payload = {
        "contract": "ClinicalDatasetManifestV1",
        "dataset_id": dataset_id,
        "dataset_name": ds_meta["name"],
        "access_tier": ds_meta["access_tier"],
        "license": ds_meta["license"],
        "verification_scope": "local-file-integrity-and-tabular-inspection-only",
        "catalog_metadata_verified": False,
        "cohort_identity_verified": False,
        "license_verified": False,
        "fetch_scope": ds_meta.get("fetch_scope", "provider-content-not-schema-validated"),
        "scientific_use_eligible": False,
        "required_reviews": ["license-and-access", "source-and-release", "patient-and-time-unit", "outcome-and-design"],
        "verified_at": datetime.now(UTC).isoformat(),
        "file_count": len(file_manifests),
        "files": file_manifests,
    }
    save_structured_file(manifest_path, manifest_payload)

    return {
        "contract": "ClinicalDatasetManifestV1",
        "status": "pass",
        "verification_scope": "local-file-integrity-and-tabular-inspection-only",
        "scientific_use_eligible": False,
        "dataset_id": dataset_id,
        "file_count": len(file_manifests),
        "manifest_path": manifest_path.relative_to(root).as_posix(),
        "files": file_manifests,
    }
