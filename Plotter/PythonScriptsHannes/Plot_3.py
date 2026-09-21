"""Interaktiver Spektrum-Viewer für Thorlabs-CCS100/M-Messdaten.

Liest eine per Tabulator getrennte Textdatei mit einer Kopfzeile ein, die
abwechselnd Wellenlängen- und Intensitätsspalten enthält und zeigt alle 
Serien in einem interaktiven Matplotlib-Fenster an (mit Wellenlänge auf der X-Achse).

Aufruf:
    python spektrum_viewer.py [pfad_zur_messdatei.txt]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.widgets import Button, CheckButtons, TextBox
from scipy.signal import peak_widths
import tkinter as tk
from tkinter import filedialog


# ---------------------------------------------------------------------------
# Konfiguration & Dateiauswahl
# ---------------------------------------------------------------------------

STANDARD_DATEI = r"C:\Users\hanne\Desktop\Prakikum Greifswald\Projekte für Andrei\Plotter\05a2p0kW_10s.txt"


def datei_auswaehlen_dialog(initial_dir: Path | str = "") -> str | None:
    """Öffnet einen stabilen Datei-Explorer unter Windows."""
    root = None
    try:
        root = tk.Tk()
        root.attributes("-topmost", True)
        root.withdraw()
        
        ausgewaehlter_pfad = filedialog.askopenfilename(
            title="Wähle eine Textdatei aus",
            initialdir=str(initial_dir) if initial_dir else "",
            filetypes=[("Textdateien (*.txt)", "*.txt"), ("Alle Dateien (*.*)", "*.*")]
        )
        return ausgewaehlter_pfad if ausgewaehlter_pfad else None
    except Exception as e:
        print(f"Dateiauswahl übersprungen (Fehler: {e}).")
        return None
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


# Initiale Dateiauswahl beim Start
initialer_pfad_str = datei_auswaehlen_dialog(Path(STANDARD_DATEI).parent)
if initialer_pfad_str:
    STANDARD_DATEI = initialer_pfad_str
    print(f"Neue Datei ausgewählt: {STANDARD_DATEI}")
else:
    print(f"Auswahl abgebrochen. Es wird die Standarddatei verwendet: {STANDARD_DATEI}")

# Farbreihenfolge für die einzelnen Messserien
FARBPALETTE = plt.rcParams["axes.prop_cycle"].by_key()["color"]

# ---------------------------------------------------------------------------
# Feste Pixel-Zuordnung für Argon-Linien (Pixel, Wellenlänge in nm)
# ---------------------------------------------------------------------------
# Literaturwerte zur automatischen Spezies-Erkennung (Ar I / Ar II)
ARGON_LINIEN_NM: list[tuple[float, str]] = [
    (401.37, "Ar II"), (404.44, "Ar I"), (407.20, "Ar II"), (410.39, "Ar II"),
    (415.86, "Ar I"), (416.41, "Ar I"), (418.19, "Ar I"), (419.10, "Ar I"),
    (422.82, "Ar II"), (425.12, "Ar I"), (425.94, "Ar I"), (426.63, "Ar I"),
    (427.22, "Ar I"), (430.01, "Ar I"), (437.13, "Ar II"), (437.97, "Ar II"),
    (440.01, "Ar II"), (442.60, "Ar II"), (451.07, "Ar I"), (454.51, "Ar II"),
    (457.93, "Ar II"), (458.99, "Ar II"), (460.96, "Ar II"), (465.79, "Ar II"),
    (470.23, "Ar I"), (472.68, "Ar II"), (473.59, "Ar II"), (480.60, "Ar II"),
    (484.78, "Ar II"), (487.99, "Ar II"), (493.32, "Ar II"), (496.51, "Ar II"),
    (500.94, "Ar II"), (506.20, "Ar II"), (514.53, "Ar II"), (516.23, "Ar I"),
    (518.78, "Ar I"), (545.17, "Ar I"), (549.59, "Ar I"), (555.87, "Ar I"),
    (560.67, "Ar I"), (565.07, "Ar I"), (573.95, "Ar I"), (588.86, "Ar I"),
    (591.21, "Ar I"), (603.21, "Ar I"), (604.32, "Ar I"), (605.94, "Ar I"),
    (617.31, "Ar I"), (621.59, "Ar I"), (629.69, "Ar I"), (636.96, "Ar I"),
    (638.47, "Ar I"), (664.37, "Ar II"), (667.73, "Ar I"), (675.28, "Ar I"),
    (687.13, "Ar I"), (693.77, "Ar I"), (696.54, "Ar I"), (703.03, "Ar I"),
    (706.72, "Ar I"), (714.71, "Ar I"), (720.70, "Ar I"), (727.29, "Ar I"),
    (735.33, "Ar I"), (737.21, "Ar I"), (738.40, "Ar I")
]

# Feste Kopplung der Peaks an die Pixelanzahl (Pixel -> Literatur-Wellenlänge)
FESTE_PIXEL_PEAKS: list[tuple[int, float]] = [
    (733,  401.37),
    (760,  404.44),
    (785,  407.20),
    (813,  410.39),
    (862,  415.86),
    (867,  416.41),
    (883,  418.19),
    (891,  419.10),
    (924,  422.82),
    (945,  425.12),
    (952,  425.94),
    (958,  426.63),
    (963,  427.22),
    (988,  430.01),
    (1050, 437.13),
    (1057, 437.97),
    (1076, 440.01),
    (1098, 442.60),
    (1173, 451.07),
    (1203, 454.51),
    (1233, 457.93),
    (1243, 458.99),
    (1259, 460.96),
    (1301, 465.79),
    (1340, 470.23),
    (1361, 472.68),
    (1369, 473.59),
    (1431, 480.60),
    (1467, 484.78),
    (1495, 487.99),
    (1540, 493.32),
    (1568, 496.51),
    (1606, 500.94),
    (1652, 506.20),
    (1724, 514.53),
    (1738, 516.23),
    (1760, 518.78),
    (1986, 545.17),
    (2023, 549.59),
    (2077, 555.87),
    (2118, 560.67),
    (2156, 565.07),
    (2231, 573.95),
    (2357, 588.86),
    (2377, 591.21),
    (2479, 603.21),
    (2488, 604.32),
    (2502, 605.94),
    (2597, 617.31),
    (2633, 621.59),
    (2702, 629.69),
    (2763, 636.96),
    (2776, 638.47),
    (2993, 664.37),
    (3022, 667.73),
    (3084, 675.28),
    (3184, 687.13),
    (3239, 693.77),
    (3263, 696.54),
    (3316, 703.03),
    (3347, 706.72),
    (3414, 714.71),
    (3464, 720.70),
    (3520, 727.29),
    (3586, 735.33),
    (3602, 737.21),
    (3612, 738.40)
]

LITERATUR_TOLERANZ_NM = 0.5

def finde_literaturwert(
    wellenlaenge: float,
    katalog: list[tuple[float, str]] = ARGON_LINIEN_NM,
    max_abstand: float = LITERATUR_TOLERANZ_NM,
) -> tuple[float, str] | None:
    abstaende = [abs(wellenlaenge - lit_wert) for lit_wert, _ in katalog]
    index = int(np.argmin(abstaende))

    if abstaende[index] > max_abstand:
        return None
    return katalog[index]


def lade_spektren(pfad: Path) -> dict[str, dict[str, np.ndarray]]:
    rohdaten = np.loadtxt(pfad, delimiter="\t", skiprows=1)
    if rohdaten.ndim == 1:
        rohdaten = rohdaten.reshape(1, -1)

    anzahl_spalten = rohdaten.shape[1]
    if anzahl_spalten % 2 != 0:
        raise ValueError(
            f"Unerwartete Spaltenzahl ({anzahl_spalten}) in '{pfad.name}': "
            "es werden Paare aus Wellenlänge und Intensität erwartet."
        )

    serien: dict[str, dict[str, np.ndarray]] = {}
    for i in range(anzahl_spalten // 2):
        if anzahl_spalten // 2 == 1:
            name = pfad.stem
        else:
            name = f"{pfad.stem} (Spalte {i + 1})"
            
        serien[name] = {
            "wellenlaenge": rohdaten[:, 2 * i],
            "intensitaet": rohdaten[:, 2 * i + 1],
            "pixel": np.arange(rohdaten.shape[0], dtype=float),
        }
    return serien


class SpektrumViewer:
    """Interaktives Matplotlib-Fenster für ein oder mehrere Spektren."""

    def __init__(self, serien: dict[str, dict[str, np.ndarray]], titel: str):
        self.serien = serien
        self.farben = {
            name: FARBPALETTE[i % len(FARBPALETTE)] for i, name in enumerate(serien)
        }

        self.sichtbar: dict[str, bool] = {name: True for name in serien}
        self.sichtbar["Peaks"] = True

        self.linien: dict[str, Line2D] = {}
        self.peak_grafik: dict[str, dict[str, list]] = {}
        self.ausgewaehlte_peaks: dict[str, list[dict[str, float]]] = {name: [] for name in serien}
        self.label_map: dict[str, str] = {}
        self.kalibrier_fig = None
        self._temp_matched_peaks = []
        self.check = None

        self._erstelle_fenster(titel)
        self._zeichne_kurven()
        self._erstelle_steuerelemente()
        self._skalierung_aktualisieren()
        self._aktiviere_klick_auswahl()
        self._aktiviere_koordinaten_anzeige()

    def _erstelle_fenster(self, titel: str) -> None:
        self.fig, self.ax = plt.subplots(figsize=(13, 6))
        
        if self.fig.canvas.manager is not None:
            self.fig.canvas.manager.set_window_title(f"Spektrum-Viewer - {titel}")
            try:
                window = self.fig.canvas.manager.window
                if hasattr(window, "state"):
                    window.state("zoomed")
            except Exception:
                pass
            
        self.fig.subplots_adjust(right=0.72, bottom=0.15)

        ax_reset_button = self.fig.add_axes([0.74, 0.03, 0.22, 0.035])
        self.reset_button = Button(ax_reset_button, "Peaks zurücksetzen")
        self.reset_button.on_clicked(self._peaks_zuruecksetzen)

        ax_auto_button = self.fig.add_axes([0.74, 0.072, 0.22, 0.035])
        self.auto_button = Button(ax_auto_button, "Peaks automatisch finden")
        self.auto_button.on_clicked(self._peaks_automatisch_finden)

        ax_button = self.fig.add_axes([0.74, 0.114, 0.22, 0.035])
        self.kalibrier_button = Button(ax_button, "Peaks bestätigen")
        self.kalibrier_button.on_clicked(self._kalibrierung_starten)

        ax_add_button = self.fig.add_axes([0.74, 0.156, 0.22, 0.035])
        self.add_button = Button(ax_add_button, "Datei hinzufügen")
        self.add_button.on_clicked(self._datei_hinzuufuegen)

        self.ax.set_xlabel("Wellenlänge [nm]")
        self.ax.set_ylabel("Intensität [a.u.]")
        self.ax.set_title("Wellenlängenspektrum")
        self.ax.grid(True, alpha=0.3)

    def _zeichne_kurven(self) -> None:
        for name, daten in self.serien.items():
            (linie,) = self.ax.plot(
                daten["wellenlaenge"], 
                daten["intensitaet"],
                label=name,
                color=self.farben[name],
                linewidth=0.9,
            )
            self.linien[name] = linie

    def _skalierung_aktualisieren(self) -> None:
        sichtbare_serien = [name for name, sichtbar in self.sichtbar.items() if sichtbar and name in self.serien]
        if not sichtbare_serien:
            return

        y_min_werte, y_max_werte = [], []
        x_min_werte, x_max_werte = [], []

        for name in sichtbare_serien:
            daten = self.serien[name]
            y_min_werte.append(np.min(daten["intensitaet"]))
            y_max_werte.append(np.max(daten["intensitaet"]))
            x_min_werte.append(np.min(daten["wellenlaenge"]))
            x_max_werte.append(np.max(daten["wellenlaenge"]))

        ges_ymin = min(y_min_werte)
        ges_ymax = max(y_max_werte)
        y_span = ges_ymax - ges_ymin
        y_puffer = (y_span * 0.05) if y_span > 0 else 1.0

        ges_xmin = min(x_min_werte)
        ges_xmax = max(x_max_werte)
        x_span = ges_xmax - ges_xmin
        x_puffer = (x_span * 0.02) if x_span > 0 else 1.0

        self.ax.set_ylim(ges_ymin - y_puffer, ges_ymax + y_puffer)
        self.ax.set_xlim(ges_xmin - x_puffer, ges_xmax + x_puffer)

    def _erstelle_steuerelemente(self) -> None:
        if hasattr(self, "ax_check") and self.ax_check in self.fig.axes:
            self.ax_check.remove()

        self.label_map.clear()
        labels_kurz = []
        serien_farben = []

        for name in self.serien.keys():
            if len(name) > 19:
                kurz = name[:16] + "..."
            else:
                kurz = name
                
            basis_kurz = kurz
            zaehler = 1
            while kurz in self.label_map:
                kurz = f"{basis_kurz[:13]}..({zaehler})"
                zaehler += 1

            self.label_map[kurz] = name
            labels_kurz.append(kurz)
            serien_farben.append(self.farben[name])

        aktive = [self.sichtbar.get(name, True) for name in self.serien.keys()]

        height = min(0.60, max(0.10, 0.035 * len(labels_kurz) + 0.02))
        self.ax_check = self.fig.add_axes([0.74, 0.205, 0.22, height])
        
        self.check = CheckButtons(
            ax=self.ax_check,
            labels=labels_kurz,
            actives=aktive
        )

        for text_label, farbe in zip(self.check.labels, serien_farben):
            text_label.set_color(farbe)
            text_label.set_fontsize(8)

        def bei_klick_checkbox(label_kurz: str) -> None:
            echter_name = self.label_map[label_kurz]
            self.sichtbar[echter_name] = not self.sichtbar.get(echter_name, True)
            self._wende_sichtbarkeit_an()
            self._skalierung_aktualisieren()
            self.fig.canvas.draw_idle()

        self.check.on_clicked(bei_klick_checkbox)

    def _datei_hinzuufuegen(self, ereignis=None) -> None:
        letzter_pfad = Path(STANDARD_DATEI).parent
        neuer_pfad_str = datei_auswaehlen_dialog(letzter_pfad)
        if not neuer_pfad_str:
            return
        
        neuer_pfad = Path(neuer_pfad_str)
        if not neuer_pfad.exists():
            print(f"Fehler: Datei '{neuer_pfad}' nicht gefunden.")
            return

        try:
            neue_serien = lade_spektren(neuer_pfad)
        except Exception as e:
            print(f"Fehler beim Laden der Datei: {e}")
            return

        gesamt_anzahl_vorher = len(self.serien)
        for i, (name, daten) in enumerate(neue_serien.items()):
            basis_name = name
            zaehler = 1
            while name in self.serien:
                name = f"{basis_name} ({zaehler})"
                zaehler += 1
            
            self.serien[name] = daten
            farb_index = gesamt_anzahl_vorher + i
            self.farben[name] = FARBPALETTE[farb_index % len(FARBPALETTE)]
            self.sichtbar[name] = True
            self.ausgewaehlte_peaks[name] = []

            (linie,) = self.ax.plot(
                daten["wellenlaenge"],
                daten["intensitaet"],
                label=name,
                color=self.farben[name],
                linewidth=0.9,
            )
            self.linien[name] = linie

        self._erstelle_steuerelemente()
        self._skalierung_aktualisieren()
        self.fig.canvas.draw_idle()
        print(f"Datei erfolgreich hinzugefügt: {neuer_pfad.name}")

    def _entferne_alte_peak_grafik(self) -> None:
        for elemente in self.peak_grafik.values():
            alle_alten = elemente["marker"] + elemente["beschriftungen"]
            for element in alle_alten:
                try:
                    element.remove()
                except Exception:
                    pass

    def _zeichne_peaks_einer_serie(
        self, name: str, peaks: list[dict[str, float]], farbe: str
    ) -> dict[str, list]:
        marker, beschriftungen = [], []

        for i, peak in enumerate(peaks):
            x_pos = peak.get("mess_wellenlaenge", peak["wellenlaenge"])

            # Farbzuweisung gemäß Anforderung: Ar I = rot, Ar II = blau
            peak_farbe = farbe
            spezies = peak.get("spezies")
            if spezies == "Ar I":
                peak_farbe = "red"
            elif spezies == "Ar II":
                peak_farbe = "blue"

            (m,) = self.ax.plot(
                x_pos, 
                peak["intensitaet"],
                "^",
                color=peak_farbe,
                markersize=6,
                markeredgecolor="black",
                markeredgewidth=0.5,
            )

            if "spezies" in peak and "lit_wert" in peak:
                label_text = f"Px {int(peak['pixel'])} | [{peak['spezies']}] {x_pos:.2f} nm (lit: {peak['lit_wert']:.2f} nm)"
            else:
                label_text = f"Pixel {int(peak['pixel'])} | {x_pos:.2f} nm"

            text = self.ax.annotate(
                label_text,
                xy=(x_pos, peak["intensitaet"]),
                xytext=(0, 10),
                textcoords="offset points",
                rotation=90,
                fontsize=6,
                ha="center",
                va="bottom",
                color=peak_farbe,
            )

            marker.append(m)
            beschriftungen.append(text)

        return {"marker": marker, "beschriftungen": beschriftungen}

    def _peaks_zuruecksetzen(self, ereignis=None) -> None:
        for name in self.ausgewaehlte_peaks:
            self.ausgewaehlte_peaks[name].clear()
        
        self._aktualisiere_peak_anzeige()
        print("Alle Peaks wurden zurückgesetzt.")

    def _peaks_automatisch_finden(self, ereignis=None) -> None:
        """Platziert die Peaks exakt anhand der fest vorgegebenen Pixel-Wellenlängen-Liste.
        Berücksichtigt dabei nur Serien, die in der Checkbox aktiviert sind."""
        for name, daten in self.serien.items():
            if not self.sichtbar.get(name, True):
                self.ausgewaehlte_peaks[name] = []
                continue
            
            intensitaeten = daten["intensitaet"]
            wellenlaengen = daten["wellenlaenge"]
            pixel_array = daten["pixel"]
            max_pixel_idx = len(pixel_array) - 1
            
            self.ausgewaehlte_peaks[name] = []
            
            for pix, lit_wert in FESTE_PIXEL_PEAKS:
                if pix > max_pixel_idx:
                    continue
                
                idx = int(pix)
                wl_aktuell = wellenlaengen[idx]
                
                # Bestimme Spezies (Ar I / Ar II) aus dem Literaturkatalog
                treffer = finde_literaturwert(lit_wert)
                spezies = treffer[1] if treffer is not None else "Unbekannt"
                
                try:
                    _, hoehen, links_idx, rechts_idx = peak_widths(intensitaeten, [idx], rel_height=0.5)
                    alle_indizes = np.arange(len(pixel_array))
                    links_wl = np.interp(links_idx, alle_indizes, wellenlaengen)
                    rechts_wl = np.interp(rechts_idx, alle_indizes, wellenlaengen)
                    fwhm = rechts_wl[0] - links_wl[0]
                    halbmax = hoehen[0]
                    l_wl = links_wl[0]
                    r_wl = rechts_wl[0]
                except Exception:
                    fwhm = 0.0
                    halbmax = intensitaeten[idx] / 2
                    l_wl = wl_aktuell
                    r_wl = wl_aktuell

                peak_daten = {
                    "pixel": float(idx),
                    "wellenlaenge": lit_wert,
                    "mess_wellenlaenge": wl_aktuell,
                    "intensitaet": intensitaeten[idx],
                    "fwhm": fwhm,
                    "halbmax_hoehe": halbmax,
                    "links_wl": l_wl,
                    "rechts_wl": r_wl,
                    "spezies": spezies,
                    "lit_wert": lit_wert,
                }
                
                self.ausgewaehlte_peaks[name].append(peak_daten)
                
        self._aktualisiere_peak_anzeige()
        print("Feste Peak-Zuordnung über Pixelanzahl abgeschlossen (nur für aktive Serien).")

    def _wende_sichtbarkeit_an(self) -> None:
        for name, linie in self.linien.items():
            linie.set_visible(self.sichtbar.get(name, True))

        peaks_global_sichtbar = self.sichtbar.get("Peaks", True)
        for name, elemente in self.peak_grafik.items():
            peaks_sichtbar = self.sichtbar.get(name, True) and peaks_global_sichtbar

            for marker in elemente["marker"]:
                marker.set_visible(peaks_sichtbar)
            for element in elemente["beschriftungen"]:
                element.set_visible(peaks_sichtbar)

    def _aktiviere_klick_auswahl(self) -> None:
        def bei_klick(ereignis) -> None:
            if ereignis.inaxes != self.ax or ereignis.xdata is None or ereignis.button != 3:
                return

            if not self.sichtbar.get("Peaks", True):
                return

            sichtbare_serien = [name for name, sichtbar in self.sichtbar.items() if sichtbar and name in self.serien]
            if not sichtbare_serien:
                return

            ziel_serie = sichtbare_serien[0]
            daten = self.serien[ziel_serie]
            pixel_array = daten["pixel"]
            intensitaeten = daten["intensitaet"]
            wellenlaengen = daten["wellenlaenge"]
            
            klick_idx = (np.abs(wellenlaengen - ereignis.xdata)).argmin()
            
            fenster = 3
            start_idx = max(0, klick_idx - fenster)
            end_idx = min(len(wellenlaengen), klick_idx + fenster)
            
            lokaler_ausschnitt = intensitaeten[start_idx:end_idx]
            if len(lokaler_ausschnitt) == 0:
                return
            
            rel_max_idx = np.argmax(lokaler_ausschnitt)
            idx = start_idx + rel_max_idx

            _, hoehen, links_idx, rechts_idx = peak_widths(intensitaeten, [idx], rel_height=0.5)
            
            alle_indizes = np.arange(len(pixel_array))
            links_wl = np.interp(links_idx, alle_indizes, wellenlaengen)
            rechts_wl = np.interp(rechts_idx, alle_indizes, wellenlaengen)

            wl_aktuell = wellenlaengen[idx]
            
            treffer = finde_literaturwert(wl_aktuell)
            
            peak_daten = {
                "pixel": float(idx),
                "wellenlaenge": wl_aktuell,
                "mess_wellenlaenge": wl_aktuell,
                "intensitaet": intensitaeten[idx],
                "fwhm": rechts_wl[0] - links_wl[0],
                "halbmax_hoehe": hoehen[0],
                "links_wl": links_wl[0],
                "rechts_wl": rechts_wl[0],
            }
            if treffer is not None:
                lit_wert, spezies = treffer
                peak_daten["spezies"] = spezies
                peak_daten["lit_wert"] = lit_wert

            existiert_bereits = False
            for p in self.ausgewaehlte_peaks[ziel_serie]:
                if abs(p["pixel"] - peak_daten["pixel"]) < 2:
                    self.ausgewaehlte_peaks[ziel_serie].remove(p)
                    existiert_bereits = True
                    break
            
            if not existiert_bereits:
                self.ausgewaehlte_peaks[ziel_serie].append(peak_daten)

            self._aktualisiere_peak_anzeige()

        self.fig.canvas.mpl_connect("button_press_event", bei_klick)

    def _aktualisiere_peak_anzeige(self) -> None:
        self._entferne_alte_peak_grafik()

        self.peak_grafik = {}
        for name, peaks in self.ausgewaehlte_peaks.items():
            self.peak_grafik[name] = self._zeichne_peaks_einer_serie(name, peaks, farbe=self.farben[name])

        self._wende_sichtbarkeit_an()
        self.fig.canvas.draw_idle()

    def _kalibrierung_starten(self, ereignis=None) -> None:
        pixel = []
        wellenlaenge_lit = []
        serienname = []
        matched_peaks_info = []

        print("\n--- Zuordnung der Peaks zu den neuen Literaturwerten ---")
        for name, peaks in self.ausgewaehlte_peaks.items():
            for peak in peaks:
                if "lit_wert" not in peak:
                    treffer = finde_literaturwert(peak["wellenlaenge"])
                    if treffer is None:
                        continue
                    lit_wert, spezies = treffer
                    peak["spezies"] = spezies
                    peak["lit_wert"] = lit_wert
                else:
                    lit_wert = peak["lit_wert"]
                    spezies = peak["spezies"]

                print(
                    f"  {name}, Pixel {int(peak['pixel']):4d}: "
                    f"{peak['wellenlaenge']:.2f} nm  ->  {spezies} {lit_wert:.3f} nm "
                    f"(Δ = {lit_wert - peak['wellenlaenge']:+.2f} nm)"
                )

                pixel.append(float(peak["pixel"]))
                wellenlaenge_lit.append(lit_wert)
                serienname.append(name)
                matched_peaks_info.append((name, peak, spezies, lit_wert))

        if len(pixel) < 3:
            print(f"Abgebrochen: Nur {len(pixel)} zugeordnete(r) Peak(s) - für Grad 3 sind mindestens 4 nötig.")
            return

        pixel = np.asarray(pixel, dtype=float)
        wellenlaenge_lit = np.asarray(wellenlaenge_lit, dtype=float)
        serienname = np.asarray(serienname)

        unique_pixel, unique_idx = np.unique(pixel, return_index=True)
        pixel = unique_pixel
        wellenlaenge_lit = wellenlaenge_lit[unique_idx]
        serienname = serienname[unique_idx]

        if len(pixel) < 3:
            print("Abgebrochen: Zu wenige eindeutige Pixel.")
            return
            
        self._temp_matched_peaks = matched_peaks_info

        self.kalibrier_fig = plt.figure(figsize=(13, 8))
        if self.kalibrier_fig.canvas.manager is not None:
            self.kalibrier_fig.canvas.manager.set_window_title(
                "Wellenlängen-Kalibrierung – Polynom-Fit gegen Literaturwerte"
            )

        ax_fit = self.kalibrier_fig.add_axes([0.10, 0.42, 0.65, 0.48])
        ax_res = self.kalibrier_fig.add_axes([0.10, 0.15, 0.65, 0.20])
        
        ax_box = self.kalibrier_fig.add_axes([0.80, 0.65, 0.15, 0.08])
        self.text_box_grad = TextBox(ax_box, "Polynom-Grad eingeben\n(und Enter drücken):", initial="3")
        self.text_box_grad.label.set_fontsize(9)

        ax_btn = self.kalibrier_fig.add_axes([0.80, 0.45, 0.15, 0.08])
        self.kalibrier_bestaetig_btn = Button(ax_btn, "Peaks bestätigen")
        self.kalibrier_bestaetig_btn.on_clicked(self._kalibrierung_abschliessen)

        self.kalibrier_fig._ax_fit = ax_fit
        self.kalibrier_fig._ax_res = ax_res
        self.kalibrier_fig._pixel = pixel
        self.kalibrier_fig._wellenlaenge_lit = wellenlaenge_lit
        self.kalibrier_fig._serienname = serienname

        def aktualisiere_plot(text_grad):
            try:
                grad = int(text_grad)
            except ValueError:
                return
            
            ax_fit.clear()
            ax_res.clear()

            if len(pixel) <= grad:
                ax_fit.text(0.5, 0.5, f"Zu wenige Punkte für Grad {grad}!", ha="center", transform=ax_fit.transAxes)
                self.kalibrier_fig.canvas.draw_idle()
                return

            koeffizienten = np.polyfit(pixel, wellenlaenge_lit, grad)
            p_poly = np.poly1d(koeffizienten)

            x_fit = np.linspace(pixel.min(), pixel.max(), 500)
            y_fit = p_poly(x_fit)
            residual_nm = wellenlaenge_lit - p_poly(pixel)

            for name in self.serien:
                maske = serienname == name
                if np.any(maske):
                    ax_fit.plot(pixel[maske], wellenlaenge_lit[maske], "o", markersize=5, color=self.farben[name], label=name)
                    ax_res.plot(pixel[maske], residual_nm[maske], "o", markersize=5, color=self.farben[name])

            ax_fit.plot(x_fit, y_fit, "-", color="red", linewidth=1.5, label="Fit-Kurve")
            ax_fit.set_ylabel("Wellenlänge (nm)")
            ax_fit.set_title("Wellenlängen-Kalibrierung des Spektrometers")
            ax_fit.grid(True, alpha=0.3)
            ax_fit.legend(loc="upper left", fontsize=8)

            ax_res.axhline(0, linestyle="--", linewidth=1, color="black")
            ax_res.axhline(0.12, linestyle=":", color="orange", label="±1 Pixel Toleranz")
            ax_res.axhline(-0.12, linestyle=":", color="orange")
            ax_res.set_xlabel("Pixel")
            ax_res.set_ylabel("Residuem (nm)")
            ax_res.set_title("Abweichungen der Literaturwerte vom Fit")
            ax_res.grid(True, alpha=0.3)

            max_abw_nm = np.max(np.abs(residual_nm))
            formel_str = " + ".join([f"{c:.5e}·P^{grad-i}" if i < grad else f"{c:.5f}" for i, c in enumerate(koeffizienten)])
            formel_str = formel_str.replace("·P^1", "·P").replace("·P^0", "")
            
            ax_fit.text(0.01, 1.05, f"λ(P) = {formel_str}  (Max. Abw: {max_abw_nm:.4f} nm)", 
                        transform=ax_fit.transAxes, fontsize=9, fontweight="bold", color="navy")

            self.kalibrier_fig.canvas.draw_idle()

        self.text_box_grad.on_submit(aktualisiere_plot)
        aktualisiere_plot("3")

        plt.show()

    def _kalibrierung_abschliessen(self, ereignis=None) -> None:
        if self.kalibrier_fig is not None:
            plt.close(self.kalibrier_fig)
            self.kalibrier_fig = None

    def _aktiviere_koordinaten_anzeige(self) -> None:
        def format_coord(x, y):
            items = list(self.serien.items())
            if not items:
                return f"x={x:.2f}, y={y:.2f}"
            
            teile = []
            for name, daten in items:
                if not self.sichtbar.get(name, True):
                    continue
                wellenlaengen = daten["wellenlaenge"]
                intensitaeten = daten["intensitaet"]
                pixel_arr = daten["pixel"]
                
                if len(wellenlaengen) > 0:
                    idx = np.searchsorted(wellenlaengen, x)
                    idx = np.clip(idx, 1, len(wellenlaengen) - 1)
                    if abs(wellenlaengen[idx - 1] - x) < abs(wellenlaengen[idx] - x):
                        idx = idx - 1
                        
                    inte = intensitaeten[idx]
                    wl = wellenlaengen[idx]
                    px = pixel_arr[idx]
                    teile.append(f"{name}: {inte:.1f} a.u. ({wl:.2f} nm, Pixel {int(px)})")
            
            infotext = " | ".join(teile)
            return f"Wellenlänge: {x:.2f} nm | {infotext}"

        self.ax.format_coord = format_coord


def main() -> None:
    pfad = Path(STANDARD_DATEI)
    if not pfad.exists():
        print(f"Fehler: Datei '{pfad}' wurde nicht gefunden.")
        sys.exit(1)

    serien = lade_spektren(pfad)
    viewer = SpektrumViewer(serien, titel=pfad.name)
    plt.show()


if __name__ == "__main__":
    main()