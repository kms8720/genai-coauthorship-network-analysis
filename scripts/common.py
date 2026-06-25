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

