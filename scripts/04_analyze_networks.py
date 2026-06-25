from __future__ import annotations

import json
from typing import Any, Dict, List

import networkx as nx
import pandas as pd

from common import OUTPUTS, ensure_dirs, load_config, semicolon_join


def load_graph(kind: str, label: str) -> nx.Graph:
    node_path = OUTPUTS / "networks" / f"{kind}_nodes_{label}.csv"
    edge_path = OUTPUTS / "networks" / f"{kind}_edges_{label}.csv"
    nodes = pd.read_csv(node_path).fillna("") if node_path.exists() else pd.DataFrame()
    edges = pd.read_csv(edge_path).fillna("") if edge_path.exists() else pd.DataFrame()
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
            years=str(row.get("years", "")),
            work_count=int(float(row.get("work_count", 1) or 1)),
        )
    return graph


def community_labels(graph: nx.Graph) -> Dict[str, int]:
    if graph.number_of_nodes() == 0:
        return {}
    try:
        import community as community_louvain

        return community_louvain.best_partition(graph, weight="weight", random_state=42)
    except Exception:
        communities = nx.algorithms.community.asyn_lpa_communities(
            graph, weight="weight", seed=42
        )
        labels = {}
        for idx, community_nodes in enumerate(communities):
            for node in community_nodes:
                labels[node] = idx
        return labels


def exact_betweenness_igraph(graph: nx.Graph) -> Dict[str, float]:
    import igraph as ig

    nodes = list(graph.nodes())
    index = {node: idx for idx, node in enumerate(nodes)}
    edges = [(index[u], index[v]) for u, v in graph.edges()]
    weights = [float(data.get("distance", 1) or 1) for _, _, data in graph.edges(data=True)]
    ig_graph = ig.Graph(n=len(nodes), edges=edges, directed=False)
    raw = ig_graph.betweenness(directed=False, weights=weights)
    n = len(nodes)
    if n <= 2:
        norm = 0
    else:
        norm = 2 / ((n - 1) * (n - 2))
    return {node: value * norm for node, value in zip(nodes, raw)}


def centralities(graph: nx.Graph, kind: str) -> tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    cfg = load_config()
    nodes = list(graph.nodes())
    if not nodes:
        return {}, {"betweenness_method": "none", "betweenness_k": 0}
    degree = nx.degree_centrality(graph)
    weighted_degree = dict(graph.degree(weight="weight"))
    method = "exact"
    k_used = 0
    if graph.number_of_edges() == 0:
        betweenness = {n: 0.0 for n in nodes}
        method = "none_no_edges"
    elif kind == "researcher" and graph.number_of_nodes() > int(cfg.get("max_exact_betweenness_nodes", 1500)):
        k = min(int(cfg.get("approx_betweenness_k", 50)), graph.number_of_nodes())
        k_used = k
        method = "approximate_weighted_brandes_sampling"
        betweenness = nx.betweenness_centrality(
            graph, k=k, weight="distance", seed=int(cfg.get("random_seed", 42))
        )
    else:
        try:
            betweenness = exact_betweenness_igraph(graph)
            method = "exact_weighted_igraph"
        except Exception:
            betweenness = nx.betweenness_centrality(graph, weight="distance")
            method = "exact_weighted_networkx"

    try:
        eigenvector = nx.eigenvector_centrality(graph, weight="weight", max_iter=1000)
    except Exception:
        eigenvector = {n: 0.0 for n in nodes}
        if graph.number_of_edges() > 0:
            largest = graph.subgraph(max(nx.connected_components(graph), key=len)).copy()
            try:
                ev_lcc = nx.eigenvector_centrality(largest, weight="weight", max_iter=2000)
                eigenvector.update(ev_lcc)
            except Exception:
                pass

    communities = community_labels(graph)
    metrics = {
        n: {
            "degree_centrality": degree.get(n, 0.0),
            "weighted_degree": weighted_degree.get(n, 0.0),
            "betweenness_centrality": betweenness.get(n, 0.0),
            "eigenvector_centrality": eigenvector.get(n, 0.0),
            "community": communities.get(n, -1),
        }
        for n in nodes
    }
    return metrics, {
        "betweenness_method": method,
        "betweenness_k": k_used,
        "max_exact_betweenness_nodes": int(cfg.get("max_exact_betweenness_nodes", 1500)),
    }


