#!/usr/bin/env python3

import argparse
import serial
import time
import sys
import os
import logging
from tqdm import tqdm

# Loader program in octal format (address, value)
LOADER = [
    (0o100, 0o012700),  # MOV #1000, R0
    (0o102, 0o001000),  # Start Address
    (0o104, 0o012701),  # MOV #length, R1
    (0o106, 0o000000),  # Length (to be filled in)
    (0o110, 0o032737),  # BIT #200, @#RCSR
    (0o112, 0o000200),
    (0o114, 0o177560),
    (0o116, 0o001774),  # BEQ 110
    (0o120, 0o113720),  # MOVB @#RBUF, (R0)+
    (0o122, 0o177562),
    (0o124, 0o077107),  # SOB R1, 110
    (0o126, 0o000000),  # HALT
]

def setup_logging(verbose):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

def log_bytes(prefix, data):
    """Log bytes in a readable format."""
    if isinstance(data, (bytes, bytearray)):
        hex_str = ' '.join(f'{b:02x}' for b in data)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
        logging.debug(f"{prefix}: {hex_str} | {ascii_str}")
    else:
        logging.debug(f"{prefix}: {data}")

def read_until_prompt(ser, expected_prompt, timeout=1.0):
    """Read from serial port until we get the expected prompt."""
    start_time = time.time()
    response = bytearray()

    while time.time() - start_time < timeout:
        if ser.in_waiting:
            char = ser.read(1)
            response.extend(char)
            log_bytes("RX", char)
            if char == expected_prompt:
                return bytes(response)

    raise TimeoutError(f"Did not receive expected prompt '{expected_prompt}' within {timeout} seconds")

def send_char(ser, char):
    """Send a character and verify echo if it's printable."""
    ser.write(bytes([char]))
    log_bytes("TX", bytes([char]))

    # Only verify echo for printable characters
    if 32 <= char <= 126:
        echo = ser.read(1)
        log_bytes("RX", echo)
        if echo != bytes([char]):
            raise RuntimeError(f"Echo mismatch: sent {char}, received {echo}")
    else:
        # For non-printable characters, just log that we sent it
        logging.debug(f"Sent non-printable character: {char:02x}")

def send_word(ser, word, timeout=1.0):
    """Send a word (2 bytes) in octal format and verify echo."""
    # Convert word to octal string, ensuring 6 digits
    octal_str = f"{word:06o}\n"
    logging.debug(f"Sending word {word:06o} (decimal: {word})")

    # Send each character
    for char in octal_str.encode():
        send_char(ser, char)

    # Read the next address prompt (should end with space)
    response = read_until_prompt(ser, b' ', timeout)
    return response

def upload_file(port, filename, start_address):
    """Upload a binary file to the PDP-11 using the loader program."""
    # Open and read the binary file
    with open(filename, 'rb') as f:
        data = f.read()

    logging.info(f"File size: {len(data)} bytes")

    # Open serial port
    with serial.Serial(port, 38400, bytesize=8, parity='N', stopbits=1, timeout=1) as ser:
        logging.info(f"Opened serial port {port} at 38400 bps, 8N1")

        # Send initial CR to get ODT's attention
        logging.info("Sending initial CR to get ODT's attention...")
        send_char(ser, ord('\r'))

        # Wait for initial prompt
        read_until_prompt(ser, b'@')

        # Upload the loader program
        logging.info("Uploading loader program...")

        # Send initial address to start input mode
        addr_str = f"{LOADER[0][0]:06o}/"
        for char in addr_str.encode():
            send_char(ser, char)

        # Read the space prompt
        read_until_prompt(ser, b' ')

        # Send all values in sequence
        for addr, value in LOADER:
            # Set dynamic values based on address
            if addr == 0o102:
                value = start_address  # Set the start address
            elif addr == 0o106:
                value = len(data)      # Set the length

            # Send the value
            value_str = f"{value:06o}\n"
            for char in value_str.encode():
                send_char(ser, char)

            # Read the next space prompt
            read_until_prompt(ser, b' ')

        # End input mode with CR
        send_char(ser, ord('\r'))

        # Wait for ODT prompt
        read_until_prompt(ser, b'@')

        # Start the loader
        logging.info("Starting loader program...")
        for char in b"100g":
            send_char(ser, char)

        # Wait for loader to start
        time.sleep(0.1)

        # Send the binary data directly
        logging.info("Sending binary data...")
        pbar = tqdm(total=len(data), unit='bytes', desc='Uploading')

        # Calculate delay per byte (10 bits at 38400 bps)
        byte_delay = 10 / 38400

        for byte in data:
            ser.write(bytes([byte]))
            time.sleep(byte_delay)  # Wait for transmission to complete
            pbar.update(1)

        pbar.close()

        # Wait for loader to finish and return to ODT
        logging.info("Waiting for loader to complete...")
        try:
            read_until_prompt(ser, b'@', timeout=5.0)
            logging.info("Upload complete")
            return True
        except TimeoutError:
            logging.error("Loader did not return to ODT prompt")
            return False

def main():
    parser = argparse.ArgumentParser(description='Upload binary file to PDP-11 via serial port')
    parser.add_argument('port', help='Serial port (e.g., /dev/ttyUSB0)')
    parser.add_argument('filename', help='Binary file to upload')
    parser.add_argument('start_address', type=lambda x: int(x, 8), help='Start address in octal')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    setup_logging(args.verbose)

    try:
        success = upload_file(args.port, args.filename, args.start_address)
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
