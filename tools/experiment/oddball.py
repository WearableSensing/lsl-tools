from psychopy import visual, core
import serial
from pylsl import StreamInfo, StreamOutlet, local_clock
from typing import Tuple, Optional
from pathlib import Path
from tools.experiment.photodiode import lightbox, multiTrigHandler

"""PsychoPy Photodiode Experiment for Clock Synchronization."""

from tools.config import (
    DEFAULT_PORT,
    DEFAULT_TRIAL_AMOUNT,
    DEFAULT_DISPLAY_RATE,
    DEFAULT_SOFTWARE_STREAM_NAME,
    DEFAULT_TRIG,
)

def draw_headers(
    cur_trial: visual.TextStim,
    trial_header: visual.TextStim,
) -> None:
    """
    Draws the headers for the experiment window.

    Args:
        cur_trial (visual.TextStim): The current trial text stimulus.
        trial_header (visual.TextStim): The trial header text stimulus.

    Returns: None
    """
    cur_trial.draw()
    trial_header.draw()

def oddball(
    portStr: str | None,
    software_stream: Tuple[StreamOutlet, int] | None,
    trials: int,
    stim_num_per_trial: int,
    display_rate: float,
    offset_value: Optional[float] = 0.0,
) -> None:
    """
    The oddball experiment using PsychoPy. It will flash a white white for
    "trials" amount of time at a rate of "display_rate". While doing so, it
    will send a trigger to the software "outlet" as well as the hardware port.

    Args:
        portStr (str): The port MMBTS is connected to in str form (Ex: COM10)
        trials (int): The numbers of trials the experiment will run.
        stim_num_per_trial (int): The number of stimuli presented in each trial.
        display_rate (float): The rate at the trial will be running at.
        image_path (str): The path to the image file to be displayed.
        offset_value (float, optional): The offset value to be applied to the trigger timing.
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
    
    win = visual.Window(
        monitor="testMonitor", units="norm", color="black", fullscr=True)
    
    # Create image stimulus
    stimuli = []
    for img in Path("tools/static/images/").glob("*.png"):
        image = visual.ImageStim(win, image=str(img), size=(0.7, 0.7), pos=(0, 0))
        stimuli.append(image)

    fixation = visual.TextStim(win, text="+", color="red", height=0.5, pos=(0, 0))
    fixation_time = 0.5  # seconds
    target_time = 2.0  # seconds
    iti = 0.1  # inter-trial interval in seconds
    cur_trial = visual.TextStim(win, pos=(-0.3, 0.5))
    trial_header = visual.TextStim(win, text="Trial #:", pos=(-0.5, 0.5))

    starting = visual.TextStim(win, "starting task..")
    starting.draw()
    win.flip()
    core.wait(5)

    target_text = visual.TextStim(win, text="Target", color="green", height=0.1, pos=(0, 0.5))

    # Main experiment loop
    for trial in range(trials):
        # Randomly select a stimulus for the oddball task
        cur_trial.text = str(trial + 1)

        # make a target stimulus (oddball)
        target_stimulus = stimuli[trial % len(stimuli)]
        target_stimulus.draw()
        target_text.draw()
        draw_headers(cur_trial, trial_header)
        win.flip()
        core.wait(target_time)  # Display target stimulus for 2 seconds

        draw_headers(cur_trial, trial_header)
        fixation.draw()
        win.flip()
        core.wait(fixation_time)

        for stim in range(stim_num_per_trial):
            stimulus = stimuli[stim % len(stimuli)]  # Cycle through stimuli

            if stimulus == target_stimulus:
                # If it's the target stimulus, display it longer
                win.callOnFlip(
                    multiTrigHandler,
                    mmbts_use,
                    software_use,
                    port,
                    bytes(chr(hard_trig_val + 1), "utf-8"),  # Target trigger
                    outlet,
                    [soft_trig_val + 1],
                    offset_value,
                )
            else:
                win.callOnFlip(
                    multiTrigHandler,
                    mmbts_use,
                    software_use,
                    port,
                    bytes(chr(hard_trig_val), "utf-8"),
                    outlet,
                    [soft_trig_val],
                    offset_value,
                )
            # Display stimulus
            draw_headers(cur_trial, trial_header)
            stimulus.draw()
            win.flip()

            core.wait(display_rate)

            draw_headers(cur_trial, trial_header)
            win.flip()
            core.wait(iti)
        
        core.wait(1)  # Wait 1 second between trials

if __name__ == "__main__":

    # update to use your MMBTS port
    port = DEFAULT_PORT

    oddball(
        portStr=None,
        software_stream=(
            StreamOutlet(
                StreamInfo(
                    DEFAULT_SOFTWARE_STREAM_NAME,
                    "Markers",
                    1,
                    0,
                    "int32",
                    "myuid34234",
                )
            ),
            DEFAULT_TRIG,
        ),
        trials=DEFAULT_TRIAL_AMOUNT,
        display_rate=DEFAULT_DISPLAY_RATE,
        stim_num_per_trial=5,
        offset_value=0.0,
    )

