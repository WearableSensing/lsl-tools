import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Optional
import argparse

from tools.config import (
    DEFAULT_SOFTWARE_CH_NAME,
    DEFAULT_HARDWARE_CH_NAME,
    DEFAULT_TIMESTAMP_CH_NAME,
    DEFAULT_TARGETS,
)


# just plotting the values
def plot_offset(
    data: pd.DataFrame,
    timestamp_col: str,
    source_channel: str,
    target_channels: list[str],
    offset_value: Optional[float] = 0.0,
) -> None:
    """
    Plots channel signals, annotates rise times, and displays offset stats.

    Args:
        data (pd.DataFrame): Preprocessed DataFrame with all necessary columns.
        timestamp_col (str): The name of the timestamp column.
        source_channel (str): The name of the source (ground truth) channel.
        target_channels (List[str]): List of target channels to compare
        against the source.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    all_channels = [source_channel] + target_channels

    for channel in all_channels:
        ax.plot(
            data.index, data[channel], label=channel, drawstyle="steps-post"
        )

    source_rises, target_rises_list = find_rises(
        data, source_channel, target_channels
    )

    all_stats_text = []
    offsets_to_plot = []
    for i, channel in enumerate(target_channels):
        offsets = calculate_time_offsets(
            source_rises,
            target_rises_list[i],
            data,
            timestamp_col,
            offset_value,
        )
        offsets_to_plot.append(offsets)
        stats_text = format_display_text(f"Offset ({channel})", offsets)
        all_stats_text.append(stats_text)

    plot_offset_difference(offsets_to_plot, target_channels)

    final_display_text = "\n\n".join(all_stats_text)
    ax.text(
        0.98,
        0.98,
        final_display_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.5", fc="wheat", alpha=0.8),
    )

    all_rises = [source_rises] + target_rises_list
    for i, channel in enumerate(all_channels):
        for index in all_rises[i]:
            x_pos, y_pos = index, data.loc[index, channel]
            timestamp = data.loc[index, timestamp_col]
            ax.annotate(
                f"{timestamp:.2f}",
                (x_pos, y_pos),
                textcoords="offset points",
                xytext=(0, 5),
                ha="center",
                fontsize=8,
            )

    ax.set_title("Comparison of Hardware and Software Triggers", fontsize=16)
    ax.set_xlabel("Sample Index", fontsize=12)
    ax.set_ylabel("Signal Value", fontsize=12)
    ax.legend(loc="upper left")
    ax.grid(True)
    ax.set_xlim(0, 250)
    ax.set_ylim(-0.5, 3.5)
    plt.tight_layout()
    plt.show()


def plot_offset_difference(
    all_offsets: list[list[float]], labels: list[str]
) -> None:
    """
    Plots the change in signal offsets over each trial.

    This creates a "drift plot" to visualize the stability of the offsets.

    Args:
        all_offsets (List[List[float]]): A list containing lists of offset
                                         values. Each inner list represents a
                                         channel.
        labels (List[str]): A list of labels corresponding to each offset list.
    """
    print("Plotting offset drift over trials...")
    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot each list of offsets as a separate line
    for i, offset_list in enumerate(all_offsets):
        if offset_list:  # Only plot if the list is not empty
            ax.plot(
                range(1, len(offset_list) + 1),  # X-axis: Trial number
                offset_list,  # Y-axis: Offset value
                marker="o",
                linestyle="-",
                label=labels[i],
            )

    ax.set_title("Trigger Offset Tracker", fontsize=16)
    ax.set_xlabel("Trial", fontsize=12)
    ax.set_ylabel("Offset (in seconds)", fontsize=12)
    ax.legend()
    ax.grid(True)

    # Ensure the x-axis uses integers for trial numbers
    ax.xaxis.get_major_locator().set_params(integer=True)

    plt.tight_layout()


# preprocess of csv file into dataframe
def preprocess(
    csv_filepath: str,
    timestamp_col: str,
    source_channel: str,
    target_channels: list[str],
) -> pd.DataFrame:
    """
    Opens a CSV file and loads specified channels into a pandas DataFrame.

    This function efficiently reads only the necessary columns for analysis,
    validates their existence, and returns a clean DataFrame.

    Args:
        csv_filepath (str): The full path to the input CSV file.
        timestamp_col (str): The name of the timestamp column.
        source_channel (str): The name of the source (ground truth) channel.
        target_channels (List[str]): A list of target channel names to include.

    Returns:
        pd.DataFrame: A DataFrame containing only the requested columns.
                      Returns an empty DataFrame if preprocessing fails.
    """
    # Check if the file exists before trying to open it.
    if not os.path.exists(csv_filepath):
        print(f"Error: The file was not found at '{csv_filepath}'")
        return pd.DataFrame()

    # Combine all required channel names into a single list.
    # Using dict.fromkeys to remove any potential duplicates.
    all_required_columns = list(
        dict.fromkeys([timestamp_col, source_channel] + target_channels)
    )

    try:
        # Read the CSV, but only load the columns specified in `usecols`.
        # This is highly memory-efficient for large files.
        print(f"Loading data from '{csv_filepath}'...")
        data = pd.read_csv(csv_filepath, usecols=all_required_columns)
        return data

    except ValueError as e:
        # This error occurs if a column in `usecols` is not in the CSV.
        print("Error: A required column was not found in the CSV file.")
        print(f"Details: {e}")
        return pd.DataFrame()
    except Exception as e:
        # Catch any other unexpected errors during file processing.
        print(f"An unexpected error occurred during preprocessing: {e}")
        return pd.DataFrame()


def find_rises(
    data: pd.DataFrame, source_channel: str, target_channels: list[str]
) -> Tuple[list[int], list[list[int]]]:
    """
    Finds the indices of rising edges for source and target channels.

    A rising edge is defined as a sample where the value changes from 0 to > 0.

    Args:
        data (pd.DataFrame): The preprocess DataFrame containing channel data.
        source_channel (str): The name of the source (ground truth) channel.
        target_channels (List[str]): A list of target channel names to analyze.

    Returns:
        Tuple[List[int], List[List[int]]]: A tuple containing two elements:
        1. A list of integer indices for the source channel's rises.
        2. A list of lists, where each inner list contains the rise
           indices for a target channel, in the same order as the input.
    """
    print("\nFinding rising edges for all channels...")

    # --- Find Rises for the Source Channel ---
    # .diff() calculates the difference from the previous row.
    # A positive difference indicates a rise from a lower value.
    source_rises = data[data[source_channel].diff() > 0].index.to_list()
    print(
        f"  -> Found {len(source_rises)} events for source '{source_channel}'."
    )

    # --- Find Rises for each Target Channel ---
    all_target_rises = []
    for channel in target_channels:
        # Apply the same logic for each target channel
        target_rises = data[data[channel].diff() > 0].index.to_list()
        print(f"  -> Found {len(target_rises)} events for target '{channel}'.")
        all_target_rises.append(target_rises)

    return (source_rises, all_target_rises)


def calculate_time_offsets(
    source_rises: list[int],
    target_rises: list[int],
    data: pd.DataFrame,
    timestamp_col: str,
    offset_value: Optional[float] = 0.0,
) -> list[float]:
    """
    Calculates the timestamp offsets between a source and target signal.

    This function assumes a one-to-one correspondence between the events in
    source_rises and target_rises. The offset is calculated as
    (target_timestamp - source_timestamp) for each pair of events.

    Args:
        source_rises (list[int]): A list of sample indices where the source
                                  (ground truth) signal rises.
        target_rises (list[int]): A list of sample indices where the target
                                  signal rises.
        data (pd.DataFrame): The DataFrame containing the channel and
                             timestamp data.
        timestamp_col (str): The name of the timestamp column in the DataFrame.

    Returns:
        list[float]: A list of the calculated offset values in seconds.
                     Returns an empty list if event counts mismatch or are zero
    """
    num_common_events = min(len(source_rises), len(target_rises))

    if len(source_rises) != len(target_rises):
        print(
            f"Warning: Mismatch in event counts. "
            f"Source has {len(source_rises)}, Target has {len(target_rises)}."
        )
        print(
            f"--> Proceeding with the first {num_common_events} common events."
        )

    # If there are no common events, return an empty list.
    if num_common_events == 0:
        print("No common events found to compare.")
        return []

    # Truncate both lists to the common length.
    source_rises_truncated = source_rises[:num_common_events]
    target_rises_truncated = target_rises[:num_common_events]

    # Get timestamps for the truncated lists.
    source_times = data.loc[source_rises_truncated, timestamp_col].values
    target_times = data.loc[target_rises_truncated, timestamp_col].values

    # Calculate the offsets by direct, element-wise subtraction.
    offsets = (target_times - source_times) - offset_value

    # Convert the resulting NumPy array to a list and return it.
    return offsets.tolist()


# Decomposes a channel
def split_channel(
    filepath: str,
    channel_to_split: str,
    new_channels: list[str],
    channel_values: list[int],
) -> None:
    """
    Reads a CSV, splits a composite trigger channel, and saves the result
    to a new file with a 'split_' prefix.

    This function assumes trigger values are powers of two (1, 2, 4, etc.)
    and that composite values are the sum of their components (e.g., 3 = 1 + 2)

    Args:
        filepath (str): The path to the CSV file.
        channel_to_split (str): The name of the column containing the composite
                                trigger values.
        new_channels (list[str]): A list of the new channel names to create.
        channel_values (list[int]): A list of the unique integer trigger values
                                    corresponding to each new channel name.
    """
    # (Argument and file existence checks remain the same)
    if len(new_channels) != len(channel_values):
        print(
            "Error: The 'new_channels' and 'channel_values' lists must have \
                the same length."
        )
        return
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' was not found.")
        return

    try:
        # (Reading and processing logic remains the same)
        print(f"Reading data from '{filepath}'...")
        data = pd.read_csv(filepath)

        if channel_to_split not in data.columns:
            print(
                f"Error: Column '{channel_to_split}' not found in the CSV \
                    file."
            )
            return

        data[channel_to_split] = data[channel_to_split].astype(int)

        for new_name, unique_value in zip(new_channels, channel_values):
            data[new_name] = 0
            is_active = (data[channel_to_split] & unique_value) != 0
            data.loc[is_active, new_name] = unique_value

        print(f"Removing original column '{channel_to_split}'...")
        data = data.drop(columns=[channel_to_split])

        # 1. Generate a new filename by adding '_split' before the extension.
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        new_filepath = f"split_{filename}"
        output_path = os.path.join(directory, new_filepath)

        # 2. Save the modified DataFrame to the new file path.
        print(f"Saving split channels to new file: '{new_filepath}'...")
        data.to_csv(output_path, index=False)

        print("Done ✅")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# The stats table
def format_display_text(label: str, offset: list[float]) -> str:
    """
    Formats the display text to include detailed statistics including mean,
    std, min, max, and range.
    """
    if not offset:
        return f"{label}: Not found"

    # --- Bug Fix Start ---
    # The original function modified the list in place, which is a side effect.
    # This version works on a copy to avoid altering the original offset list.
    offset_copy = offset.copy()
    if len(offset_copy) < 2:
        # Cannot calculate range with fewer than 2 values after removing one.
        # Handle this case gracefully.
        mean_val = np.mean(offset_copy)
        std_val = np.std(offset_copy)
        min_val: float = np.min(offset_copy)
        max_val: float = np.max(offset_copy)
        range_val = max_val - min_val
    else:
        mean_val = np.mean(offset_copy)
        std_val = np.std(offset_copy)
        sorted_offsets = sorted(offset_copy)
        min_val = sorted_offsets[1]  # The second smallest value
        max_val = sorted_offsets[-2]  # The second largest value
        range_val = max_val - min_val

    stats_text = (
        f"{label}\n"
        f"  Mean: {mean_val:.4f} s\n"
        f"  SD:   {std_val:.4f} s\n"
        f"  Min:  {min_val:.4f} s\n"
        f"  Max:  {max_val:.4f} s\n"
        f"  Range:{range_val:.4f} s"
    )
    return stats_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script that reads a CSV file, calculates the "
        "offsets between triggers"
    )
    parser.add_argument(
        "--filepath",
        type=str,
        help="The path to the CSV file. (Required)",
        required=True,
    )
    parser.add_argument(
        "--source",
        type=str,
        default=DEFAULT_SOFTWARE_CH_NAME,
        help="The source channel name",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=DEFAULT_TARGETS,
        help="List of targeted channels.",
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default=DEFAULT_TIMESTAMP_CH_NAME,
        help="The timestamp channel name",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Split the hardware triggers first",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="A offset value you can add, it will not affect the normal graph \
            It will only show a difference on the offset difference graph and \
                stats table.",
    )
    args = parser.parse_args()

    filepath = args.filepath
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    if args.split:
        split_channel(filepath, DEFAULT_HARDWARE_CH_NAME, args.targets, [2, 1])
        filepath = "split_" + filename
    else:
        filepath = filename
    
    output_path = os.path.join(directory, filepath)

    data = preprocess(output_path, args.timestamp, args.source, args.targets)
    plot_offset(data, args.timestamp, args.source, args.targets, args.offset)
