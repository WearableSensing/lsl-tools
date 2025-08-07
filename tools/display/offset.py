import os
import argparse

from typing import List

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt
from scipy.signal import find_peaks


def plot_statistics_summary(diffs: np.ndarray, show: bool):
    """Creates a histogram to visualize the statistical distribution of
    timestamp differences.

    Args:
        diffs (np.ndarray): The array of timestamp differences.
        show (bool): Whether to show statistics summary.

    Returns:
       None
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
    if show:
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


def load_csv(csv_filepath: str, col_name: str):
    """This function reads the col_name from a CSV.

    Args:
        csv_filepath (str): The file path to the csv to analyze.
        col_name (str): The column name to look for in the csv file

    Returns:
        pd.DataFrame: The DataFrame containing the specified column.
    """
    if not os.path.exists(csv_filepath):
        raise FileNotFoundError(f"Error: The file '{csv_filepath}' was not found.")

    try:
        data = pd.read_csv(csv_filepath, skiprows=5, usecols=[col_name])
    except Exception as e:
        raise IOError(f"Error reading CSV file: {e}")

    if col_name not in data.columns:
        raise ValueError("Error: CSV file must contain a column named 'lsl_timestamp'.")
    return data


def lsl_timestamp_diffs(diffs: np.ndarray, start_value: int, end_value: int, show: bool):
    """Plots timestamp differences and optionally shows statistics.

    Args:
        diffs (np.ndarray): The array of timestamp differences.
        start_value (int): The starting x-value to crop (default 0).
        end_value (int): The ending x-value to crop (default 0).
        show (bool): The bool value to determine whether to show the
            statistics or not.

    Returns:
        None
    """
    spike_indices, _ = find_peaks(diffs, height=0.01, distance=5)
    print(f"Spikes found at sample numbers: {(spike_indices + 1).tolist()}")

    # Generate main plot.
    plt.figure(figsize=(12, 6))
    plt.title("LSL Timestamp Differences")
    plt.xlabel("Sample Number")
    plt.ylabel("Difference (seconds)")
    plt.plot(np.arange(1, len(diffs) + 1), diffs)
    # ... (rest of the main plotting code is the same)
    max_y_value: float = np.max(diffs)
    plt.ylim(bottom=np.min(diffs) - 0.01, top=max_y_value * 1.45)
    if start_value > 0 or end_value > 0:
        current_xlim = plt.xlim()
        left = start_value if start_value > 0 else current_xlim[0]
        right = end_value if end_value > 0 else current_xlim[1]
        plt.xlim(left, right)
    plt.grid(True, linestyle=":", alpha=0.6)

    plot_statistics_summary(diffs, show)
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script that reads a CSV file, calculates the "
        "differences between consecutive timestamps, and annotates every peak."
    )
    parser.add_argument("--filepath", type=str, help="The path to the CSV file. (Required)", required=True)
    parser.add_argument(
        "--start", type=int, default=0, help="Allows the crop start sample number to visualize" " plot better"
    )
    parser.add_argument(
        "--end", type=int, default=0, help="Allows the crop end sample number to visualize" " plot better"
    )
    parser.add_argument(
        "--show",
        type=bool,
        default=False,
        help="Allows to show a stats table describing the " "mean, range, and std to observe.",
    )

    args = parser.parse_args()

    # Load and process the data
    data = load_csv(args.filepath, "lsl_timestamp")
    lsl_timestamps = data["lsl_timestamp"].to_numpy()
    diffs = np.diff(lsl_timestamps)

    # Plot the differences
    lsl_timestamp_diffs(diffs, args.start, args.end, args.show)
