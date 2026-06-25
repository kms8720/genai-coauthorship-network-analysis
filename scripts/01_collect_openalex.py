from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from typing import Any, Dict, List

import requests

from common import DATA_RAW, ensure_dirs, load_config, write_jsonl


API_URL = "https://api.openalex.org/works"
SELECT_FIELDS = ",".join(
    [
        "id",
        "doi",
        "display_name",
        "title",
        "publication_year",
        "publication_date",
        "cited_by_count",
        "primary_topic",
        "concepts",
        "authorships",
    ]
)


def sample_work(work_id: str, title: str, year: int, terms: List[str], authors: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "id": f"https://openalex.org/{work_id}",
        "doi": "",
        "display_name": title,
        "title": title,
        "publication_year": year,
        "publication_date": f"{year}-06-01",
        "cited_by_count": 0,
        "primary_topic": {"display_name": "Artificial intelligence"},
        "concepts": [],
        "matched_terms": terms,
        "authorships": [
            {
                "author_position": "middle",
                "author": {
                    "id": f"https://openalex.org/{a['author_id']}",
                    "display_name": a["author_name"],
                },
                "raw_affiliation_strings": [a["institution_name"]],
                "institutions": [
                    {
                        "id": f"https://openalex.org/{a['institution_id']}",
                        "display_name": a["institution_name"],
                        "type": a["institution_type"],
                        "country_code": a.get("country_code", "US"),
                    }
                ],
            }
            for a in authors
        ],
    }


def offline_sample_works() -> List[Dict[str, Any]]:
    return [
        sample_work(
            "W_SAMPLE_2022_1",
            "Large Language Models for Scientific Discovery",
            2022,
            ["large language model"],
            [
                {"author_id": "A_SAMPLE_1", "author_name": "Avery Kim", "institution_id": "I_OPENAI", "institution_name": "OpenAI", "institution_type": "company"},
                {"author_id": "A_SAMPLE_2", "author_name": "Morgan Lee", "institution_id": "I_STANFORD", "institution_name": "Stanford University", "institution_type": "education"},
                {"author_id": "A_SAMPLE_3", "author_name": "Jordan Park", "institution_id": "I_GOOGLE", "institution_name": "Google DeepMind", "institution_type": "company"},
            ],
        ),
        sample_work(
            "W_SAMPLE_2023_1",
            "Instruction Tuning and Human Feedback",
            2023,
            ["instruction tuning", "RLHF"],
            [
                {"author_id": "A_SAMPLE_1", "author_name": "Avery Kim", "institution_id": "I_OPENAI", "institution_name": "OpenAI", "institution_type": "company"},
                {"author_id": "A_SAMPLE_4", "author_name": "Riley Chen", "institution_id": "I_MIT", "institution_name": "Massachusetts Institute of Technology", "institution_type": "education"},
                {"author_id": "A_SAMPLE_5", "author_name": "Taylor Smith", "institution_id": "I_META", "institution_name": "Meta AI", "institution_type": "company"},
            ],
        ),
        sample_work(
            "W_SAMPLE_2023_2",
            "Foundation Models in Multimodal Systems",
            2023,
            ["foundation model"],
            [
                {"author_id": "A_SAMPLE_6", "author_name": "Casey Nguyen", "institution_id": "I_MICROSOFT", "institution_name": "Microsoft Research", "institution_type": "company"},
                {"author_id": "A_SAMPLE_2", "author_name": "Morgan Lee", "institution_id": "I_STANFORD", "institution_name": "Stanford University", "institution_type": "education"},
                {"author_id": "A_SAMPLE_7", "author_name": "Jamie Patel", "institution_id": "I_ALLEN", "institution_name": "Allen Institute for AI", "institution_type": "nonprofit"},
            ],
        ),
        sample_work(
            "W_SAMPLE_2024_1",
            "Diffusion Models for Text-to-Image Generation",
            2024,
            ["diffusion model", "text-to-image"],
            [
                {"author_id": "A_SAMPLE_8", "author_name": "Sam Rivera", "institution_id": "I_STABILITY", "institution_name": "Stability AI", "institution_type": "company"},
                {"author_id": "A_SAMPLE_9", "author_name": "Drew Miller", "institution_id": "I_BERKELEY", "institution_name": "University of California, Berkeley", "institution_type": "education"},
                {"author_id": "A_SAMPLE_10", "author_name": "Quinn Davis", "institution_id": "I_NVIDIA", "institution_name": "NVIDIA", "institution_type": "company"},
            ],
        ),
        sample_work(
            "W_SAMPLE_2025_1",
            "Evaluating Generative AI Research Collaboration",
            2025,
            ["generative AI"],
            [
                {"author_id": "A_SAMPLE_4", "author_name": "Riley Chen", "institution_id": "I_ANTHROPIC", "institution_name": "Anthropic", "institution_type": "company"},
                {"author_id": "A_SAMPLE_5", "author_name": "Taylor Smith", "institution_id": "I_META", "institution_name": "Meta AI", "institution_type": "company"},
                {"author_id": "A_SAMPLE_9", "author_name": "Drew Miller", "institution_id": "I_BERKELEY", "institution_name": "University of California, Berkeley", "institution_type": "education"},
            ],
        ),
        sample_work(
            "W_SAMPLE_2025_2",
            "Open Models and Cross-Institution AI Networks",
            2025,
            ["LLM", "generative AI"],
            [
                {"author_id": "A_SAMPLE_11", "author_name": "Sky Johnson", "institution_id": "I_HF", "institution_name": "Hugging Face", "institution_type": "company"},
                {"author_id": "A_SAMPLE_7", "author_name": "Jamie Patel", "institution_id": "I_ALLEN", "institution_name": "Allen Institute for AI", "institution_type": "nonprofit"},
                {"author_id": "A_SAMPLE_2", "author_name": "Morgan Lee", "institution_id": "I_STANFORD", "institution_name": "Stanford University", "institution_type": "education"},
            ],
        ),
    ]


