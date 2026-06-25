from __future__ import annotations

import itertools
import json
from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple

import networkx as nx
import pandas as pd

from common import DATA_PROCESSED, OUTPUTS, ensure_dirs, load_config, semicolon_join


def first_mode(values: Iterable[Any]) -> str:
    cleaned = [str(v) for v in values if pd.notna(v) and str(v) != ""]
    if not cleaned:
        return ""
    return Counter(cleaned).most_common(1)[0][0]


def split_values(value: Any) -> List[str]:
    if pd.isna(value) or str(value) == "":
        return []
    return [v for v in str(value).split(";") if v]


def add_or_update_edge(graph: nx.Graph, u: str, v: str, year: Any, work_id: str) -> None:
    if u == v:
        return
    if graph.has_edge(u, v):
        graph[u][v]["weight"] += 1
        graph[u][v]["work_count"] += 1
        graph[u][v]["years_set"].add(str(year))
        graph[u][v]["works_set"].add(work_id)
    else:
        graph.add_edge(
            u,
            v,
            weight=1,
            work_count=1,
            years_set={str(year)},
            works_set={work_id},
        )


def finalize_graph(graph: nx.Graph) -> nx.Graph:
    for _, _, data in graph.edges(data=True):
        data["years"] = semicolon_join(data.pop("years_set", []))
        data["work_ids"] = semicolon_join(data.pop("works_set", []))
        data["distance"] = 1 / data["weight"] if data["weight"] else 1
    return graph


def write_graph_tables(graph: nx.Graph, node_path, edge_path) -> None:
    nodes = []
    for node, data in graph.nodes(data=True):
        row = {"id": node}
        row.update(data)
        nodes.append(row)
    edges = []
    for u, v, data in graph.edges(data=True):
        row = {"source": u, "target": v}
        row.update(data)
        edges.append(row)
    pd.DataFrame(nodes).to_csv(node_path, index=False)
    pd.DataFrame(edges).to_csv(edge_path, index=False)


def load_institution_lookup() -> Dict[str, Dict[str, Any]]:
    path = DATA_PROCESSED / "institutions.csv"
    if not path.exists():
        return {}
    institutions = pd.read_csv(path).fillna("")
    return {
        str(row["institution_id"]): {
            "institution_id": str(row["institution_id"]),
            "institution_display_name": row.get("institution_display_name", ""),
            "institution_type": row.get("institution_type", ""),
            "institution_country_code": row.get("institution_country_code", ""),
            "simplified_institution_category": row.get("simplified_institution_category", "unknown") or "unknown",
            "target_firm_label": row.get("target_firm_label", "Other") or "Other",
        }
        for _, row in institutions.iterrows()
        if str(row.get("institution_id", "")) != ""
    }


def category_pattern(categories: Iterable[Any]) -> str:
    cats = {str(c) for c in categories if pd.notna(c) and str(c) not in {"", "unknown"}}
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


def author_year_attrs(author_id: str, group: pd.DataFrame, ay_lookup: Dict[Tuple[str, int], Dict[str, Any]], year: int) -> Dict[str, Any]:
    row = ay_lookup.get((author_id, year), {})
    category = row.get("primary_category_for_display_this_year", "unknown") or "unknown"
    firm = row.get("primary_target_firm_for_display_this_year", "Other") or "Other"
    return {
        "author_id": author_id,
        "display_name": row.get("author_name") or first_mode(group["author_display_name"]),
        "main_institution_name": row.get("primary_institution_for_display_this_year", ""),
        "main_institution_id": row.get("primary_institution_id_for_display_this_year", ""),
        "main_institution_type": row.get("primary_institution_type_for_display_this_year", ""),
        "simplified_institution_category": category,
        "target_firm_label": firm,
        "primary_institution_for_display_this_year": row.get("primary_institution_for_display_this_year", ""),
        "primary_category_for_display_this_year": category,
        "primary_target_firm_for_display_this_year": firm,
        "all_institution_names_this_year": row.get("all_institution_names_this_year", ""),
        "all_target_firm_labels_this_year": row.get("all_target_firm_labels_this_year", ""),
        "has_multiple_affiliations_this_year": bool(row.get("has_multiple_affiliations_this_year", False)),
        "has_multiple_categories_this_year": bool(row.get("has_multiple_categories_this_year", False)),
        "publication_count": int(group["work_id"].nunique()),
        "year_list": str(year),
    }


