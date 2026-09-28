import csv
import itertools
import os
import random
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from simulator.topology import create_hex_grid, assign_domains
from simulator.mobility import create_nodes, step_node, signal_strength
from simulator.baseline import BaselineAlgorithm
from simulator.improved import ImprovedAlgorithm
from simulator.ai_predictor import AIAlgorithm
from simulator.session import SessionManager
from simulator.metrics import compute_basic_metrics, compute_session_metrics, compute_prediction_accuracy


DEFAULT_CONFIG = {
    "rows": 5,
    "cols": 5,
    "cell_size": 1.0,
    "num_domains": 2,
    "num_nodes": 20,
    "speed": 0.3,
    "num_steps": 200,
    "mobility_model": "random_walk",
    "ho_threshold": 5.0,
    "lu_period": 10,
    "ho_timer": 3,
    "improved_lu_period": 20,
    "ho_threshold_predicted": 2.5,
    "ho_timer_predicted": 1,
    "ai_lu_period": 20,
    "predictor_order": "zero",
    "call_arrival_prob": 0.05,
    "drop_threshold": 60.0,
    "pingpong_window": 5,
}


def build_algorithm(name, config):
    if name == "baseline":
        return BaselineAlgorithm(ho_threshold=config["ho_threshold"], lu_period=config["lu_period"])
    if name == "improved":
        return ImprovedAlgorithm(
            ho_threshold=config["ho_threshold"],
            ho_timer=config["ho_timer"],
            lu_period=config["improved_lu_period"],
        )
    if name == "ai":
        return AIAlgorithm(
            ho_threshold=config["ho_threshold"],
            ho_timer=config["ho_timer"],
            ho_threshold_predicted=config["ho_threshold_predicted"],
            ho_timer_predicted=config["ho_timer_predicted"],
            lu_period=config["ai_lu_period"],
            predictor_order=config.get("predictor_order", "zero"),
        )
    raise ValueError(f"unknown algorithm: {name}")


def run_single(config, seed):
    rng = random.Random(seed)
    topology = create_hex_grid(rows=config["rows"], cols=config["cols"], cell_size=config["cell_size"])
    assign_domains(topology, num_domains=config["num_domains"])
    nodes = create_nodes(topology, num_nodes=config["num_nodes"], speed=config["speed"], rng=rng)

    algorithm = build_algorithm(config["algorithm"], config)
    session_manager = SessionManager()
    for node in nodes:
        algorithm.init_node(node)
        session_manager.init_session(node)

    signal_log = []
    for timestep in range(config["num_steps"]):
        for node in nodes:
            step_node(node, topology, rng, model=config["mobility_model"])
            algorithm.step_handover(node, topology, timestep)
            algorithm.step_lm(node, timestep)
            if rng.random() < config["call_arrival_prob"]:
                algorithm.trigger_paging(node, topology, timestep)
            session_manager.update(node, timestep)

            distance = topology.distance_to_cell(node.cell_id, node.x, node.y)
            signal_log.append({
                "node_id": node.node_id,
                "timestep": timestep,
                "signal": signal_strength(distance),
            })

    basic_metrics = compute_basic_metrics(
        algorithm.lu_log,
        algorithm.paging_log,
        algorithm.ho_log,
        signal_log,
        config["drop_threshold"],
        pingpong_window=config["pingpong_window"],
    )
    session_metrics = compute_session_metrics(
        session_manager.reset_log, len(nodes), config["num_steps"]
    )

    prediction_log = getattr(algorithm, "prediction_log", None)
    prediction_accuracy = (
        compute_prediction_accuracy(prediction_log) if prediction_log is not None else None
    )

    result = dict(config)
    result.update(basic_metrics)
    result.update(session_metrics)
    result["prediction_accuracy"] = prediction_accuracy
    return result


def run_sweep(base_config, sweep_params, algorithm_names, seed=42):
    keys = list(sweep_params.keys())
    value_lists = [sweep_params[k] for k in keys]

    results = []
    for algorithm_name in algorithm_names:
        for combo in itertools.product(*value_lists):
            config = dict(base_config)
            config.update(dict(zip(keys, combo)))
            config["algorithm"] = algorithm_name
            results.append(run_single(config, seed))
    return results


def run_sweep_repeated(base_config, sweep_params, algorithm_names, num_repeats=10, base_seed=42):
    keys = list(sweep_params.keys())
    value_lists = [sweep_params[k] for k in keys]

    raw_results = []
    for algorithm_name in algorithm_names:
        for combo in itertools.product(*value_lists):
            config = dict(base_config)
            config.update(dict(zip(keys, combo)))
            config["algorithm"] = algorithm_name
            for repeat in range(num_repeats):
                seed = base_seed + repeat
                result = run_single(config, seed)
                result["seed"] = seed
                result["repeat"] = repeat
                raw_results.append(result)
    return raw_results


def aggregate_repeats(raw_results, metric_names, sweep_keys):
    config_keys = ["algorithm"] + sweep_keys
    groups = {}
    for row in raw_results:
        key = tuple(row[k] for k in config_keys)
        groups.setdefault(key, []).append(row)

    aggregated = []
    for key, rows in groups.items():
        agg = dict(zip(config_keys, key))
        for metric in metric_names:
            values = [row[metric] for row in rows if row[metric] is not None]
            if values:
                agg[f"{metric}_mean"] = statistics.mean(values)
                agg[f"{metric}_std"] = statistics.stdev(values) if len(values) > 1 else 0.0
            else:
                agg[f"{metric}_mean"] = None
                agg[f"{metric}_std"] = None
        agg["num_repeats"] = len(rows)
        aggregated.append(agg)
    return aggregated


