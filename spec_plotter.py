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

class SpecPlotter():
    def __init__(self):
        self.data_dir = None
        self.fpath = None

    def read_spec_file(self, fpath):
        if not fpath:
            fpath = fu.select_file(self.data_dir,)
        if fpath:
            self.data_dir = fpath.parent 
            self.fpath = fpath
            df = pd.read_csv(
                fpath, sep="\t", header=1, 
                names=["wavelength1", "intensity1",
                        "wavelength2", "intensity2"],
                dtype={"wavelength1": float, "intensity1": float,
                        "wavelength2": float, "intensity2": float},
                                )
        else:
            print(f"{TC.RED} ERROR: {TC.RESET} file not selected")
            return
        return df   


    


