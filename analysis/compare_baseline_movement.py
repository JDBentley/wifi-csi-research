"""
compare_baseline_movement.py

Compares CSI signal energy across two capture modes:

  1. Baseline/Movement — hotel-style captures (baseline_*.csv, movement_*.csv)
     Used for motion detection validation.

  2. Placement Runs — environmental comparison captures (*_run_*.csv)
     Used for placement and RF density comparison across desk, kitchen,
     and work_rf_dense environments.

Auto-discovers datasets from data/raw/ by environment subfolder.
Outputs statistics to stdout and saves plots to results/figures/.

Usage:
    # All environments, all modes
    python analysis/compare_baseline_movement.py

    # Specific environments
    python analysis/compare_baseline_movement.py --env hotel
    python analysis/compare_baseline_movement.py --env desk kitchen work_rf_dense

    # Force a specific mode
    python analysis/compare_baseline_movement.py --mode baseline_movement
    python analysis/compare_baseline_movement.py --mode placement
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Path resolution — works regardless of where the script is called from
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data" / "raw"
FIGURES_DIR = REPO_ROOT / "results" / "figures"

# Environments that use placement run naming (*_run_*.csv)
PLACEMENT_ENVS = {"desk", "kitchen", "work_rf_dense"}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_csi_file(filepath: Path) -> pd.DataFrame:
    """
    Parse a raw CSI log file into a DataFrame.
    Skips empty lines, firmware log lines, and rows with non-numeric values.
    Expected column order: timestamp, RSSI, len, csi_values...
    """
    rows = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or not line[0].isdigit():
                continue
            parts = line.split(",")
            try:
                rows.append([int(x) for x in parts])
            except ValueError:
                continue

    if not rows:
        print(f"  [WARN] No valid rows found in {filepath.name}", file=sys.stderr)
        return pd.DataFrame()

    return pd.DataFrame(rows)


def calculate_energy(df: pd.DataFrame) -> pd.Series:
    """
    Signal energy = sum of squared CSI subcarrier values.
    Columns 0-2 are timestamp, RSSI, len — skipped.
    """
    csi_values = df.iloc[:, 3:]
    return (csi_values ** 2).sum(axis=1)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_stats(name: str, energy: pd.Series, filepath: Path) -> dict:
    return {
        "name": name,
        "file": filepath.name,
        "rows": len(energy),
        "mean": energy.mean(),
        "variance": energy.var(),
        "std": energy.std(),
        "min": energy.min(),
        "max": energy.max(),
    }


def print_stats(stats: dict):
    print(f"\n=== {stats['name']} ({stats['file']}) ===")
    print(f"  Rows         : {stats['rows']}")
    print(f"  Mean Energy  : {stats['mean']:.2f}")
    print(f"  Variance     : {stats['variance']:.2f}")
    print(f"  Std Dev      : {stats['std']:.2f}")
    print(f"  Min          : {stats['min']:.2f}")
    print(f"  Max          : {stats['max']:.2f}")


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def detect_mode(env_dir: Path) -> str:
    """
    Auto-detect capture mode for an environment directory.
    Returns 'placement' if *_run_*.csv files exist, otherwise 'baseline_movement'.
    """
    if env_dir.name in PLACEMENT_ENVS:
        return "placement"
    has_runs = any(env_dir.glob("*_run_*.csv"))
    if has_runs:
        return "placement"
    return "baseline_movement"


def discover_baseline_movement(env_dir: Path) -> tuple[list[Path], list[Path]]:
    """Discover baseline_*.csv and movement_*.csv files."""
    baseline = sorted(env_dir.glob("baseline_*.csv"))
    movement = sorted(env_dir.glob("movement_*.csv"))
    return baseline, movement


def discover_placement_runs(env_dir: Path) -> list[Path]:
    """
    Discover placement run files (*_run_*.csv).
    Matches: desk_run_01.csv, kitchen_run_03.csv, work_rf_dense_run_02.csv
    """
    return sorted(env_dir.glob("*_run_*.csv"))


def get_environments(requested: list[str] | None) -> list[Path]:
    """
    Return environment subdirectories under data/raw/.
    If requested is provided, filter to those names only.
    """
    if not DATA_ROOT.exists():
        print(f"[ERROR] data/raw/ not found at {DATA_ROOT}", file=sys.stderr)
        sys.exit(1)

    all_envs = [d for d in sorted(DATA_ROOT.iterdir()) if d.is_dir()]

    if not all_envs:
        print(f"[ERROR] No environment folders found in {DATA_ROOT}", file=sys.stderr)
        sys.exit(1)

    if requested:
        filtered = [e for e in all_envs if e.name in requested]
        missing = set(requested) - {e.name for e in filtered}
        if missing:
            print(f"[WARN] Requested environments not found: {missing}", file=sys.stderr)
        return filtered

    return all_envs


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_baseline_movement(
    baseline_energies: list[tuple[str, pd.Series]],
    movement_energies: list[tuple[str, pd.Series]],
    env_name: str,
    output_path: Path,
):
    """Plot baseline vs movement energy for a single environment."""
    fig, ax = plt.subplots(figsize=(12, 5))

    for label, energy in baseline_energies:
        ax.plot(energy.values, label=label, color="steelblue", alpha=0.8)

    for label, energy in movement_energies:
        ax.plot(energy.values, label=label, color="darkorange", alpha=0.8)

    ax.set_title(f"Baseline vs Movement CSI Energy — {env_name}")
    ax.set_xlabel("Sample Number")
    ax.set_ylabel("Signal Energy")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"\n  [+] Plot saved: {output_path.relative_to(REPO_ROOT)}")


def plot_placement_runs(
    run_energies: list[tuple[str, pd.Series]],
    env_name: str,
    output_path: Path,
):
    """
    Plot all placement runs for a single environment.
    Each run gets its own line with distinct color cycling.
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    colors = plt.cm.tab10.colors
    for i, (label, energy) in enumerate(run_energies):
        ax.plot(energy.values, label=label, color=colors[i % len(colors)], alpha=0.8)

    ax.set_title(f"Placement Run CSI Energy — {env_name}")
    ax.set_xlabel("Sample Number")
    ax.set_ylabel("Signal Energy")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"\n  [+] Plot saved: {output_path.relative_to(REPO_ROOT)}")


