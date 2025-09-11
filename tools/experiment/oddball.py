from psychopy import visual, core
import serial
from pylsl import StreamInfo, StreamOutlet, local_clock
import argparse
from typing import Tuple, Optional
from tools.experiment.photodiode import multiTrigHandler

"""PsychoPy Photodiode Experiment for Clock Synchronization."""

from tools.config import (
    DEFAULT_PORT,
    DEFAULT_TRIAL_AMOUNT,
    DEFAULT_DISPLAY_RATE,
    DEFAULT_SOFTWARE_STREAM_NAME,
    DEFAULT_TRIG,
)

def oddball(
    portStr: str | None,
    software_stream: Tuple[StreamOutlet, int] | None,
    trials: int,
    display_rate: float,
    image_path: str,
    offset_value: Optional[float] = 0.0,
) -> None:
    """
    The oddball experiment using PsychoPy. It will flash a white white for
    "trials" amount of time at a rate of "display_rate". While doing so, it
    will send a trigger to the software "outlet" as well as the hardware port.

    Args:
        portStr (str): The port MMBTS is connected to in str form (Ex: COM10)
        trials (int): The numbers of trials the experiment will run.
        display_rate (float): The rate at the trial will be running at.
        image_path (str): The path to the image file to be displayed.
        offset_value (float, optional): The offset value to be applied to the trigger timing.
    Returns: None
    """
    
    win = visual.Window(
        monitor="testMonitor", units="norm", color="black", fullscr=True)