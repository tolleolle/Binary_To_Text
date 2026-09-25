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

class SpecPlotter():
    def __init__(self):
        self.data_dir = None
        self.fpath = None
        self.fig = None
        self.ax = None

    def read_spec_file(self, fpath=None):
        if not fpath:
            fpath = fu.select_file(self.data_dir,)
            print(f"{TC.BLUE} {fpath} {TC.RESET}")
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


    def make_fig(self, figsize=(20, 5), fontsize=25, dpi=100):
        styler = PlotStyler()
        styler.set_plt_font_style(size=fontsize, profile='default')
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        styler.set_scale_steps(ax)
    
        ax.minorticks_on()
        ax.tick_params(which="major", length=8, width=1.5, direction="out")
        ax.tick_params(which="minor", length=4, width=1.0, direction="out")
        for spine in ax.spines.values():
                spine.set_linewidth(1.5)
    
        ax.set_xlabel("wavelength [nm]") 
        ax.set_ylabel("intensity [counts/s]") 
        fig.tight_layout()

        self.fig = fig
        self.ax = ax

        return self


