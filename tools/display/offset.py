import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np


def plot_offset_difference(offset1, offset2):
    """
    Plots the change in signal offsets over time on a second graph.

    Args:
        offset1 (list): A list of offset values for the first signal.
        offset2 (list): A list of offset values for the second signal.
    """
    # Make sure there is data
    if not offset1 and not offset2:
        print("No offset data found to generate the second plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot each offsets
    if offset1:
        ax.plot(range(1, len(offset1) + 1), offset1, marker="o", linestyle="-", label="Offset (MMBTS)")
    if offset2:
        ax.plot(range(1, len(offset2) + 1), offset2, marker="x", linestyle="--", label="Offset (PsychoPy)")

    # Labels and Titles
    ax.set_title("Trigger Offset Tracker", fontsize=16)
    ax.set_xlabel("Trial", fontsize=12)
    ax.set_ylabel("Offset (in seconds)", fontsize=12)
    ax.legend()
    ax.grid(True)

    # Ensure the x-axis uses integers for samples
    ax.xaxis.get_major_locator().set_params(integer=True)

    plt.tight_layout()


def offset(csv_filepath: str, channel1: str, channel2: str, timestamp_col: str):
    """
    Loads channels, separates one into components, plots them with timestamp annotations,
    and calculates the separate offsets from the lightdiode to the other signals.

    Args:
        csv_filepath (str): The file path to the CSV to analyze.
        channel1 (str): The name of the primary channel column (e.g., PsychoPy marker).
        channel2 (str): The name of the composite channel to be separated (e.g., WS-default_TRG).
        timestamp_col (str): The name of the timestamp column.

    Returns:
        tuple: A tuple containing the list of MMBTS offsets and PsychoPy offsets.
    """
    # Check if file exist
    if not os.path.exists(csv_filepath):
        print(f"Error: The file '{csv_filepath}' was not found.")
        return [], []

    try:
        # Read all required columns from the CSV at once
        columns_to_load = [channel1, channel2, timestamp_col]
        print(f"Loading columns {columns_to_load}...")
        data = pd.read_csv(csv_filepath, usecols=columns_to_load)

        # Separate the composite channel (channel2) into two signals
        print(f"Separating '{channel2}' into its component signals...")
        data["MMBTS"] = 0
        data.loc[data[channel2].isin([2, 3]), "MMBTS"] = 2
        data["lightdiode"] = 0
        data.loc[data[channel2].isin([1, 3]), "lightdiode"] = 1

        # Create the plot with the three signals
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot the signals
        ax.plot(data.index, data[channel1], label=channel1, color="blue", drawstyle="steps-post")
        ax.plot(data.index, data["MMBTS"], label="MMBTS (Step to 2)", color="green", drawstyle="steps-post")
        ax.plot(
            data.index,
            data["lightdiode"],
            label="lightdiode (Step to 1)",
            color="red",
            drawstyle="steps-post",
            alpha=0.8,
        )

        # Find step-up points and add timestamp annotations
        signals_to_annotate = [channel1, "MMBTS", "lightdiode"]
        for signal in signals_to_annotate:
            step_ups = data[signal].diff() > 0
            for index in data[step_ups].index:
                x_pos, y_pos = index, data[signal][index]
                timestamp = data[timestamp_col][index]
                ax.annotate(
                    f"{timestamp:.2f}",
                    (x_pos, y_pos),
                    textcoords="offset points",
                    xytext=(0, 5),
                    ha="center",
                    fontsize=8,
                    color="black",
                )

        # Calculate and display the separate offsets
        lightdiode_rises = data[data["lightdiode"].diff() > 0].index.to_list()
        mmbts_rises = data[data["MMBTS"].diff() > 0].index.to_list()
        psychopy_rises = data[data[channel1].diff() > 0].index.to_list()

        def calculate_time_offsets(source_rises, target_rises, data, timestamp_col):
            """Pairs events on a 1-to-1 basis and calculates the offset."""
            offsets = []
            num_events = min(len(source_rises), len(target_rises))
            for i in range(num_events):
                source_idx = source_rises[i]
                target_idx = target_rises[i]
                time_offset = data[timestamp_col][target_idx] - data[timestamp_col][source_idx]
                offsets.append(time_offset)
            return offsets

        # This function now formats the text to include mean, std, min, max, and range.
        def format_display_text(label, offsets):
            """Formats the display text to include detailed statistics."""
            if not offsets:
                return f"{label}: Not found"

            mean_val = np.mean(offsets)
            std_val = np.std(offsets)
            min_val: float = np.min(offsets)
            max_val: float = np.max(offsets)
            range_val = max_val - min_val

            # Create a multi-line string with all the stats
            stats_text = (
                f"{label}\n"
                f"  Mean: {mean_val:.4f} s\n"
                f"  SD:   {std_val:.4f} s\n"
                f"  Min:  {min_val:.4f} s\n"
                f"  Max:  {max_val:.4f} s\n"
                f"  Range:{range_val:.4f} s"
            )
            return stats_text

        # Both offsets are now calculated relative to the lightdiode as the source.
        offsets_mmbts = calculate_time_offsets(lightdiode_rises, mmbts_rises, data, timestamp_col)
        offsets_psychopy = calculate_time_offsets(lightdiode_rises, psychopy_rises, data, timestamp_col)

        display_text_mmbts = format_display_text("Offset (MMBTS)", offsets_mmbts)
        display_text_psychopy = format_display_text("Offset (PsychoPy)", offsets_psychopy)
        final_display_text = f"{display_text_mmbts}\n\n{display_text_psychopy}"

        ax.text(
            0.97,
            0.97,
            final_display_text,
            transform=ax.transAxes,
            fontsize=8,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round,pad=0.5", fc="wheat", alpha=0.7),
        )

        # labels and a title
        ax.set_title("Comparison of PsychoPy Marker and Separated TRG Components", fontsize=16)
        ax.set_xlabel("Sample Index", fontsize=12)
        ax.set_ylabel("Signal Value", fontsize=12)
        ax.legend()
        ax.grid(True)
        ax.set_xlim(0, 250)
        ax.set_ylim(-0.5, 3.5)
        plt.tight_layout()

        return offsets_mmbts, offsets_psychopy

    except ValueError:
        print(
            f"Error: Could not find one or more columns in the file '{csv_filepath}'. Please double-check the column names."
        )
        return [], []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return [], []


if __name__ == "__main__":
    file_path = "experiment_data-20250812-140409.csv"

    # Call the first function to generate the primary plot and get the offset data
    mmbts_offsets, psychopy_offsets = offset(
        csv_filepath=file_path,
        channel1="PsychoPyMarkers_SoftwareMarker",
        channel2="WS-default_TRG",
        timestamp_col="lsl_timestamp",
    )

    # Call the second function to generate the offset drift plot
    plot_offset_difference(mmbts_offsets, psychopy_offsets)

    # Display all generated plots
    print("\nPlot windows are now open.")
    print("Use the pan/zoom tools in the plot windows to navigate the data.")
    plt.show()
    print("Plots displayed successfully.")
