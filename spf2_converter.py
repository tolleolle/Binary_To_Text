# THORLabsSpectrometer\spf2_converter.py
"""
Script for converting Thorlabs .spf2 files to .txt files
Thorlabs CCS100/M spectrometer
"""
import struct
from pathlib import Path
import os
import subprocess
import sys

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from utils.terminal_styler import TerminalColours
import utils.file_utils as fu


class SPF2Converter(TerminalColours):
    BYTE_OFFSET = 6132 #524 6160 Number of Header bytes
    NUMERIC_BYTES = 4

    def __init__(self):
        self.data_dir = PROJECT_DIR
        self.filepath = None
        self.metadata = {}
        self.df: pd.DataFrame | None = None
        self._raw_bytes = None


    def select_file(self, 
                    filter="spf2 (*.spf2)", # "All Files (*.*)",
                    silent=False    
                    ):
        self.filepath = fu.select_file(self.data_dir, filter)
        self.data_dir = self.filepath.parent if self.filepath else self.data_dir
        if not silent:
            print(f"{self.BLUE} Selected file: {self.RESET} {self.filepath}")
            print(f"{self.BLUE} Data directory: {self.RESET} {self.data_dir}")
        return self


    def load(self, silent=False):
        if not self.filepath or not self.filepath.exists():
            print(f"{self.RED}SPF2Converter.load(): No file selected. {self.RESET}")
            return self

        try:
            with open(self.filepath, 'rb') as f:
                self._raw_bytes = f.read()
            if not silent:
                print(f"{self.GREEN} File loaded successfully: {self.RESET} {self.filepath}")
        except Exception as e:
            print(f"{self.RED} Error loading file: {self.RESET} {self.filepath}")
            print(f"{self.RED} Error: {self.RESET} {e} ")    
                 
        return self


    def _search_words(self, min_len=3, silent=False):
        header = self._raw_bytes[:self.BYTE_OFFSET]
        current_chars = []
        start_offset = 0

        print(f"{self.BLUE} Searching for words in the header... {self.RESET}")
        for offset, byte in enumerate(header):
            if 32 <= byte <= 126:  # Printable ASCII range
                if not current_chars:
                    start_offset = offset
                current_chars.append(chr(byte))
            else:
                if len(current_chars) >= min_len:
                    word = ''.join(current_chars)
                    end_offset = start_offset + len(current_chars) - 1
                    print(f"Found word: {word} at offset {start_offset}-{end_offset}")
                current_chars = []
                    
    def _search_numbers(self, silent=False):
        limit = min(self.BYTE_OFFSET, len(self._raw_bytes) - 3)
        for offset in range(0, limit, 4):
            chunk = self._raw_bytes[offset : offset + 4]

            ## Unpack as a 32-bit signed/unsigned integer.
            val_int = struct.unpack("<i", chunk)[0]
            val_uint = struct.unpack("<I", chunk)[0]

            ## Unpack as a 32-bit floating-point number (float)
            val_float = struct.unpack("<f", chunk)[0]

            ## Skip empty (zero) bytes.
            if val_uint == 0:
                continue

            findings = []

            ## Filter for integers (e.g., number of points, time in ms/μs)
            if 0 < val_int < 1_000_000_000:
                findings.append(f"int32 = {self.GREEN}{val_int}{self.RESET}")

            ## Filter for floating-point numbers (time in seconds, calibration coefficients)
            if not np.isnan(val_float) and not np.isinf(val_float):
                if 0.00001 <= abs(val_float) <= 1_000_000.0:
                    findings.append(f"float32 = {self.YELLOW2}{val_float:.6g}{self.RESET}")

            ## Print meaningful numbers
            if findings and not silent:
                range_str = f"{offset:4d}..{offset+3:4d}"
                print(f" Offset {self.BLUE}{range_str}{self.RESET} байт | " + " | ".join(findings))

        return self

    def _search_64bit_numbers(self, silent=False):
        print(f"{self.BLUE} Searching for 64-bit numbers in the header... {self.RESET}")
        limit = min(self.BYTE_OFFSET, len(self._raw_bytes) - 7)
        for offset in range(0, limit, 8):
            chunk = self._raw_bytes[offset : offset + 8]

            # Unpack as a 64-bit floating-point number (double)
            val_double = struct.unpack("<d", chunk)[0]

            # Skip empty (zero) bytes.
            if val_double == 0.0:
                continue

            # Filter for floating-point numbers (time in seconds, calibration coefficients)
            if not np.isnan(val_double) and not np.isinf(val_double):
                if 0.00001 <= abs(val_double) <= 1_000_000.0:
                    if not silent:
                        range_str = f"{offset:4d}..{offset+7:4d}"
                        print(f" Offset {self.BLUE}{range_str}{self.RESET} байт | double64 = {self.YELLOW2}{val_double:.6g}{self.RESET}")

        return self


    def _parse_header(self, silent=False):
        if not self._raw_bytes:
            print(f"{self.RED} No raw bytes to parse. {self.RESET}")
            return self

        try:
            raw_header_text = self._raw_bytes[:self.BYTE_OFFSET].decode("latin-1", errors="ignore").strip()
            print(f"{raw_header_text=}")

            # header_bytes = self._raw_bytes[self.BYTE_OFFSET:self.BYTE_OFFSET + self.NUMERIC_BYTES]
            # length = struct.unpack("<I", header_bytes)[0]

            # self.metadata['length'] = length
        except Exception as e:
            print(f"{self.RED} Error parsing header: {self.RESET} {e}")
        
        return self


if __name__ == "__main__":
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
    converter = SPF2Converter()
    converter.select_file(silent=False).load(silent=False)
    print(len(converter._raw_bytes) if converter._raw_bytes else "No data loaded.")
    converter._search_words(silent=False)
    converter._search_numbers(silent=False)
    converter._search_64bit_numbers(silent=False)

