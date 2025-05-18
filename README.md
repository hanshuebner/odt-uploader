# ODT Uploader

A Python script for uploading binary files to a PDP-11 via serial port using ODT (Octal Debugging Technique).

## Overview

This script implements a two-phase upload process:
1. First, a small loader program is uploaded using ODT. This loader is responsible for receiving the binary data and storing it in memory.
2. Then, the actual binary program is sent directly over the serial port, with the loader handling the byte-by-byte transfer.

This approach is much faster than using ODT for the entire transfer, as it minimizes the overhead of ASCII conversion and handshaking.

## Requirements

- Python 3.x
- pyserial
- tqdm

## Usage

```bash
./odt-uploader.py <port> <filename> <start_address>
```

Arguments:
- `port`: Serial port (e.g., /dev/ttyUSB0)
- `filename`: Binary file to upload
- `start_address`: Start address in octal

Options:
- `-v, --verbose`: Enable verbose logging

## Example

```bash
./odt-uploader.py /dev/ttyUSB0 program.bin 1000
```

This will:
1. Upload the loader program to address 100
2. Start the loader
3. Send the binary data directly
4. Wait for the loader to complete

## How it Works

1. The script first uploads a small loader program using ODT. The loader:
   - Sets up registers for the destination address and data length
   - Waits for bytes from the serial port
   - Copies each byte to memory
   - Halts when complete

2. Once the loader is in place, the script:
   - Starts the loader with the ODT command "100g"
   - Sends the binary data directly over the serial port
   - Waits for the loader to complete and return to ODT

The loader handles the actual byte-by-byte transfer, making the process much faster than using ODT for the entire transfer.

## Notes

- The loader program is stored in the script as a constant
- The loader automatically adjusts the length based on the input file size
- The script includes proper timing to ensure reliable transmission
- Progress is shown with a progress bar during the binary transfer phase

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
