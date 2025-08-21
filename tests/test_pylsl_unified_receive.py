import unittest
from unittest.mock import MagicMock, patch, mock_open
import pandas as pd
import numpy as np
from io import StringIO

from tools.consume.unified_receive import (
    find_stream,
    unified_receive,
    format_csv,
)


class TestUnifiedFindStream(unittest.TestCase):
    """
    Test suite for the find_stream function in unified_receive.
    """

    def setUp(self):
        """
        Sets up the mocking environment.
        """
        self.resolve_streams_patcher = patch(
            "tools.consume.unified_receive.resolve_streams"
        )
        self.stream_inlet_patcher = patch(
            "tools.consume.unified_receive.StreamInlet"
        )

        self.mock_resolve_streams = self.resolve_streams_patcher.start()
        self.mock_stream_inlet = self.stream_inlet_patcher.start()

        self.mock_stream1_info = MagicMock()
        self.mock_stream1_info.name.return_value = "DSI-Stream"
        self.mock_stream1_info.channel_count.return_value = 2
        mock_stream1_desc = MagicMock()
        self.mock_stream1_info.desc.return_value = mock_stream1_desc
        mock_stream1_ch1 = MagicMock()
        mock_stream1_ch1.child_value.return_value = "EEG1"
        mock_stream1_ch2 = MagicMock()
        mock_stream1_ch2.child_value.return_value = "EEG2"
        mock_stream1_ch1.next_sibling.return_value = mock_stream1_ch2
        mock_stream1_ch2.next_sibling.return_value = None
        mock_stream1_desc.child.return_value.child.return_value = (
            mock_stream1_ch1
        )

        self.mock_stream2_info = MagicMock()
        self.mock_stream2_info.name.return_value = "Marker-Stream"
        self.mock_stream2_info.channel_count.return_value = 1
        mock_stream2_desc = MagicMock()
        self.mock_stream2_info.desc.return_value = mock_stream2_desc
        mock_stream2_ch1 = MagicMock()
        mock_stream2_ch1.child_value.return_value = "Marker1"
        mock_stream2_ch1.next_sibling.return_value = None
        mock_stream2_desc.child.return_value.child.return_value = (
            mock_stream2_ch1
        )

        self.mock_stream1 = MagicMock()
        self.mock_stream1.name.return_value = "DSI-Stream"
        self.mock_stream2 = MagicMock()
        self.mock_stream2.name.return_value = "Marker-Stream"
        self.mock_resolve_streams.return_value = [
            self.mock_stream1,
            self.mock_stream2,
        ]

        self.mock_inlet1 = MagicMock()
        self.mock_inlet1.info.return_value = self.mock_stream1_info
        self.mock_inlet2 = MagicMock()
        self.mock_inlet2.info.return_value = self.mock_stream2_info
        self.mock_stream_inlet.side_effect = [
            self.mock_inlet1,
            self.mock_inlet2,
        ]

    def tearDown(self):
        """
        Stop all patchers after each test.
        """
        self.resolve_streams_patcher.stop()
        self.stream_inlet_patcher.stop()

    def test_find_stream_success(self):
        """
        Test finding multiple streams successfully.
        """
        stream_names = ["DSI-Stream", "Marker-Stream"]
        inlets, channel_labels = find_stream(stream_names)

        self.assertEqual(len(inlets), 2)
        self.assertIn(self.mock_inlet1, inlets)
        self.assertIn(self.mock_inlet2, inlets)
        self.assertEqual(
            channel_labels,
            {"DSI-Stream": ["EEG1", "EEG2"], "Marker-Stream": ["Marker1"]},
        )
        self.mock_resolve_streams.assert_called_once_with(wait_time=5.0)

    def test_find_stream_not_found(self):
        """
        Test that an exception is raised when no streams are found.
        """
        self.mock_resolve_streams.return_value = []
        with self.assertRaises(RuntimeError) as context:
            find_stream(["NonExistentStream"])
        self.assertIn(
            "No specified LSL streams were found", str(context.exception)
        )


