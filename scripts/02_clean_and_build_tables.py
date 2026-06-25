from __future__ import annotations

import json
from collections import Counter
from typing import Any, Dict, List, Tuple

import pandas as pd

from common import (
    DATA_PROCESSED,
    DATA_RAW,
    OUTPUTS,
    ensure_dirs,
    normalize_openalex_id,
    read_jsonl,
    recover_raw_affiliations,
    semicolon_join,
    simplify_institution_category,
    target_firm_label,
)


CATEGORY_PRIORITY = {
    "company": 0,
    "research_institute": 1,
    "education": 2,
    "government": 3,
    "nonprofit": 4,
    "healthcare": 5,
    "other": 6,
    "unknown": 7,
    "": 8,
}


def get_primary_topic(work: Dict[str, Any]) -> str:
    topic = work.get("primary_topic") or {}
    return topic.get("display_name") or topic.get("id") or ""


def institution_record(
    inst_id: str,
    inst_name: str,
    inst_type: str,
    country: str,
    category: str | None = None,
    firm: str | None = None,
) -> Dict[str, Any]:
    return {
        "institution_id": inst_id,
        "institution_display_name": inst_name,
        "institution_type": inst_type,
        "institution_country_code": country,
        "simplified_institution_category": category or simplify_institution_category(inst_type, inst_name),
        "target_firm_label": firm or target_firm_label(inst_name),
    }


def affiliation_row(
    work_id: str,
    publication_year: int,
    publication_date: str,
    author_id: str,
    author_name: str,
    raw_affiliation: str,
    inst: Dict[str, Any],
    source: str,
) -> Dict[str, Any]:
    return {
        "work_id": work_id,
        "publication_year": publication_year,
        "publication_date": publication_date,
        "author_id": author_id,
        "author_name": author_name,
        "raw_affiliation": raw_affiliation,
        "institution_id": inst.get("institution_id", ""),
        "institution_name": inst.get("institution_display_name", ""),
        "institution_type": inst.get("institution_type", ""),
        "institution_country_code": inst.get("institution_country_code", ""),
        "simplified_institution_category": inst.get("simplified_institution_category", "unknown") or "unknown",
        "target_firm_label": inst.get("target_firm_label", "Other") or "Other",
        "affiliation_source": source,
    }


def unknown_authorship_row(
    work_id: str,
    publication_year: int,
    author_position: int,
    author_id: str,
    author_name: str,
    raw_affiliation: str,
) -> Dict[str, Any]:
    return {
        "work_id": work_id,
        "publication_year": publication_year,
        "author_position": author_position,
        "author_id": author_id,
        "author_display_name": author_name,
        "raw_affiliation": raw_affiliation,
        "institution_id": "",
        "institution_display_name": "",
        "institution_type": "",
        "institution_country_code": "",
        "simplified_institution_category": "unknown",
        "target_firm_label": "Other",
        "affiliation_source": "missing",
    }


def primary_affiliation_for_display(group: pd.DataFrame) -> pd.Series:
    if group.empty:
        return pd.Series(dtype=object)
    ranked = (
        group.assign(
            affiliation_count=group.groupby("institution_id")["work_id"].transform("nunique"),
            latest_date=pd.to_datetime(group["publication_date"], errors="coerce").fillna(pd.Timestamp("1900-01-01")),
            raw_target_ai_firm=(
                (group["affiliation_source"] == "raw_affiliation_rule")
                & (group["target_firm_label"] != "Other")
            ).astype(int),
            category_rank=group["simplified_institution_category"].map(CATEGORY_PRIORITY).fillna(99),
        )
        .sort_values(
            ["affiliation_count", "latest_date", "raw_target_ai_firm", "category_rank", "institution_name"],
            ascending=[False, False, False, True, True],
        )
    )
    return ranked.iloc[0]


def category_pattern(categories: List[str]) -> str:
    cats = {c for c in categories if c and c != "unknown"}
    if not cats:
        return "unknown"
    if cats == {"company"}:
        return "company_only"
    if cats == {"education"}:
        return "education_only"
    if cats == {"research_institute"}:
        return "research_institute_only"
    if cats == {"company", "education"}:
        return "company_plus_education"
    if cats == {"company", "research_institute"}:
        return "company_plus_research_institute"
    return "multiple_categories"


