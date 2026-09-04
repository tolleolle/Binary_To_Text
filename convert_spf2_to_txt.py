"""
Skript zur Konvertierung von Thorlabs .spf2-Dateien in .txt-Dateien
unter Verwendung von pathlib.

Gedacht für Spektren des Thorlabs-Spektrometers CCS100/M.
"""
import struct
from pathlib import Path

import numpy as np


HEADER_OFFSET = 524       # Byte-Position der Messpunktanzahl im Header
HEADER_FIELD_SIZE = 4     # Anzahl ist ein 32-Bit-Integer (4 Bytes)
VALUES_PER_POINT = 2      # pro Messpunkt: Wellenlänge + Intensität
BYTES_PER_VALUE = 4       # jeder Wert ist ein 32-Bit-Float (4 Bytes)
BYTES_PER_POINT = VALUES_PER_POINT * BYTES_PER_VALUE


def convert_spf2_to_txt(filepath: Path) -> bool:
   
    #Ermittelt die Dateigröße und speichert diese
    file_size = filepath.stat().st_size 
    #Ermittelt die minimale Dateigröße, die für eine Konvertierung erforderlich ist
    min_size = HEADER_OFFSET + HEADER_FIELD_SIZE

   #Überprüft, ob die Datei groß genug ist, um konvertiert zu werden
    if file_size < min_size:
        print(f"Übersprungen (Datei zu klein): {filepath.name}")
        return False

    try:
        # Öffnet die Datei im Binärmodus und liest die Messpunktanzahl aus dem Header.
        with open(filepath, "rb") as f:
            # Die Anzahl der Messpunkte steht ab Byte 524 im Header.
            f.seek(HEADER_OFFSET)
            #liest die 4 Bytes
            length_bytes = f.read(HEADER_FIELD_SIZE)
            #Interpretiert die Bytes als Zahl
            length = struct.unpack("<I", length_bytes)[0]
            # Berechnet die Anzahl der Bytes, die für die Messdaten benötigt werden.
            offset = length * BYTES_PER_POINT
             #Überprüft, damit kein Fehler auftritt
            if length == 0 or offset > file_size:
                print(f"Übersprungen (unplausibler Header): {filepath.name}")
                return False
            #Springt zum Anfang der Messdaten und liest sie ein.
            f.seek(-offset, 2)
            #liest die Messdaten
            raw_data = f.read(offset)

        # Binärdaten in ein NumPy-Array umwandeln.(Fließkommazahlen)
        data = np.frombuffer(raw_data, dtype="<f4")
       #Bringt die Daten in eine Tabellenform
        data_cols = data.reshape((VALUES_PER_POINT, length)).T
    #Fängt die Fehler beim Einlesen ab
    except (OSError, struct.error, ValueError) as error:
        print(f"Fehler beim Einlesen von {filepath.name}: {error}")
        return False

    # Ersetzt die Dateiendung .spf2 durch .txt für die Ausgabedatei.
    out_path = filepath.with_suffix(".txt")
    try:
        # Speichert die Daten als Tab-getrennte Textdatei ab.
        np.savetxt(
            out_path,
            data_cols,
            delimiter="\t",
            header="Wellenlänge (nm)\tIntensität (Counts)",
            #Entfernt das Hash-Zeichen, das normalerweise am Anfang des Headers steht.
            comments="",
            #Speichert Umlaute korrekt ab
            encoding="utf-8",
        )
    except OSError as error:
        print(f"Fehler beim Schreiben von {out_path.name}: {error}")
        return False

    print(f"Erfolgreich konvertiert: {out_path.name}")
    return True


def main() -> None:
    """
    Sucht alle .spf2-Dateien im Verzeichnis dieses Skripts und
    konvertiert sie. Ein Fehler bei einer einzelnen Datei bricht die
    Verarbeitung der übrigen Dateien nicht ab.
    """
    # Bestimme das Verzeichnis, in dem dieses Skript liegt.
    script_dir = Path(__file__).resolve().parent
    # pathlib hat eine eigene .glob()-Funktion direkt eingebaut.
    files = sorted(script_dir.glob("*.spf2"))

    if not files:
        print(f"Keine .spf2-Dateien im Ordner gefunden:\n{script_dir}")
        return

    results = [convert_spf2_to_txt(file) for file in files]
    print(f"\n{sum(results)} von {len(files)} Datei(en) erfolgreich "
          f"konvertiert.")


if __name__ == "__main__":
    main()
