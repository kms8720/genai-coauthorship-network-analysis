from __future__ import annotations

import itertools
import json
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, Tuple

import networkx as nx
import pandas as pd

from common import DATA_PROCESSED, OUTPUTS, ensure_dirs, load_config, semicolon_join


def first_mode(values: Iterable[Any]) -> str:
    cleaned = [str(v) for v in values if pd.notna(v) and str(v) != ""]
    if not cleaned:
        return ""
    return Counter(cleaned).most_common(1)[0][0]


def representative_institution(group: pd.DataFrame, institution_lookup: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    usable = group[group["institution_id"].astype(str) != ""].copy()
    if usable.empty:
        return {
            "institution_id": "",
            "institution_display_name": "",
            "institution_type": "",
            "institution_country_code": "",
            "simplified_institution_category": "unknown",
            "target_firm_label": "Other",
        }

    counts = (
        usable.groupby("institution_id")
        .agg(work_count=("work_id", "nunique"), row_count=("work_id", "size"))
        .sort_values(["work_count", "row_count"], ascending=False)
    )
    institution_id = str(counts.index[0])
    if institution_id in institution_lookup:
        return institution_lookup[institution_id]

    inst_rows = usable[usable["institution_id"].astype(str) == institution_id]
    return {
        "institution_id": institution_id,
        "institution_display_name": first_mode(inst_rows["institution_display_name"]),
        "institution_type": first_mode(inst_rows["institution_type"]),
        "institution_country_code": first_mode(inst_rows["institution_country_code"]),
        "simplified_institution_category": first_mode(inst_rows["simplified_institution_category"]) or "unknown",
        "target_firm_label": first_mode(inst_rows["target_firm_label"]) or "Other",
    }


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


def build_researcher_graph(
    authorships: pd.DataFrame,
    works: pd.DataFrame,
    institution_lookup: Dict[str, Dict[str, Any]],
    year: Any = None,
) -> nx.Graph:
    cfg = load_config()
    threshold = int(cfg.get("max_authors_per_paper_for_pairwise_edges", 50))
    if year != "full":
        authorships = authorships[authorships["publication_year"] == int(year)]
        works = works[works["publication_year"] == int(year)]

    graph = nx.Graph()
    for author_id, group in authorships.groupby("author_id"):
        if not author_id or pd.isna(author_id):
            continue
        inst = representative_institution(group, institution_lookup)
        graph.add_node(
            author_id,
            author_id=author_id,
            display_name=first_mode(group["author_display_name"]),
            main_institution_name=inst["institution_display_name"],
            main_institution_id=inst["institution_id"],
            main_institution_type=inst["institution_type"],
            simplified_institution_category=inst["simplified_institution_category"],
            target_firm_label=inst["target_firm_label"],
            publication_count=int(group["work_id"].nunique()),
            year_list=semicolon_join(group["publication_year"]),
        )

    skipped = 0
    for work_id, group in authorships.groupby("work_id"):
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
    authorships: pd.DataFrame,
    institution_lookup: Dict[str, Dict[str, Any]],
    year: Any = None,
) -> Tuple[nx.Graph, int]:
    if year != "full":
        authorships = authorships[authorships["publication_year"] == int(year)]

    graph = nx.Graph()
    for inst_id, group in authorships.dropna(subset=["institution_id"]).groupby("institution_id"):
        if not inst_id or str(inst_id) == "":
            continue
        inst = institution_lookup.get(
            str(inst_id),
            {
                "institution_id": str(inst_id),
                "institution_display_name": first_mode(group["institution_display_name"]),
                "institution_type": first_mode(group["institution_type"]),
                "institution_country_code": first_mode(group["institution_country_code"]),
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
            country_code=inst["institution_country_code"],
            publication_count=int(group["work_id"].nunique()),
        )

    self_institution_collaboration_count = 0
    for work_id, group in authorships.groupby("work_id"):
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
    works = pd.read_csv(DATA_PROCESSED / "works.csv")
    authorships = pd.read_csv(DATA_PROCESSED / "authorships.csv").fillna("")
    institution_lookup = load_institution_lookup()
    years = ["full"] + list(range(int(load_config()["start_year"]), int(load_config()["end_year"]) + 1))
    counts: Dict[str, Any] = {}

    for label in years:
        researcher = build_researcher_graph(authorships, works, institution_lookup, label)
        institution, self_count = build_institution_graph(authorships, institution_lookup, label)

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
