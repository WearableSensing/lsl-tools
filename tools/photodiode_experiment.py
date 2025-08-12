from psychopy import visual, core
import serial
from .consume.receive import receive_data, find_stream
from pylsl import StreamInfo, StreamOutlet
import threading

# This is a simple photodiode experiment built with PsychoPy that will aid in
# observing clock drifts
# You will need to be connected to a MMTBS and a headset for this experiement
# to run
# This is built with python 3.10
# You will need dsi2lsl running as well to receive data
DEFAULT_PORT = "COM10"
DEFAULT_TRIAL_AMOUNT = 25
DEFAULT_DISPLAY_RATE = 0.25  # seconds
DEFAULT_STREAM_NAME = "WS-default"
DEFAULT_OUTPUT_PATH = "."
DEFAULT_OUTPUT_PATH2 = "./softwareStream"


def createMarkerStream() -> StreamOutlet:
    """
    Creates the PsychoPy Marker Stream for software markers.

    Returns:
        outlet (StreamOutlet): the outlet for the PsychoPy Stream
    """
    marker_stream_info = StreamInfo(
        name="PsychoPyMarkers",
        type="Markers",
        channel_count=1,  # Number of channels (1 for a single marker stream)
        nominal_srate=0,  # The rate is irregular, so we set it to 0
        channel_format="int32",  # Data type of the markers
        source_id="my_unique_id_12345",  # A unique identifier
    )
    description = marker_stream_info.desc()
    channels_node = description.append_child("channels")

    ch_node = channels_node.append_child("channel")
    ch_node.append_child_value("label", "SoftwareMarker")

    # Create the stream outlet
    outlet = StreamOutlet(marker_stream_info)
    print("LSL Marker stream created.")

    return outlet


def multiTrigHandler(port, arg1, outlet, arg2):
    port.write(arg1)
    outlet.push_sample(arg2)


def photodiode(portStr: str, trials: int, display_rate: float, outlet: StreamOutlet) -> None:
    port = serial.Serial(portStr)  # Change the COM port to match your setup

    # Set up the PsychoPy Window and Stimuli
    win = visual.Window(monitor="testMonitor", units="pix", color="gray", fullscr=True)
    win_width, win_height = win.size
    # Rectangle to represent the trigger light
    rect_size = (200, 200)
    top_right_x = (win_width / 2) - (rect_size[0] / 2)
    top_right_y = (win_height / 2) - (rect_size[1] / 2)
    top_right_pos = (top_right_x, top_right_y)
    lightTrig = visual.Rect(win, size=rect_size, fillColor="white", pos=top_right_pos)

    Trigger = 2  # trigger code must be between 2-255, 1 set for photodiode

    # Startup countdown
    countdown = 3
    cd = visual.TextStim(win, text=countdown)
    while countdown != 0:
        cd.text = countdown
        cd.draw()
        win.flip()
        countdown -= 1
        core.wait(1.0)

    # Experiment paramters
    disRate = visual.TextStim(win, text="Display Rate:" + str(display_rate), pos=(0, -25))
    curTrial = visual.TextStim(win)
    trialHeader = visual.TextStim(win, text="Trial #:", pos=(-20, 0))

    for trial in range(trials):
        curTrial.text = str(trial + 1)
        curTrial.pos = (25, 0)
        curTrial.draw()
        disRate.draw()
        trialHeader.draw()
        lightTrig.draw()
        # Show the stimulus and send the marker almost simultaneously
        win.callOnFlip(multiTrigHandler, port, bytes(chr(Trigger), "utf-8"), outlet, [3])
        win.flip()
        core.wait(display_rate)  # fixation appears for 1 second

        # wait for 2s
        win.callOnFlip(multiTrigHandler, port, bytes(chr(0), "utf-8"), outlet, [0])
        disRate.draw()
        trialHeader.draw()
        win.flip()
        core.wait(display_rate)

    port.write(bytes(chr(0), "utf-8"))  # Reset the trigger
    win.close()
    core.quit()
    port.close()


if __name__ == "__main__":
    import argparse
    import subprocess  # Import subprocess
    import sys  # Import sys to get python executable

    # ... (all your argparse setup remains the same) ...
    parser = argparse.ArgumentParser(description="A script that runs a simple photodiode experiment")
    # (Add all your arguments here as before)
    # ...
    parser.add_argument("--port", default=DEFAULT_PORT, type=str, help="The COM port (ex: 'COM10')")
    parser.add_argument("--trialAmount", type=int, default=DEFAULT_TRIAL_AMOUNT, help="Number of trials")
    parser.add_argument("--displayRate", type=float, default=DEFAULT_DISPLAY_RATE, help="Display rate in seconds")
    parser.add_argument("--record", action="store_true", help="Enable recording with the unified recorder.")
    parser.add_argument("--stream", type=str, default=DEFAULT_STREAM_NAME, help="The hardware stream name.")
    parser.add_argument("--output", type=str, default=DEFAULT_OUTPUT_PATH, help="The path for the output file.")
    args = parser.parse_args()

    # Create the LSL outlet for markers
    softwareOutlet = createMarkerStream()

    recorder_process = None
    if args.record:
        import os

        # Get the directory where this script (photodiode_experiment.py) is located
        current_script_dir = os.path.dirname(os.path.abspath(__file__))

        # Join that path with the relative path to the recorder
        recorder_script_path = os.path.join(current_script_dir, "consume", "unified_receive.py")

        # Check if the file actually exists before trying to run it
        if not os.path.exists(recorder_script_path):
            print(f"FATAL ERROR: Recorder script not found at {recorder_script_path}")
            quit()

        # Calculate the total duration needed for the recording
        duration = 3 + (args.trialAmount * args.displayRate * 2) + 2

        # Command to run the unified recorder script
        command = [
            sys.executable,  # The current python interpreter
            recorder_script_path,  # The name of the script
            "--streams",
            args.stream,
            "PsychoPyMarkers",  # Streams to record
            "--duration",
            str(int(duration)),  # How long to record
            "--filename",
            f"{args.output}/photodiode_exp",  # Output file
        ]

        print("Starting unified recorder...")
        # Use Popen to start the recorder as a non-blocking background process
        recorder_process = subprocess.Popen(command)
        core.wait(2.0)  # Give the recorder a moment to start up and find streams

    # Run the experiment regardless of recording
    try:
        photodiode(args.port, args.trialAmount, args.displayRate, softwareOutlet)
    finally:
        # Ensure the recorder process is terminated and we see its output
        if recorder_process:
            print("Waiting for recorder to finish...")

            # Use communicate() to get the output and errors from the recorder
            stdout, stderr = recorder_process.communicate()

            print("--- Recorder Script Output ---")
            if stdout:
                print(stdout.decode())
            if stderr:
                print("--- Recorder Script Errors ---")
                print(stderr.decode())
            print("----------------------------")

        print("Experiment finished.")
