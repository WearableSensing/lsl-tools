from psychopy import visual, core
import serial
from pylsl import StreamInfo, StreamOutlet, local_clock
import argparse
from typing import Tuple, Optional

"""PsychoPy Photodiode Experiment for Clock Synchronization."""

DEFAULT_PORT = "COM10"
DEFAULT_TRIAL_AMOUNT = 25
DEFAULT_DISPLAY_RATE = 0.25  # seconds
DEFAULT_STREAM_NAME = "PsychoPyMarkers"
DEFAULT_TRIG = int(3)


def photodiode(
    portStr: str | None,
    software_stream: Tuple[StreamOutlet, int] | None,
    trials: int,
    display_rate: float,
    offset_value: Optional[float] = 0.0
) -> None:
    """
    The photodiode experiment using PsychoPy. It will flash a white white for
    "trials" amount of time at a rate of "display_rate". While doing so, it
    will send a trigger to the software "outlet" as well as the hardware port.

    Args:
        portStr (str): The port MMBTS is connected to in str form (Ex: COM10)
        trials (int): The numbers of trials the experiment will run.
        display_rate (float): The rate at the trial will be running at.
        outlet (StreamOutlet): The LSL outlet which the trigger will be sent to

    Returns: None
    """
    mmbts_use = False
    software_use = False
    port = None
    hard_trig_val = 0
    outlet = None
    soft_trig_val = 0

    if portStr:
        port = serial.Serial(portStr)
        hard_trig_val = 2
        mmbts_use = True
    if software_stream:
        outlet, soft_trig_val = software_stream
        software_use = True

    # Set up the PsychoPy Window and Stimuli
    win = visual.Window(
        monitor="testMonitor", units="pix", color="gray", fullscr=True
    )
    # Create light box
    lightTrig = lightbox(win, 200, "top_right")
    # Startup countdown
    timer(win, 3)

    # Experiment paramters
    disRate = visual.TextStim(
        win, text="Display Rate:" + str(display_rate), pos=(0, -25)
    )
    curTrial = visual.TextStim(win)
    trialHeader = visual.TextStim(win, text="Trial #:", pos=(-25, 0))

    for trial in range(trials):
        curTrial.text = str(trial + 1)
        curTrial.pos = (25, 0)
        curTrial.draw()
        disRate.draw()
        trialHeader.draw()
        lightTrig.draw()
        # Show the stimulus and send the marker almost simultaneously
        win.callOnFlip(
            multiTrigHandler,
            mmbts_use,
            software_use,
            port,
            bytes(chr(hard_trig_val), "utf-8"),
            outlet,
            [soft_trig_val],
            offset_value
        )
        win.flip()
        core.wait(display_rate)

        win.callOnFlip(
            multiTrigHandler,
            mmbts_use,
            software_use,
            port,
            bytes(chr(0), "utf-8"),
            outlet,
            [0],
            offset_value
        )
        disRate.draw()
        trialHeader.draw()
        win.flip()
        core.wait(display_rate)

    if port:
        port.write(bytes(chr(0), "utf-8"))  # Reset the trigger
        port.close()
    win.close()
    core.quit()


def createMarkerStream(
    stram_name: str, trig_val: int
) -> Tuple[StreamOutlet, int]:
    """
    Creates the PsychoPy Marker Stream for software markers.

    Args: None

    Returns:
        outlet (StreamOutlet): the outlet for the PsychoPy Stream
    """
    marker_stream_info = StreamInfo(
        name=stram_name,
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

    return outlet, trig_val


def multiTrigHandler(mmbts_use, software_use, port, arg1, outlet, arg2,
                     offset_value):
    if mmbts_use:
        port.write(arg1)
    if software_use:
        now = local_clock()
        adjusted_timestamp = now - offset_value
        outlet.push_sample(arg2, adjusted_timestamp)


def timer(win: visual.Window, countdown: int):
    cd = visual.TextStim(win, text=countdown)
    while countdown != 0:
        cd.text = countdown
        cd.draw()
        win.flip()
        countdown -= 1
        core.wait(1.0)


def lightbox(win: visual.Window, size: int, pos: str):
    win_width, win_height = win.size
    # Rectangle to represent the trigger light
    rect_size = (size, size)
    if pos == "top_right":
        top_right_x = (win_width / 2) - (rect_size[0] / 2)
        top_right_y = (win_height / 2) - (rect_size[1] / 2)
        box_pos = (top_right_x, top_right_y)
    elif pos == "top_left":
        top_left_x = -(win_width / 2) + (rect_size[0] / 2)
        top_left_y = (win_height / 2) - (rect_size[1] / 2)
        box_pos = (top_left_x, top_left_y)
    lightTrig = visual.Rect(
        win, size=rect_size, fillColor="white", pos=box_pos
    )

    return lightTrig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script that runs a \
                                     simple photodiode experiment"
    )
    parser.add_argument(
        "--port",
        default=None,
        type=str,
        help="The COM port (ex: 'COM10')",
    )
    parser.add_argument(
        "--trialAmount",
        type=int,
        default=DEFAULT_TRIAL_AMOUNT,
        help="Number of trials",
    )
    parser.add_argument(
        "--displayRate",
        type=float,
        default=DEFAULT_DISPLAY_RATE,
        help="Display rate in seconds",
    )
    parser.add_argument(
        "--newstream",
        type=str,
        default=DEFAULT_STREAM_NAME,
        help="The software stream name.",
    )
    parser.add_argument(
        "--trig",
        type=int,
        default=DEFAULT_TRIG,
        help="Trig value",
    )
    parser.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="A offset value you can add",
    )

    args = parser.parse_args()

    # Create the LSL outlet for markers
    softwareOutlet = createMarkerStream(args.newstream, args.trig)
    photodiode(args.port, softwareOutlet, args.trialAmount, args.displayRate,
               args.offset)
