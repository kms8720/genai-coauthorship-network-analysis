from __future__ import annotations

import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from common import OUTPUTS, ensure_dirs


CATEGORY_COLORS = {
    "company": "#E15759",
    "education": "#4E79A7",
    "research_institute": "#59A14F",
    "government": "#F28E2B",
    "nonprofit": "#B07AA1",
    "healthcare": "#76B7B2",
    "other": "#9D9D9D",
    "unknown": "#9D9D9D",
    "company_only": "#E15759",
    "education_only": "#4E79A7",
    "research_institute_only": "#59A14F",
    "company_plus_education": "#B07AA1",
    "company_plus_research_institute": "#F28E2B",
    "multiple_categories": "#76B7B2",
}

TARGET_AI_FIRMS = {
    "OpenAI",
    "Anthropic",
    "Google / Google DeepMind / DeepMind",
    "Microsoft",
    "Meta",
    "NVIDIA",
    "Salesforce",
    "Amazon",
}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path).fillna("") if path.exists() else pd.DataFrame()


def load_graph(kind: str) -> nx.Graph:
    nodes = read_csv(OUTPUTS / "networks" / f"{kind}_nodes_full.csv")
    edges = read_csv(OUTPUTS / "networks" / f"{kind}_edges_full.csv")
    graph = nx.Graph()
    for _, row in nodes.iterrows():
        node_id = str(row["id"])
        graph.add_node(node_id, **{k: row[k] for k in nodes.columns if k != "id"})
    for _, row in edges.iterrows():
        graph.add_edge(
            str(row["source"]),
            str(row["target"]),
            weight=float(row.get("weight", 1) or 1),
            distance=float(row.get("distance", 1) or 1),
            work_count=float(row.get("work_count", 1) or 1),
        )
    return graph


def largest_component_subgraph(graph: nx.Graph) -> nx.Graph:
    if graph.number_of_nodes() == 0:
        return graph.copy()
    component = max(nx.connected_components(graph), key=len)
    return graph.subgraph(component).copy()


def weighted_degree(graph: nx.Graph) -> Dict[str, float]:
    return dict(graph.degree(weight="weight"))


def top_nodes_by_attr(graph: nx.Graph, attr: str, n: int) -> Set[str]:
    ranked = sorted(
        graph.nodes,
        key=lambda node: float(graph.nodes[node].get(attr, 0) or 0),
        reverse=True,
    )
    return set(ranked[:n])


def target_firm_nodes(graph: nx.Graph) -> Set[str]:
    return {
        node
        for node, data in graph.nodes(data=True)
        if data.get("target_firm_label") in TARGET_AI_FIRMS
        or data.get("institution_name") in TARGET_AI_FIRMS
        or data.get("latest_target_firm_for_display") in TARGET_AI_FIRMS
    }


def label_for_node(graph: nx.Graph, node: str) -> str:
    data = graph.nodes[node]
    return (
        str(data.get("institution_name") or "")
        or str(data.get("display_name") or "")
        or str(data.get("latest_institution_for_display") or "")
        or str(node)
    )


def color_for_node(graph: nx.Graph, node: str, attr: str = "simplified_institution_category") -> str:
    value = str(graph.nodes[node].get(attr, "unknown") or "unknown")
    return CATEGORY_COLORS.get(value, "#9D9D9D")


def edge_width(weight: float) -> float:
    return 0.4 + math.log1p(max(float(weight), 0)) * 0.8


def node_size_from_attr(graph: nx.Graph, node: str, attr: str, base: float = 120, scale: float = 7000) -> float:
    value = float(graph.nodes[node].get(attr, 0) or 0)
    return base + scale * value


def add_category_legend(ax, categories: Iterable[str]) -> None:
    handles = []
    labels = []
    for cat in sorted(set(categories)):
        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=CATEGORY_COLORS.get(cat, "#9D9D9D"),
                markersize=9,
            )
        )
        labels.append(cat)
    if handles:
        ax.legend(handles, labels, loc="lower left", frameon=False, fontsize=9)


