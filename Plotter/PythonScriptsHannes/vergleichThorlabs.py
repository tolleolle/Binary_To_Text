from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.widgets import TextBox, RadioButtons

Datei = r"C:\Users\hanne\Desktop\Prakikum Greifswald\Projekte für Andrei\Plotter\bg_abgezogen\08_P1P1p170kW_a300msx100_b3000msx10_BG_abgezogen.txt"

FESTE_PIXEL_PEAKS = [
    ( 733,  401.37), ( 760,  404.44), ( 785,  407.20), ( 813,  410.39), ( 862,  415.86),
    ( 867,  416.41), ( 883,  418.19), ( 891,  419.10), ( 924,  422.82), ( 945,  425.12),
    ( 952,  425.94), ( 958,  426.63), ( 963,  427.22), ( 988,  430.01), (1050,  437.13),
    (1057,  437.97), (1076,  440.01), (1098,  442.60), (1173,  451.07), (1203,  454.51),
    (1233,  457.93), (1243,  458.99), (1259,  460.96), (1301,  465.79), (1340,  470.23),
    (1361,  472.68), (1369,  473.59), (1431,  480.60), (1467,  484.78), (1495,  487.99),
    (1540,  493.32), (1568,  496.51), (1606,  500.94), (1652,  506.20), (1724,  514.53),
    (1738,  516.23), (1760,  518.78), (1986,  545.17), (2023,  549.59), (2077,  555.87),
    (2118,  560.67), (2156,  565.07), (2231,  573.95), (2357,  588.86), (2377,  591.21),
    (2479,  603.21), (2488,  604.32), (2502,  605.94), (2597,  617.31), (2633,  621.59),
    (2702,  629.69), (2763,  636.96), (2776,  638.47), (2993,  664.37), (3022,  667.73),
    (3084,  675.28), (3184,  687.13), (3239,  693.77), (3263,  696.54), (3316,  703.03),
    (3347,  706.72), (3414,  714.71), (3464,  720.70), (3520,  727.29), (3586,  735.33),
    (3602,  737.21), (3612,  738.40)
]

spezielle_pixel = [785, 952, 958, 963, 988, 1431, 1467, 3022, 3263, 3347, 3612]


