# lsl-tools
This repository contains scripts to support the processing of Wearable Sensing data using LabStreamingLayer (LSL).

# EEG Data Recorder for Wearable Sensing (dsi2lsl) using ```pylsl```
This project provides a Python script for recording any specified duration of data from the [```dsi2lsl```]( https://github.com/labstreaminglayer/App-WearableSensing/releases) stream and saving it directly to a ```.csv``` file.

This is the preferred method for data recording, as it does not require a strict, outdated version of Python. It uses the pylsl and pandas libraries directly, simplifying the setup process significantly.

### Requirements
Before you can run the script, you must install the necessary files and dependencies on your system.
- [Python](https://www.python.org/downloads/): Any modern version of Python (3.8+).
- [dsi2lsl program](https://github.com/labstreaminglayer/App-WearableSensing/releases)
- The ```pylsl``` and ```pandas``` Python libraries. This guide will walk you through installing these using the ```requirements.txt``` file.
  
## Setup Instructions

Follow these steps to prepare your environment for running the recording script.

### 1. Clone the Project Repository 
In Visual Studio Code, create a new folder where you will put this repository. 
* Paste this command into the terminal.
```sh
git clone https://github.com/WearableSensing/lsl-tools.git
```

### 2. Create  and Activate a Virtual Environment 
* Create the environment:
```sh
python -m venv .venv
```
> [!NOTE]
> Ensure your in the ```lsl-tools``` directory

* Activate the environment:
```bash
.venv\Scripts\activate
```
Once activated, you will see **(venv)** appear at the beginning of your terminal prompt.

### 3. Install requirements.txt
Once your virtual environment has been activated, we need to install all of the dependencies in order to make the code run.
* Paste this command into the terminal.
  
```sh
pip install -e .
```
> [!NOTE]
> Ensure your in the ```lsl-tools``` directory.

## Basic Usage 
To run the script and record data, follow these steps:

### 1. Start the LSL Stream
Ensure your Wearable Sensing device is properly connected to your computer.
* Launch the ```dsi2lslGUI``` application to begin streaming EEG data using LabStreamingLayer:

### 2. Run the Recording Script
> [!NOTE]
> Make sure your virtual environment is still active

Run the following in your terminal while your LSL stream is running:
```sh
python tools/consume/receive.py
```
If the script was ran successfully, you should see a .csv file saved to your specified path.

## Developer Guidelines

This section is for developers who wish to contribute to the lsl-tools repository. To maintain code quality and consistency, please follow these guidelines.

### 1. Development Setup

Install all development dependencies, including tools for formatting, linting, and testing, by running this command from the project's root directory:

```Bash
pip install -e .[dev]
```

### 2. Pre-Push Quality Checks

The project uses a GitHub Actions workflow to automatically check all pushes and pull requests. To avoid breaking the build, please run these same checks locally on your machine before pushing your changes.

#### A. Format Code (flake8)

Run this command to automatically have black format your code before committing:

```Bash
flake8 .
```

#### B. Type Checking (MyPy)

Run the following command to use mypy to check your code for type errors:

```Bash
mypy ./
```

#### C. Run Tests (Unittest & Coverage)

Ensure that all tests pass. You can run the same command locally:

```Bash
coverage run --branch -m unittest discover
```

After the tests complete, you can view a quick coverage report in your terminal with coverage report -m.

## Running Experiments

### 1. Photodiode Experiment

PsychoPy Photodiode Experiment for Clock Synchronization.

This script displays a simple visual stimulus (e.g., a flashing square) intended to be captured by a photodiode. Its primary purpose is to generate events that can be used to measure and correct for timing offsets (clock drift) between the stimulus presentation computer and an LSL-streaming data acquisition system (e.g., a DSI headset).

#### How to Run

To start the experiment, run the main.py script from your terminal:

```bash
python main.py
```

The script will present a menu. You can press Enter to select the default choice and begin the interactive setup.

#### Interactive Setup Arguments

After launching, the script will ask a series of questions to configure the experiment. Pressing Enter without typing will select the default value shown in the prompt.

##### 1. MMBTS Hardware Triggers

This configures the connection to an MMBTS device for sending hardware-timed event markers.

> ```Do you want to connect a MMBTS? (y/n):```

- y / Default: Use if you are connecting an MMBTS device.
- n: Use if you are not using an MMBTS device.

> ```What is the COM port for MMBTS? (DEFAULT: COM10):```

- This prompt only appears if you answered yes above.
- Enter the COM port your MMBTS is connected to (DEFAULT: COM10).

##### 2. Software Triggers

This configures a software-based LSL marker stream for sending event markers directly from the script.

> ```Do you want to send software triggers? (y/n):```

- y / Default: Creates a new LSL marker stream.
- n: Skips the creation of a software marker stream.

> ```Create a marker stream name (DEFAULT: PsychoPyMarkers):```

- Provide a unique name to identify your software LSL stream on the network.

> ```Input a unique software integer trigger (DEFAULT: 3):```

- Enter a specific integer value that will be sent as the marker.

##### 3. Experiment Parameters

These prompts control the behavior of the photodiode flash sequence.

> ```How many trials do you want to run? (DEFAULT: 25):```

- Defines the total number of flashes (trials) for the experiment.

> ```At what rate do you want the flashes to run? (DEFAULT: 0.25):```

- Sets the duration (in seconds) of each flash and the pause that follows. A value of 0.25 means a 0.25s flash followed by a 0.25s pause.

> ```At what rate do you want to offset? (DEFAULT: 0):```

- Sets a timing offset value in seconds.

##### 4. Recording

This option automatically records the LSL streams you have configured.

> ```Do you want to record? (y/n):```

- y / Default: Starts the recorder (tools/consume/unified_receive.py) as a background process.
- The recording begins just before the experiment and stops automatically after it finishes.
- The output is saved as photodiode_exp.csv in the same directory.

#### Example Walkthrough

Here is an example of a complete interaction:

```bash
Please select an option:
    1. Photodiode
Enter your choice (1): 1

Do you want to connect a MMBTS? (y/n): [PRESS ENTER]
What is the COM port for MMBTS? (DEFAULT: COM10): [PRESS ENTER] 

Do you want to send software triggers? (y/n): [PRESS ENTER]
Create a marker stream name (DEFAULT: PsychoPyMarkers): [PRESS ENTER]
Input a unique software integer trigger (DEFAULT: 3): [PRESS ENTER]

How many trials do you want to run?(DEFAULT: 25): 10
At what rate do you want the flashes to run? ( DEFAULT: 0.25): [PRESS ENTER]
At what rate do you want to offset? ( DEFAULT: 0.0): [PRESS ENTER]

Do you want to record? (y/n): y
```

##### Outcome of this example

The experiment will connect to an MMBTS on COM10.

It will create a software LSL stream named PsychoPyMarkers that sends the integer marker 3.

The photodiode will flash 10 times with a 0.25-second rate.

The recorder script will launch in the background, recording both the hardware stream and the PsychoPyMarkers into a file named photodiode_exp.csv.
