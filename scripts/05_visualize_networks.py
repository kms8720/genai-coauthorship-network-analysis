from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import seaborn as sns

from common import OUTPUTS, ensure_dirs, load_config
from scripts_04_loader import load_graph_for_visual


COLOR_MAP = {
    "company": "#E15759",
    "education": "#4E79A7",
    "research_institute": "#59A14F",
    "government": "#F28E2B",
    "nonprofit": "#B07AA1",
    "healthcare": "#76B7B2",
    "unknown": "#9D9D9D",
}


def save_line_plot(summary: pd.DataFrame, network: str, metric: str, filename: str, ylabel: str) -> None:
    df = summary[(summary["network"] == network) & (summary["year"] != "full")].copy()
    if df.empty:
        return
    df["year"] = df["year"].astype(int)
    plt.figure(figsize=(7, 4))
    sns.lineplot(data=df, x="year", y=metric, marker="o")
    plt.title(ylabel)
    plt.xlabel("Year")
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(OUTPUTS / "figures" / filename, dpi=200)
    plt.close()


def draw_network(graph: nx.Graph, filename: str, title: str, max_nodes: int = 120) -> None:
    if graph.number_of_nodes() == 0:
        return
    if graph.number_of_nodes() > max_nodes:
        ranked = sorted(graph.degree(weight="weight"), key=lambda x: x[1], reverse=True)[:max_nodes]
        graph = graph.subgraph([n for n, _ in ranked]).copy()
    graph.remove_nodes_from(list(nx.isolates(graph)))
    if graph.number_of_nodes() == 0:
        return
    pos = nx.spring_layout(graph, seed=42, weight="weight", k=1 / math.sqrt(max(graph.number_of_nodes(), 1)))
    colors = [COLOR_MAP.get(graph.nodes[n].get("simplified_institution_category", "unknown"), "#9D9D9D") for n in graph.nodes()]
    sizes = [
        80 + 900 * float(graph.nodes[n].get("betweenness_centrality", 0) or 0)
        for n in graph.nodes()
    ]
    widths = [0.4 + min(float(d.get("weight", 1)), 10) * 0.25 for _, _, d in graph.edges(data=True)]
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_edges(graph, pos, width=widths, alpha=0.25, edge_color="#555555")
    nx.draw_networkx_nodes(graph, pos, node_color=colors, node_size=sizes, alpha=0.88, linewidths=0.2)
    if graph.number_of_nodes() <= 40:
        labels = {
            n: graph.nodes[n].get("institution_name")
            or graph.nodes[n].get("display_name")
            or str(n)
            for n in graph.nodes()
        }
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=7)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(OUTPUTS / "figures" / filename, dpi=220)
    plt.close()


def heatmap_mixing() -> None:
    path = OUTPUTS / "tables" / "institution_type_edge_mixing.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    full = df[df["year"].astype(str) == "full"].copy()
    if full.empty:
        return
    split = full["category_pair"].str.split("-", expand=True)
    full["source_category"] = split[0]
    full["target_category"] = split[1]
    pivot = full.pivot_table(
        index="source_category", columns="target_category", values="edge_weight", aggfunc="sum", fill_value=0
    )
    plt.figure(figsize=(7, 5))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues")
    plt.title("Institution Type Edge Mixing, Full Period")
    plt.tight_layout()
    plt.savefig(OUTPUTS / "figures" / "institution_type_mixing_heatmap.png", dpi=220)
    plt.close()


def bar_top(table_name: str, label_col: str, value_col: str, filename: str, title: str) -> None:
    path = OUTPUTS / "tables" / table_name
    if not path.exists():
        return
    df = pd.read_csv(path).head(15)
    if df.empty or value_col not in df:
        return
    labels = df[label_col].fillna(df.get("id", "")).astype(str)
    plt.figure(figsize=(8, 5))
    sns.barplot(x=df[value_col], y=labels, color="#4E79A7")
    plt.title(title)
    plt.xlabel(value_col)
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(OUTPUTS / "figures" / filename, dpi=220)
    plt.close()


def visualize() -> None:
    ensure_dirs()
    cfg = load_config()
    summary_path = OUTPUTS / "tables" / "network_summary_by_year.csv"
    summary = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()
    if not summary.empty:
        save_line_plot(summary, "researcher", "node_count", "network_size_by_year.png", "Researcher Nodes by Year")
        save_line_plot(summary, "researcher", "density", "density_by_year.png", "Researcher Network Density by Year")
        save_line_plot(summary, "researcher", "connected_components", "components_by_year.png", "Researcher Components by Year")
    heatmap_mixing()
    bar_top(
        "top_researchers_betweenness.csv",
        "display_name",
        "betweenness_centrality",
        "top_researchers_betweenness.png",
        "Top Researchers by Betweenness",
    )
    bar_top(
        "top_institutions_betweenness.csv",
        "institution_name",
        "betweenness_centrality",
        "top_institutions_betweenness.png",
        "Top Institutions by Betweenness",
    )

    max_nodes = int(cfg.get("sample_figure_node_limit", 120))
    draw_network(
        load_graph_for_visual("researcher", "full"),
        "researcher_network_full_static.png",
        "Researcher Coauthorship Network, Full Period",
        max_nodes=max_nodes,
    )
    draw_network(
        load_graph_for_visual("institution", "full"),
        "institution_network_full_static.png",
        "Institution Coauthorship Network, Full Period",
        max_nodes=max_nodes,
    )
    for year in range(int(cfg["start_year"]), int(cfg["end_year"]) + 1):
        draw_network(
            load_graph_for_visual("institution", str(year)),
            f"institution_network_by_year_{year}.png",
            f"Institution Coauthorship Network, {year}",
            max_nodes=max_nodes,
        )
    print(f"Wrote figures to {OUTPUTS / 'figures'}")


if __name__ == "__main__":
    visualize()

