import unittest
from unittest.mock import patch, MagicMock, call, ANY

from tools.experiment.photodiode import (
    photodiode,
    createMarkerStream,
    multiTrigHandler,
)


class TestCreateMarkerStream(unittest.TestCase):
    """Tests the LSL stream creation logic using setUp and tearDown."""

    def setUp(self):
        """Set up patchers for LSL stream classes."""
        self.stream_outlet_patcher = patch(
            "tools.experiment.photodiode.StreamOutlet"
        )
        self.stream_info_patcher = patch(
            "tools.experiment.photodiode.StreamInfo"
        )

        self.mock_stream_outlet = self.stream_outlet_patcher.start()
        self.mock_stream_info = self.stream_info_patcher.start()

    def tearDown(self):
        """Stop the patchers to clean up the test environment."""
        self.stream_outlet_patcher.stop()
        self.stream_info_patcher.stop()

    def test_createMarkerStream_success(self):
        """
        Verify that StreamInfo and StreamOutlet are created with correct
        parameters.
        """
        stream_name = "MyTestStream"
        trig_val = 5

        outlet, returned_trig = createMarkerStream(stream_name, trig_val)
        self.mock_stream_info.assert_called_once_with(
            name=stream_name,
            type="Markers",
            channel_count=1,
            nominal_srate=0,
            channel_format="int32",
            source_id=ANY,
        )

        self.mock_stream_outlet.assert_called_once_with(
            self.mock_stream_info.return_value
        )
        self.assertEqual(outlet, self.mock_stream_outlet.return_value)
        self.assertEqual(returned_trig, trig_val)


class TestMultiTrigHandler(unittest.TestCase):
    """Tests the trigger handler logic using setUp and tearDown."""

    def setUp(self):
        """Set up and start the patcher for local_clock."""
        self.clock_patcher = patch(
            "tools.experiment.photodiode.local_clock", return_value=1000.0
        )
        self.mock_clock = self.clock_patcher.start()

    def tearDown(self):
        """Stop the patcher after the test."""
        self.clock_patcher.stop()

    def test_multiTrigHandler_all_systems_go(self):
        """
        Test that both hardware and software triggers are sent correctly.
        """
        mock_port = MagicMock()
        mock_outlet = MagicMock()
        offset = 5.5

        multiTrigHandler(
            mmbts_use=True,
            software_use=True,
            port=mock_port,
            arg1=b"\x02",
            outlet=mock_outlet,
            arg2=[2],
            offset_value=offset,
        )

        mock_port.write.assert_called_once_with(b"\x02")
        expected_timestamp = 1000.0 - offset
        mock_outlet.push_sample.assert_called_once_with(
            [2], expected_timestamp
        )


class TestPhotodiodeExperiment(unittest.TestCase):
    """Tests the main photodiode experiment logic using setUp and tearDown."""

    def setUp(self):
        """Set up patchers for all external libraries."""
        self.serial_patcher = patch("tools.experiment.photodiode.serial")
        self.core_patcher = patch("tools.experiment.photodiode.core")
        self.visual_patcher = patch("tools.experiment.photodiode.visual")

        self.mock_serial = self.serial_patcher.start()
        self.mock_core = self.core_patcher.start()
        self.mock_visual = self.visual_patcher.start()

        self.mock_win = self.mock_visual.Window.return_value
        self.mock_win.size = (800, 600)
        self.mock_port_instance = self.mock_serial.Serial.return_value

    def tearDown(self):
        """Stop all patchers."""
        self.serial_patcher.stop()
        self.core_patcher.stop()
        self.visual_patcher.stop()

    def test_photodiode_with_hardware_and_software(self):
        """
        Verify the main loop and triggers when using both hardware and
        software.
        """
        mock_outlet = MagicMock()
        trials = 2
        display_rate = 0.1
        port_string = "COM3"
        soft_trig_val = 1
        software_stream = (mock_outlet, soft_trig_val)

        photodiode(
            portStr=port_string,
            software_stream=software_stream,
            trials=trials,
            display_rate=display_rate,
        )

        self.mock_serial.Serial.assert_called_once_with(port_string)
        self.mock_win.close.assert_called_once()
        self.mock_core.quit.assert_called_once()
        self.mock_port_instance.close.assert_called_once()

        on_trigger_hardware_arg = bytes(chr(2), "utf-8")
        on_trigger_software_arg = [soft_trig_val]
        off_trigger_hardware_arg = bytes(chr(0), "utf-8")
        off_trigger_software_arg = [0]

        expected_calls = [
            call(
                ANY,
                True,
                True,
                self.mock_port_instance,
                on_trigger_hardware_arg,
                mock_outlet,
                on_trigger_software_arg,
                0.0,
            ),
            call(
                ANY,
                True,
                True,
                self.mock_port_instance,
                off_trigger_hardware_arg,
                mock_outlet,
                off_trigger_software_arg,
                0.0,
            ),
            call(
                ANY,
                True,
                True,
                self.mock_port_instance,
                on_trigger_hardware_arg,
                mock_outlet,
                on_trigger_software_arg,
                0.0,
            ),
            call(
                ANY,
                True,
                True,
                self.mock_port_instance,
                off_trigger_hardware_arg,
                mock_outlet,
                off_trigger_software_arg,
                0.0,
            ),
        ]
        self.mock_win.callOnFlip.assert_has_calls(expected_calls)

    def test_photodiode_no_hardware_or_software(self):
        """
        Test that the experiment runs but sends no triggers if both are None.
        """
        photodiode(
            portStr=None, software_stream=None, trials=1, display_rate=0.1
        )
        self.mock_serial.Serial.assert_not_called()
        self.mock_win.close.assert_called_once()
        self.mock_core.quit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