def draw_graph(
    graph: nx.Graph,
    labels: Dict[str, str],
    title: str,
    output_stem: str,
    color_attr: str = "simplified_institution_category",
    size_attr: str = "betweenness_centrality",
    figsize: Tuple[int, int] = (16, 12),
    pos: Dict[str, Tuple[float, float]] | None = None,
    edge_alpha: float = 0.25,
    seed: int = 42,
) -> Dict[str, object]:
    if graph.number_of_nodes() == 0:
        return {"nodes": 0, "edges": 0, "labels": []}
    if pos is None:
        pos = nx.spring_layout(graph, seed=seed, weight="weight", k=1.2 / math.sqrt(max(graph.number_of_nodes(), 1)))
    fig, ax = plt.subplots(figsize=figsize)
    widths = [edge_width(data.get("weight", 1)) for _, _, data in graph.edges(data=True)]
    nx.draw_networkx_edges(graph, pos, width=widths, alpha=edge_alpha, edge_color="#555555", ax=ax)
    colors = [color_for_node(graph, node, color_attr) for node in graph.nodes]
    sizes = [node_size_from_attr(graph, node, size_attr) for node in graph.nodes]
    nx.draw_networkx_nodes(graph, pos, node_color=colors, node_size=sizes, alpha=0.9, linewidths=0.3, edgecolors="white", ax=ax)
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8, font_color="#202020", ax=ax)
    ax.set_title(title, fontsize=16, pad=12)
    ax.axis("off")
    add_category_legend(ax, [str(graph.nodes[n].get(color_attr, "unknown") or "unknown") for n in graph.nodes])
    fig.tight_layout()
    png = OUTPUTS / "figures" / f"{output_stem}.png"
    pdf = OUTPUTS / "figures" / f"{output_stem}.pdf"
    fig.savefig(png, dpi=260)
    fig.savefig(pdf)
    plt.close(fig)
    return {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "labels": list(labels.values())}


def keep_top_edges(graph: nx.Graph, n: int) -> nx.Graph:
    if graph.number_of_edges() <= n:
        return graph.copy()
    edges = sorted(graph.edges(data=True), key=lambda e: float(e[2].get("weight", 0) or 0), reverse=True)[:n]
    kept = nx.Graph()
    for u, v, data in edges:
        kept.add_node(u, **graph.nodes[u])
        kept.add_node(v, **graph.nodes[v])
        kept.add_edge(u, v, **data)
    return kept


def institution_backbone(inst_graph: nx.Graph) -> Dict[str, object]:
    graph = largest_component_subgraph(inst_graph)
    keep = top_nodes_by_attr(graph, "weighted_degree", 100) | top_nodes_by_attr(graph, "betweenness_centrality", 100) | target_firm_nodes(graph)
    sub = graph.subgraph(keep).copy()
    filtered = nx.Graph()
    target_nodes = target_firm_nodes(sub)
    for u, v, data in sub.edges(data=True):
        weight = float(data.get("weight", 1) or 1)
        ucat = sub.nodes[u].get("simplified_institution_category", "unknown")
        vcat = sub.nodes[v].get("simplified_institution_category", "unknown")
        target_academic = (
            (u in target_nodes and vcat in {"education", "research_institute"})
            or (v in target_nodes and ucat in {"education", "research_institute"})
        )
        if weight >= 2 or target_academic:
            filtered.add_node(u, **sub.nodes[u])
            filtered.add_node(v, **sub.nodes[v])
            filtered.add_edge(u, v, **data)
    filtered = keep_top_edges(filtered, 300)
    top_bet = top_nodes_by_attr(filtered, "betweenness_centrality", 25)
    labels = {n: label_for_node(filtered, n) for n in top_bet | target_firm_nodes(filtered)}
    return draw_graph(
        filtered,
        labels,
        "Institution Collaboration Backbone",
        "report_institution_backbone",
        figsize=(16, 12),
        edge_alpha=0.22,
    )


def company_academic_subnetwork(inst_graph: nx.Graph) -> Dict[str, object]:
    candidate_edges = []
    company_weight = defaultdict(float)
    academic_weight = defaultdict(float)
    target_nodes = target_firm_nodes(inst_graph)
    for u, v, data in inst_graph.edges(data=True):
        ucat = inst_graph.nodes[u].get("simplified_institution_category", "unknown")
        vcat = inst_graph.nodes[v].get("simplified_institution_category", "unknown")
        if {ucat, vcat} & {"company"} and ({ucat, vcat} & {"education", "research_institute"}):
            weight = float(data.get("weight", 1) or 1)
            candidate_edges.append((u, v, data))
            if ucat == "company":
                company_weight[u] += weight
                academic_weight[v] += weight
            else:
                company_weight[v] += weight
                academic_weight[u] += weight
    top_companies = {n for n, _ in sorted(company_weight.items(), key=lambda x: x[1], reverse=True)[:50]} | target_nodes
    top_academic = {n for n, _ in sorted(academic_weight.items(), key=lambda x: x[1], reverse=True)[:50]}
    graph = nx.Graph()
    for u, v, data in candidate_edges:
        if (u in top_companies and v in top_academic) or (v in top_companies and u in top_academic):
            graph.add_node(u, **inst_graph.nodes[u])
            graph.add_node(v, **inst_graph.nodes[v])
            graph.add_edge(u, v, **data)
    graph = keep_top_edges(graph, 250)
    left = [n for n in graph.nodes if graph.nodes[n].get("simplified_institution_category") == "company"]
    right = [n for n in graph.nodes if n not in left]
    pos = {}
    for idx, node in enumerate(sorted(left, key=lambda n: -company_weight.get(n, 0))):
        pos[node] = (-1.0, idx / max(len(left) - 1, 1) * 2 - 1)
    for idx, node in enumerate(sorted(right, key=lambda n: -academic_weight.get(n, 0))):
        pos[node] = (1.0, idx / max(len(right) - 1, 1) * 2 - 1)
    acad_top_labels = set(sorted(right, key=lambda n: graph.degree(n, weight="weight"), reverse=True)[:30])
    labels = {n: label_for_node(graph, n) for n in set(left) | acad_top_labels}
    result = draw_graph(
        graph,
        labels,
        "Company–University/Research Institute Collaboration Backbone",
        "report_company_academic_subnetwork",
        figsize=(16, 12),
        pos=pos,
        edge_alpha=0.25,
    )
    result["target_firms_present"] = sorted({label_for_node(graph, n) for n in target_nodes if n in graph})
    return result


