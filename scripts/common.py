from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS = PROJECT_ROOT / "outputs"


def load_config() -> Dict[str, Any]:
    with open(PROJECT_ROOT / "config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs() -> None:
    for path in [
        DATA_RAW,
        DATA_PROCESSED,
        OUTPUTS / "tables",
        OUTPUTS / "networks",
        OUTPUTS / "figures",
        OUTPUTS / "gephi",
        OUTPUTS / "report",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_openalex_id(value: Any) -> str:
    if pd.isna(value) or value is None:
        return ""
    return str(value).rstrip("/").split("/")[-1]


def simplify_institution_category(inst_type: Any, inst_name: Any = "") -> str:
    t = str(inst_type or "").lower()
    name = str(inst_name or "").lower()
    firm = target_firm_label(name)
    if firm != "Other":
        return "company"
    if "company" in t:
        return "company"
    if "education" in t:
        return "education"
    if "government" in t:
        return "government"
    if "healthcare" in t:
        return "healthcare"
    if "nonprofit" in t:
        return "nonprofit"
    if any(x in t for x in ["facility", "archive", "repository"]):
        return "research_institute"
    if any(x in name for x in ["research institute", "laboratory", "lab ", " labs", "institute of"]):
        return "research_institute"
    return "unknown"


def target_firm_label(inst_name: Any) -> str:
    name = str(inst_name or "").lower()
    rules = [
        ("OpenAI", ["openai"]),
        ("Google / Google DeepMind / DeepMind", ["google deepmind", "deepmind", "google research", "google llc", "google inc", "google"]),
        ("Meta", ["meta ai", "facebook ai", "facebook research", "meta platforms", "facebook"]),
        ("Microsoft", ["microsoft research", "microsoft corporation", "microsoft"]),
        ("Anthropic", ["anthropic"]),
        ("Apple", ["apple inc", "apple"]),
        ("Amazon", ["amazon science", "amazon web services", "amazon.com", "amazon"]),
        ("NVIDIA", ["nvidia"]),
        ("Cohere", ["cohere"]),
        ("Mistral AI", ["mistral ai"]),
        ("xAI", ["xai", "x.ai"]),
        ("Stability AI", ["stability ai"]),
        ("Hugging Face", ["hugging face"]),
    ]
    for label, patterns in rules:
        if any(pattern in name for pattern in patterns):
            return label
    return "Other"


RAW_TARGET_FIRM_RULES = [
    {
        "institution_id": "RAW_OPENAI",
        "institution_display_name": "OpenAI",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "OpenAI",
        "patterns": ["openai", "open ai"],
    },
    {
        "institution_id": "RAW_ANTHROPIC",
        "institution_display_name": "Anthropic",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "Anthropic",
        "patterns": ["anthropic"],
    },
    {
        "institution_id": "RAW_GOOGLE_DEEPMIND",
        "institution_display_name": "Google DeepMind",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "Google / Google DeepMind / DeepMind",
        "patterns": ["google deepmind", "deepmind", "google research"],
    },
    {
        "institution_id": "RAW_META",
        "institution_display_name": "Meta AI",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "Meta",
        "patterns": ["meta ai", "facebook ai", "facebook research"],
    },
    {
        "institution_id": "RAW_MICROSOFT",
        "institution_display_name": "Microsoft Research",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "Microsoft",
        "patterns": ["microsoft research", "microsoft"],
    },
    {
        "institution_id": "RAW_NVIDIA",
        "institution_display_name": "NVIDIA",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "NVIDIA",
        "patterns": ["nvidia"],
    },
    {
        "institution_id": "RAW_COHERE",
        "institution_display_name": "Cohere",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "Cohere",
        "patterns": ["cohere"],
    },
    {
        "institution_id": "RAW_MISTRAL_AI",
        "institution_display_name": "Mistral AI",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "Mistral AI",
        "patterns": ["mistral ai"],
    },
    {
        "institution_id": "RAW_XAI",
        "institution_display_name": "xAI",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "xAI",
        "patterns": ["x.ai", " xai", "xai "],
    },
    {
        "institution_id": "RAW_STABILITY_AI",
        "institution_display_name": "Stability AI",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "Stability AI",
        "patterns": ["stability ai"],
    },
    {
        "institution_id": "RAW_HUGGING_FACE",
        "institution_display_name": "Hugging Face",
        "institution_type": "company",
        "institution_country_code": "",
        "simplified_institution_category": "company",
        "target_firm_label": "Hugging Face",
        "patterns": ["hugging face"],
    },
]


def recover_raw_affiliations(raw_affiliation: Any) -> List[Dict[str, str]]:
    text = f" {str(raw_affiliation or '').lower()} "
    recovered = []
    seen = set()
    for rule in RAW_TARGET_FIRM_RULES:
        if any(pattern in text for pattern in rule["patterns"]):
            inst_id = rule["institution_id"]
            if inst_id in seen:
                continue
            seen.add(inst_id)
            recovered.append(
                {
                    key: value
                    for key, value in rule.items()
                    if key != "patterns"
                }
            )
    return recovered


def csv_or_empty(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size > 0:
        return pd.read_csv(path)
    return pd.DataFrame()


def semicolon_join(values: Iterable[Any]) -> str:
    return ";".join(str(v) for v in sorted(set(v for v in values if pd.notna(v) and str(v) != "")))


def env_note() -> str:
    key = "set" if os.getenv("OPENALEX_API_KEY") else "not set"
    email = "set" if os.getenv("OPENALEX_EMAIL") else "not set"
    return f"OPENALEX_API_KEY={key}; OPENALEX_EMAIL={email}"
