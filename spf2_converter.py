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


class spf2Converter(TerminalColours):
    BYTE_OFFSET = 524
    NUMERIC_BYTES = 4

    def __init__(self):
        self.data_dir = PROJECT_DIR
        self.file = None

    def select_file(self, 
                    filter="spf2 (*.spf2)", # "All Files (*.*)",
                    silent=False    
                    ):
        self.file = fu.select_file(self.data_dir, filter)
        self.data_dir = self.file.parent if self.file else self.data_dir
        if not silent:
            print(f"{self.BLUE} Selected file: {self.RESET} {self.file}")
            print(f"{self.BLUE} Data directory: {self.RESET} {self.data_dir}")
        return self
    


if __name__ == "__main__":
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
    converter = spf2Converter()

    converter.select_file(silent=False)






    # tc = TerminalColours()
    # print(f"{tc.BLUE} Project directory:{tc.RESET} {PROJECT_DIR}")
    
    # # data_dir = fu.select_folder(PROJECT_DIR)
    # # print(f"{tc.BLUE} Data directory: {tc.RESET} {data_dir}")
    # file = fu.select_file(PROJECT_DIR,)  # "spf2"
    # print(f"{tc.BLUE} Selected file: {tc.RESET} {file}")