def bridge_institution_ego(inst_graph: nx.Graph) -> Dict[str, object]:
    bridges = read_csv(OUTPUTS / "tables" / "potential_bridge_institutions.csv").head(10)
    bridge_nodes = [str(v) for v in bridges["id"].tolist()]
    graph = nx.Graph()
    for node in bridge_nodes:
        if node not in inst_graph:
            continue
        graph.add_node(node, **inst_graph.nodes[node])
        neighbors = sorted(inst_graph[node].items(), key=lambda item: float(item[1].get("weight", 0) or 0), reverse=True)[:10]
        for nbr, data in neighbors:
            graph.add_node(nbr, **inst_graph.nodes[nbr])
            graph.add_edge(node, nbr, **data)
    graph = keep_top_edges(graph, 150)
    bridge_set = set(bridge_nodes) & set(graph.nodes)
    top_neighbors = set(sorted(graph.nodes, key=lambda n: graph.degree(n, weight="weight"), reverse=True)[:20])
    labels = {n: label_for_node(graph, n) for n in bridge_set | target_firm_nodes(graph) | top_neighbors}
    result = draw_graph(
        graph,
        labels,
        "Ego Network of Top Bridge Institutions",
        "report_bridge_institution_ego_network",
        figsize=(16, 12),
        edge_alpha=0.28,
    )
    return result


def bridge_researcher_ego(researcher_graph: nx.Graph) -> Dict[str, object]:
    bridges = read_csv(OUTPUTS / "tables" / "potential_bridge_researchers.csv").head(10)
    bridge_nodes = [str(v) for v in bridges["id"].tolist()]
    graph = nx.Graph()
    for node in bridge_nodes:
        if node not in researcher_graph:
            continue
        graph.add_node(node, **researcher_graph.nodes[node])
        neighbors = sorted(researcher_graph[node].items(), key=lambda item: float(item[1].get("weight", 0) or 0), reverse=True)[:10]
        for nbr, data in neighbors:
            graph.add_node(nbr, **researcher_graph.nodes[nbr])
            graph.add_edge(node, nbr, **data)
    graph = keep_top_edges(graph, 150)
    bridge_set = set(bridge_nodes) & set(graph.nodes)
    top_coauthors = set(sorted(graph.nodes, key=lambda n: graph.degree(n, weight="weight"), reverse=True)[:20])
    labels = {n: label_for_node(graph, n) for n in bridge_set | top_coauthors}
    return draw_graph(
        graph,
        labels,
        "Ego Network of Top Bridge Researchers",
        "report_bridge_researcher_ego_network",
        color_attr="affiliation_category_pattern",
        figsize=(16, 12),
        edge_alpha=0.25,
    )


