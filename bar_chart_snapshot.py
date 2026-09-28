import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


METRIC_NAMES = [
    "signaling_overhead",
    "ping_pong_ratio",
    "call_drop_approx",
    "session_reset_count",
    "session_continuity_rate",
]

REPRESENTATIVE_COMBO = {"cell_size": "1.0", "speed": "0.3", "num_nodes": "30"}


def load_results(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def filter_combo(rows, combo):
    return [r for r in rows if all(r[k] == v for k, v in combo.items())]


def plot_bar_snapshot(rows, metric, out_path):
    algorithms = sorted(set(r["algorithm"] for r in rows))
    means = []
    errors = []
    for algorithm in algorithms:
        row = next(r for r in rows if r["algorithm"] == algorithm)
        means.append(float(row[f"{metric}_mean"]))
        errors.append(float(row[f"{metric}_std"]))

    plt.figure()
    plt.bar(algorithms, means, yerr=errors, capsize=4)
    plt.xlabel("algorithm")
    plt.ylabel(metric)
    plt.title(f"{metric} by algorithm (mean ± std)")
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path)
    plt.close()


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "results/05_raw_data/results.csv"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "results/01_main_comparison"

    rows = filter_combo(load_results(csv_path), REPRESENTATIVE_COMBO)
    if not rows:
        print(f"no rows found in {csv_path} matching {REPRESENTATIVE_COMBO}")
        return

    for metric in METRIC_NAMES:
        out_path = os.path.join(out_dir, f"bar_{metric}.png")
        plot_bar_snapshot(rows, metric, out_path)
        print(f"saved {out_path}")


if __name__ == "__main__":
    main()
