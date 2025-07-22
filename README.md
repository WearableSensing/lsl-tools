# lsl-tools
This repository contains scripts to support the processing of Wearable Sensing data using LabStreamingLayer (LSL).

# EEG Data Recorder for Wearable Sensing (dsi2lsl) using ```pylsl```
This project provides a Python script for recording any specified duration of data from the [```dsi2lsl```]( https://github.com/labstreaminglayer/App-WearableSensing/releases) stream and saving it directly to a ```.csv``` file.

This is the preferred method for data recording, as it does not require a strict, outdated version of Python. It uses the pylsl and pandas libraries directly, simplifying the setup process significantly.

The dsi2lsl program can be found [here]( https://github.com/labstreaminglayer/App-WearableSensing/releases)

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

## Testing
To run the test for the receive script. 

### 1. Navigate
Naviagte the the root of the project folder, 'lsl-tools'.

### 2. Run
> [!NOTE]
> Make sure your virtual environment is still active

Run the following in your terminal:
```sh
python -m unittest discover
```