def graph_summary(graph: nx.Graph, kind: str, label: str) -> Dict[str, Any]:
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()
    components = list(nx.connected_components(graph)) if node_count else []
    largest = max((len(c) for c in components), default=0)
    avg_degree = (sum(dict(graph.degree()).values()) / node_count) if node_count else 0
    return {
        "network": kind,
        "year": label,
        "node_count": node_count,
        "edge_count": edge_count,
        "density": nx.density(graph) if node_count > 1 else 0,
        "average_degree": avg_degree,
        "connected_components": len(components),
        "largest_component_size": largest,
        "share_nodes_largest_component": largest / node_count if node_count else 0,
    }


def attach_metrics_to_node_csv(kind: str, label: str, metrics: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    path = OUTPUTS / "networks" / f"{kind}_nodes_{label}.csv"
    nodes = pd.read_csv(path).fillna("") if path.exists() else pd.DataFrame()
    if nodes.empty:
        return nodes
    metric_df = pd.DataFrame([{"id": k, **v} for k, v in metrics.items()])
    merged = nodes.drop(columns=[c for c in metric_df.columns if c in nodes.columns and c != "id"], errors="ignore")
    merged = merged.merge(metric_df, on="id", how="left")
    merged.to_csv(path, index=False)
    return merged


def neighbor_diversity(graph: nx.Graph, node: str, attr: str) -> int:
    values = {str(graph.nodes[n].get(attr, "")) for n in graph.neighbors(node)}
    values.discard("")
    values.discard("Other")
    values.discard("unknown")
    return len(values)


def institution_type_mixing(graph: nx.Graph, label: str) -> pd.DataFrame:
    rows = []
    for u, v, data in graph.edges(data=True):
        cu = graph.nodes[u].get("simplified_institution_category", "unknown")
        cv = graph.nodes[v].get("simplified_institution_category", "unknown")
        a, b = sorted([str(cu), str(cv)])
        rows.append({"year": label, "category_pair": f"{a}-{b}", "edge_count": 1, "edge_weight": data.get("weight", 1)})
    if not rows:
        return pd.DataFrame(columns=["year", "category_pair", "edge_count", "edge_weight"])
    return pd.DataFrame(rows).groupby(["year", "category_pair"], as_index=False).sum()


def analyze() -> None:
    ensure_dirs()
    cfg = load_config()
    labels = ["full"] + [str(y) for y in range(int(cfg["start_year"]), int(cfg["end_year"]) + 1)]
    summaries: List[Dict[str, Any]] = []
    all_mixing = []
    method_rows = []
    full_researcher_nodes = pd.DataFrame()
    full_institution_nodes = pd.DataFrame()
    full_researcher_graph = None
    full_institution_graph = None

    for label in labels:
        for kind in ["researcher", "institution"]:
            print(f"Analyzing {kind} network: {label}", flush=True)
            graph = load_graph(kind, label)
            metrics, method_info = centralities(graph, kind)
            method_rows.append(
                {
                    "network": kind,
                    "year": label,
                    "node_count": graph.number_of_nodes(),
                    "edge_count": graph.number_of_edges(),
                    **method_info,
                }
            )
            for node, attrs in metrics.items():
                if node in graph:
                    graph.nodes[node].update(attrs)
            nodes_with_metrics = attach_metrics_to_node_csv(kind, label, metrics)
            summaries.append(graph_summary(graph, kind, label))
            pd.DataFrame([{"id": k, **v} for k, v in metrics.items()]).to_csv(
                OUTPUTS / "tables" / f"{kind}_centrality_{label}.csv", index=False
            )
            nx.write_gexf(graph, OUTPUTS / "gephi" / f"{kind}_{label}.gexf")
            if kind == "institution":
                all_mixing.append(institution_type_mixing(graph, label))
            if label == "full" and kind == "researcher":
                full_researcher_nodes = nodes_with_metrics
                full_researcher_graph = graph
            if label == "full" and kind == "institution":
                full_institution_nodes = nodes_with_metrics
                full_institution_graph = graph

    pd.DataFrame(summaries).to_csv(OUTPUTS / "tables" / "network_summary_by_year.csv", index=False)
    pd.DataFrame(method_rows).to_csv(OUTPUTS / "tables" / "centrality_method_summary.csv", index=False)
    pd.concat(all_mixing, ignore_index=True).to_csv(
        OUTPUTS / "tables" / "institution_type_edge_mixing.csv", index=False
    )

    top_specs = [
        (full_researcher_nodes, "degree_centrality", "top_researchers_degree.csv"),
        (full_researcher_nodes, "betweenness_centrality", "top_researchers_betweenness.csv"),
        (full_researcher_nodes, "eigenvector_centrality", "top_researchers_eigenvector.csv"),
        (full_institution_nodes, "degree_centrality", "top_institutions_degree.csv"),
        (full_institution_nodes, "betweenness_centrality", "top_institutions_betweenness.csv"),
    ]
    for df, column, filename in top_specs:
        if df.empty or column not in df:
            pd.DataFrame().to_csv(OUTPUTS / "tables" / filename, index=False)
        else:
            df.sort_values(column, ascending=False).head(30).to_csv(OUTPUTS / "tables" / filename, index=False)

    if full_institution_graph is not None:
        firm_edges = []
        firm_univ_edges = []
        for u, v, data in full_institution_graph.edges(data=True):
            nu, nv = full_institution_graph.nodes[u], full_institution_graph.nodes[v]
            fu, fv = nu.get("target_firm_label", "Other"), nv.get("target_firm_label", "Other")
            cu, cv = nu.get("simplified_institution_category", "unknown"), nv.get("simplified_institution_category", "unknown")
            row = {
                "source": u,
                "target": v,
                "source_name": nu.get("institution_name", ""),
                "target_name": nv.get("institution_name", ""),
                "source_category": cu,
                "target_category": cv,
                "source_firm": fu,
                "target_firm": fv,
                "weight": data.get("weight", 1),
            }
            if fu != "Other" and fv != "Other" and fu != fv:
                firm_edges.append(row)
            if sorted([cu, cv]) == ["company", "education"]:
                firm_univ_edges.append(row)
        pd.DataFrame(firm_edges).to_csv(OUTPUTS / "tables" / "firm_to_firm_edges.csv", index=False)
        pd.DataFrame(firm_univ_edges).to_csv(OUTPUTS / "tables" / "firm_university_edges.csv", index=False)

    if full_researcher_graph is not None and not full_researcher_nodes.empty:
        bridge_rows = []
        for _, row in full_researcher_nodes.sort_values("betweenness_centrality", ascending=False).head(100).iterrows():
            node = str(row["id"])
            bridge_rows.append(
                {
                    **row.to_dict(),
                    "neighbor_institution_category_count": neighbor_diversity(
                        full_researcher_graph, node, "simplified_institution_category"
                    ),
                    "neighbor_target_firm_count": neighbor_diversity(full_researcher_graph, node, "target_firm_label"),
                    "years_active_in_dataset": row.get("year_list", ""),
                }
            )
        pd.DataFrame(bridge_rows).to_csv(OUTPUTS / "tables" / "potential_bridge_researchers.csv", index=False)

    if full_institution_graph is not None and not full_institution_nodes.empty:
        bridge_rows = []
        for _, row in full_institution_nodes.sort_values("betweenness_centrality", ascending=False).head(100).iterrows():
            node = str(row["id"])
            neigh = [full_institution_graph.nodes[n] for n in full_institution_graph.neighbors(node)]
            bridge_rows.append(
                {
                    **row.to_dict(),
                    "company_neighbor_count": sum(1 for n in neigh if n.get("simplified_institution_category") == "company"),
                    "education_neighbor_count": sum(1 for n in neigh if n.get("simplified_institution_category") == "education"),
                    "research_institute_neighbor_count": sum(
                        1 for n in neigh if n.get("simplified_institution_category") == "research_institute"
                    ),
                }
            )
        pd.DataFrame(bridge_rows).to_csv(OUTPUTS / "tables" / "potential_bridge_institutions.csv", index=False)

    with open(OUTPUTS / "tables" / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump({"summary_rows": len(summaries)}, f, indent=2)
    print(f"Wrote analysis tables to {OUTPUTS / 'tables'}")


if __name__ == "__main__":
    analyze()
