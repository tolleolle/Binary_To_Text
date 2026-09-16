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
from matplotlib.widgets import Button, CheckButtons
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
# Literaturwerte zur Wellenlängenkalibrierung (Luftwellenlängen nach NIST, in nm)
# ---------------------------------------------------------------------------
ARGON_LINIEN_NM: list[tuple[float, str]] = [
    # --- Ar I (neutrales Argon) ---
    (404.442, "Ar"),
    (415.859, "Ar"),
    (419.832, "Ar"),
    (420.068, "Ar"),
    (425.936, "Ar"),
    (427.217, "Ar"),
    (430.010, "Ar"),
    (433.534, "Ar"),
    (451.073, "Ar"),
    (459.626, "Ar"),
    (462.818, "Ar"),
    (470.232, "Ar"),
    (484.781, "Ar"),
    (488.903, "Ar"),
    (493.321, "Ar"),
    (506.204, "Ar"),
    (518.775, "Ar"),
    (522.127, "Ar"),
    (549.587, "Ar"),
    (555.870, "Ar"),
    (560.673, "Ar"),
    (588.858, "Ar"),
    (591.208, "Ar"),
    (603.213, "Ar"),
    (605.937, "Ar"),
    (609.616, "Ar"),
    (617.228, "Ar"),
    (624.212, "Ar"),
    (631.545, "Ar"),
    (641.631, "Ar"),
    (650.653, "Ar"),
    (667.728, "Ar"),
    (675.283, "Ar"),
    (687.129, "Ar"),
    (696.543, "Ar"),
    (706.722, "Ar"),
    (714.704, "Ar"),
    (727.294, "Ar"),
    (738.398, "Ar"),
    (750.387, "Ar"),
    (763.511, "Ar"),
    (772.376, "Ar"),
    (789.106, "Ar"),
    (794.818, "Ar"),
    (800.616, "Ar"),
    (801.479, "Ar"),
    (810.369, "Ar"),
    (811.531, "Ar"),
    (826.452, "Ar"),
    (837.761, "Ar"),
    (840.821, "Ar"),
    (842.465, "Ar"),
    (852.144, "Ar"),
    (866.794, "Ar"),
    (912.297, "Ar"),
    (922.450, "Ar"),
    (965.778, "Ar"),
    
    # --- Ar II (einfach ionisiertes Argon, Ar+) ---
    (434.800, "Ar+"),
    (454.504, "Ar+"),
    (457.936, "Ar+"),
    (465.795, "Ar+"),
    (472.689, "Ar+"),
    (476.488, "Ar+"),
    (480.602, "Ar+"),
    (487.986, "Ar+"),
    (496.508, "Ar+"),
    (501.717, "Ar+"),
    (514.533, "Ar+"),
    (528.700, "Ar+"),
]

