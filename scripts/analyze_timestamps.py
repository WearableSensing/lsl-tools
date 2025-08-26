# Load in a CSV with SND, RVC, TRG
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tools.display.offset import preprocess
from tools.config import DEFAULT_TIMESTAMP_CH_NAME, DEFAULT_SOFTWARE_CH_NAME, DEFAULT_TARGETS

path_to_data = "C:/Users/Tab Memmott/Desktop/lsl-tools/split_photodiode_exp-20250826-103318.csv"

data = preprocess(path_to_data, DEFAULT_TIMESTAMP_CH_NAME, DEFAULT_SOFTWARE_CH_NAME, DEFAULT_TARGETS)

# breakpoint()

# We want to break each triggering event into a trial. The lightdiode, PsychoPyMarkers_SoftwareMarker, mmbts will all have values >0. Find the first index of each event, and then grab a window around it until all values are 0.

trig_events = data[(data['lightdiode'] > 0)]
trig_events_list = trig_events.index.tolist()
buffer = 50 # define buffer size
display_length = 0.35 * 300

# find the start time of each trial only (removing sequential samples)
trial_starts = []
for i in range(len(trig_events_list)):
    if i == 0 or trig_events_list[i] - trig_events_list[i-1] > 1:
        trial_starts.append(int(trig_events_list[i] - buffer))

trial_ends = []
for start in trial_starts:
    end = start + display_length + buffer
    trial_ends.append(int(end))



# segment the pandas data based on trial_start and trial_stop
segmented_trials = []
i = 0
for start, end in zip(trial_starts, trial_ends):
    # skip the first one
    if i > 0:
        segmented_trials.append(data.iloc[start:end])
    i += 1

# validate that the lightdiode, mmbts, and psychopy markers all start the trial with 0 and end with 0
for trial in segmented_trials:
    assert trial['lightdiode'].iloc[0] == 0
    assert trial['mmbts'].iloc[0] == 0
    assert trial['PsychoPyMarkers_SoftwareMarker'].iloc[0] == 0
    assert trial['lightdiode'].iloc[-1] == 0
    assert trial['mmbts'].iloc[-1] == 0
    assert trial['PsychoPyMarkers_SoftwareMarker'].iloc[-1] == 0

    # validate that each has a value > 0
    assert trial['lightdiode'].iloc[1:-1].max() > 0
    assert trial['mmbts'].iloc[1:-1].max() > 0
    assert trial['PsychoPyMarkers_SoftwareMarker'].iloc[1:-1].max() > 0


# This will plot every segemented trial block

# for trial in segmented_trials:
#     plt.figure()
#     plt.plot(trial['lightdiode'], label='Light Diode')
#     plt.plot(trial['mmbts'], label='MMBTS')
#     plt.plot(trial['PsychoPyMarkers_SoftwareMarker'], label='PsychoPy Marker')
#     plt.legend()
#     plt.title('Trial Segment')
#     plt.xlabel('Time (samples)')
#     plt.ylabel('Amplitude')
#     plt.show()


# for each trial determine the offset between lightdiode, mmbts and psychopy
offsets = []
for trial in segmented_trials:
    lightdiode_onset = trial['lightdiode'].idxmax()
    mmbts_onset = trial['mmbts'].idxmax()
    psychopy_onset = trial['PsychoPyMarkers_SoftwareMarker'].idxmax()

    # get the SND and RCV values at the time of the lightdiode onset
    SND = trial['WS-default_SND'].loc[lightdiode_onset]
    RCV = trial['WS-default_RCV'].loc[lightdiode_onset]

    offsets.append({
        'lightdiode': lightdiode_onset,
        'SND': SND,
        'RCV': RCV,
        'mmbts': mmbts_onset,
        'psychopy': psychopy_onset
})


SND_values = [offset['SND'] for offset in offsets]
RCV_values = [offset['RCV'] for offset in offsets]
differences = [snd - rcv for snd, rcv in zip(SND_values, RCV_values)]


plt.figure(figsize=(10, 5))
plt.plot(differences, label='Difference (SND - RCV)', marker='o')
plt.title('Difference between SND and RCV Values')
plt.xlabel('Trial')
plt.ylabel('Value')
plt.legend()
plt.grid()
plt.show()

# summary stats on diff
diff_df = pd.DataFrame(differences, columns=['Difference'])
print(diff_df.describe())

# start all of these clocks at 1 and increment based on the next value
SND_timestamps = data['WS-default_SND'].values
RCV_timestamps = data['WS-default_RCV'].values
LSL_timestamps = data['lsl_timestamp'].values

SND_timestamps = SND_timestamps - SND_timestamps[0] + 1
RCV_timestamps = RCV_timestamps - RCV_timestamps[0] + 1
LSL_timestamps = LSL_timestamps - LSL_timestamps[0] + 1

SND_diff = np.diff(SND_timestamps, prepend=SND_timestamps[0])
RCV_diff = np.diff(RCV_timestamps, prepend=RCV_timestamps[0])
LSL_diff = np.diff(LSL_timestamps, prepend=LSL_timestamps[0])

# plot the diffs
plt.figure(figsize=(10, 5))
# plt.plot(SND_diff, label='SND Diff', marker='o')
plt.plot(RCV_diff, label='RCV Diff')
# plt.plot(LSL_diff, label='LSL Diff', marker='o')
plt.title('Differences between Timestamps')
plt.xlabel('Sample')
plt.ylabel('Time (ms)')
plt.legend()
plt.grid()
plt.show()

# plot the differences between lightdiode onset (ground truth) and mmbts and psychopy
mmbts_diffs = [offset['lightdiode'] - offset['mmbts'] for offset in offsets]
psychopy_diffs = [offset['lightdiode'] - offset['psychopy'] for offset in offsets]

plt.figure(figsize=(10, 5))
plt.plot(mmbts_diffs, label='MMBTS Onset Difference', marker='o')
plt.plot(psychopy_diffs, label='PsychoPy Onset Difference', marker='o')
plt.title('Onset Differences between Light Diode, MMBTS, and PsychoPy')
plt.xlabel('Trial')
plt.ylabel('Sample')
plt.legend()
plt.grid()
plt.show()