def full_author_attrs(author_id: str, group: pd.DataFrame, author_years: pd.DataFrame, observed: pd.DataFrame) -> Dict[str, Any]:
    if not author_years.empty:
        author_years = author_years.sort_values("year")
    latest = author_years.iloc[-1].to_dict() if not author_years.empty else {}

    if observed.empty:
        dominant = {}
        all_names: List[str] = []
        all_categories: List[str] = ["unknown"]
        all_firms: List[str] = []
    else:
        counts = (
            observed.groupby("institution_id")
            .agg(
                work_count=("work_id", "nunique"),
                institution_name=("institution_name", "first"),
                institution_type=("institution_type", "first"),
                category=("simplified_institution_category", "first"),
                firm=("target_firm_label", "first"),
            )
            .sort_values(["work_count", "institution_name"], ascending=[False, True])
        )
        dominant = counts.iloc[0].to_dict()
        dominant["institution_id"] = counts.index[0]
        all_names = sorted(set(observed["institution_name"].dropna().astype(str)))
        all_categories = sorted(set(observed["simplified_institution_category"].dropna().astype(str)))
        all_firms = sorted(set(observed["target_firm_label"].dropna().astype(str)))

    yearly_categories = [
        str(v)
        for v in author_years.get("primary_category_for_display_this_year", pd.Series(dtype=str)).tolist()
        if str(v) != ""
    ]
    yearly_affiliations = [
        str(v)
        for v in author_years.get("primary_institution_for_display_this_year", pd.Series(dtype=str)).tolist()
        if str(v) != ""
    ]
    observed_years = semicolon_join(author_years["year"].tolist()) if not author_years.empty else semicolon_join(group["publication_year"])

    latest_category = latest.get("primary_category_for_display_this_year", "unknown") or "unknown"
    latest_firm = latest.get("primary_target_firm_for_display_this_year", "Other") or "Other"
    return {
        "author_id": author_id,
        "display_name": latest.get("author_name") or first_mode(group["author_display_name"]),
        "main_institution_name": latest.get("primary_institution_for_display_this_year", ""),
        "main_institution_id": latest.get("primary_institution_id_for_display_this_year", ""),
        "main_institution_type": latest.get("primary_institution_type_for_display_this_year", ""),
        "simplified_institution_category": latest_category,
        "target_firm_label": latest_firm,
        "latest_institution_for_display": latest.get("primary_institution_for_display_this_year", ""),
        "latest_category_for_display": latest_category,
        "latest_target_firm_for_display": latest_firm,
        "dominant_institution_for_display": dominant.get("institution_name", ""),
        "dominant_category_for_display": dominant.get("category", "unknown"),
        "dominant_target_firm_for_display": dominant.get("firm", "Other"),
        "all_institution_names_2022_2025": semicolon_join(all_names),
        "all_categories_2022_2025": semicolon_join(all_categories),
        "all_target_firms_2022_2025": semicolon_join(all_firms),
        "affiliation_category_pattern": category_pattern(all_categories),
        "has_affiliation_change_across_years": len(set(yearly_affiliations)) > 1,
        "has_category_change_across_years": len({c for c in yearly_categories if c}) > 1,
        "observed_years": observed_years,
        "publication_count": int(group["work_id"].nunique()),
        "year_list": semicolon_join(group["publication_year"]),
    }


