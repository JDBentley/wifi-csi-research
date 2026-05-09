import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


BASELINE_FILE = "baseline_01.csv"
MOVEMENT_FILE = "movement_01.csv"


def load_csi_file(filename):
    rows = []

    with open(filename, "r") as file:
        for line in file:

            line = line.strip()

            # Skip logs and empty lines
            if not line:
                continue

            # Only keep lines starting with numbers
            if not line[0].isdigit():
                continue

            parts = line.split(",")

            try:
                values = [int(x) for x in parts]
                rows.append(values)
            except ValueError:
                continue

    return pd.DataFrame(rows)


def calculate_signal_energy(df):
    # Skip timestamp, RSSI, len
    csi_values = df.iloc[:, 3:]

    # Energy = sum of squared CSI values
    energy = (csi_values ** 2).sum(axis=1)

    return energy


def main():

    print("[*] Loading datasets...")

    baseline_df = load_csi_file(BASELINE_FILE)
    movement_df = load_csi_file(MOVEMENT_FILE)

    print(f"[+] Baseline rows: {len(baseline_df)}")
    print(f"[+] Movement rows: {len(movement_df)}")

    print("[*] Calculating signal energy...")

    baseline_energy = calculate_signal_energy(baseline_df)
    movement_energy = calculate_signal_energy(movement_df)

    print("[*] Creating graph...")

    plt.figure(figsize=(12, 6))

    plt.plot(
        baseline_energy.values,
        label="Baseline"
    )

    plt.plot(
        movement_energy.values,
        label="Movement"
    )

    plt.xlabel("Sample Number")
    plt.ylabel("Signal Energy")
    plt.title("Baseline vs Movement CSI Energy")
    plt.legend()

    output_path = Path("analysis/output/energy_comparison.png")

    plt.savefig(output_path)

    print(f"[+] Graph saved to: {output_path}")


if __name__ == "__main__":
    main()