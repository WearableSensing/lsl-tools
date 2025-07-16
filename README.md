# lsl-tools
This repository contains scripts to support the processing of Wearable Sensing data using LabStreamingLayer (LSL).

# EEG Data Recorder for Wearable Sensing (dsi2lsl)
This project provides a Python script for recording a specified duration of data from the dsi2lsl stream and saving it directly to a .csv file.

The script must run in parallel with an active LSL stream to capture the real-time EEG data for analysis and processing.

### Requirements
Before you can run the script, you must install the necessary files and dependencies on your system.
- [BciPy](https://github.com/CAMBI-tech/BciPy): Python application that supports experimental data collection.
  
- [Python](https://www.python.org/downloads/release/python-390/): Python 3.9 is strictly required. This is necessary for compatibility with the ```bcipy``` dependancy.
> This script has been set up using Python 3.9.13


## Setup Instructions

Follow these steps to prepare your environment for running the recording script.

### 1. Clone the Project Repository 
In Visual Studio Code, create a new folder where you will put this repository. 
* Paste this command into the terminal.
```powershell
git clone https://github.com/WearableSensing/lsl-tools.git
```


### 2. Create  and Activate a Virtual Environment 
* Create the environment:
```powershell
python -m venv .venv
```
> [!NOTE]
> When creating the virtual environment ensure Python 3.9 is selected.

* Activate the environment:
```bash
venv\Scripts\activate
```
Once activated, you will see **(venv)** appear at the beginning of your terminal prompt.

### 3. Install requirements.txt
Once your virtual environment has been activated, we need to install all of the dependencies inside of requirements.txt in order to make the script run.
* Paste this command into the terminal.
  
```powershell
pip install -r requirements.txt
```
> [!NOTE]
> Ensure your in the lsl-tools directory.
### 4. Install BciPy and Dependencies
This script relies on BciPy, which must be installed from its source repository.
* Clone the BciPy repository inside of your current folder:
```powershell
git clone https://github.com/CAMBI-tech/BciPy.git
```
* Navigate into the BciPy directory:
```powershell
cd BciPy
```
* Install the BciPy package:
```powershell
pip install .
```

## Basic Usage 
To run the script and record data, follow these steps:

### 1. Start the LSL Stream
Ensure your Wearable Sensing device is properly connected to your computer.
* Launch the ```dsi2lslGUI``` application to begin streaming EEG data using LabStreamingLayer:

### 2. Run the Recording Script
> [!NOTE]
> Make sure your virtual environment is still active

* Navigate into the scripts directory:
```powershell
cd scripts
```

* From the scripts directory, paste this command into your terminal while your LSL stream is running:
```powershell
python receive.py
```
If the script was ran successfully, you should see a .csv file saved to your specified path.
