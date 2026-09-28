import os
import statistics
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from run_experiment import DEFAULT_CONFIG, run_single

NODE_COUNTS = [100, 500, 1000]
ALGORITHMS = ["baseline", "improved", "ai"]
NUM_REPEATS = 3
BASE_SEED = 42


def benchmark():
    timings = {algorithm: [] for algorithm in ALGORITHMS}

    for algorithm in ALGORITHMS:
        for num_nodes in NODE_COUNTS:
            elapsed_list = []
            for repeat in range(NUM_REPEATS):
                config = dict(DEFAULT_CONFIG)
                config["num_nodes"] = num_nodes
                config["algorithm"] = algorithm
                seed = BASE_SEED + repeat

                t0 = time.time()
                run_single(config, seed)
                elapsed_list.append(time.time() - t0)

            mean_elapsed = statistics.mean(elapsed_list)
            timings[algorithm].append(mean_elapsed)
            print(f"{algorithm:10} num_nodes={num_nodes:5} mean_elapsed={mean_elapsed:.3f}s")

    return timings


def plot_benchmark(timings, out_path):
    plt.figure()
    for algorithm in ALGORITHMS:
        plt.plot(NODE_COUNTS, timings[algorithm], marker="o", label=algorithm)

    plt.xlabel("num_nodes")
    plt.ylabel("wall-clock time (s)")
    plt.title(f"scalability benchmark (num_steps={DEFAULT_CONFIG['num_steps']}, mean of {NUM_REPEATS} runs)")
    plt.legend()
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path)
    plt.close()


def main():
    timings = benchmark()
    out_path = "results/04_validation/scalability_benchmark.png"
    plot_benchmark(timings, out_path)
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
