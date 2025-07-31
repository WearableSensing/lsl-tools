import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
import tempfile

from tools.consume.receive import find_stream, receive_data


class TestFindStream(unittest.TestCase):
    """
    Test suite for the find_stream function
    """

    def setUp(self):
        """
        This method runs before each test. It sets up a shared mock
        environment for the tests in this class.
        """
        # Start the patcher for 'pylsl' and store the mock object on self.
        self.pylsl_patcher = patch("tools.consume.receive.pylsl")
        self.mock_pylsl = self.pylsl_patcher.start()

        # Pre-define all the mock objects as instance attributes.
        self.mock_stream = MagicMock()
        self.mock_stream.name.return_value = "TestStream"

        self.mock_inlet_inst = MagicMock()

        # Pre-configure the main mock's default behavior for a success case.
        self.mock_pylsl.resolve_byprop.return_value = [self.mock_stream]
        self.mock_pylsl.StreamInlet.return_value = self.mock_inlet_inst

    def tearDown(self):
        """
        Method that stops the patcher after each test.
        """
        self.pylsl_patcher.stop()

    def test_find_stream_success(self):
        """
        Test finding a stream by name when it exists.
        """
        stream_name = "TestStream"
        result_inlet = find_stream(stream_name)  # Calls find_stream method from consume.receive module.

        # Checks that methods were called corectly
        self.mock_pylsl.resolve_byprop.assert_called_once_with(prop="name", value=stream_name, timeout=10)
        self.mock_pylsl.StreamInlet.assert_called_once_with(self.mock_stream)

        self.assertEqual(result_inlet, self.mock_inlet_inst)

    def test_find_stream_no_streams(self):
        """
        Test that raises an exception when no streams are found.
        """
        self.mock_pylsl.resolve_byprop.return_value = []
        stream_name = "NoStream"
        with self.assertRaises(Exception) as context:
            find_stream(stream_name)  # Calls find_stream method from consume.receive module.

        # Final check that function returns the correct inlet
        self.assertTrue("Could not find stream name" in str(context.exception))

    def test_find_stream_multiple_streams(self):
        """
        Test finding a stream when multiple streams are found
        """
        self.mock_pylsl.resolve_byprop.return_value = [self.mock_stream, MagicMock()]
        stream_name = "MultiStreams"

        # Acting and asserting
        with self.assertRaises(Exception) as context:
            find_stream(stream_name)
        self.assertTrue("Expected one Stream." in str(context.exception))


class TestReceiveData(unittest.TestCase):
    """
    Test suite for the receive_data function.
    """

    def setUp(self):
        """
        This method is run before each test. It sets up a shared mock
        environment for the tests in this class.
        """
        self.pd_patcher = patch("tools.consume.receive.pd.DataFrame")
        self.time_patcher = patch("tools.consume.receive.time")
        self.datetime_patcher = patch("tools.consume.receive.datetime")
        self.open_patcher = patch("tools.consume.receive.open", new_callable=mock_open)
        self.mock_dataframe = self.pd_patcher.start()
        self.mock_time = self.time_patcher.start()
        self.mock_datetime = self.datetime_patcher.start()
        self.mock_open = self.open_patcher.start()

        # Configure the mock time and datetime
        self.mock_time.time.side_effect = [0, 4, 6]  # Will return 0 on first call, 4 on second, 6 on third
        self.mock_datetime.now.return_value = datetime(2025, 7, 22, 12, 0, 0)
        self.mock_df_instance = MagicMock()
        self.mock_dataframe.return_value = self.mock_df_instance

        self.mock_stream_inlet = MagicMock()
        mock_stream_info = MagicMock()
        self.mock_stream_inlet.info.return_value = mock_stream_info

        # Configure additional properties of the stream info
        mock_stream_info.name.return_value = "TestStream"
        mock_stream_info.type.return_value = "EEG"
        mock_stream_info.nominal_srate.return_value = "300"
        mock_stream_info.channel_count.return_value = 2
        mock_stream_info.as_xml.return_value = "<xml>...</xml>"

        # Mock the stream's description and channels
        mock_desc = MagicMock()
        mock_channels = MagicMock()
        mock_ch = MagicMock()
        mock_reference = MagicMock()
        mock_stream_info.desc.return_value = mock_desc
        mock_desc.child.side_effect = lambda x: {"channels": mock_channels, "reference": mock_reference}[x]
        mock_channels.child.return_value = mock_ch
        mock_ch.child_value.side_effect = lambda x: {"label": "CH1", "unit": "microvolts"}[x]
        mock_ch.next_sibling.return_value = mock_ch
        mock_reference.child_value.return_value = "Ref1"

        # Mock data pulling from the stream
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

    def test_data_collect_success(self):
        """
        Test successful data collection and CSV writing.
        """
        # Define the output path using a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = temp_dir
            test_dur = 5

            # Acting
            receive_data(self.mock_stream_inlet, output_path, test_dur)

            # Check that the DataFrame was created with correct columns
            self.mock_dataframe.assert_called_once()
            self.mock_df_instance.to_csv.assert_called_once()

            # Check that the file was opened correctly and correct filename
            expected_filename = f"DSIdata-{test_dur}s-20250722-120000.csv"
            expected_full_path = os.path.join(output_path, expected_filename)
            self.mock_open.assert_called_once_with(expected_full_path, "w", newline="")
            # 'w' mode for writing, newline='' to avoid extra newlines in csv

            # Check that the metadata was written to the file
            handle = self.mock_open()
            handle.write.assert_any_call("stream_name,TestStream\n")
            handle.write.assert_any_call("daq_type,EEG\n")
            handle.write.assert_any_call("units,microvolts\n")
            handle.write.assert_any_call("reference,Ref1\n")
            handle.write.assert_any_call("sample_rate,300\n")

            # Check that the DataFrame was saved
            expected_col = ["Timestamp", "CH1", "CH1", "lsl_timestamp"]
            expected_data = [[1, 1.0, 2.0, 12345.1], [2, 1.1, 2.1, 12345.2]]
            self.mock_dataframe.assert_called_once_with(expected_data, columns=expected_col)
            self.mock_df_instance.to_csv.assert_called_once_with(handle, index=False)


if __name__ == "__main__":
    unittest.main()
