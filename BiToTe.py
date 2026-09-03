#!/usr/bin/env python3
"""
Thorlabs CCS – Binary -> TXT Converter

Dieses Skript wandelt eine rohe Binärdatei (.bin/.dat) in eine
lesbare TXT-Datei um.

WICHTIG:
Das exakte Binärformat der CCS-Messdaten ist ohne einen Beispiel-Datenblock
nicht sicher bekannt. Deshalb sind die wichtigsten Einstellungen oben
konfigurierbar.

Standard:
- 2 Bytes pro Messwert
- Little Endian
- unsigned 16-bit integer
- kein Header
- ein Messwert pro Zeile

Aufruf in VS Code:
    python ccs_binary_to_txt.py messung.bin

oder:
    python ccs_binary_to_txt.py messung.bin messung.txt

Weitere Optionen:
    python ccs_binary_to_txt.py messung.bin --signed
    python ccs_binary_to_txt.py messung.bin --big-endian
    python ccs_binary_to_txt.py messung.bin --bytes-per-value 4
    python ccs_binary_to_txt.py messung.bin --skip-bytes 16
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys


def decode_values(
    data: bytes,
    bytes_per_value: int = 2,
    signed: bool = False,
    little_endian: bool = True,
    skip_bytes: int = 0,
) -> list[int]:
    """Dekodiert die Binärdaten in Integer-Messwerte."""

    if skip_bytes < 0:
        raise ValueError("skip_bytes darf nicht negativ sein.")

    if bytes_per_value not in (1, 2, 4, 8):
        raise ValueError("bytes_per_value muss 1, 2, 4 oder 8 sein.")

    data = data[skip_bytes:]

    # Nur vollständige Werte verwenden.
    remainder = len(data) % bytes_per_value
    if remainder:
        print(
            f"Warnung: {remainder} Byte am Ende werden ignoriert, "
            f"weil kein vollständiger Messwert daraus gebildet werden kann."
        )
        data = data[:-remainder]

    byte_order = "<" if little_endian else ">"

    format_char = {
        (1, False): "B",
        (1, True): "b",
        (2, False): "H",
        (2, True): "h",
        (4, False): "I",
        (4, True): "i",
        (8, False): "Q",
        (8, True): "q",
    }[(bytes_per_value, signed)]

    fmt = f"{byte_order}{format_char}"

    return [
        value[0]
        for value in struct.iter_unpack(fmt, data)
    ]


def write_txt(
    output_file: Path,
    values: list[int],
    input_file: Path,
    bytes_per_value: int,
    signed: bool,
    little_endian: bool,
    skip_bytes: int,
) -> None:
    """Schreibt die Messwerte als TXT-Datei."""

    with output_file.open("w", encoding="utf-8") as f:
        f.write("# Thorlabs CCS Binary Data\n")
        f.write(f"# Quelle: {input_file.name}\n")
        f.write(f"# Anzahl Messwerte: {len(values)}\n")
        f.write(f"# Bytes pro Messwert: {bytes_per_value}\n")
        f.write(f"# Signed: {signed}\n")
        f.write(
            f"# Byte-Reihenfolge: "
            f"{'Little Endian' if little_endian else 'Big Endian'}\n"
        )
        f.write(f"# Übersprungene Bytes: {skip_bytes}\n")
        f.write("#\n")
        f.write("# Index\tIntensitaet\n")

        for index, value in enumerate(values):
            f.write(f"{index}\t{value}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Thorlabs-CCS-Binärdaten in eine lesbare TXT-Datei umwandeln."
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Eingabe-Binärdatei (.bin, .dat, ...)",
    )

    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Ausgabe-TXT. Wenn nicht angegeben, wird automatisch eine erzeugt.",
    )

    parser.add_argument(
        "--bytes-per-value",
        type=int,
        choices=[1, 2, 4, 8],
        default=2,
        help="Anzahl Bytes pro Messwert (Standard: 2)",
    )

    parser.add_argument(
        "--signed",
        action="store_true",
        help="Messwerte als signed Integer interpretieren.",
    )

    parser.add_argument(
        "--big-endian",
        action="store_true",
        help="Big Endian statt Little Endian verwenden.",
    )

    parser.add_argument(
        "--skip-bytes",
        type=int,
        default=0,
        help="Anzahl Bytes am Dateianfang überspringen (Standard: 0).",
    )

    args = parser.parse_args()

    input_file = args.input

    if not input_file.exists():
        print(f"FEHLER: Datei nicht gefunden: {input_file}")
        sys.exit(1)

    if args.output is None:
        output_file = input_file.with_suffix(".txt")
    else:
        output_file = args.output

    try:
        data = input_file.read_bytes()

        print("==========================================")
        print(" Thorlabs CCS Binary -> TXT")
        print("==========================================")
        print(f"Eingabedatei : {input_file}")
        print(f"Dateigröße   : {len(data)} Bytes")
        print(f"Bytes/Wert   : {args.bytes_per_value}")
        print(
            f"Byte-Reihenfolge: "
            f"{'Big Endian' if args.big_endian else 'Little Endian'}"
        )
        print(f"Signed       : {args.signed}")
        print(f"Skip Bytes   : {args.skip_bytes}")

        # Die ersten Bytes anzeigen. Das ist später sehr hilfreich,
        # falls das CCS-Format angepasst werden muss.
        preview_length = min(32, len(data))
        print("\nErste Bytes (HEX):")
        print(data[:preview_length].hex(" "))

        values = decode_values(
            data=data,
            bytes_per_value=args.bytes_per_value,
            signed=args.signed,
            little_endian=not args.big_endian,
            skip_bytes=args.skip_bytes,
        )

        write_txt(
            output_file=output_file,
            values=values,
            input_file=input_file,
            bytes_per_value=args.bytes_per_value,
            signed=args.signed,
            little_endian=not args.big_endian,
            skip_bytes=args.skip_bytes,
        )

        print(f"\nAnzahl Werte: {len(values)}")
        print(f"Ausgabedatei: {output_file}")

        print("\nErste 10 dekodierte Werte:")
        for i, value in enumerate(values[:10]):
            print(f"  {i:5d}: {value}")

        print("\nFertig.")

    except Exception as exc:
        print(f"\nFEHLER: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
