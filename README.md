# PDP-11 Binary File Uploader

This tool uploads binary files to a PDP-11 through a serial port while the ODT monitor is running. It handles the communication protocol and ensures proper byte ordering for the PDP-11 architecture.

## Requirements

- Python 3.6 or higher
- pyserial library for serial port access
- tqdm library for progress reporting

## Installation

1. Install the required dependencies (you may want to use a [virtual environment](https://docs.python.org/3/library/venv.html)):
```bash
pip install -r requirements.txt
```

## Usage

```bash
python odt-uploader.py <serial_port> <binary_file> <start_address> [-v]
```

Where:
- `<serial_port>` is the serial port device (e.g., `/dev/ttyUSB0` on Linux, `COM1` on Windows)
- `<binary_file>` is the path to the binary file to upload
- `<start_address>` is the octal start address where the file should be loaded
- `-v` or `--verbose` enables detailed logging of serial communication

Example:
```bash
python odt-uploader.py /dev/ttyUSB0 program.bin 1000 -v
```

This will upload `program.bin` starting at address 1000 (octal) with verbose logging enabled.

## Features

- Configures serial port for 38400 bps, 8N1
- Handles PDP-11 little-endian byte ordering
- Verifies character echo from ODT
- Provides progress updates during upload
- Handles timeouts and communication errors
- Ensures even number of bytes by padding if necessary
- Optional verbose logging of all serial communication

## Verbose Logging

When the `-v` flag is used, the tool will log:
- All bytes sent and received in hex and ASCII format
- Detailed information about each word being sent
- File size and padding information
- Serial port configuration details
- Progress updates during upload

Example verbose output:
```
12:34:56 - INFO - File size: 1024 bytes
12:34:56 - INFO - Opened serial port /dev/ttyUSB0 at 38400 bps, 8N1
12:34:56 - INFO - Waiting for initial prompt...
12:34:56 - DEBUG - RX: 40 | @
12:34:56 - DEBUG - TX: 0d | \r
12:34:56 - DEBUG - RX: 0d | \r
12:34:56 - DEBUG - RX: 40 | @
12:34:56 - DEBUG - Sending word 000123 (decimal: 83)
12:34:56 - DEBUG - TX: 31 | 1
12:34:56 - DEBUG - RX: 31 | 1
...
```

## Error Handling

The tool will:
- Verify character echo from ODT
- Timeout if expected responses are not received
- Report any communication errors
- Exit with status code 1 if any errors occur 
