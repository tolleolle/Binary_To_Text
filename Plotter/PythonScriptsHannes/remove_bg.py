
import tkinter as tk
from tkinter import filedialog
import os


# ==========================================
# Dateien auswählen
# ==========================================

root = tk.Tk()
root.withdraw()

dateien = filedialog.askopenfilenames(
    title="Wähle Messdatei und BG-Datei aus",
    filetypes=[("Textdateien", "*.txt")]
)

if len(dateien) != 2:
    print("Bitte genau zwei TXT-Dateien auswählen.")
    exit()


# ==========================================
# BG-Datei erkennen
# ==========================================

bg_datei = None
mess_datei = None

for datei in dateien:

    if "bg" in os.path.basename(datei).lower():
        bg_datei = datei
    else:
        mess_datei = datei


if bg_datei is None or mess_datei is None:
    print("Fehler: Eine Datei muss 'bg' im Dateinamen enthalten.")
    exit()


print("Messdatei:")
print(mess_datei)

print("\nBG-Datei:")
print(bg_datei)


# ==========================================
# Datei einlesen
# ==========================================

def lese_datei(dateiname):

    daten = []

    with open(dateiname, "r", encoding="utf-8") as f:

        for zeile in f:

            zeile = zeile.strip()

            if not zeile:
                continue

            try:

                werte = zeile.split()

                if len(werte) < 4:
                    continue

                wl1 = float(werte[0])
                int1 = float(werte[1])
                wl2 = float(werte[2])
                int2 = float(werte[3])

                daten.append(
                    (wl1, int1, wl2, int2)
                )

            except ValueError:
                continue

    return daten


# Dateien einlesen
messung = lese_datei(mess_datei)
background = lese_datei(bg_datei)


# ==========================================
# Prüfen
# ==========================================

if len(messung) != len(background):

    print("\nFEHLER:")
    print("Die beiden Dateien haben unterschiedlich")
    print("viele Messpunkte.")

    print("Messdatei:", len(messung))
    print("BG-Datei:", len(background))

    exit()


# ==========================================
# Background abziehen
# ==========================================

ergebnis = []

for mess, bg in zip(messung, background):

    wl1_mess, int1_mess, wl2_mess, int2_mess = mess

    wl1_bg, int1_bg, wl2_bg, int2_bg = bg

    # Wellenlängen prüfen
    if wl1_mess != wl1_bg or wl2_mess != wl2_bg:

        print(
            "Warnung: Wellenlängen stimmen "
            "nicht überein!"
        )

    # Intensitäten subtrahieren
    int1_neu = int1_mess - int1_bg
    int2_neu = int2_mess - int2_bg

    ergebnis.append(
        (
            wl1_mess,
            int1_neu,
            wl2_mess,
            int2_neu
        )
    )


# ==========================================
# AUSGABEORDNER
# ==========================================

# Ordner, in dem die Messdatei liegt
hauptordner = os.path.abspath(
    os.path.dirname(mess_datei)
)

print("\nHauptordner:")
print(hauptordner)


# "without_bg_txt" darin erstellen
ausgabeordner = os.path.join(
    hauptordner,
    "without_bg_txt"
)

# Erstellen, falls nicht vorhanden
# Bereits vorhandenen Ordner einfach benutzen
os.makedirs(
    ausgabeordner,
    exist_ok=True
)

print("\nAusgabeordner:")
print(ausgabeordner)


# ==========================================
# AUSGABEDATEI
# ==========================================

dateiname = os.path.basename(mess_datei)

dateiname_ohne_endung = os.path.splitext(
    dateiname
)[0]

ausgabe_datei = os.path.join(
    ausgabeordner,
    dateiname_ohne_endung + "_BG_abgezogen.txt"
)


# ==========================================
# SPEICHERN
# ==========================================

with open(
    ausgabe_datei,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "Wellenlänge 1\t"
        "Intensität 1\t"
        "Wellenlänge 2\t"
        "Intensität 2\n"
    )

    for wl1, int1, wl2, int2 in ergebnis:

        f.write(
            f"{wl1}\t"
            f"{int1}\t"
            f"{wl2}\t"
            f"{int2}\n"
        )


# ==========================================
# FERTIG
# ==========================================

print("\n==============================")
print("Background erfolgreich abgezogen!")
print("==============================")

print("\nDatei gespeichert unter:")
print(ausgabe_datei)
