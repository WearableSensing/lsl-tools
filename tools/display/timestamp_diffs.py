import numpy as np
from typing import List
from matplotlib import pyplot as plt
import pandas as pd
import os
import argparse
from scipy.signal import find_peaks


def plot_statistics_summary(diffs: np.ndarray):
    """
    Creates a histogram to visualize the statistical distribution of timestamp differences.

    Parameters:
    -----------
        diffs (np.ndarray): The array of timestamp differences.
    """
    # 1. Calculate Statistics
    mean_val = np.mean(diffs)
    std_val = np.std(diffs)
    min_val: float = np.min(diffs)
    max_val: float = np.max(diffs)
    range_val = max_val - min_val

    stats_text = (
        f"Mean: {mean_val}\n"
        f"Std Dev: {std_val:.6f}s\n"
        f"Range:   {range_val:.6f}s\n"
        f"Min:     {min_val:.6f}s\n"
        f"Max:     {max_val:.6f}s"
    )

    # Place text box in the upper right corner
    plt.text(
        0.95,
        0.95,
        stats_text,
        transform=plt.gca().transAxes,
        fontsize=8,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.5", fc="wheat", alpha=0.5),
    )


def lsl_timestamp_diffs(csv_filepath: str, start_value: int, end_value: int):
    """
    This function reads 'lsl_timestamp' from a CSV, calculates the differences,
    and plots the results, highlighting every peak.
    """
    if not os.path.exists(csv_filepath):
        raise FileNotFoundError(f"Error: The file '{csv_filepath}' was not found.")

    try:
        data = pd.read_csv(csv_filepath, skiprows=5, usecols=["lsl_timestamp"])
    except Exception as e:
        raise IOError(f"Error reading CSV file: {e}")

    if "lsl_timestamp" not in data.columns:
        raise ValueError("Error: CSV file must contain a column named 'lsl_timestamp'.")

    lsl_timestamps = data["lsl_timestamp"].to_numpy()
    diffs = np.diff(lsl_timestamps)

    spike_indices, _ = find_peaks(diffs, height=0.01, distance=5)
    print(f"Spikes found at sample numbers: {(spike_indices + 1).tolist()}")

    # --- Generate the main plot ---
    plt.figure(figsize=(12, 6))
    plt.title("LSL Timestamp Differences")
    plt.xlabel("Sample Number")
    plt.ylabel("Difference (seconds)")
    plt.plot(np.arange(1, len(diffs) + 1), diffs)
    # ... (rest of the main plotting code is the same)
    max_y_value: float = np.max(diffs)
    plt.ylim(bottom=np.min(diffs) - 0.01, top=max_y_value * 1.45)
    for idx in spike_indices:
        plot_idx = idx + 1
        peak_value = diffs[idx]
        plt.axvline(x=plot_idx, color="gray", linestyle="--", linewidth=0.8, zorder=0)
        plt.annotate(
            text=f"{plot_idx}",
            xy=(plot_idx, 0),
            xytext=(plot_idx, -0.004),
            ha="center",
            arrowprops=dict(arrowstyle="->", color="red"),
        )
        plt.annotate(
            text=f"{peak_value:.4f}",
            xy=(plot_idx, peak_value),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color="darkgreen",
        )
    if start_value > 0 or end_value > 0:
        current_xlim = plt.xlim()
        left = start_value if start_value > 0 else current_xlim[0]
        right = end_value if end_value > 0 else current_xlim[1]
        plt.xlim(left, right)
    plt.grid(True, linestyle=":", alpha=0.6)

    plot_statistics_summary(diffs)
    plt.show()

    return (spike_indices + 1).tolist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script that reads a CSV file, calculates the differences between consecutive timestamps, and annotates every peak."
    )
    parser.add_argument("--filepath", type=str, help="The path to the CSV file. (Required)", required=True)
    parser.add_argument("--start", type=int, default=0, help="The start sample number for the plot's x-axis (1-based).")
    parser.add_argument("--end", type=int, default=0, help="The end sample number for the plot's x-axis (1-based).")

    args = parser.parse_args()

    lsl_timestamp_diffs(args.filepath, args.start, args.end)
