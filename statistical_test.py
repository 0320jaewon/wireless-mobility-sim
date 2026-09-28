import csv
import itertools
import os

from scipy import stats

METRIC_NAMES = [
    "signaling_overhead",
    "ping_pong_ratio",
    "call_drop_approx",
    "session_reset_count",
    "session_continuity_rate",
]

REPRESENTATIVE_COMBO = {"cell_size": "1.0", "speed": "0.3", "num_nodes": "30"}
ALGORITHMS = ["baseline", "improved", "ai"]


def load_raw(path="results/05_raw_data/results_raw.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def filter_combo(rows, combo):
    return [r for r in rows if all(r[k] == v for k, v in combo.items())]


def values_by_seed(rows, algorithm, metric):
    subset = [r for r in rows if r["algorithm"] == algorithm]
    subset.sort(key=lambda r: int(r["seed"]))
    return [float(r[metric]) for r in subset], [int(r["seed"]) for r in subset]


def run_tests(rows):
    results = []
    for metric in METRIC_NAMES:
        for algo_a, algo_b in itertools.combinations(ALGORITHMS, 2):
            values_a, seeds_a = values_by_seed(rows, algo_a, metric)
            values_b, seeds_b = values_by_seed(rows, algo_b, metric)
            assert seeds_a == seeds_b, "seed mismatch between algorithms, paired t-test requires alignment"

            t_stat, p_value = stats.ttest_rel(values_a, values_b)
            mean_a = sum(values_a) / len(values_a)
            mean_b = sum(values_b) / len(values_b)

            results.append({
                "metric": metric,
                "comparison": f"{algo_a}_vs_{algo_b}",
                "n": len(values_a),
                "mean_a": mean_a,
                "mean_b": mean_b,
                "mean_diff": mean_a - mean_b,
                "t_statistic": t_stat,
                "p_value": p_value,
                "significant_0.05": p_value < 0.05,
            })
    return results


def save_csv(results, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)


def main():
    rows = filter_combo(load_raw(), REPRESENTATIVE_COMBO)
    results = run_tests(rows)
    out_path = "results/04_validation/statistical_test_results.csv"
    save_csv(results, out_path)
    print(f"saved {len(results)} rows to {out_path}")
    for r in results:
        marker = "*" if r["significant_0.05"] else ""
        print(f"{r['metric']:24} {r['comparison']:20} p={r['p_value']:.4f}{marker}")


if __name__ == "__main__":
    main()