def build_full_author_attr_lookup(
    authorships: pd.DataFrame,
    author_year: pd.DataFrame,
    long_df: pd.DataFrame,
) -> Dict[str, Dict[str, Any]]:
    base = (
        authorships.groupby("author_id")
        .agg(
            display_name=("author_display_name", first_mode),
            publication_count=("work_id", "nunique"),
            year_list=("publication_year", semicolon_join),
        )
        .reset_index()
    )

    if author_year.empty:
        latest = pd.DataFrame(columns=["author_id"])
    else:
        latest = (
            author_year.sort_values(["author_id", "year"])
            .drop_duplicates("author_id", keep="last")
            .rename(
                columns={
                    "author_name": "latest_author_name",
                    "primary_institution_for_display_this_year": "latest_institution_for_display",
                    "primary_institution_id_for_display_this_year": "latest_institution_id_for_display",
                    "primary_institution_type_for_display_this_year": "latest_institution_type_for_display",
                    "primary_category_for_display_this_year": "latest_category_for_display",
                    "primary_target_firm_for_display_this_year": "latest_target_firm_for_display",
                }
            )
        )

    if long_df.empty:
        observed_summary = pd.DataFrame(columns=["author_id"])
        dominant = pd.DataFrame(columns=["author_id"])
    else:
        observed_summary = (
            long_df.groupby("author_id")
            .agg(
                all_institution_names_2022_2025=("institution_name", semicolon_join),
                all_categories_2022_2025=("simplified_institution_category", semicolon_join),
                all_target_firms_2022_2025=("target_firm_label", semicolon_join),
            )
            .reset_index()
        )
        observed_summary["affiliation_category_pattern"] = observed_summary[
            "all_categories_2022_2025"
        ].apply(lambda x: category_pattern(split_values(x)))

        dominant_counts = (
            long_df.groupby(["author_id", "institution_id"])
            .agg(
                work_count=("work_id", "nunique"),
                dominant_institution_for_display=("institution_name", "first"),
                dominant_category_for_display=("simplified_institution_category", "first"),
                dominant_target_firm_for_display=("target_firm_label", "first"),
            )
            .reset_index()
            .sort_values(["author_id", "work_count", "dominant_institution_for_display"], ascending=[True, False, True])
            .drop_duplicates("author_id", keep="first")
        )
        dominant = dominant_counts[
            [
                "author_id",
                "dominant_institution_for_display",
                "dominant_category_for_display",
                "dominant_target_firm_for_display",
            ]
        ]

    if author_year.empty:
        change = pd.DataFrame(columns=["author_id"])
    else:
        change = (
            author_year.groupby("author_id")
            .agg(
                observed_years=("year", semicolon_join),
                has_affiliation_change_across_years=(
                    "primary_institution_for_display_this_year",
                    lambda s: len({str(v) for v in s if str(v) != ""}) > 1,
                ),
                has_category_change_across_years=(
                    "primary_category_for_display_this_year",
                    lambda s: len({str(v) for v in s if str(v) != ""}) > 1,
                ),
            )
            .reset_index()
        )

    merged = base.merge(latest, on="author_id", how="left")
    merged = merged.merge(observed_summary, on="author_id", how="left")
    merged = merged.merge(dominant, on="author_id", how="left")
    merged = merged.merge(change, on="author_id", how="left")
    merged = merged.fillna("")

    attrs = {}
    for _, row in merged.iterrows():
        latest_category = row.get("latest_category_for_display") or "unknown"
        latest_firm = row.get("latest_target_firm_for_display") or "Other"
        all_categories = row.get("all_categories_2022_2025") or "unknown"
        attrs[str(row["author_id"])] = {
            "author_id": str(row["author_id"]),
            "display_name": row.get("latest_author_name") or row.get("display_name", ""),
            "main_institution_name": row.get("latest_institution_for_display", ""),
            "main_institution_id": row.get("latest_institution_id_for_display", ""),
            "main_institution_type": row.get("latest_institution_type_for_display", ""),
            "simplified_institution_category": latest_category,
            "target_firm_label": latest_firm,
            "latest_institution_for_display": row.get("latest_institution_for_display", ""),
            "latest_category_for_display": latest_category,
            "latest_target_firm_for_display": latest_firm,
            "dominant_institution_for_display": row.get("dominant_institution_for_display", ""),
            "dominant_category_for_display": row.get("dominant_category_for_display", "unknown") or "unknown",
            "dominant_target_firm_for_display": row.get("dominant_target_firm_for_display", "Other") or "Other",
            "all_institution_names_2022_2025": row.get("all_institution_names_2022_2025", ""),
            "all_categories_2022_2025": all_categories,
            "all_target_firms_2022_2025": row.get("all_target_firms_2022_2025", ""),
            "affiliation_category_pattern": row.get("affiliation_category_pattern") or category_pattern(split_values(all_categories)),
            "has_affiliation_change_across_years": bool(row.get("has_affiliation_change_across_years", False)),
            "has_category_change_across_years": bool(row.get("has_category_change_across_years", False)),
            "observed_years": row.get("observed_years") or row.get("year_list", ""),
            "publication_count": int(row.get("publication_count", 0)),
            "year_list": row.get("year_list", ""),
        }
    return attrs


def build_researcher_graph(
    authorships: pd.DataFrame,
    author_year: pd.DataFrame,
    long_df: pd.DataFrame,
    year: Any = None,
) -> nx.Graph:
    cfg = load_config()
    threshold = int(cfg.get("max_authors_per_paper_for_pairwise_edges", 50))
    if year != "full":
        year = int(year)
        active_authorships = authorships[authorships["publication_year"] == year]
    else:
        active_authorships = authorships

    ay_lookup = {
        (str(row["author_id"]), int(row["year"])): row.to_dict()
        for _, row in author_year.iterrows()
    } if not author_year.empty else {}
    full_attr_lookup = {}
    if year == "full":
        full_attr_lookup = build_full_author_attr_lookup(active_authorships, author_year, long_df)

    graph = nx.Graph()
    for author_id, group in active_authorships.groupby("author_id"):
        if not author_id or pd.isna(author_id):
            continue
        if year == "full":
            attrs = full_attr_lookup.get(str(author_id), {})
        else:
            attrs = author_year_attrs(str(author_id), group, ay_lookup, int(year))
        graph.add_node(str(author_id), **attrs)

    skipped = 0
    for work_id, group in active_authorships.groupby("work_id"):
        paper_year = first_mode(group["publication_year"])
        author_ids = sorted(set(str(a) for a in group["author_id"] if pd.notna(a) and str(a) != ""))
        if len(author_ids) > threshold:
            skipped += 1
            continue
        for u, v in itertools.combinations(author_ids, 2):
            add_or_update_edge(graph, u, v, paper_year, str(work_id))
    graph.graph["skipped_large_author_papers"] = skipped
    return finalize_graph(graph)