class TestUnifiedReceiveData(unittest.TestCase):
    """
    Test suite for the unified_receive function.
    """

    def setUp(self):
        """
        Set up the mocking environment for each test.
        """
        self.time_patcher = patch("tools.consume.unified_receive.time")
        self.open_patcher = patch(
            "tools.consume.unified_receive.open", new_callable=mock_open
        )
        self.csv_writer_patcher = patch(
            "tools.consume.unified_receive.csv.writer"
        )

        self.mock_time = self.time_patcher.start()
        self.mock_open_func = self.open_patcher.start()
        self.mock_csv_writer = self.csv_writer_patcher.start()
        self.mock_time.time.side_effect = [
            0,
            1,
            2,
            6,
        ]

        mock_inlet1_info = MagicMock()
        mock_inlet1_info.name.return_value = "DSI-Stream"
        mock_inlet1_info.channel_count.return_value = 2
        self.mock_inlet1 = MagicMock()
        self.mock_inlet1.info.return_value = mock_inlet1_info
        self.mock_inlet1.pull_sample.return_value = ([1.0, 2.0], 12345.1)

        mock_inlet2_info = MagicMock()
        mock_inlet2_info.name.return_value = "Marker-Stream"
        mock_inlet2_info.channel_count.return_value = 1
        self.mock_inlet2 = MagicMock()
        self.mock_inlet2.info.return_value = mock_inlet2_info
        self.mock_inlet2.pull_sample.return_value = ([100], 12345.2)

    def tearDown(self):
        """
        Stop all patchers after each test.
        """
        self.time_patcher.stop()
        self.open_patcher.stop()
        self.csv_writer_patcher.stop()

    def test_unified_receive_creates_temp_file(self):
        """
        Test that data is recorded to a temporary CSV file.
        """
        inlets = [self.mock_inlet1, self.mock_inlet2]
        duration = 5
        temp_filename = unified_receive(inlets, duration)

        self.assertTrue(temp_filename.startswith("temp-"))
        self.assertTrue(temp_filename.endswith(".csv"))

        self.mock_open_func.assert_called_once_with(
            temp_filename, "w", newline=""
        )
        mock_writer_instance = self.mock_csv_writer.return_value
        mock_writer_instance.writerow.assert_any_call(
            ["lsl_timestamp", "stream_name", "value_ch1", "value_ch2"]
        )
        mock_writer_instance.writerow.assert_any_call(
            [12345.1, "DSI-Stream", 1.0, 2.0]
        )
        mock_writer_instance.writerow.assert_any_call(
            [12345.2, "Marker-Stream", 100]
        )


class TestFormatCsv(unittest.TestCase):
    """
    Test suite for the format_csv function.
    """

    def setUp(self):
        """
        Set up the mocking environment for each test.
        """
        self.os_remove_patcher = patch(
            "tools.consume.unified_receive.os.remove"
        )
        self.open_patcher = patch("builtins.open", mock_open())
        self.read_csv_patcher = patch(
            "tools.consume.unified_receive.pd.read_csv"
        )

        self.mock_os_remove = self.os_remove_patcher.start()
        self.mock_open = self.open_patcher.start()
        self.mock_read_csv = self.read_csv_patcher.start()

        mock_data = {
            "lsl_timestamp": [100.1, 100.2, 100.3],
            "stream_name": ["DSI-Stream", "Marker-Stream", "DSI-Stream"],
            "value_ch1": [1.1, 10, 1.2],
            "value_ch2": [2.1, np.nan, 2.2],
        }
        self.mock_df = pd.DataFrame(mock_data)
        self.mock_read_csv.return_value = self.mock_df

    def tearDown(self):
        """
        Stop all patchers after each test.
        """
        self.os_remove_patcher.stop()
        self.open_patcher.stop()
        self.read_csv_patcher.stop()

    def test_format_csv_success(self):
        """
        Test successful formatting of the temporary CSV into a wide format.
        """
        stream_channel_labels = {
            "DSI-Stream": ["EEG1", "EEG2"],
            "Marker-Stream": ["Marker"],
        }
        temp_filename = "temp-test.csv"
        final_filename_base = "output"

        format_csv(final_filename_base, temp_filename, stream_channel_labels)

        self.mock_read_csv.assert_called_once_with(temp_filename)
        written_data = "".join(
            call.args[0] for call in self.mock_open().write.call_args_list
        )
        self.read_csv_patcher.stop()
        saved_df = pd.read_csv(StringIO(written_data))

        self.assertIn("lsl_timestamp", saved_df.columns)
        self.assertIn("DSI-Stream_EEG1", saved_df.columns)
        self.assertIn("DSI-Stream_EEG2", saved_df.columns)
        self.assertIn("Marker-Stream_Marker", saved_df.columns)
        self.assertEqual(saved_df.shape, (2, 4))
        self.assertEqual(saved_df["Marker-Stream_Marker"].iloc[0], 0)
        self.assertEqual(saved_df["Marker-Stream_Marker"].iloc[1], 10)
        self.mock_os_remove.assert_called_once_with(temp_filename)


if __name__ == "__main__":
    unittest.main()