def plot_environment_comparison(
    env_summaries: list[dict],
    output_path: Path,
):
    """
    Cross-environment bar chart: mean energy and std dev per environment.
    This is figure 07-environment-comparison-graph from the experiment plan.
    """
    if not env_summaries:
        return

    labels = [s["env"] for s in env_summaries]
    means = [s["mean"] for s in env_summaries]
    stds = [s["std"] for s in env_summaries]

    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(10, 5))

    bars = ax.bar(x, means, yerr=stds, capsize=6, color="steelblue",
                  alpha=0.8, error_kw={"ecolor": "darkorange", "linewidth": 2})

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_title("CSI Signal Energy by Environment (Mean ± Std Dev)")
    ax.set_xlabel("Environment")
    ax.set_ylabel("Mean Signal Energy")
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"\n  [+] Environment comparison plot saved: {output_path.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# Processing — baseline/movement mode
# ---------------------------------------------------------------------------

def process_baseline_movement(env_dir: Path, env_name: str) -> dict | None:
    baseline_files, movement_files = discover_baseline_movement(env_dir)

    if not baseline_files and not movement_files:
        print(f"  [SKIP] No baseline or movement files found.")
        return None

    baseline_energies = []
    movement_energies = []
    all_stats = []

    for i, fp in enumerate(baseline_files, start=1):
        df = load_csi_file(fp)
        if df.empty:
            continue
        energy = calculate_energy(df)
        label = f"Baseline {i}"
        stats = compute_stats(label, energy, fp)
        print_stats(stats)
        all_stats.append(stats)
        baseline_energies.append((label, energy))

    for i, fp in enumerate(movement_files, start=1):
        df = load_csi_file(fp)
        if df.empty:
            continue
        energy = calculate_energy(df)
        label = f"Movement {i}"
        stats = compute_stats(label, energy, fp)
        print_stats(stats)
        all_stats.append(stats)
        movement_energies.append((label, energy))

    b_stats = [s for s in all_stats if "Baseline" in s["name"]]
    m_stats = [s for s in all_stats if "Movement" in s["name"]]

    if b_stats and m_stats:
        avg_b_std = sum(s["std"] for s in b_stats) / len(b_stats)
        avg_m_std = sum(s["std"] for s in m_stats) / len(m_stats)
        avg_b_mean = sum(s["mean"] for s in b_stats) / len(b_stats)
        avg_m_mean = sum(s["mean"] for s in m_stats) / len(m_stats)

        print(f"\n--- Repeatability Summary: {env_name} ---")
        print(f"  Avg Baseline Mean    : {avg_b_mean:.2f}")
        print(f"  Avg Movement Mean    : {avg_m_mean:.2f}")
        print(f"  Mean Separation      : {avg_m_mean - avg_b_mean:.2f}")
        print(f"  Avg Baseline Std Dev : {avg_b_std:.2f}")
        print(f"  Avg Movement Std Dev : {avg_m_std:.2f}")
        print(f"  Movement/Baseline Std Ratio: {avg_m_std / avg_b_std:.2f}x")

    if baseline_energies or movement_energies:
        plot_path = FIGURES_DIR / f"energy_comparison_{env_name}.png"
        plot_baseline_movement(baseline_energies, movement_energies, env_name, plot_path)

    return None  # baseline/movement envs excluded from cross-env comparison


