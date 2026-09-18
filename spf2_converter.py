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

from utils.terminal_styler import TerminalColours as TC
import utils.file_utils as fu
import thorlabs_spf2_to_txt as hannes 

class SPF2Converter(TC):
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


    def convert_folder(self):
        folder_path = fu.select_folder(self.data_dir)
        self.data_dir = folder_path.parent
        if not folder_path.exists() or not folder_path.is_dir():
            print(f"{self.RED}Invalid folder path: {self.RESET} {folder_path}")
            return

        hannes.convert_folder(folder_path)
        return self


class BGCorrector():
    def __init__(self):
        self.data_dir = PROJECT_DIR
        self.output_fname = None
        self.spec_fpath = None
        self.fpath_paired = []
        self.fpath_single = []
        self.bg_fpath = None
        self.fname_parts = None


    def select_spec_file(self):
        filepath = fu.select_file(self.data_dir,)
        if filepath:
            self.data_dir = filepath.parent 
            self.spec_fpath = filepath
        else:
            print(f"{TC.RED} ERROR: {TC.RESET} file not selected")
        return self

    def select_bg_file(self):
        filepath = fu.select_file(self.data_dir,)
        if filepath:
            self.data_dir = filepath.parent if filepath else self.data_dir
            self.bg_fpath = filepath
        else:
            print(f"{TC.RED} ERROR: {TC.RESET} file not selected")
        return self

    def select_folder(self):
        self.data_dir = fu.select_folder(self.data_dir)
        print(f"{self.data_dir=}")


    def read_file(self, fpath):
        if not fpath:
            print(f"{TC.RED} ERROR: {TC.RESET}: files spec or bg not selected")
            return self
        df = pd.read_csv(fpath, sep="\t", header=1, 
                               names=["wavelength1", "intensity1",
                                    "wavelength2", "intensity2"],
                                dtype={"wavelength1": float, "intensity1": float,
                                       "wavelength2": float, "intensity2": float},
                                    )
        return df
    

    def correct_file(self, tx_A=1, tx_B=1):
        """
        correcting backgraund and explosure time
        tx_A and tx_B in seconds are assumed 
        """
        if not self.spec_fpath or not self.bg_fpath:
            print(f"{TC.RED} ERROR: {TC.RESET}: files spec or bg not selected")
            return self

        df = self.read_file(fpath=self.spec_fpath)
        df_bg = self.read_file(fpath=self.bg_fpath)

        df_substracted = df_bg.copy()
        df_substracted["intensity1"] = (df["intensity1"] - df_bg["intensity1"]) / tx_A
        df_substracted["intensity2"] = (df["intensity2"] - df_bg["intensity2"]) / tx_B

        if not self.fname_parts:
            output_fname = self.spec_fpath.name
        else:
            print("make new name")
            output_fname = self.fname_parts[0] + '_' + self.fname_parts[1] + '.txt'

        output_dir = self.data_dir.parent / "bg_corr"
        output_path = output_dir / output_fname
        print(f"{output_path=}")
        output_dir.mkdir(exist_ok=True)
        df_substracted.to_csv(output_path, sep="\t", index=False)

        return self


    def _get_tx(self, fpath:Path):
        """takes spec_fpath and parse tx_A, tx_B 
           takes tx in ms and returns in sec
        """
        if fpath:   
            self.spec_fpath = fpath
        if not self.spec_fpath:
            print(f"{TC.RED} ERROR:{TC.RESET} file not selected")
            return None 
        sp_name = fpath.name.split('_')

        txa_part = sp_name[2].split('ms')
        tx_A = txa_part[0].replace("a", "")
        tx_A = int(tx_A) / 1000

        txb_part = sp_name[2].split('ms')
        tx_B = txb_part[0].replace("a", "")
        tx_B = int(tx_B) / 1000
        return {'tx_A': tx_A, 'tx_B': tx_B}
   

    def get_spec_bg_pairs(self):
        self.select_folder()
        files = fu.list_files_in_folder(self.data_dir)

        ## seporate spec and bg files
        bg_files = []
        spec_files = []
        for file in files:
            if file.name.endswith('_bg.txt'):
                bg_files.append(file)
            else:
                spec_files.append(file)

        # for f in bg_files:
        #     print(f.name)
        ## seporate piared and single files
        self.fpath_paired = []
        self.fpath_single = []
        for f in spec_files:
            f_bg = f.parent / f"{f.stem}_bg.txt"
            if f_bg in bg_files:
                print(f"{TC.GREEN} {f.stem} {TC.RESET}")
                self.fpath_paired.append(f)
            else:
                print(f"{TC.RED}{f.stem} {TC.RESET}")
                self.fpath_single.append(f)
        return self

    def correct_folder(self):
        if not self.fpath_paired:
            print(f"{TC.RED} ERROR:{TC.RESET} run get_spec_bg_pairs() first")
            return 

        for f in self.fpath_paired:
            self.spec_fpath = f
            self.bg_fpath = f.parent / f"{f.stem}_bg.txt"
            tx = self._get_tx(f)
            self.correct_file(**tx)




if __name__ == "__main__":
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
    # converter = SPF2Converter()
    # converter.select_file(silent=False).load(silent=False)
    # print(len(converter._raw_bytes) if converter._raw_bytes else "No data loaded.")
    # converter._search_words(silent=False)
    # converter._search_numbers(silent=False)
    # converter._search_64bit_numbers(silent=False)

    # print(f"{converter.filepath=}, {converter.data_dir=},")
    # hannes.thorlabs_spf2_to_txt(converter.filepath)
    #converter.convert_folder()

    corrector = BGCorrector()
    corrector.select_spec_file().select_bg_file()
    corrector.correct_file()

