#!/usr/bin/env python3

import argparse
import serial
import time
import sys
import os
import logging
from tqdm import tqdm

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
    """Upload a binary file to the PDP-11 starting at the specified address."""
    # Open and read the binary file
    with open(filename, 'rb') as f:
        data = f.read()
    
    logging.info(f"File size: {len(data)} bytes")
    
    # Ensure even number of bytes
    if len(data) % 2 != 0:
        data += b'\0'
        logging.info("Added padding byte to ensure even length")
    
    # Calculate total words to upload
    total_words = len(data) // 2
    
    # Open serial port
    with serial.Serial(port, 38400, bytesize=8, parity='N', stopbits=1, timeout=1) as ser:
        logging.info(f"Opened serial port {port} at 38400 bps, 8N1")
        
        # Send initial CR to get ODT's attention
        logging.info("Sending initial CR to get ODT's attention...")
        send_char(ser, ord('\r'))
        
        # Wait for initial prompt
        read_until_prompt(ser, b'@')
        
        # Send start address
        logging.info(f"Setting start address to {start_address:06o}")
        addr_str = f"{start_address:06o}/"
        for char in addr_str.encode():
            send_char(ser, char)
        
        # Read the space prompt
        read_until_prompt(ser, b' ')
        
        # Create progress bar
        pbar = tqdm(total=total_words, unit='words', desc='Uploading')
        
        # Upload data word by word
        words_uploaded = 0
        for i in range(0, len(data), 2):
            # PDP-11 is little-endian, so swap bytes if needed
            word = (data[i+1] << 8) | data[i]
            
            try:
                # Format word in octal, suppressing leading zeros but keeping single zero for zero
                octal_str = f"{word:o}\n" if word > 0 else "0\n"
                logging.debug(f"Sending word {octal_str.strip()} (decimal: {word})")
                
                # Send each character
                for char in octal_str.encode():
                    send_char(ser, char)
                
                # Read the next space prompt
                read_until_prompt(ser, b' ')
                
                words_uploaded += 1
                pbar.update(1)
            except Exception as e:
                pbar.close()
                logging.error(f"\nError at word {words_uploaded}: {e}")
                return False
        
        pbar.close()
        logging.info(f"\nUpload complete: {words_uploaded} words uploaded")
        return True

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