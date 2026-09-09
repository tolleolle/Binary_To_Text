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
    BYTE_OFFSET = 6160 #524 
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
        pass

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


    # converter._parse_header(silent=False)






    # tc = TerminalColours()
    # print(f"{tc.BLUE} Project directory:{tc.RESET} {PROJECT_DIR}")
    
    # # data_dir = fu.select_folder(PROJECT_DIR)
    # # print(f"{tc.BLUE} Data directory: {tc.RESET} {data_dir}")
    # file = fu.select_file(PROJECT_DIR,)  # "spf2"
    # print(f"{tc.BLUE} Selected file: {tc.RESET} {file}")
