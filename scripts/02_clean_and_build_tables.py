from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List

import pandas as pd

from common import (
    DATA_PROCESSED,
    DATA_RAW,
    ensure_dirs,
    normalize_openalex_id,
    read_jsonl,
    semicolon_join,
    simplify_institution_category,
    target_firm_label,
)


def get_primary_topic(work: Dict[str, Any]) -> str:
    topic = work.get("primary_topic") or {}
    return topic.get("display_name") or topic.get("id") or ""


def clean() -> None:
    ensure_dirs()
    raw_path = DATA_RAW / "openalex_works_raw.jsonl"
    works = read_jsonl(raw_path)

    works_rows: List[Dict[str, Any]] = []
    authorship_rows: List[Dict[str, Any]] = []
    institution_rows: Dict[str, Dict[str, Any]] = {}
    author_year_affils = defaultdict(lambda: {"institution_names": set(), "institution_ids": set(), "institution_categories": set()})

    for work in works:
        authorships = work.get("authorships") or []
        usable_authors = [a for a in authorships if (a.get("author") or {}).get("id")]
        if not usable_authors:
            continue

        work_id = normalize_openalex_id(work.get("id"))
        year = work.get("publication_year")
        works_rows.append(
            {
                "work_id": work_id,
                "openalex_url": work.get("id", ""),
                "doi": work.get("doi", ""),
                "title": work.get("display_name") or work.get("title", ""),
                "publication_year": year,
                "publication_date": work.get("publication_date", ""),
                "cited_by_count": work.get("cited_by_count", 0),
                "primary_topic": get_primary_topic(work),
                "matched_terms": semicolon_join(work.get("matched_terms", [])),
                "author_count": len(usable_authors),
                "large_author_list_flag": len(usable_authors) > 50,
            }
        )

        for pos, authorship in enumerate(usable_authors, start=1):
            author = authorship.get("author") or {}
            author_id = normalize_openalex_id(author.get("id"))
            author_name = author.get("display_name", "")
            raw_affiliation = "; ".join(authorship.get("raw_affiliation_strings") or [])
            institutions = authorship.get("institutions") or []
            if not institutions:
                authorship_rows.append(
                    {
                        "work_id": work_id,
                        "publication_year": year,
                        "author_position": pos,
                        "author_id": author_id,
                        "author_display_name": author_name,
                        "raw_affiliation": raw_affiliation,
                        "institution_id": "",
                        "institution_display_name": "",
                        "institution_type": "",
                        "institution_country_code": "",
                        "simplified_institution_category": "unknown",
                        "target_firm_label": "Other",
                    }
                )
                author_year_affils[(author_id, year)]["institution_categories"].add("unknown")
                continue

            for inst in institutions:
                inst_id = normalize_openalex_id(inst.get("id"))
                inst_name = inst.get("display_name", "")
                inst_type = inst.get("type", "")
                country = inst.get("country_code", "")
                category = simplify_institution_category(inst_type, inst_name)
                firm = target_firm_label(inst_name)
                institution_rows[inst_id] = {
                    "institution_id": inst_id,
                    "institution_display_name": inst_name,
                    "institution_type": inst_type,
                    "institution_country_code": country,
                    "simplified_institution_category": category,
                    "target_firm_label": firm,
                }
                authorship_rows.append(
                    {
                        "work_id": work_id,
                        "publication_year": year,
                        "author_position": pos,
                        "author_id": author_id,
                        "author_display_name": author_name,
                        "raw_affiliation": raw_affiliation,
                        "institution_id": inst_id,
                        "institution_display_name": inst_name,
                        "institution_type": inst_type,
                        "institution_country_code": country,
                        "simplified_institution_category": category,
                        "target_firm_label": firm,
                    }
                )
                aff = author_year_affils[(author_id, year)]
                aff["institution_names"].add(inst_name)
                aff["institution_ids"].add(inst_id)
                aff["institution_categories"].add(category)

    works_df = pd.DataFrame(works_rows).drop_duplicates("work_id")
    authorships_df = pd.DataFrame(authorship_rows).drop_duplicates(
        ["work_id", "author_id", "institution_id"]
    )
    institutions_df = pd.DataFrame(institution_rows.values()).drop_duplicates("institution_id")
    affil_rows = [
        {
            "author_id": author_id,
            "publication_year": year,
            "institution_ids": semicolon_join(v["institution_ids"]),
            "institution_names": semicolon_join(v["institution_names"]),
            "institution_categories": semicolon_join(v["institution_categories"]),
        }
        for (author_id, year), v in author_year_affils.items()
    ]
    affils_df = pd.DataFrame(affil_rows)

    works_df.to_csv(DATA_PROCESSED / "works.csv", index=False)
    authorships_df.to_csv(DATA_PROCESSED / "authorships.csv", index=False)
    institutions_df.to_csv(DATA_PROCESSED / "institutions.csv", index=False)
    affils_df.to_csv(DATA_PROCESSED / "author_year_affiliations.csv", index=False)

    summary = {
        "processed_works": int(len(works_df)),
        "authorship_rows": int(len(authorships_df)),
        "unique_authors": int(authorships_df["author_id"].nunique()) if not authorships_df.empty else 0,
        "unique_institutions": int(institutions_df["institution_id"].nunique()) if not institutions_df.empty else 0,
    }
    with open(DATA_PROCESSED / "cleaning_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    clean()

