import time
import os
from datetime import datetime
from bcipy.acquisition.protocols.lsl.lsl_recorder import LslRecorder

DURATION = 5
BASE_PATH = '.' 

def main():
    '''
    Script to record data from Wearable Sensing LSL stream (dsi2lsl).
    Records for specified duration and saves .csv to specified path.
    '''

    # Generates unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    desired_filename = f"eeg-data-ws-default-{timestamp}-{DURATION}s.csv"
    
    try:
        custom_filenames = {'EEG': desired_filename}
        recorder = LslRecorder(path=BASE_PATH, filenames=custom_filenames)
        recorder.start()
        print(f'\nCollecting data for {DURATION}s to path=[{BASE_PATH}\\{desired_filename}]... (Interrupt [Ctl-C] to stop)\n')

        while True:
            time.sleep(DURATION)
            recorder.stop()
            break
            
        print(f"File saved as: {os.path.join(BASE_PATH, desired_filename)}")
    except IOError as e:
        print(f'{e.strerror}; make sure you started the LSL app or server.')
    except KeyboardInterrupt:
        print('Keyboard Interrupt\n')
        recorder.stop()
        print('Stopped')
    except Exception as e:
        print(f'{e}')
        raise e
    finally:
        print('Stopped')

if __name__ == '__main__':
    main()


