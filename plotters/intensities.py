import matplotlib.pyplot as plt
import sys
from pathlib import Path
import pandas as pd

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.terminal_styler import TerminalColours as TC
import utils.file_utils as fu
from utils.plt_styler_avp import PlotStyler

class IntensityPlotter():
    '''
    A - spectrometer Antenna 
    B - spectrometer Backside
    '''
    PIXEL_MAP = {
        'A': {'ArI': 3262, 'ArII': 1028},
        'B': {'ArI': 3262-11, 'ArII': 1028-3}
    }

    def __init__(self):
        self.data_dir = None
        self.fig = None
        self.ax = None

    def read_int_tables(self, fpath=None, silent=False, comment:str=None):
        data = {}
        required_files = {"spectr_A.csv", "spectr_B.csv", "wavelengths_map.csv"}
        if not fpath:
            fpath = fu.select_file(self.data_dir,)
            print(f"{TC.BLUE} {fpath} {TC.RESET}")

        if not fpath:
            print(f"{TC.RED} ERROR: {TC.RESET} file not selected")
            return None

        self.data_dir = fpath.parent 
        files = fu.list_files_in_folder(folder_path=self.data_dir)
        list_files = []
        for file in files:
            list_files.append(file.name)
            if not silent:
                print(file.name)
        existing_files = set(list_files)
        if not required_files.issubset(existing_files):
            print(f"{TC.RED} ERROR: {TC.RESET} incorrect file set")
            print(f"{required_files=}")
            print(f"{existing_files=}")
            return None
        path = self.data_dir / "spectr_A.csv"
        df_A = pd.read_csv(path, sep="\t",
                       index_col=0
                       )
        path = self.data_dir / "spectr_B.csv"
        df_B = pd.read_csv(path, sep="\t",
                       index_col=0
                       )
        path = self.data_dir / "wavelengths_map.csv"
        wln_map = 

