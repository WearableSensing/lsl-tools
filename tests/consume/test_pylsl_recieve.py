import unittest
import pylsl
from consume.receive import find_stream, recieve_data
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
import os
import tempfile
import pandas as pd

class TestFindStream(unittest.TestCase):
    '''
    Test suite for the find_stream function
    '''
    def setUp(self):
        '''
        This method is run before each test. It sets up a shared mock
        environment for the tests in this class.
        '''
        # Start the patcher for 'pylsl' and store the mock object on self
        self.pylsl_patcher = patch('consume.receive.pylsl')
        self.mock_pylsl = self.pylsl_patcher.start()

        # --- Pre-define all the mock objects as instance attributes ---
        self.mock_stream_info = MagicMock()
        self.mock_stream_info.name.return_value = 'TestStream'

        self.mock_inlet_instance = MagicMock()

        # --- Pre-configure the main mock's default behavior for a success case ---
        self.mock_pylsl.resolve_byprop.return_value = [self.mock_stream_info]
        self.mock_pylsl.StreamInlet.return_value = self.mock_inlet_instance

    def tearDown(self):
        '''
        This method is run after each test to clean up. It stops the patcher.
        '''
        self.pylsl_patcher.stop()

    def test_find_stream_success(self):
        '''
        Test successfully finding a stream by name
        '''
        # Acting
        stream_name = 'TestStream'
        result_inlet = find_stream(stream_name) # This calls the actual function find_stream

        # Checks that methods were call corectly
        self.mock_pylsl.resolve_byprop.assert_called_once_with(prop='name', value=stream_name, timeout=10)
        self.mock_pylsl.StreamInlet.assert_called_once_with(self.mock_stream)
        
        # Final check that function returns the correct inlet
        self.assertEqual(result_inlet, mock_inlet_inst)
        print("\nTestFindStream.test_find_stream_success passed")
        
    def test_find_stream_no_streams(self):
        '''
        Test finding a stream when no streams are found
        '''
        # Acting and asserting
        stream_name = 'NoStream'
        with self.assertRaises(Exception) as context:
            find_stream(stream_name) # This calls the actual function find_stream
        
        # Final check that function returns the correct inlet
        self.assertTrue('Could not find stream name' in str(context.exception))
        print("\nTestFindStream.test_find_stream_no_streams passed")

    def test_find_stream_multiple_streams(self):
        '''
        Test finding a stream when multiple streams are found
        '''
        # Override the default return_value set in setUp for this specific test
        self.mock_pylsl.resolve_byprop.return_value = [self.mock_stream_info, MagicMock()]
        stream_name = 'MultiStreams'

        # Acting and asserting
        with self.assertRaises(Exception) as context:
            find_stream(stream_name)
        self.assertTrue('Expected one Stream.' in str(context.exception))
        print("\nTestFindStream.test_find_stream_multiple_streams passed")


class TestRecieveData(unittest.TestCase):
    '''
    Test suite for the receive_data function.
    '''
    def setUp(self):
        '''
        This method is run before each test. It sets up a shared mock
        environment for the tests in this class.
        '''
        # Start the patcher for 'pylsl' and store the mock object on self
        self.pd_patcher = patch('consume.receive.pd.DataFrame')
        self.time_patcher = patch('consume.receive.time')
        self.datetime_patcher = patch('consume.receive.datetime')
        self.open_patcher = patch('consume.receive.open', new_callable=mock_open)
        self.mock_dataframe = self.pd_patcher.start()
        self.mock_time = self.time_patcher.start()
        self.mock_datetime = self.datetime_patcher.start()
        self.mock_open = self.open_patcher.start()
        
        # --- Configure default mock behaviors ---
        self.mock_time.time.side_effect = [0, 10]  # Default for one loop iteration
        self.mock_datetime.now.return_value = datetime(2025, 2, 25, 12, 0, 0)
        self.mock_df_instance = MagicMock()
        self.mock_dataframe_class.return_value = self.mock_df_instance

        # --- Mock the pylsl.StreamInlet and its nested info object ---
        self.mock_stream_inlet = MagicMock()        
        mock_stream_info = MagicMock()
        self.mock_stream_inlet.info.return_value = mock_stream_info
        
        # Configure the info object's attributes
        mock_stream_info.name.return_value = 'TestStream'
        mock_stream_info.type.return_value = 'EEG'
        mock_stream_info.nominal_srate.return_value = '300'
        mock_stream_info.channel_count.return_value = 2
        mock_stream_info.as_xml.return_value = '<xml>...</xml>'

        # Mock the deeply nested XML description structure
        mock_desc = MagicMock()
        mock_channels = MagicMock()
        mock_ch = MagicMock()
        mock_reference = MagicMock()
        mock_stream_info.desc.return_value = mock_desc
        mock_desc.child.side_effect = lambda x: {'channels': mock_channels, 'reference': mock_reference}[x]
        mock_channels.child.return_value = mock_ch
        mock_ch.child_value.side_effect = lambda x: {'label': 'CH1', 'unit': 'microvolts'}[x]
        mock_ch.next_sibling.return_value = mock_ch
        mock_reference.child_value.return_value = 'Ref1'

        # Configure default data the stream will "receive"
        mock_samples = [[1.0, 2.0], [1.1, 2.1]]
        mock_timestamps = [12345.1, 12345.2]
        self.mock_stream_inlet.pull_chunk.return_value = (mock_samples, mock_timestamps)

    def tearDown(self):
        """
        This method is run after each test to clean up by stopping all patchers.
        """
        self.time_patcher.stop()
        self.datetime_patcher.stop()
        self.open_patcher.stop()
        self.pd_patcher.stop()


# Allows to run test by executing the script directly: 
# 'python -m unittest tests/consume/test_pylsl_receive.py'
if __name__ == '__main__':
    unittest.main()