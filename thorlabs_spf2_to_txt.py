# THORLabsSpectrometer\Thorlabs_spf2_to_txt.py
"""
Skript zur Konvertierung von Thorlabs .spf2-Dateien in .txt-Dateien
unter Verwendung von pathlib.

Gedacht für Spektren des Thorlabs-Spektrometers CCS100/M.
"""

import struct
from pathlib import Path
import os
import sys
import subprocess

import numpy as np
import pandas as pd
current_file = Path(__file__).resolve()
project_root = current_file.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.terminal_styler import TerminalColours
tc=TerminalColours()



HEADER_OFFSET = 524        ## Byte-Position der Messpunktanzahl im Header, vorher Informationen zum Gerätentypus
HEADER_FIELD_SIZE = 4      ## Anzahl ist ein 32-Bit-Integer (4 Bytes)
VALUES_PER_POINT = 4       ## pro Messpunkt: Wellenlänge 1 + Intensität 1 + Wellenlänge 2 + Intensität 2
BYTES_PER_VALUE = 4        ## jeder Wert ist ein 32-Bit-Float (4 Bytes)
wavelength_min = 100
wavelength_max = 950


def find_wavelength_start(values: np.ndarray, length: int, start_from: int = 0) -> int:

    is_increasing = np.diff(values) > 0
    needed_length = length - 1 ##Die Anzahl der Vergleiche ist länge minus eins
    counter = 0  ## Zählt die anzahl der steigenden werte

    for i in range(start_from, len(is_increasing)):
        if not is_increasing[i]:
            counter = 0   ## Wenn nicht mehr steigend wird der Zähler wieder auf null gesetzt
            continue

        counter = counter + 1 ## Wenn steigend wird der zähler um 1 erhöht
        if counter != needed_length: ## wenn noch nicht genug steigende werte gefunden wurden wird weitergesucht
            continue

        start = i - needed_length + 1 ##Starpunkt der Wellenlängen in der Datei
        while not (wavelength_min < values[start] < wavelength_max):
            start += 1
        return start

    raise ValueError(
        "Keine zusammenhängende aufsteigenden werte gefunden"
    )


def thorlabs_spf2_to_txt(filepath: Path) -> bool:

    # Ermittelt die Dateigröße und speichert diese
    file_size = filepath.stat().st_size
    # Ermittelt die minimale Dateigröße, die für eine Konvertierung erforderlich ist
    min_size = HEADER_OFFSET + HEADER_FIELD_SIZE

    # Überprüft, ob die Datei groß genug ist, um konvertiert zu werden
    if file_size < min_size:
        print(f"Übersprungen (Datei zu klein): {filepath.name}")
        return False

    try:
        with open(filepath, "rb") as f:
            ## Die Anzahl der Messpunkte steht ab Byte 524 im Header.
            f.seek(HEADER_OFFSET)
            length_bytes = f.read(HEADER_FIELD_SIZE)
            ## Interpretiert die Bytes als Zahl definiert die länge der datei
            length = struct.unpack("<I", length_bytes)[0]
            ## Größe, die die vier Messreihen zusammen mindestens belegen
            data_size = length * VALUES_PER_POINT * BYTES_PER_VALUE

            ## Überprüft ob die länge oder datei größe sinvoll ist
            if length == 0 or data_size > file_size:
                print(f"Übersprungen (unplausibler Header): {filepath.name}")
                return False
            f.seek(0)
            raw_data = f.read()


        values = np.frombuffer(raw_data, dtype="<f4") ## Binärdaten werden als float32 interpretiert

        ## Erstes Paar: Wellenlänge 1 + Intensität 1, diese liegen direkt hintereinander)
        start_1 = find_wavelength_start(values, length)
        wl1 = values[start_1: start_1 + length]
        int1 = values[start_1 + length: start_1 + 2 * length]

        ## Zweites Paar: Wellenlänge 2 + Intensität 2, weiter hinten in der Datei
        start_2 = find_wavelength_start(values, length, start_from=start_1 + 2 * length)
        wl2 = values[start_2: start_2 + length]
        int2 = values[start_2 + length: start_2 + 2 * length]

        data_cols = pd.DataFrame(
            {
                "Wellenlänge 1": wl1,
                "Intensität 1": int1,
                "Wellenlänge 2": wl2,
                "Intensität 2": int2,
            }
        )

    # Fängt die Fehler beim Einlesen ab
    except (OSError, struct.error, ValueError) as error:
        print(f"Fehler beim Einlesen von {filepath.name}: {error}")
        return False

    # Ersetzt die Dateiendung .spf2 durch .txt für die Ausgabedatei.
    ## out_path = filepath.with_suffix(".txt")
    out_path = filepath.parent / "txt" / filepath.with_suffix(".txt").name
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Speichert die Daten als Tab-getrennte Textdatei ab.
        data_cols.to_csv(
            out_path,
            sep="\t",
            index=False,
            # Speichert Umlaute korrekt ab
            encoding="utf-8",
            float_format="%.9e",
        )
    except OSError as error:
        print(f"{tc.RED}Fehler beim Schreiben von {tc.RESET} {out_path.name}: {tc.RED}{error}{tc.RESET}")
        return False

    print(f"{tc.GREEN}Erfolgreich konvertiert: {tc.RESET} {out_path.name}")
    return True


def convert_folder(folder_path: Path) -> None:
    """
    Konvertiert alle .spf2-Dateien in einem Ordner in .txt-Dateien.
    """
    if not folder_path.is_dir():
        print(f"{tc.RED}Fehler: {tc.RESET} {folder_path} ist kein gültiger Ordner.")
        return

    spf2_files = list(folder_path.glob("*.spf2"))
    if not spf2_files:
        print(f"{tc.YELLOW}Keine .spf2-Dateien im Ordner gefunden: {tc.RESET} {folder_path}")
        return

    for spf2_file in spf2_files:
        thorlabs_spf2_to_txt(spf2_file)
        print(f"{tc.BLUE}Konvertiere Datei: {tc.RESET} {spf2_file.name}")


if __name__ == "__main__":
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
    print(f"Projektverzeichnis: {project_root}")
    f_path = project_root / "DATA" / "05a2p0kW_10s.spf2"
    print(f"Test Datei: {f_path}")
    print(f"{type(f_path)=}, {f_path.name=}, {f_path.suffix=}, {f_path.stem=}")
    thorlabs_spf2_to_txt(f_path)


    # f_path = Path(file)
    # print(f"Konvertiere Datei: {f_path}")
    # thorlabs_spf2_to_txt(f_path)
