import unittest
from unittest.mock import MagicMock, call
import sys

mock_psychopy = MagicMock()
sys.modules["psychopy"] = mock_psychopy
sys.modules["psychopy.visual"] = mock_psychopy.visual
sys.modules["psychopy.core"] = mock_psychopy.core

mock_serial = MagicMock()
sys.modules["serial"] = mock_serial

mock_pylsl = MagicMock()
sys.modules["pylsl"] = mock_pylsl

import tools.experiment.photodiode as pd


class TestPhotodiodeSuite(unittest.TestCase):
    """A unittest test suite for the photodiode experiment script."""

    def setUp(self):
        """
        Reset all mocks before each test method in the suite is executed.
        This is the standard unittest setup method.
        """
        mock_psychopy.reset_mock()
        mock_serial.reset_mock()
        mock_pylsl.reset_mock()

    def test_createMarkerStream(self):
        """
        Tests the creation of a LabStreamingLayer (LSL) marker stream.
        """
        stream_name = "TestStream"
        trig_val = 5
        mock_outlet = MagicMock()
        mock_pylsl.StreamOutlet.return_value = mock_outlet
        outlet, returned_trig_val = pd.createMarkerStream(
            stream_name, trig_val
        )

        mock_pylsl.StreamInfo.assert_called_once_with(
            name=stream_name,
            type="Markers",
            channel_count=1,
            nominal_srate=0,
            channel_format="int32",
            source_id="my_unique_id_12345",
        )
        mock_pylsl.StreamOutlet.assert_called_once()
        self.assertEqual(outlet, mock_outlet)
        self.assertEqual(returned_trig_val, trig_val)

    def test_multiTrigHandler_all_triggers(self):
        """
        Tests the trigger handler when both hardware and software triggers are
        active.
        """
        mock_port = MagicMock()
        mock_outlet = MagicMock()
        port_arg = bytes(chr(2), "utf-8")
        outlet_arg = [2]
        mock_pylsl.local_clock.return_value = 1000.0
        offset = 5.0
        pd.multiTrigHandler(
            mmbts_use=True,
            software_use=True,
            port=mock_port,
            arg1=port_arg,
            outlet=mock_outlet,
            arg2=outlet_arg,
            offset_value=offset,
        )
        mock_port.write.assert_called_once_with(port_arg)
        mock_outlet.push_sample.assert_called_once_with(
            outlet_arg, 1000.0 - offset
        )

    def test_multiTrigHandler_no_triggers(self):
        """
        Tests the trigger handler when both hardware and software triggers are
        disabled.
        """
        mock_port = MagicMock()
        mock_outlet = MagicMock()
        pd.multiTrigHandler(
            mmbts_use=False,
            software_use=False,
            port=mock_port,
            arg1=None,
            outlet=mock_outlet,
            arg2=None,
            offset_value=0.0,
        )

        mock_port.write.assert_not_called()
        mock_outlet.push_sample.assert_not_called()

    def test_timer(self):
        """
        Tests the countdown timer functionality.
        """
        mock_win = MagicMock()
        countdown = 3
        pd.timer(mock_win, countdown)

        self.assertEqual(
            mock_psychopy.visual.TextStim().draw.call_count, countdown
        )
        self.assertEqual(mock_win.flip.call_count, countdown)
        mock_psychopy.core.wait.assert_has_calls([call(1.0)] * countdown)

    def test_lightbox_top_right(self):
        """
        Tests lightbox creation in the top-right position.
        """
        mock_win = MagicMock()
        mock_win.size = [1920, 1080]
        box_size = 200

        pd.lightbox(mock_win, box_size, "top_right")

        expected_pos_x = (1920 / 2) - (box_size / 2)
        expected_pos_y = (1080 / 2) - (box_size / 2)
        mock_psychopy.visual.Rect.assert_called_once_with(
            mock_win,
            size=(box_size, box_size),
            fillColor="white",
            pos=(expected_pos_x, expected_pos_y),
        )

    def test_lightbox_top_left(self):
        """
        Tests lightbox creation in the top-left position.
        """
        mock_win = MagicMock()
        mock_win.size = [1920, 1080]
        box_size = 200

        pd.lightbox(mock_win, box_size, "top_left")

        expected_pos_x = -((1920 / 2) - (box_size / 2))
        expected_pos_y = (1080 / 2) - (box_size / 2)

        mock_psychopy.visual.Rect.assert_called_once_with(
            mock_win,
            size=(box_size, box_size),
            fillColor="white",
            pos=(expected_pos_x, expected_pos_y),
        )

    def test_photodiode_main_function(self):
        """
        Tests the main photodiode experiment workflow.
        """
        port_str = "COM10"
        num_trials = 2
        display_rate = 0.5
        offset = 0.1
        mock_outlet = MagicMock()
        software_stream = (mock_outlet, 5)

        mock_port_instance = MagicMock()
        mock_serial.Serial.return_value = mock_port_instance

        mock_win_instance = MagicMock()
        mock_win_instance.size = [1920, 1080]

        mock_psychopy.visual.Window.return_value = mock_win_instance

        pd.photodiode(
            port_str, software_stream, num_trials, display_rate, offset
        )

        mock_serial.Serial.assert_called_once_with(port_str)
        mock_psychopy.visual.Window.assert_called_once()

        expected_flip_count = (num_trials * 2) + 3
        self.assertEqual(
            mock_win_instance.flip.call_count, expected_flip_count
        )

        mock_port_instance.write.assert_called_with(bytes(chr(0), "utf-8"))
        mock_port_instance.close.assert_called_once()
        mock_win_instance.close.assert_called_once()
        mock_psychopy.core.quit.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
