import serial
import time

def send_serial_trigger(portStr, triggerVal):
    """
    Sends a trigger value to the specified serial port.

    Args:
        portStr (str): The serial port to which the trigger will be sent (e.g., 'COM3' or '/dev/ttyUSB0').
        triggerVal (int): The trigger value to send (0-255).

    Returns:
        None
    """
    try:
        print(f"Attempting to send trigger value {triggerVal} to port {portStr}")
        with serial.Serial(portStr, baudrate=9600) as port:
            port.write(bytes([triggerVal]))
            time.sleep(1)  # Hold the trigger for 1 second
            print(f"Sent trigger value {triggerVal} to port {portStr}")
            port.write(bytes([0]))  # Reset trigger
    except serial.SerialException as e:
        print(f"Error opening or using serial port {portStr}: {e}")
    except ValueError as e:
        print(f"Invalid trigger value {triggerVal}: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send a trigger value to a serial port.")
    parser.add_argument("--port", type=str, help="The serial port to which the trigger will be sent (e.g., 'COM3' or '/dev/ttyUSB0').")
    parser.add_argument("--value", type=int, help="The trigger value to send (0-255).")
    parser.add_argument("-i", "--iterations", help="Number of iterations.", type=int, default=1)
    parser.add_argument("--buffer", type=int, default=1, help="Buffer time in seconds between sends.")

    args = parser.parse_args()

    try:
        if 0 <= args.value <= 255:
            for i in range(args.iterations):
                send_serial_trigger(args.port, args.value)
                time.sleep(args.buffer)
        else:
            print("Trigger value must be between 0 and 255.")
    except KeyboardInterrupt:
        print("Process interrupted by user.")
        exit(0)
        