from __future__ import annotations

import networkx as nx
import pandas as pd

from common import OUTPUTS


def load_graph_for_visual(kind: str, label: str) -> nx.Graph:
    node_path = OUTPUTS / "networks" / f"{kind}_nodes_{label}.csv"
    edge_path = OUTPUTS / "networks" / f"{kind}_edges_{label}.csv"
    graph = nx.Graph()
    if node_path.exists():
        nodes = pd.read_csv(node_path).fillna("")
        for _, row in nodes.iterrows():
            node_id = str(row["id"])
            graph.add_node(node_id, **{k: row[k] for k in nodes.columns if k != "id"})
    if edge_path.exists():
        edges = pd.read_csv(edge_path).fillna("")
        for _, row in edges.iterrows():
            graph.add_edge(
                str(row["source"]),
                str(row["target"]),
                weight=float(row.get("weight", 1) or 1),
            )
    return graph