# ---------------------------------------------------------------------------
# Processing — placement run mode
# ---------------------------------------------------------------------------

def process_placement_runs(env_dir: Path, env_name: str) -> dict | None:
    """
    Process all *_run_*.csv files for one environment.
    Returns a summary dict for cross-environment comparison, or None if no data.
    """
    run_files = discover_placement_runs(env_dir)

    if not run_files:
        print(f"  [SKIP] No placement run files found.")
        return None

    run_energies = []
    all_stats = []

    for fp in run_files:
        df = load_csi_file(fp)
        if df.empty:
            continue
        energy = calculate_energy(df)
        # Label from filename: desk_run_01.csv -> "desk run 01"
        label = fp.stem.replace("_", " ")
        stats = compute_stats(label, energy, fp)
        print_stats(stats)
        all_stats.append(stats)
        run_energies.append((label, energy))

    if not all_stats:
        return None

    avg_mean = sum(s["mean"] for s in all_stats) / len(all_stats)
    avg_std = sum(s["std"] for s in all_stats) / len(all_stats)
    avg_var = sum(s["variance"] for s in all_stats) / len(all_stats)

    print(f"\n--- Placement Summary: {env_name} ({len(all_stats)} runs) ---")
    print(f"  Avg Mean Energy  : {avg_mean:.2f}")
    print(f"  Avg Variance     : {avg_var:.2f}")
    print(f"  Avg Std Dev      : {avg_std:.2f}")
    print(f"  Runs complete    : {len(all_stats)} / 5")

    if run_energies:
        plot_path = FIGURES_DIR / f"placement_runs_{env_name}.png"
        plot_placement_runs(run_energies, env_name, plot_path)

    return {"env": env_name, "mean": avg_mean, "std": avg_std, "variance": avg_var}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze CSI energy across environments and capture modes."
    )
    parser.add_argument(
        "--env",
        nargs="+",
        metavar="ENV",
        help="Environment folder name(s) to process. Defaults to all.",
    )
    parser.add_argument(
        "--mode",
        choices=["baseline_movement", "placement", "auto"],
        default="auto",
        help="Force analysis mode. Default: auto-detect per environment.",
    )
    args = parser.parse_args()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    environments = get_environments(args.env)
    print(f"[*] Environments to process: {[e.name for e in environments]}")

    env_summaries = []  # for cross-environment comparison plot

    for env_dir in environments:
        env_name = env_dir.name
        print(f"\n{'='*60}")
        print(f"  Environment : {env_name.upper()}")

        mode = args.mode if args.mode != "auto" else detect_mode(env_dir)
        print(f"  Mode        : {mode}")
        print(f"{'='*60}")

        if mode == "placement":
            summary = process_placement_runs(env_dir, env_name)
            if summary:
                env_summaries.append(summary)
        else:
            process_baseline_movement(env_dir, env_name)

    # Cross-environment comparison — only when 2+ placement environments have data
    if len(env_summaries) >= 2:
        print(f"\n{'='*60}")
        print(f"  CROSS-ENVIRONMENT COMPARISON ({len(env_summaries)} environments)")
        print(f"{'='*60}")
        for s in env_summaries:
            print(f"\n  {s['env']}")
            print(f"    Avg Mean Energy : {s['mean']:.2f}")
            print(f"    Avg Std Dev     : {s['std']:.2f}")
            print(f"    Avg Variance    : {s['variance']:.2f}")

        plot_path = FIGURES_DIR / "environment_comparison.png"
        plot_environment_comparison(env_summaries, plot_path)
        print(f"\n  📸 CAPTURE NOW")
        print(f"  Type    : SCREEN CAPTURE")
        print(f"  What    : environment_comparison.png in results/figures/")
        print(f"  Why     : CFP evidence — figure 07-environment-comparison-graph")
        print(f"  Filename: 07-environment-comparison-graph.png")

    print(f"\n[*] Done.")


if __name__ == "__main__":
    main()