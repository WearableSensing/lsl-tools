from tools.experiment.photodiode import photodiode, createMarkerStream
import time
import sys
import os
import subprocess

from tools.config import (
    DEFAULT_STREAM_NAME,
    DEFAULT_TRIAL_AMOUNT,
    DEFAULT_TRIG,
    DEFAULT_DISPLAY_RATE,
    DEFAULT_OFFSET_VALUE,
    DEFAULT_PORT
)


def main():
    menu = """
    Please select an option:
        1. Photodiode
    """
    print(menu)

    # Get the user's choice
    choice = input("Enter your choice (1): ") or "1"

    match choice:
        case "1":
            run_photodiode_experiment()

        case _:
            print(
                f"\n Invalid choice: '{choice}'. Please run the script "
                + "again and select a number between 1 and 5."
            )


def run_photodiode_experiment():
    """
    Gathers parameters, handles recording, and runs the photodiode experiment.
    """
    # --- Initialization ---
    com_port = None
    hardware_stream = None
    software_stream = None
    software_stream_outlet = None
    recorder_process = None

    # --- Gather Parameters ---
    if get_boolean_input("Do you want to connect a MMBTS? (y/n): "):
        com_port = (input("What is the COM port for MMBTS? "
                          + f"(DEFAULT: {DEFAULT_PORT}):")
                    or DEFAULT_PORT)
        hardware_stream = DEFAULT_STREAM_NAME

    if get_boolean_input("Do you want to send software triggers? (y/n): "):
        software_stream = (
            input("Create a marker stream name (DEFAULT: PsychoPyMarkers): ")
            or "PsychoPyMarkers")
        trig_val_input = input("Input a unique software integer trigger " +
                               f"(DEFAULT: {DEFAULT_TRIG}):")
        if trig_val_input == "":
            trig_val = DEFAULT_TRIG
        try:
            trig_val = int(trig_val_input)
        except ValueError:
            print(f"Invalid input. Using DEFAULT ({DEFAULT_TRIG})...:")
            trig_val = DEFAULT_TRIG
        software_stream_outlet = createMarkerStream(software_stream, trig_val)

    trials_input = input("How many trials do you want to run?"
                         + f"(DEFAULT: {DEFAULT_TRIAL_AMOUNT}):")
    if not trials_input.strip():
        trials = DEFAULT_TRIAL_AMOUNT
    try:
        trials = int(trials_input)
    except ValueError:
        print("Invalid input. Using DEFAULT..")
        trials = DEFAULT_TRIAL_AMOUNT
    display_rate_input = input(
        "At what rate do you want the flashes to run? ("
        + f" DEFAULT: {DEFAULT_DISPLAY_RATE}): "
    )
    if not display_rate_input.strip():
        display_rate = DEFAULT_DISPLAY_RATE
    try:
        display_rate = float(display_rate_input)
    except ValueError:
        print("Invalid input. Using DEFAULT..")
        display_rate = DEFAULT_DISPLAY_RATE
    offset_value_input = input(
        "At what rate do you want to offset? ("
        + f" DEFAULT: {DEFAULT_OFFSET_VALUE}): "
    )
    if not offset_value_input.strip():
        offset_value = DEFAULT_OFFSET_VALUE
    try:
        offset_value = float(offset_value_input)
    except ValueError:
        print("Invalid input. Using DEFAULT..")
        offset_value = DEFAULT_OFFSET_VALUE

    # --- Handle Recording using Subprocess ---
    if get_boolean_input("Do you want to record? (y/n): "):
        duration = 5 + (trials * display_rate * 2)  # Add extra buffer time
        print(trials)
        print(display_rate)
        streams_to_record = []
        if hardware_stream:
            streams_to_record.append(hardware_stream)
        if software_stream:
            streams_to_record.append(software_stream)

        if not streams_to_record:
            print(
                "Warning: Recording requested, but no streams "
                + "were specified."
            )
        else:
            # This assumes your recorder script is in a 'consume' subdirectory
            # Adjust the path if your file structure is different.
            current_dir = os.path.dirname(os.path.abspath(__file__))
            recorder_script_path = os.path.join(
                current_dir, "tools", "consume", "unified_receive.py"
            )

            if not os.path.exists(recorder_script_path):
                print(
                    "FATAL ERROR: Recorder script not found "
                    + f"at {recorder_script_path}"
                )
                print(
                    "Please ensure 'unified_receive.py' is in a 'consume' "
                    + "folder next to this script."
                )
                sys.exit(1)  # Exit if the recorder can't be found

            # Command to run the unified recorder script in a new process
            command = [
                sys.executable,  # The current python interpreter
                recorder_script_path,
                "--streams",
                *streams_to_record,  # Unpack the list of streams
                "--duration",
                str(int(duration)),
                "--filename",
                "./photodiode_exp",
            ]

            print("Starting recorder as a background process...")
            print(f"Command: {' '.join(command)}")

            # Use Popen to start the recorder as a non-blocking background
            # process
            recorder_process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(2)  # Give the recorder a moment to start up

    # --- Run Experiment ---
    # This runs in the main process, concurrently with the recorder process.
    try:
        photodiode(
            com_port,
            software_stream_outlet,
            trials,
            display_rate,
            offset_value,
        )
    except Exception as e:
        print(f"An error occurred during the photodiode experiment: {e}")
    finally:
        # --- Cleanup ---
        # If a recorder process was started, wait for it to finish.
        if recorder_process:
            print("Waiting for recorder process to finish...")
            # .communicate() waits for the process to end and gets its output
            stdout, stderr = recorder_process.communicate()

            print("--- Recorder Script Output ---")
            if stdout:
                print(stdout.decode())
            if stderr:
                print("--- Recorder Script Errors ---")
                print(stderr.decode())
            print("----------------------------")

        print("Experiment script finished.")


def get_boolean_input(prompt):
    """
    Prompts the user for a true/false input and returns a boolean.
    Handles various text inputs for true/false and re-prompts for
    invalid input.
    """
    while True:
        user_input = input(prompt).lower() or "y"
        if user_input in ["true", "t", "yes", "y"]:
            return True
        elif user_input in ["false", "f", "no", "n"]:
            return False
        else:
            print(
                "Invalid input. Please enter 'True', 'False', 'Yes', "
                + "or 'No'."
            )


if __name__ == "__main__":
    main()