LITERATUR_TOLERANZ_NM = 1.0

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
        self.text_artists = []
        self.check = None  # Wichtig, damit CheckButtons Referenz behält

        self._erstelle_fenster(titel)
        self._zeichne_kurven()
        self._erstelle_steuerelemente()
        self._skalierung_aktualisieren()
        self._aktiviere_klick_auswahl()
        self._aktiviere_koordinaten_anzeige()

    # -- Aufbau ---------------------------------------------------------

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
            
        # Mehr Platz für das rechte Panel schaffen
        self.fig.subplots_adjust(right=0.72, bottom=0.15)

        # Buttons im rechten Steuerungsbereich
        ax_reset_button = self.fig.add_axes([0.74, 0.03, 0.22, 0.038])
        self.reset_button = Button(ax_reset_button, "Peaks zurücksetzen")
        self.reset_button.on_clicked(self._peaks_zuruecksetzen)

        ax_button = self.fig.add_axes([0.74, 0.075, 0.22, 0.038])
        self.kalibrier_button = Button(ax_button, "Peaks bestätigen")
        self.kalibrier_button.on_clicked(self._kalibrierung_starten)

        ax_add_button = self.fig.add_axes([0.74, 0.12, 0.22, 0.038])
        self.add_button = Button(ax_add_button, "Datei hinzufügen")
        self.add_button.on_clicked(self._datei_hinzuufuegen)

        self.ax.set_xlabel("Wellenlänge (nm)")
        self.ax.set_ylabel("Intensität (a.u.)")
        self.ax.set_title("Spektren-Viewer (Wellenlängen-Ansicht)")
        self.ax.grid(True, alpha=0.3)

        # Farb-kodiertes Info-Panel für erkannte Peaks auf der rechten Seite
        self.ax_info = self.fig.add_axes([0.74, 0.40, 0.22, 0.55])
        self.ax_info.axis("off")

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
        """Passt die Achsen-Skalierung dynamisch an die aktuell sichtbaren Serien an."""
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

        height = min(0.70, max(0.1, 0.035 * len(labels_kurz) + 0.04))
        self.ax_check = self.fig.add_axes([0.74, 0.175, 0.22, height])
        
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

    # -- Peaks ------------------------------------------------------------

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

            (m,) = self.ax.plot(
                x_pos, 
                peak["intensitaet"],
                "^",
                color=farbe,
                markersize=6,
                markeredgecolor="black",
                markeredgewidth=0.5,
            )

            if "spezies" in peak and "lit_wert" in peak:
                label_text = f"[{peak['spezies']}] {x_pos:.2f} nm \n(lit: {peak['lit_wert']:.2f} nm)"
            else:
                label_text = f"Pixel {int(peak['pixel'])} | {x_pos:.2f} nm"

            offset_y = 12 if (i % 2 == 0) else 32

            text = self.ax.annotate(
                label_text,
                xy=(x_pos, peak["intensitaet"]),
                xytext=(0, offset_y),
                textcoords="offset points",
                fontsize=7,
                ha="center",
                color=farbe,
            )

            marker.append(m)
            beschriftungen.append(text)

        return {"marker": marker, "beschriftungen": beschriftungen}

    def _peaks_zuruecksetzen(self, ereignis=None) -> None:
        """Setzt alle ausgewählten Peaks zurück."""
        for name in self.ausgewaehlte_peaks:
            self.ausgewaehlte_peaks[name].clear()
        
        self._aktualisiere_peak_anzeige()
        print("Alle Peaks wurden zurückgesetzt.")

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
            
            fenster = 15
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

        for t in self.text_artists:
            try:
                t.remove()
            except Exception:
                pass
        self.text_artists = []

        self.peak_grafik = {}
        y_cursor = 0.95
        line_height = 0.05

        if hasattr(self, "ax_info"):
            t_head = self.ax_info.text(0.02, y_cursor, "Erkannte Peaks:", fontsize=9, fontweight="bold", transform=self.ax_info.transAxes)
            self.text_artists.append(t_head)
            y_cursor -= line_height * 1.2

        for name, peaks in self.ausgewaehlte_peaks.items():
            self.peak_grafik[name] = self._zeichne_peaks_einer_serie(name, peaks, farbe=self.farben[name])
            
            if peaks and hasattr(self, "ax_info"):
                farbe = self.farben[name]
                t_serie = self.ax_info.text(0.02, y_cursor, f"--- {name[:18]} ---", fontsize=8, fontweight="bold", color=farbe, transform=self.ax_info.transAxes)
                self.text_artists.append(t_serie)
                y_cursor -= line_height
                
                for p in sorted(peaks, key=lambda x: x["wellenlaenge"]):
                    if y_cursor < 0.05:
                        t_more = self.ax_info.text(0.05, y_cursor, "... (weitere)", fontsize=7, color=farbe, transform=self.ax_info.transAxes)
                        self.text_artists.append(t_more)
                        break
                        
                    if "spezies" in p and "lit_wert" in p:
                        meas_wl = p.get("mess_wellenlaenge", p["wellenlaenge"])
                        txt = f"{p['spezies']} {meas_wl:.2f} (lit: {p['lit_wert']:.2f} nm)"
                    else:
                        txt = f"Unbek.: {p['wellenlaenge']:.2f} nm (Px {int(p['pixel'])})"
                    
                    t_peak = self.ax_info.text(0.05, y_cursor, txt, fontsize=7, color=farbe, transform=self.ax_info.transAxes)
                    self.text_artists.append(t_peak)
                    y_cursor -= line_height

        self._wende_sichtbarkeit_an()
        self.fig.canvas.draw_idle()

    # -- Kalibrierung -------------------------------------------------------

    def _kalibrierung_starten(self, ereignis=None) -> None:
        pixel = []
        wellenlaenge_lit = []
        serienname = []
        matched_peaks_info = []

        print("\n--- Zuordnung der Peaks zu Argon-Literaturwerten ---")
        for name, peaks in self.ausgewaehlte_peaks.items():
            for peak in peaks:
                treffer = finde_literaturwert(peak["wellenlaenge"])

                if treffer is None:
                    print(
                        f"  {name}, Pixel {int(peak['pixel']):4d} "
                        f"(≈ {peak['wellenlaenge']:.2f} nm): kein Literaturwert "
                        f"innerhalb von {LITERATUR_TOLERANZ_NM:g} nm gefunden - "
                        f"wird ignoriert."
                    )
                    continue

                lit_wert, spezies = treffer
                print(
                    f"  {name}, Pixel {int(peak['pixel']):4d}: "
                    f"{peak['wellenlaenge']:.2f} nm  ->  {spezies} {lit_wert:.3f} nm "
                    f"(Δ = {lit_wert - peak['wellenlaenge']:+.2f} nm)"
                )

                pixel.append(float(peak["pixel"]))
                wellenlaenge_lit.append(lit_wert)
                serienname.append(name)
                matched_peaks_info.append((name, peak, spezies, lit_wert))

        if len(pixel) < 2:
            print(f"Abgebrochen: Nur {len(pixel)} zugeordnete(r) Peak(s) - mindestens 2 nötig.")
            return

        pixel = np.asarray(pixel, dtype=float)
        wellenlaenge_lit = np.asarray(wellenlaenge_lit, dtype=float)
        serienname = np.asarray(serienname)

        unique_pixel, unique_idx = np.unique(pixel, return_index=True)
        pixel = unique_pixel
        wellenlaenge_lit = wellenlaenge_lit[unique_idx]
        serienname = serienname[unique_idx]

        if len(pixel) < 2:
            print("Abgebrochen: Es werden mindestens 2 verschiedene Pixel benötigt.")
            return
            
        m, b = np.polyfit(pixel, wellenlaenge_lit, 1)

        self._temp_matched_peaks = matched_peaks_info

        self.kalibrier_fig = plt.figure(figsize=(12, 9))
        if self.kalibrier_fig.canvas.manager is not None:
            self.kalibrier_fig.canvas.manager.set_window_title(
                "Wellenlängen-Kalibrierung – linearer Fit gegen Literaturwerte"
            )

        ax_fit = self.kalibrier_fig.add_axes([0.10, 0.58, 0.86, 0.33])
        ax_res = self.kalibrier_fig.add_axes([0.10, 0.23, 0.86, 0.25])
        
        ax_btn = self.kalibrier_fig.add_axes([0.38, 0.05, 0.24, 0.08])
        self.kalibrier_bestaetig_btn = Button(ax_btn, "Peaks bestätigen")
        self.kalibrier_bestaetig_btn.on_clicked(self._kalibrierung_abschliessen)

        x_fit = np.linspace(pixel.min(), pixel.max(), 500)
        y_fit = m * x_fit + b
        residual_nm = wellenlaenge_lit - (m * pixel + b)

        for name in self.serien:
            maske = serienname == name
            if np.any(maske):
                punkte = ax_fit.plot(
                    pixel[maske],
                    wellenlaenge_lit[maske],
                    "o",
                    markersize=7,
                    label=name,
                )
                farbe_serie = punkte[0].get_color()
                for px, lit_wert in zip(pixel[maske], wellenlaenge_lit[maske]):
                    ax_fit.annotate(
                        f"{lit_wert:.2f} nm",
                        xy=(px, lit_wert),
                        xytext=(0, 7),
                        textcoords="offset points",
                        fontsize=7,
                        ha="center",
                        color=farbe_serie,
                    )

        ax_fit.plot(x_fit, y_fit, "-", linewidth=1.5, label="Linearer Fit")
        ax_fit.set_xlabel("Pixel")
        ax_fit.set_ylabel("Wellenlänge λ (nm, Literaturwert)")
        ax_fit.set_title(f"Wellenlängen-Kalibrierung: λ = {m:.8g} · Pixel + {b:.8g}")
        ax_fit.grid(True, alpha=0.3)
        ax_fit.legend()

        for name in self.serien:
            maske = serienname == name
            if np.any(maske):
                ax_res.plot(pixel[maske], residual_nm[maske], "o", markersize=7, label=name)

        ax_res.axhline(0, linestyle="-", linewidth=1, color="black")
        ax_res.set_xlabel("Pixel")
        ax_res.set_ylabel("Abweichung vom Fit (nm)")
        ax_res.set_title("Abweichung der Literaturwerte vom linearen Fit (in nm)")
        ax_res.grid(True, alpha=0.3)
        ax_res.legend()

        max_abw_nm = np.max(np.abs(residual_nm))
        max_abw_pixel = max_abw_nm / abs(m)

        self.kalibrier_fig.text(
            0.10, 0.15,
            f"Steigung = {m:.8g} nm/Pixel    |    "
            f"Achsenabschnitt = {b:.8g} nm    |    "
            f"max. Abweichung = {max_abw_nm:.4g} nm (≈ {max_abw_pixel:.2f} Pixel)",
            fontsize=9,
        )

        print(f"{len(pixel)} Peaks validiert – Kalibrierungsfenster geöffnet.")
        plt.show()

    def _kalibrierung_abschliessen(self, ereignis=None) -> None:
        """Wird aufgerufen, wenn im Kalibrierungsfenster auf 'Peaks bestätigen' geklickt wird."""
        if hasattr(self, "_temp_matched_peaks"):
            neue_ausgewaehlte_peaks = {name: [] for name in self.serien}

            for name, peak, spezies, lit_wert in self._temp_matched_peaks:
                if "mess_wellenlaenge" not in peak:
                    peak["mess_wellenlaenge"] = peak["wellenlaenge"]
                
                peak["spezies"] = spezies
                peak["lit_wert"] = lit_wert
                
                if name in neue_ausgewaehlte_peaks:
                    neue_ausgewaehlte_peaks[name].append(peak)

            self.ausgewaehlte_peaks = neue_ausgewaehlte_peaks
            self._aktualisiere_peak_anzeige()
            print("Nicht zugeordnete Peaks wurden entfernt. Gemessene Wellenlängen bleiben im Plot erhalten.")

        if self.kalibrier_fig is not None:
            plt.close(self.kalibrier_fig)
            self.kalibrier_fig = None

    # -- Ereignisse ---------------------------------------------------------

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