def community_level_institution_network(inst_graph: nx.Graph) -> Dict[str, object]:
    try:
        import community as community_louvain

        partition = community_louvain.best_partition(inst_graph, weight="weight", random_state=42)
    except Exception:
        partition = {}
        for idx, nodes in enumerate(nx.algorithms.community.greedy_modularity_communities(inst_graph, weight="weight")):
            for node in nodes:
                partition[node] = idx
    wd = weighted_degree(inst_graph)
    rows = []
    for node, community_id in partition.items():
        data = inst_graph.nodes[node]
        rows.append(
            {
                "institution_id": node,
                "institution_name": label_for_node(inst_graph, node),
                "community_id": community_id,
                "simplified_institution_category": data.get("simplified_institution_category", "unknown"),
                "target_firm_label": data.get("target_firm_label", "Other"),
                "weighted_degree": wd.get(node, 0),
                "betweenness_centrality": float(data.get("betweenness_centrality", 0) or 0),
            }
        )
    communities = pd.DataFrame(rows)
    communities.to_csv(OUTPUTS / "tables" / "institution_communities.csv", index=False)
    comm_graph = nx.Graph()
    for community_id, group in communities.groupby("community_id"):
        categories = Counter(group["simplified_institution_category"])
        top = group.sort_values(["betweenness_centrality", "weighted_degree"], ascending=False).head(3)
        comm_graph.add_node(
            str(community_id),
            community_id=int(community_id),
            institution_count=int(len(group)),
            weighted_degree=float(group["weighted_degree"].sum()),
            dominant_category=categories.most_common(1)[0][0],
            label=f"Community {community_id}: " + ", ".join(top["institution_name"].tolist()),
        )
    edge_weights = defaultdict(float)
    for u, v, data in inst_graph.edges(data=True):
        cu, cv = str(partition[u]), str(partition[v])
        if cu == cv:
            continue
        a, b = sorted([cu, cv])
        edge_weights[(a, b)] += float(data.get("weight", 1) or 1)
    edge_rows = []
    for (a, b), weight in edge_weights.items():
        edge_rows.append({"source_community": a, "target_community": b, "weight": weight})
        comm_graph.add_edge(a, b, weight=weight)
    pd.DataFrame(edge_rows).sort_values("weight", ascending=False).to_csv(
        OUTPUTS / "tables" / "institution_community_edges.csv", index=False
    )
    top_communities = set(
        sorted(comm_graph.nodes, key=lambda n: comm_graph.nodes[n]["institution_count"], reverse=True)[:20]
    ) | set(sorted(comm_graph.nodes, key=lambda n: comm_graph.nodes[n]["weighted_degree"], reverse=True)[:20])
    sub = comm_graph.subgraph(top_communities).copy()
    sub = keep_top_edges(sub, 80)
    labels = {n: sub.nodes[n]["label"] for n in sub.nodes}
    for n in sub.nodes:
        sub.nodes[n]["simplified_institution_category"] = sub.nodes[n].get("dominant_category", "unknown")
        sub.nodes[n]["betweenness_centrality"] = sub.nodes[n].get("institution_count", 1) / max(communities["community_id"].value_counts().max(), 1)
    return draw_graph(
        sub,
        labels,
        "Community-Level Institution Collaboration Network",
        "report_institution_community_network",
        figsize=(18, 12),
        edge_alpha=0.3,
    )


def overview_figures(inst_graph: nx.Graph, researcher_graph: nx.Graph) -> Dict[str, Dict[str, object]]:
    results = {}
    for kind, graph, output, title, color_attr in [
        (
            "researcher",
            researcher_graph,
            "researcher_network_full_overview",
            "Researcher Network Full Overview\nLabels show top betweenness nodes only; full network shown for structural overview.",
            "affiliation_category_pattern",
        ),
        (
            "institution",
            inst_graph,
            "institution_network_full_overview",
            "Institution Network Full Overview\nLabels show top betweenness nodes only; full network shown for structural overview.",
            "simplified_institution_category",
        ),
    ]:
        ranked = sorted(graph.nodes, key=lambda n: graph.degree(n, weight="weight"), reverse=True)[:300]
        sub = graph.subgraph(ranked).copy()
        labels = {n: label_for_node(sub, n) for n in top_nodes_by_attr(sub, "betweenness_centrality", 20)}
        results[kind] = draw_graph(
            sub,
            labels,
            title,
            output,
            color_attr=color_attr,
            figsize=(16, 12),
            edge_alpha=0.08,
        )
    return results


def main() -> None:
    ensure_dirs()
    inst_graph = load_graph("institution")
    researcher_graph = load_graph("researcher")
    validation = {
        "report_institution_backbone": institution_backbone(inst_graph),
        "report_company_academic_subnetwork": company_academic_subnetwork(inst_graph),
        "report_bridge_institution_ego_network": bridge_institution_ego(inst_graph),
        "report_bridge_researcher_ego_network": bridge_researcher_ego(researcher_graph),
        "report_institution_community_network": community_level_institution_network(inst_graph),
    }
    validation.update({f"{k}_network_full_overview": v for k, v in overview_figures(inst_graph, researcher_graph).items()})
    with open(OUTPUTS / "figures" / "report_ready_visualization_summary.json", "w", encoding="utf-8") as f:
        json.dump(validation, f, indent=2, ensure_ascii=False)
    for name, info in validation.items():
        print(name)
        print("  nodes:", info.get("nodes"), "edges:", info.get("edges"))
        print("  labeled nodes:", len(info.get("labels", [])))
        print("  labels:", "; ".join(info.get("labels", [])[:40]))
        if "target_firms_present" in info:
            print("  target AI firms present:", "; ".join(info["target_firms_present"]))


if __name__ == "__main__":
    main()