def lade_spektren(pfad: Path) -> dict[str, dict[str, np.ndarray]]:
    if not pfad.exists():
        return {}

    rohdaten = np.loadtxt(pfad, delimiter="\t", skiprows=1)

    serien = {}
    # Feste Zuweisung: Erste beiden Spalten = Spektrometer A, Letzte beiden Spalten = Spektrometer B
    namen = ["Spektrometer Antenne", "Spektrometer Backend"]
    for i in range(min(rohdaten.shape[1] // 2, len(namen))):
        name = namen[i]
        serien[name] = {
            "wellenlaenge": rohdaten[:, 2 * i],
            "intensitaet": rohdaten[:, 2 * i + 1],
            "pixel": np.arange(rohdaten.shape[0], dtype=float),
        }
    return serien


def formel_string_erstellen(koeffizienten):
    grad = len(koeffizienten) - 1
    teile = []
    for i, koeff in enumerate(koeffizienten):
        p_grad = grad - i
        if p_grad > 1:
            teile.append(f"{koeff:+.6g}·P^{p_grad}")
        elif p_grad == 1:
            teile.append(f"{koeff:+.6g}·P")
        else:
            teile.append(f"{koeff:+.6g}")
    return "λ(P) = " + " ".join(teile)


def main():
    pfad = Path(Datei)
    serien = lade_spektren(pfad)
    if not serien:
        print(f"Fehler: Datei '{pfad}' nicht gefunden oder ungültig.")
        return

    # Start-Spektrometer (Standard: Spektrometer A)
    aktiver_name = "Spektrometer Antenne"

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    fig.subplots_adjust(right=0.74, top=0.88)
    formel_text_box = fig.text(0.10, 0.92, "", fontsize=9, fontweight="bold", color="darkblue")

    def update_fit(text=None):
        nonlocal aktiver_name
        daten = serien[aktiver_name]

        # Peak-Daten für das aktuell ausgewählte Spektrometer extrahieren
        pixel_liste, lit_liste, thorlabs_liste = [], [], []
        for pix, lit_wert in FESTE_PIXEL_PEAKS:
            idx = int(pix)
            if idx >= len(daten["pixel"]):
                continue
            pixel_liste.append(float(idx))
            lit_liste.append(lit_wert)
            thorlabs_liste.append(daten["wellenlaenge"][idx])

        pixel_werte = np.array(pixel_liste)
        wellenlaengen_lit = np.array(lit_liste)
        thorlabs_arr = np.array(thorlabs_liste)

        maske_spezial = np.isin(pixel_werte, spezielle_pixel)
        maske_normal = ~maske_spezial

        try:
            grad_lit = int(text_box_lit.text)
            if grad_lit < 1 or grad_lit >= len(pixel_werte):
                return
        except ValueError:
            return

        # Fit gegen die Literaturwerte (eigene Kalibrierung)
        koeff_lit = np.polyfit(pixel_werte, wellenlaengen_lit, grad_lit)
        poly_func_lit = np.poly1d(koeff_lit)
        fit_wellenlaengen = poly_func_lit(pixel_werte)
        x_lin_aktuell = np.linspace(pixel_werte.min(), pixel_werte.max(), 500)
        fit_kurve_lit = poly_func_lit(x_lin_aktuell)
        residuen_lit = wellenlaengen_lit - fit_wellenlaengen
        max_abw_lit = np.max(np.abs(residuen_lit))

        # Abweichung der werksseitigen Thorlabs-Kalibrierung von den Literaturwerten
        # (keine eigene Fit-Kurve mehr nötig, da direkter Vergleich mit den Rohwerten)
        residuen_thor = thorlabs_arr - wellenlaengen_lit

        # Formeltext oben aktualisieren
        formel_str = formel_string_erstellen(koeff_lit)
        formel_text_box.set_text(f"Fit Lit ({aktiver_name}): {formel_str}  (Max. Abw: {max_abw_lit:.4f} nm)")

        # Fenstertitel mitführen (z. B. relevant als Vorschlag beim Abspeichern über die Matplotlib-Toolbar)
        fig.canvas.manager.set_window_title(f"{pfad.stem}_{aktiver_name.replace(' ', '_')}")

        # Oberer Plot
        ax1.clear()
        ax1.plot(pixel_werte, wellenlaengen_lit, 'ko', markersize=4)
        ax1.plot(x_lin_aktuell, fit_kurve_lit, 'r-', linewidth=1.5)
        ax1.plot(pixel_werte, thorlabs_arr, 's', color='darkorange', markersize=4)

        ax1.set_ylabel('Wellenlänge (nm)')
        ax1.set_title(f'Wellenlängen-Kalibrierung: {pfad.stem} ({aktiver_name})')
        ax1.grid(True, alpha=0.3)

        # Unterer Plot
        ax1_deriv = poly_func_lit.deriv()
        toleranz_1_pixel = np.abs(ax1_deriv(x_lin_aktuell))

        ax2.clear()
        ax2.plot(pixel_werte, residuen_lit, 'g-', linewidth=1, alpha=0.5)
        ax2.plot(pixel_werte[maske_normal], residuen_lit[maske_normal], 'go', markersize=4)
        ax2.plot(pixel_werte[maske_spezial], residuen_lit[maske_spezial], 'rx', markersize=6, markeredgewidth=1.5)
        ax2.plot(pixel_werte, residuen_thor, 'x', color='purple', markersize=5)

        ax2.axhline(0, color='black', linestyle='--', linewidth=0.8)
        ax2.plot(x_lin_aktuell, toleranz_1_pixel, color='orange', linestyle=':', linewidth=1.2)
        ax2.plot(x_lin_aktuell, -toleranz_1_pixel, color='orange', linestyle=':', linewidth=1.2)

        ax2.set_xlabel('Pixel')
        ax2.set_ylabel('Residuen (nm)')
        ax2.set_title(f'Abweichungen vom Soll ({aktiver_name})')
        ax2.grid(True, alpha=0.3)

        fig.canvas.draw_idle()

    def spektr_wechsel(label):
        nonlocal aktiver_name
        aktiver_name = label
        update_fit()

    # Radio-Buttons zur Auswahl zwischen Spektrometer A und B
    fig.text(0.77, 0.84, "Spektrometer wählen:", fontsize=9, fontweight="bold")
    ax_radio = fig.add_axes([0.77, 0.74, 0.18, 0.08])
    radio = RadioButtons(ax_radio, ["Spektrometer Antenne", "Spektrometer Backend"], active=0)
    radio.on_clicked(spektr_wechsel)

    # Textbox für den Polynomgrad des eigenen Fits (Literaturwerte)
    fig.text(0.77, 0.67, "Polynom-Grad Fit:", fontsize=9, fontweight="bold")
    ax_box_lit = fig.add_axes([0.77, 0.60, 0.18, 0.04])
    text_box_lit = TextBox(ax_box_lit, "", initial="3")
    text_box_lit.on_submit(update_fit)

    # Legende (rutscht in den frei gewordenen Platz der entfernten Thorlabs-Textbox)
    ax_legende = fig.add_axes([0.77, 0.05, 0.18, 0.48])
    ax_legende.axis("off")
    legend_handles = [
        mlines.Line2D([], [], color='k', marker='o', linestyle='None', markersize=4, label='Literaturwerte'),
        mlines.Line2D([], [], color='darkorange', marker='s', linestyle='None', markersize=4, label='Thorlabswerte'),
        mlines.Line2D([], [], color='r', marker='x', linestyle='None', markersize=6, markeredgewidth=1.5, label='Hervorgehobene Peaks'),
        mlines.Line2D([], [], color='r', linestyle='-', linewidth=1.5, label='Fit-Kurve (Lit)'),
        mlines.Line2D([], [], color='green', marker='o', linestyle='None', markersize=4, label='Residuum Lit'),
        mlines.Line2D([], [], color='purple', marker='x', linestyle='None', markersize=5, label='Abw. Thorlabs vs Lit'),
        mlines.Line2D([], [], color='orange', linestyle=':', linewidth=1.2, label='±1 Pixel Toleranz')
    ]

    ax_legende.legend(
        handles=legend_handles,
        loc='upper left',
        frameon=True,
        facecolor='#f9f9f9',
        edgecolor='#cccccc',
        fontsize=8,
        labelspacing=0.6
    )

    update_fit()
    plt.show()


if __name__ == "__main__":
    main()