def build_author_year_affiliations(long_df: pd.DataFrame, authors_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if long_df.empty:
        return pd.DataFrame()
    for (author_id, year), group in long_df.groupby(["author_id", "publication_year"]):
        primary = primary_affiliation_for_display(group)
        categories = sorted(set(group["simplified_institution_category"].dropna().astype(str)))
        firms = sorted(set(group["target_firm_label"].dropna().astype(str)))
        inst_ids = sorted(set(group["institution_id"].dropna().astype(str)))
        inst_names = sorted(set(group["institution_name"].dropna().astype(str)))
        inst_types = sorted(set(group["institution_type"].dropna().astype(str)))
        rows.append(
            {
                "author_id": author_id,
                "author_name": primary.get("author_name", ""),
                "year": int(year),
                "all_institution_ids_this_year": semicolon_join(inst_ids),
                "all_institution_names_this_year": semicolon_join(inst_names),
                "all_institution_types_this_year": semicolon_join(inst_types),
                "all_target_firm_labels_this_year": semicolon_join(firms),
                "has_company_affiliation_this_year": "company" in categories,
                "has_education_affiliation_this_year": "education" in categories,
                "has_research_institute_affiliation_this_year": "research_institute" in categories,
                "has_multiple_affiliations_this_year": len({i for i in inst_ids if i}) > 1,
                "has_multiple_categories_this_year": len({c for c in categories if c and c != "unknown"}) > 1,
                "has_company_and_education_this_year": {"company", "education"}.issubset(categories),
                "has_company_and_research_institute_this_year": {"company", "research_institute"}.issubset(categories),
                "primary_institution_for_display_this_year": primary.get("institution_name", ""),
                "primary_institution_id_for_display_this_year": primary.get("institution_id", ""),
                "primary_institution_type_for_display_this_year": primary.get("institution_type", ""),
                "primary_category_for_display_this_year": primary.get("simplified_institution_category", "unknown"),
                "primary_target_firm_for_display_this_year": primary.get("target_firm_label", "Other"),
                "raw_recovered_affiliation_count_this_year": int((group["affiliation_source"] == "raw_affiliation_rule").sum()),
            }
        )
    ay = pd.DataFrame(rows)

    observed = set(zip(ay["author_id"], ay["year"])) if not ay.empty else set()
    missing_rows = []
    for (author_id, year), group in authors_df.groupby(["author_id", "publication_year"]):
        if (author_id, year) in observed:
            continue
        missing_rows.append(
            {
                "author_id": author_id,
                "author_name": group["author_display_name"].iloc[0],
                "year": int(year),
                "all_institution_ids_this_year": "",
                "all_institution_names_this_year": "",
                "all_institution_types_this_year": "",
                "all_target_firm_labels_this_year": "",
                "has_company_affiliation_this_year": False,
                "has_education_affiliation_this_year": False,
                "has_research_institute_affiliation_this_year": False,
                "has_multiple_affiliations_this_year": False,
                "has_multiple_categories_this_year": False,
                "has_company_and_education_this_year": False,
                "has_company_and_research_institute_this_year": False,
                "primary_institution_for_display_this_year": "",
                "primary_institution_id_for_display_this_year": "",
                "primary_institution_type_for_display_this_year": "",
                "primary_category_for_display_this_year": "unknown",
                "primary_target_firm_for_display_this_year": "Other",
                "raw_recovered_affiliation_count_this_year": 0,
            }
        )
    if missing_rows:
        ay = pd.concat([ay, pd.DataFrame(missing_rows)], ignore_index=True)
    return ay.sort_values(["author_id", "year"])


def build_mobility_table(author_year_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if author_year_df.empty:
        return pd.DataFrame()
    for author_id, group in author_year_df.sort_values("year").groupby("author_id"):
        if group["year"].nunique() < 2:
            continue
        records = group.to_dict("records")
        for prev, curr in zip(records, records[1:]):
            rows.append(
                {
                    "author_id": author_id,
                    "author_name": curr.get("author_name") or prev.get("author_name", ""),
                    "from_year": prev["year"],
                    "to_year": curr["year"],
                    "from_primary_affiliation": prev.get("primary_institution_for_display_this_year", ""),
                    "to_primary_affiliation": curr.get("primary_institution_for_display_this_year", ""),
                    "from_category": prev.get("primary_category_for_display_this_year", "unknown"),
                    "to_category": curr.get("primary_category_for_display_this_year", "unknown"),
                    "from_target_firm": prev.get("primary_target_firm_for_display_this_year", "Other"),
                    "to_target_firm": curr.get("primary_target_firm_for_display_this_year", "Other"),
                    "changed_affiliation": prev.get("primary_institution_for_display_this_year", "")
                    != curr.get("primary_institution_for_display_this_year", ""),
                    "changed_category": prev.get("primary_category_for_display_this_year", "unknown")
                    != curr.get("primary_category_for_display_this_year", "unknown"),
                    "changed_target_firm": prev.get("primary_target_firm_for_display_this_year", "Other")
                    != curr.get("primary_target_firm_for_display_this_year", "Other"),
                }
            )
    return pd.DataFrame(rows)


def clean() -> None:
    ensure_dirs()
    raw_path = DATA_RAW / "openalex_works_raw.jsonl"
    works = read_jsonl(raw_path)

    works_rows: List[Dict[str, Any]] = []
    authorship_rows: List[Dict[str, Any]] = []
    affiliation_rows: List[Dict[str, Any]] = []
    institution_rows: Dict[str, Dict[str, Any]] = {}

    for work in works:
        authorships = work.get("authorships") or []
        usable_authors = [a for a in authorships if (a.get("author") or {}).get("id")]
        if not usable_authors:
            continue

        work_id = normalize_openalex_id(work.get("id"))
        year = int(work.get("publication_year"))
        publication_date = work.get("publication_date", "")
        works_rows.append(
            {
                "work_id": work_id,
                "openalex_url": work.get("id", ""),
                "doi": work.get("doi", ""),
                "title": work.get("display_name") or work.get("title", ""),
                "publication_year": year,
                "publication_date": publication_date,
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
            observed_affiliations: List[Tuple[Dict[str, Any], str]] = []

            for inst in authorship.get("institutions") or []:
                inst_id = normalize_openalex_id(inst.get("id"))
                inst_name = inst.get("display_name", "")
                inst_type = inst.get("type", "")
                country = inst.get("country_code", "")
                record = institution_record(inst_id, inst_name, inst_type, country)
                observed_affiliations.append((record, "structured_openalex"))

            existing_firms = {inst["target_firm_label"] for inst, _ in observed_affiliations}
            existing_ids = {inst["institution_id"] for inst, _ in observed_affiliations}
            for recovered in recover_raw_affiliations(raw_affiliation):
                if recovered["target_firm_label"] in existing_firms or recovered["institution_id"] in existing_ids:
                    continue
                observed_affiliations.append((recovered, "raw_affiliation_rule"))

            if not observed_affiliations:
                authorship_rows.append(
                    unknown_authorship_row(work_id, year, pos, author_id, author_name, raw_affiliation)
                )
                continue

            for inst, source in observed_affiliations:
                institution_rows[inst["institution_id"]] = inst
                row = affiliation_row(
                    work_id,
                    year,
                    publication_date,
                    author_id,
                    author_name,
                    raw_affiliation,
                    inst,
                    source,
                )
                affiliation_rows.append(row)
                authorship_rows.append(
                    {
                        "work_id": work_id,
                        "publication_year": year,
                        "author_position": pos,
                        "author_id": author_id,
                        "author_display_name": author_name,
                        "raw_affiliation": raw_affiliation,
                        "institution_id": inst["institution_id"],
                        "institution_display_name": inst["institution_display_name"],
                        "institution_type": inst["institution_type"],
                        "institution_country_code": inst.get("institution_country_code", ""),
                        "simplified_institution_category": inst["simplified_institution_category"],
                        "target_firm_label": inst["target_firm_label"],
                        "affiliation_source": source,
                    }
                )

    works_df = pd.DataFrame(works_rows).drop_duplicates("work_id")
    authorships_df = pd.DataFrame(authorship_rows).drop_duplicates(
        ["work_id", "author_id", "institution_id", "affiliation_source"]
    )
    institutions_df = pd.DataFrame(institution_rows.values()).drop_duplicates("institution_id")
    long_df = pd.DataFrame(affiliation_rows).drop_duplicates(
        ["work_id", "author_id", "institution_id", "affiliation_source"]
    )
    author_year_df = build_author_year_affiliations(long_df, authorships_df)
    mobility_df = build_mobility_table(author_year_df)

    works_df.to_csv(DATA_PROCESSED / "works.csv", index=False)
    authorships_df.to_csv(DATA_PROCESSED / "authorships.csv", index=False)
    institutions_df.to_csv(DATA_PROCESSED / "institutions.csv", index=False)
    author_year_df.to_csv(DATA_PROCESSED / "author_year_affiliations.csv", index=False)

    long_output_cols = [
        "work_id",
        "publication_year",
        "author_id",
        "author_name",
        "institution_id",
        "institution_name",
        "institution_type",
        "simplified_institution_category",
        "target_firm_label",
        "affiliation_source",
    ]
    long_df[long_output_cols].to_csv(OUTPUTS / "tables" / "authorship_affiliations_long.csv", index=False)
    author_year_df.to_csv(OUTPUTS / "tables" / "author_year_affiliations.csv", index=False)
    mobility_df.to_csv(OUTPUTS / "tables" / "researcher_affiliation_changes.csv", index=False)

    authors_with_raw_recovered = int(
        long_df.loc[long_df["affiliation_source"] == "raw_affiliation_rule", "author_id"].nunique()
    ) if not long_df.empty else 0
    authors_with_no_observed = int(
        authorship_rows and authorships_df.groupby("author_id")["institution_id"].apply(lambda s: (s.astype(str) == "").all()).sum()
    )
    authors_with_multiple_affiliations = int(
        author_year_df.groupby("author_id")["has_multiple_affiliations_this_year"].any().sum()
    ) if not author_year_df.empty else 0
    authors_with_category_changes = int(
        mobility_df.groupby("author_id")["changed_category"].any().sum()
    ) if not mobility_df.empty else 0

    summary = {
        "processed_works": int(len(works_df)),
        "authorship_rows": int(len(authorships_df)),
        "authorship_affiliation_rows": int(len(long_df)),
        "unique_authors": int(authorships_df["author_id"].nunique()) if not authorships_df.empty else 0,
        "unique_institutions": int(institutions_df["institution_id"].nunique()) if not institutions_df.empty else 0,
        "authors_with_no_observed_institution_metadata": authors_with_no_observed,
        "authors_with_raw_affiliation_recovered": authors_with_raw_recovered,
        "authors_with_multiple_affiliations": authors_with_multiple_affiliations,
        "authors_with_category_changes_across_years": authors_with_category_changes,
    }
    with open(DATA_PROCESSED / "cleaning_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    clean()
