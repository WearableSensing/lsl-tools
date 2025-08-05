import numpy as np
from typing import List
from matplotlib import pyplot as plt
import pandas as pd
import os
import argparse
from scipy.signal import find_peaks


def lsl_timestamp_diffs(csv_filepath: str, start_value: int, end_value: int):
    """
    This function reads 'lsl_timestamp' from a CSV, calculates the differences,
    and plots the results, highlighting and annotating every peak.

    Parameters:
    -----------
        csv_filepath (str): The path to the CSV file.
        start_value (int): The starting index for the x-axis crop.
        end_value (int): The ending index for the x-axis crop.
    Returns:
    -----------
    """
    if not os.path.exists(csv_filepath):
        raise FileNotFoundError(f"Error: The file '{csv_filepath}' was not found.")

    try:
        # Read the CSV file, skipping the first 5 rows and using only 'lsl_timestamp' column.
        data = pd.read_csv(csv_filepath, skiprows=5, usecols=["lsl_timestamp"])
    except Exception as e:
        raise IOError(f"Error reading CSV file: {e}")

    if "lsl_timestamp" not in data.columns:
        raise ValueError("Error: CSV file must contain a column named 'lsl_timestamp'.")

    lsl_timestamps = data["lsl_timestamp"].to_numpy()
    diffs = np.diff(lsl_timestamps)

    # Finds every peak using scipy
    spike_indices, _ = find_peaks(diffs, height=0.01, distance=5)
    print(spike_indices.tolist())

    plt.title("LSL Timestamp Differences")
    plt.xlabel("Sample Index")
    plt.ylabel("Difference (seconds)")

    plt.plot(diffs, label="Timestamp Difference")
    max_y_value: float = np.max(diffs)
    plt.ylim(top=max_y_value * 1.2)

    for idx in spike_indices:
        peak_value = diffs[idx]
        plt.annotate(
            text=f"{idx}",
            xy=(idx, peak_value),
            xytext=(0, 15),
            textcoords="offset points",
            ha="center",
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", color="red"),
        )
        plt.plot(idx, peak_value, "ro", label="_nolegend_")

    # Simplified logic for cropping the x-axis
    if start_value > 0 or end_value > 0:
        current_xlim = plt.xlim()
        left = start_value if start_value > 0 else current_xlim[0]
        right = end_value if end_value > 0 else current_xlim[1]
        plt.xlim(left, right)

    plt.show()

    return spike_indices.tolist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script that reads a CSV file, calculates the differences between consecutive timestamps, and annotates every peak."
    )
    # --- Arguments are unchanged ---
    parser.add_argument(
        "--filepath",
        type=str,
        help="The path to the CSV file. (Required)",
        required=True,
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="The start index for the plot's x-axis (default: 0, no crop).",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=0,
        help="The end index for the plot's x-axis (default: 0, no crop).",
    )
    args = parser.parse_args()

    lsl_timestamp_diffs(args.filepath, args.start, args.end)