def save_csv(results, path):
    if not results:
        return
    fieldnames = list(results[0].keys())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def plot_metric(results, metric, sweep_param, out_path, error_metric=None, ylabel=None, title_suffix=""):
    algorithms = sorted(set(r["algorithm"] for r in results))

    plt.figure()
    for algorithm_name in algorithms:
        subset = sorted(
            (r for r in results if r["algorithm"] == algorithm_name),
            key=lambda r: r[sweep_param],
        )
        xs = [r[sweep_param] for r in subset]
        ys = [r[metric] for r in subset]
        if error_metric:
            yerr = [r[error_metric] for r in subset]
            plt.errorbar(xs, ys, yerr=yerr, marker="o", capsize=4, label=algorithm_name)
        else:
            plt.plot(xs, ys, marker="o", label=algorithm_name)

    plt.xlabel(sweep_param)
    plt.ylabel(ylabel or metric)
    plt.title(f"{ylabel or metric} vs {sweep_param}{title_suffix}")
    plt.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path)
    plt.close()


def plot_heatmap(aggregated, algorithm, metric, x_param, y_param, held_params, out_path):
    rows = [
        r for r in aggregated
        if r["algorithm"] == algorithm and all(r[p] == v for p, v in held_params.items())
    ]
    x_values = sorted(set(r[x_param] for r in rows))
    y_values = sorted(set(r[y_param] for r in rows))

    grid = [[None for _ in x_values] for _ in y_values]
    for r in rows:
        xi = x_values.index(r[x_param])
        yi = y_values.index(r[y_param])
        grid[yi][xi] = r[f"{metric}_mean"]

    fig, ax = plt.subplots()
    im = ax.imshow(grid, origin="lower", cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(x_values)))
    ax.set_xticklabels(x_values)
    ax.set_yticks(range(len(y_values)))
    ax.set_yticklabels(y_values)
    ax.set_xlabel(x_param)
    ax.set_ylabel(y_param)

    held_str = ", ".join(f"{p}={v}" for p, v in held_params.items())
    ax.set_title(f"{metric} heatmap ({algorithm}, {held_str})")

    for yi in range(len(y_values)):
        for xi in range(len(x_values)):
            value = grid[yi][xi]
            if value is not None:
                ax.text(xi, yi, f"{value:.0f}", ha="center", va="center", color="white")

    fig.colorbar(im, ax=ax, label=metric)
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


METRIC_NAMES = [
    "signaling_overhead",
    "ping_pong_ratio",
    "call_drop_approx",
    "session_reset_count",
    "session_continuity_rate",
]

SWEEP_GRID = {
    "cell_size": [0.5, 1.0, 1.5],
    "speed": [0.1, 0.3, 0.6],
    "num_nodes": [10, 30, 50],
}

ALL_METRIC_NAMES = METRIC_NAMES + ["prediction_accuracy"]
NUM_REPEATS = 10
BASE_SEED = 42

RAW_DATA_DIR = "results/05_raw_data"
SENSITIVITY_DIR = "results/02_sensitivity"
SPECIAL_DIR = "results/03_special_analysis"


def main():
    algorithm_names = ["baseline", "improved", "ai"]

    raw_results = run_sweep_repeated(
        DEFAULT_CONFIG, SWEEP_GRID, algorithm_names,
        num_repeats=NUM_REPEATS, base_seed=BASE_SEED,
    )
    raw_path = f"{RAW_DATA_DIR}/results_raw.csv"
    save_csv(raw_results, raw_path)
    print(f"saved {len(raw_results)} rows to {raw_path}")

    sweep_keys = list(SWEEP_GRID.keys())
    aggregated = aggregate_repeats(raw_results, ALL_METRIC_NAMES, sweep_keys)
    aggregated_path = f"{RAW_DATA_DIR}/results.csv"
    save_csv(aggregated, aggregated_path)
    print(f"saved {len(aggregated)} rows to {aggregated_path} (mean/std over {NUM_REPEATS} seeds)")

    baseline_values = {param: values[0] for param, values in SWEEP_GRID.items()}
    title_suffix = f" (mean ± std, n={NUM_REPEATS})"

    for sweep_param in SWEEP_GRID:
        other_params = [p for p in SWEEP_GRID if p != sweep_param]
        filtered = [
            r for r in aggregated
            if all(r[p] == baseline_values[p] for p in other_params)
        ]

        for metric in METRIC_NAMES:
            out_path = f"{SENSITIVITY_DIR}/{metric}_vs_{sweep_param}.png"
            plot_metric(
                filtered, f"{metric}_mean", sweep_param, out_path,
                error_metric=f"{metric}_std", ylabel=metric, title_suffix=title_suffix,
            )
            print(f"saved {out_path}")

        ai_filtered = [r for r in filtered if r["algorithm"] == "ai"]
        out_path = f"{SPECIAL_DIR}/prediction_accuracy_vs_{sweep_param}.png"
        plot_metric(
            ai_filtered, "prediction_accuracy_mean", sweep_param, out_path,
            error_metric="prediction_accuracy_std", ylabel="prediction_accuracy", title_suffix=title_suffix,
        )
        print(f"saved {out_path}")

    heatmap_path = f"{SPECIAL_DIR}/heatmap_signaling_overhead.png"
    plot_heatmap(
        aggregated, "ai", "signaling_overhead", "cell_size", "speed",
        {"num_nodes": baseline_values["num_nodes"]}, heatmap_path,
    )
    print(f"saved {heatmap_path}")


if __name__ == "__main__":
    main()
