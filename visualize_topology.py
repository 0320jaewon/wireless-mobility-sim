import math
import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from simulator.topology import create_hex_grid, assign_domains
from simulator.mobility import create_nodes, step_node
from simulator.improved import ImprovedAlgorithm
from simulator.session import SessionManager

CELL_SIZE = 1.0
DOMAIN_COLORS = {0: "#cfe8ff", 1: "#ffe0cf"}
NODE_COLORS = ["#1f77b4", "#9467bd"]


def hexagon_vertices(cx, cy, size):
    return [
        (cx + size * math.cos(math.radians(60 * k)), cy + size * math.sin(math.radians(60 * k)))
        for k in range(6)
    ]


def shared_edge(vertices_a, vertices_b, tol=1e-6):
    shared = []
    for va in vertices_a:
        for vb in vertices_b:
            if abs(va[0] - vb[0]) < tol and abs(va[1] - vb[1]) < tol:
                shared.append(va)
    return shared


def run_and_collect(num_nodes=2, num_steps=150, speed=0.3, seed=7):
    rng = random.Random(seed)
    topology = create_hex_grid(rows=5, cols=5, cell_size=CELL_SIZE)
    assign_domains(topology, num_domains=2)

    nodes = create_nodes(topology, num_nodes=num_nodes, speed=speed, rng=rng)
    algorithm = ImprovedAlgorithm(ho_threshold=5.0, ho_timer=3, lu_period=15)
    session_manager = SessionManager()
    for node in nodes:
        algorithm.init_node(node)
        session_manager.init_session(node)

    paths = {node.node_id: [(node.x, node.y)] for node in nodes}
    for timestep in range(num_steps):
        for node in nodes:
            step_node(node, topology, rng, model="random_walk")
            algorithm.step_handover(node, topology, timestep)
            algorithm.step_lm(node, timestep)
            session_manager.update(node, timestep)
            paths[node.node_id].append((node.x, node.y))

    return topology, paths, algorithm.ho_log


def plot_topology(topology, paths, ho_log, out_path):
    fig, ax = plt.subplots(figsize=(8, 8))

    for cell in topology.cells.values():
        vertices = hexagon_vertices(cell.x, cell.y, CELL_SIZE)
        polygon = Polygon(
            vertices, closed=True,
            facecolor=DOMAIN_COLORS[cell.domain_id], edgecolor="gray", linewidth=1, zorder=1,
        )
        ax.add_patch(polygon)
        ax.text(cell.x, cell.y, str(cell.cell_id), ha="center", va="center", fontsize=8, zorder=3)

    drawn_pairs = set()
    for cell in topology.cells.values():
        cell_vertices = hexagon_vertices(cell.x, cell.y, CELL_SIZE)
        for neighbor_id in cell.neighbor_ids:
            neighbor = topology.get_cell(neighbor_id)
            pair = tuple(sorted((cell.cell_id, neighbor_id)))
            if neighbor.domain_id == cell.domain_id or pair in drawn_pairs:
                continue
            drawn_pairs.add(pair)
            neighbor_vertices = hexagon_vertices(neighbor.x, neighbor.y, CELL_SIZE)
            edge = shared_edge(cell_vertices, neighbor_vertices)
            if len(edge) == 2:
                xs = [p[0] for p in edge]
                ys = [p[1] for p in edge]
                ax.plot(xs, ys, color="red", linewidth=3, zorder=2)

    for i, (node_id, path) in enumerate(paths.items()):
        color = NODE_COLORS[i % len(NODE_COLORS)]
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        ax.plot(xs, ys, color=color, linewidth=1.2, alpha=0.8, zorder=4, label=f"node {node_id} path")
        ax.scatter([xs[0]], [ys[0]], color=color, marker="o", s=80, zorder=5, edgecolor="black")
        ax.scatter([xs[-1]], [ys[-1]], color=color, marker="s", s=80, zorder=5, edgecolor="black")

    ho_xs, ho_ys = [], []
    for event in ho_log:
        node_id = event["node_id"]
        timestep = event["timestep"]
        pos = paths[node_id][timestep + 1]
        ho_xs.append(pos[0])
        ho_ys.append(pos[1])
    if ho_xs:
        ax.scatter(ho_xs, ho_ys, color="black", marker="x", s=90, zorder=6, label="HO event")

    ax.set_aspect("equal")
    ax.set_title("5x5 hex grid, Domain boundary(red), node path, HO events(x)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0))
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    topology, paths, ho_log = run_and_collect()
    out_path = "results/03_special_analysis/topology_visualization.png"
    plot_topology(topology, paths, ho_log, out_path)
    print(f"saved {out_path} (HO events: {len(ho_log)})")


if __name__ == "__main__":
    main()