def build_institution_graph(
    long_df: pd.DataFrame,
    institution_lookup: Dict[str, Dict[str, Any]],
    year: Any = None,
) -> Tuple[nx.Graph, int]:
    if year != "full":
        long_df = long_df[long_df["publication_year"] == int(year)]

    graph = nx.Graph()
    for inst_id, group in long_df.groupby("institution_id"):
        if not inst_id or str(inst_id) == "":
            continue
        inst = institution_lookup.get(
            str(inst_id),
            {
                "institution_id": str(inst_id),
                "institution_display_name": first_mode(group["institution_name"]),
                "institution_type": first_mode(group["institution_type"]),
                "institution_country_code": first_mode(group.get("institution_country_code", pd.Series([""]))),
                "simplified_institution_category": first_mode(group["simplified_institution_category"]) or "unknown",
                "target_firm_label": first_mode(group["target_firm_label"]) or "Other",
            },
        )
        graph.add_node(
            str(inst_id),
            institution_id=str(inst_id),
            institution_name=inst["institution_display_name"],
            institution_type=inst["institution_type"],
            simplified_institution_category=inst["simplified_institution_category"],
            target_firm_label=inst["target_firm_label"],
            country_code=inst.get("institution_country_code", ""),
            publication_count=int(group["work_id"].nunique()),
        )

    self_institution_collaboration_count = 0
    for work_id, group in long_df.groupby("work_id"):
        paper_year = first_mode(group["publication_year"])
        inst_ids = sorted(set(str(i) for i in group["institution_id"] if pd.notna(i) and str(i) != ""))
        if len(inst_ids) == 1:
            self_institution_collaboration_count += 1
            continue
        for u, v in itertools.combinations(inst_ids, 2):
            add_or_update_edge(graph, u, v, paper_year, str(work_id))
    return finalize_graph(graph), self_institution_collaboration_count


def build_all() -> None:
    ensure_dirs()
    authorships = pd.read_csv(DATA_PROCESSED / "authorships.csv").fillna("")
    author_year = pd.read_csv(OUTPUTS / "tables" / "author_year_affiliations.csv").fillna("")
    long_df = pd.read_csv(OUTPUTS / "tables" / "authorship_affiliations_long.csv").fillna("")
    institution_lookup = load_institution_lookup()
    years = ["full"] + list(range(int(load_config()["start_year"]), int(load_config()["end_year"]) + 1))
    counts: Dict[str, Any] = {}

    for label in years:
        researcher = build_researcher_graph(authorships, author_year, long_df, label)
        institution, self_count = build_institution_graph(long_df, institution_lookup, label)

        write_graph_tables(
            researcher,
            OUTPUTS / "networks" / f"researcher_nodes_{label}.csv",
            OUTPUTS / "networks" / f"researcher_edges_{label}.csv",
        )
        write_graph_tables(
            institution,
            OUTPUTS / "networks" / f"institution_nodes_{label}.csv",
            OUTPUTS / "networks" / f"institution_edges_{label}.csv",
        )
        nx.write_gexf(researcher, OUTPUTS / "gephi" / f"researcher_{label}.gexf")
        nx.write_gexf(institution, OUTPUTS / "gephi" / f"institution_{label}.gexf")
        counts[str(label)] = {
            "researcher_nodes": researcher.number_of_nodes(),
            "researcher_edges": researcher.number_of_edges(),
            "institution_nodes": institution.number_of_nodes(),
            "institution_edges": institution.number_of_edges(),
            "self_institution_collaboration_count": self_count,
            "skipped_large_author_papers": researcher.graph.get("skipped_large_author_papers", 0),
        }
        print(label, counts[str(label)])

    with open(OUTPUTS / "networks" / "network_build_summary.json", "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)


if __name__ == "__main__":
    build_all()
