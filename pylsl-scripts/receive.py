import time
from typing import List
import pandas as pd
from datetime import datetime
import os

import pylsl

DURATION = 5
STREAM_NAME = 'WS-default'
OUTPUT_PATH = '.' 

class Inlet:
    pass

def main():
    '''
    Python script to record data from Wearable Sensing LSL stream (dsi2lsl).
    Records for specified duration and saves CSV to desired path.
    '''
    try:
        # Look for any running streams that contain STREAM_NAME.
        inlets: List[Inlet] = []
        print('Looking for EEG streams')
        streams = pylsl.resolve_byprop(prop='name', value=STREAM_NAME, timeout=10)

        # If timeout, end stream to prevent terminal from being frozen.
        if len(streams) == 0:
            raise Exception(f"Could not find stream name {STREAM_NAME}. Ending now...")
        
        print(f'Found {len(streams)} stream(s):')
        for i, stream in enumerate(streams):
                print(f"Name: '{stream.name()}'")
                dsi_stream = stream

        dsi_stream_inlet = pylsl.StreamInlet(dsi_stream)
        print('Connected to stream. Press Ctrl+C to exit.')

        # Generate unique filename for new CSV file.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"eeg-data-ws-default-{timestamp}-{DURATION}s.csv"
        full_path = os.path.join(OUTPUT_PATH, unique_filename)

        # Get stream metadata.
        info = dsi_stream_inlet.info()
        
        # Get channel labels.
        ch = info.desc().child("channels").child("channel")
        labels = []
        for i in range(info.channel_count()):
            labels.append(ch.child_value("label"))
            ch = ch.next_sibling()
        
        # Create column names in same row as channels.
        columns = ['Timestamp'] + labels + ['lsl_timestamp']
        
        # Collect all the data first.
        all_data = []
        start_time = time.time()
        sample_counter = 1
        
        print(f'\nCollecting data for {DURATION}s... (Interrupt [Ctrl-C] to stop)\n')
        
        # While loop that records data for DURATION seconds and ensures data is correctly paired in each row.
        while time.time() - start_time < DURATION:
            samples, timestamps = dsi_stream_inlet.pull_chunk()
            if samples:
                for sample, lsl_timestamp in zip(samples, timestamps):
                    row = [sample_counter] + sample + [lsl_timestamp]
                    all_data.append(row)
                    sample_counter += 1
            
            time.sleep(0.01)
        
        # Create DataFrame and save to CSV.
        df = pd.DataFrame(all_data, columns=columns)
        
        # Add info about 'daq_type' and 'sample_rate' as rows.
        with open(full_path, 'w', newline='') as f:
            f.write(f"daq_type,{info.name()}\n")
            f.write(f"sample_rate,{info.nominal_srate()}\n")
            df.to_csv(f, index=False)
        
        print(f"\nRecording finished.")
        print(f"Saved {len(df)} samples to {full_path}")

    except KeyboardInterrupt:
        print('\nInterrupted by user (Ctrl+C). Exiting gracefully...')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    main()