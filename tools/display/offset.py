import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

DEFAULT_SOFTWARE_CH_NAME = "PsychoPyMarkers_SoftwareMarker"
DEFAULT_HARDWARE_CH_NAME = "WS-default_TRG"
DEFAULT_TIMESTAMP_CH_NAME = "lsl_timestamp"


def plot_offset_difference(offsets: list[list], labels: list[str]) -> None:
    """
    Plots the change in signal offsets over time on a different graph.

    Args:
        offsets (list[list]): List of lists of offset values to plot.
        labels (list[str]): List of labels in accordance to offsets.
    Returns: None
    """

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot each offsets
    index = 0
    for o in offsets:
        if o:
            ax.plot(
                range(1, len(o) + 1),
                o,
                marker="o",
                linestyle="-",
                label=labels[index],
            )
        index += 1

    # Labels and Titles
    ax.set_title("Trigger Offset Tracker", fontsize=16)
    ax.set_xlabel("Trial", fontsize=12)
    ax.set_ylabel("Offset (in seconds)", fontsize=12)
    ax.legend()
    ax.grid(True)

    # Ensure the x-axis uses integers for samples
    ax.xaxis.get_major_locator().set_params(integer=True)

    plt.tight_layout()


def calculate_time_offsets(
    source_rises: list[int],
    target_rises: list[int],
    data: pd.DataFrame,
    timestamp_col: str,
) -> list[float]:
    """
    Calculates the offsets based on the rises of each signal.

    Args:
        sources_rises (list[int]): The rising index of the source.
        target_rises (list[int]): The rising index of the target.
        data (pd.DataFrame): The data extracted from the CSV file.
        timestamp_col (str): The name of the timestamp column.

        Returns:
            offset (list): The list of offsets

    """
    offset = []
    num_events = min(len(source_rises), len(target_rises))
    for i in range(num_events):
        source_idx = source_rises[i]
        target_idx = target_rises[i]
        time_offset = (
            data[timestamp_col][target_idx] - data[timestamp_col][source_idx]
        )
        offset.append(time_offset)
    return offset


def format_display_text(label: str, offset: list[float]) -> str:
    """
    Formats the display text to include detailed statistics including mean,
    std, min, max, and range.

    Args:
        label (str): The label for the offset stats
        offset (list[float]): The list of offsets

    Returns: stats_text (str): The stats as str
    """
    if not offset:
        return f"{label}: Not found"

    mean_val = np.mean(offset)
    std_val = np.std(offset)
    min_val: float = np.min(offset)
    max_val: float = np.max(offset)
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


def offset_hardware_software(
    csv_filepath: str,
    softChannel: str,
    hardChannel: str,
    timestamp_col: str,
    hardwareTrigVal: list[int],
) -> list[list[float]]:
    """
    Loads channels, separates one into components, plots them with timestamp
    annotations, and calculates the separate offsets from the lightdiode
    the other signals.

    Args:
        csv_filepath (str): The file path to the CSV to analyze.
        softChannel (str): The name of the software channel column
                            (e.g., PsychoPy marker).
        hardChannel (str): The name of the composite hardware channel
                            to be separated (e.g., WS-default_TRG).
        timestamp_col (str): The name of the timestamp column.
        hardwareTrigVal (list[int]): The trigger values for each hardware
                                        triggers(To implement)

    Returns: None
    """
    # Check if file exist
    if not os.path.exists(csv_filepath):
        print(f"Error: The file '{csv_filepath}' was not found.")
        return [[], []]

    try:
        # Read all required columns from the CSV at once
        columns_to_load = [softChannel, hardChannel, timestamp_col]
        print(f"Loading columns {columns_to_load}...")
        data = pd.read_csv(csv_filepath, usecols=columns_to_load)

        # Separate the composite channel (hardChannel) into two signals
        print(f"Separating '{hardChannel}' into its component signals...")
        # ---- Need to implement hardwareTrigVal if needed ----
        data["MMBTS"] = 0
        data.loc[data[hardChannel].isin([2, 3]), "MMBTS"] = 2
        data["lightdiode"] = 0
        data.loc[data[hardChannel].isin([1, 3]), "lightdiode"] = 1

        # Create the plot with the three signals
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot the signals
        ax.plot(
            data.index,
            data[softChannel],
            label=softChannel,
            color="blue",
            drawstyle="steps-post",
        )
        ax.plot(
            data.index,
            data["MMBTS"],
            label="MMBTS (Step to 2)",
            color="green",
            drawstyle="steps-post",
        )
        ax.plot(
            data.index,
            data["lightdiode"],
            label="lightdiode (Step to 1)",
            color="red",
            drawstyle="steps-post",
            alpha=0.8,
        )

        # Calculate rise indices for the signal and store in the dictionary
        signals_of_interest = [softChannel, "MMBTS", "lightdiode"]
        rise_events = {}
        for signal in signals_of_interest:
            indices = data[data[signal].diff() > 0].index.to_list()
            rise_events[signal] = indices
            print(f"  Found {len(indices)} events for '{signal}'.")

        # Annotate the plot
        for signal, indices in rise_events.items():
            for index in indices:
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

        # Calculated offsets relative to the lightdiode as the source.
        lightdiode_rises = rise_events.get("lightdiode", [])
        mmbts_rises = rise_events.get("MMBTS", [])
        psychopy_rises = rise_events.get(softChannel, [])
        offsets_mmbts = calculate_time_offsets(
            lightdiode_rises, mmbts_rises, data, timestamp_col
        )
        offsets_psychopy = calculate_time_offsets(
            lightdiode_rises, psychopy_rises, data, timestamp_col
        )

        display_text_mmbts = format_display_text(
            "Offset (MMBTS)", offsets_mmbts
        )
        display_text_psychopy = format_display_text(
            "Offset (PsychoPy)", offsets_psychopy
        )
        final_display_text = f"{display_text_mmbts}\n\n{display_text_psychopy}"

        # The stats table
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
        ax.set_title(
            "Comparison of PsychoPy Marker and Separated TRG \
                     Components",
            fontsize=16,
        )
        ax.set_xlabel("Sample Index", fontsize=12)
        ax.set_ylabel("Signal Value", fontsize=12)
        ax.legend()
        ax.grid(True)
        ax.set_xlim(0, 250)
        ax.set_ylim(-0.5, 3.5)
        plt.tight_layout()

        return [offsets_mmbts, offsets_psychopy]

    except ValueError:
        print(
            f"Error: Could not find one or more columns in the file \
                '{csv_filepath}'. Please double-check the column names."
        )
        return [[], []]
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return [[], []]


if __name__ == "__main__":
    import argparse

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
        "--hs", action="store_true", help="Runs offset_hardware_software"
    )
    parser.add_argument(
        "--software",
        type=str,
        default=DEFAULT_SOFTWARE_CH_NAME,
        help="The software channel name",
    )
    parser.add_argument(
        "--hardware",
        type=str,
        default=DEFAULT_HARDWARE_CH_NAME,
        help="The hardware cahnnel name",
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default=DEFAULT_TIMESTAMP_CH_NAME,
        help="The timestamp channel name",
    )

    args = parser.parse_args()

    if args.hs:
        offsets = offset_hardware_software(
            csv_filepath=args.filepath,
            softChannel=args.software,
            hardChannel=args.hardware,
            timestamp_col=args.timestamp,
            hardwareTrigVal=[1, 2],
        )
        # Call the second function to generate the offset drift plot
        plot_offset_difference(offsets, ["mmbts_offsets", "psychopy_offsets"])
    # else:
    #     offsets = offset_standard()

    plt.show()
    print("Plots displayed successfully.")