def request_with_retries(params: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("OPENALEX_API_KEY")
    email = os.getenv("OPENALEX_EMAIL")
    if api_key:
        params["api_key"] = api_key
    if email:
        params["mailto"] = email

    attempts = int(cfg.get("retry_attempts", 4))
    timeout = int(cfg.get("request_timeout_seconds", 30))
    last_error = None
    for attempt in range(attempts):
        try:
            response = requests.get(API_URL, params=params, timeout=timeout)
            if response.status_code in {429, 500, 502, 503, 504}:
                wait = min(60, (2**attempt) + 0.5)
                print(f"Retryable OpenAlex status {response.status_code}; sleeping {wait:.1f}s", flush=True)
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            wait = min(60, (2**attempt) + 0.5)
            print(f"Request failed: {exc}; sleeping {wait:.1f}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"OpenAlex request failed after {attempts} attempts: {last_error}")


def collect() -> None:
    ensure_dirs()
    cfg = load_config()
    start_year = int(cfg["start_year"])
    end_year = int(cfg["end_year"])
    per_page = min(int(cfg.get("per_page", 100)), 100)
    max_pages = int(cfg.get("max_pages_per_query", 5))
    if cfg.get("full_run"):
        max_pages = max(max_pages, 50)

    works_by_id: Dict[str, Dict[str, Any]] = {}
    matched_terms = defaultdict(set)
    skipped_requests = []
    consecutive_initial_failures = 0
    max_initial_failures = int(cfg.get("max_initial_api_failures_before_offline_sample", 4))

    for term in cfg["search_terms"]:
        for year in range(start_year, end_year + 1):
            for page in range(1, max_pages + 1):
                params = {
                    "search": term,
                    "filter": f"from_publication_date:{year}-01-01,to_publication_date:{year}-12-31",
                    "per-page": per_page,
                    "page": page,
                    "select": SELECT_FIELDS,
                }
                try:
                    payload = request_with_retries(params, cfg)
                except RuntimeError as exc:
                    skipped_requests.append(
                        {"term": term, "year": year, "page": page, "error": str(exc)}
                    )
                    print(
                        f"Skipping term={term!r} year={year} page={page}: {exc}",
                        flush=True,
                    )
                    if not works_by_id:
                        consecutive_initial_failures += 1
                        if (
                            cfg.get("use_offline_sample_if_api_unavailable", True)
                            and consecutive_initial_failures >= max_initial_failures
                        ):
                            print(
                                "OpenAlex appears unavailable or rate-limited before any records were collected.",
                                flush=True,
                            )
                            rows = offline_sample_works()
                            raw_path = DATA_RAW / "openalex_works_raw.jsonl"
                            write_jsonl(raw_path, rows)
                            meta = {
                                "collected_works": len(rows),
                                "start_year": start_year,
                                "end_year": end_year,
                                "full_run": bool(cfg.get("full_run")),
                                "max_pages_per_query": max_pages,
                                "api_key_set": bool(os.getenv("OPENALEX_API_KEY")),
                                "email_set": bool(os.getenv("OPENALEX_EMAIL")),
                                "skipped_requests": skipped_requests,
                                "used_offline_sample": True,
                            }
                            with open(DATA_RAW / "collection_metadata.json", "w", encoding="utf-8") as f:
                                json.dump(meta, f, indent=2)
                            print(json.dumps(meta, indent=2), flush=True)
                            print(f"Wrote {raw_path}", flush=True)
                            return
                    break
                results: List[Dict[str, Any]] = payload.get("results", [])
                if not results:
                    break
                for work in results:
                    work_id = work.get("id")
                    if not work_id:
                        continue
                    works_by_id[work_id] = work
                    matched_terms[work_id].add(term)
                print(f"Collected term={term!r} year={year} page={page} results={len(results)}", flush=True)
                time.sleep(float(cfg.get("sleep_seconds", 0.2)))

    rows = []
    for work_id, work in works_by_id.items():
        work["matched_terms"] = sorted(matched_terms[work_id])
        rows.append(work)
    used_offline_sample = False
    if not rows and cfg.get("use_offline_sample_if_api_unavailable", True):
        rows = offline_sample_works()
        used_offline_sample = True
        print("OpenAlex returned no usable records; wrote offline sample data for pipeline validation.", flush=True)

    raw_path = DATA_RAW / "openalex_works_raw.jsonl"
    write_jsonl(raw_path, rows)
    meta = {
        "collected_works": len(rows),
        "start_year": start_year,
        "end_year": end_year,
        "full_run": bool(cfg.get("full_run")),
        "max_pages_per_query": max_pages,
        "api_key_set": bool(os.getenv("OPENALEX_API_KEY")),
        "email_set": bool(os.getenv("OPENALEX_EMAIL")),
        "skipped_requests": skipped_requests,
        "used_offline_sample": used_offline_sample,
    }
    with open(DATA_RAW / "collection_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))
    print(f"Wrote {raw_path}")


if __name__ == "__main__":
    collect()
