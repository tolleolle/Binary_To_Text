import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.widgets import TextBox

# ==========================================
# HIER DEINE DATEN ALS TABELLE EINTRAGEN:
# Format pro Zeile: [Pixel, Wellenlänge in nm]
# ==========================================
messdaten = np.array([
    [ 733,  401.37],
    [ 760,  404.44],
    [ 785,  407.20],
    [ 813,  410.39],
    [ 862,  415.86],
    [ 867,  416.41],
    [ 883,  418.19],
    [ 891,  419.10],
    [ 924,  422.82],
    [ 945,  425.12],
    [ 952,  425.94],
    [ 958,  426.63],
    [ 963,  427.22],
    [ 988,  430.01],
    [1050,  437.13],
    [1057,  437.97],
    [1076,  440.01],
    [1098,  442.60],
    [1173,  451.07],
    [1203,  454.51],
    [1233,  457.93],
    [1243,  458.99],
    [1259,  460.96],
    [1301,  465.79],
    [1340,  470.23],
    [1361,  472.68],
    [1369,  473.59],
    [1431,  480.60],
    [1467,  484.78],
    [1495,  487.99],
    [1540,  493.32],
    [1568,  496.51],
    [1606,  500.94],
    [1652,  506.20],
    [1724,  514.53],
    [1738,  516.23],
    [1760,  518.78],
    [1986,  545.17],
    [2023,  549.59],
    [2077,  555.87],
    [2118,  560.67],
    [2156,  565.07],
    [2231,  573.95],
    [2357,  588.86],
    [2377,  591.21],
    [2479,  603.21],
    [2488,  604.32],
    [2502,  605.94],
    [2597,  617.31],
    [2633,  621.59],
    [2702,  629.69],
    [2763,  636.96],
    [2776,  638.47],
    [2993,  664.37],
    [3022,  667.73],
    [3084,  675.28],
    [3184,  687.13],
    [3239,  693.77],
    [3263,  696.54],
    [3316,  703.03],
    [3347,  706.72],
    [3414,  714.71],
    [3464,  720.70],
    [3520,  727.29],
    [3586,  735.33],
    [3602,  737.21],
    [3612,  738.40]
], dtype=float)

# Automatische Trennung in die beiden Arrays
pixel_werte = messdaten[:, 0]
wellenlaengen_lit = messdaten[:, 1]
# ==========================================

# Liste der Pixel, die als Kreuz dargestellt werden sollen
spezielle_pixel = [785, 952, 958, 963, 988, 1431, 1467, 3022, 3263, 3347, 3612]

if len(pixel_werte) != len(wellenlaengen_lit):
    print("Fehler: Die Anzahl der Pixelwerte und Literaturwerte stimmt nicht überein!")
else:
    # Grafische Darstellung mit Platz für das Menü rechts und Formel oben
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    fig.subplots_adjust(right=0.74, top=0.88)

    maske_spezial = np.isin(pixel_werte, spezielle_pixel)
    maske_normal = ~maske_spezial

    x_lin = np.linspace(pixel_werte.min(), pixel_werte.max(), 500)

    # Textfeld für Formelanzeige oben im Fenster
    formel_text_box = fig.text(0.10, 0.92, "", fontsize=10, fontweight="bold", color="darkblue")

    def formel_string_erstellen(koeffizienten):
        """Erzeugt einen lesbaren String für das Polynom."""
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

    def update_fit(text_input):
        try:
            grad = int(text_input)
            if grad < 1:
                print("Grad muss mindestens 1 sein.")
                return
            if grad >= len(pixel_werte):
                print(f"Fehler: Grad zu hoch! Maximaler Grad ist {len(pixel_werte)-1}.")
                return
        except ValueError:
            print("Bitte eine gültige ganze Zahl eingeben.")
            return
        
        # Polynomfit berechnen
        koeffizienten = np.polyfit(pixel_werte, wellenlaengen_lit, grad)
        poly_func = np.poly1d(koeffizienten)
        
        # Werte und Residuen berechnen
        fit_wellenlaengen = poly_func(pixel_werte)
        fit_kurve = poly_func(x_lin)
        residuen = wellenlaengen_lit - fit_wellenlaengen
        max_abw = np.max(np.abs(residuen))
        
        # Formel oben im Fenster aktualisieren
        formel_str = formel_string_erstellen(koeffizienten)
        formel_text_box.set_text(f"{formel_str}  (Max. Abw: {max_abw:.4f} nm)")

        print(f"\n--- FIT-ERGEBNIS (Grad {grad}) ---")
        print(f"Formel: {formel_str}")
        print(f"Maximale Abweichung: {max_abw:.4f} nm")

        # Oberer Plot aktualisieren
        ax1.clear()
        ax1.plot(pixel_werte, wellenlaengen_lit, 'ko', markersize=4)
        ax1.plot(x_lin, fit_kurve, 'r-', linewidth=1.5)
        ax1.set_ylabel('Wellenlänge (nm)')
        ax1.set_title('Wellenlängen-Kalibrierung des Spektrometers')
        ax1.grid(True, alpha=0.3)

        # Unterer Plot aktualisieren
        ax2.clear()
        ax2.plot(pixel_werte, residuen, 'g-', linewidth=1, alpha=0.5)
        ax2.plot(pixel_werte[maske_normal], residuen[maske_normal], 'go', markersize=4)
        ax2.plot(pixel_werte[maske_spezial], residuen[maske_spezial], 'rx', markersize=6, markeredgewidth=1.5)
        ax2.axhline(0, color='black', linestyle='--', linewidth=0.8)
        
        # Toleranzlinien basierend auf der lokalen Steigung des Fits für ±1 Pixel
        mittlere_steigung = np.mean(np.gradient(fit_kurve, x_lin))
        toleranz_1_pixel = abs(mittlere_steigung)
        ax2.axhline(toleranz_1_pixel, color='orange', linestyle=':', linewidth=1.2)
        ax2.axhline(-toleranz_1_pixel, color='orange', linestyle=':', linewidth=1.2)

        ax2.set_xlabel('Pixel')
        ax2.set_ylabel('Residuen (nm)')
        ax2.set_title('Abweichungen der Literaturwerte vom Fit')
        ax2.grid(True, alpha=0.3)

        fig.canvas.draw_idle()

    # --- UI-ELEMENTE RECHTS PLATZIEREN ---
    
    # 1. Eingabefeld für den Grad
    ax_box_label = fig.add_axes([0.77, 0.74, 0.18, 0.04])
    ax_box_label.axis("off")
    ax_box_label.text(0, 0.5, "Polynom-Grad eingeben\n(und Enter drücken):", fontsize=9, fontweight="bold")

    ax_box = fig.add_axes([0.77, 0.65, 0.18, 0.05])
    text_box = TextBox(ax_box, "", initial="1")
    text_box.on_submit(update_fit)

    # 2. Saubere, native matplotlib-Legende rechts
    ax_legende = fig.add_axes([0.77, 0.15, 0.18, 0.45])
    ax_legende.axis("off")

    legend_handles = [
        mlines.Line2D([], [], color='k', marker='o', linestyle='None', markersize=4, label='Zuordnungen'),
        mlines.Line2D([], [], color='r', marker='x', linestyle='None', markersize=6, markeredgewidth=1.5, label='Hervorgehobene Peaks'),
        mlines.Line2D([], [], color='r', linestyle='-', linewidth=1.5, label='Fit-Kurve'),
        mlines.Line2D([], [], color='g', linestyle='-', linewidth=1, label='Residuen-Linie'),
        mlines.Line2D([], [], color='orange', linestyle=':', linewidth=1.2, label='±1 Pixel Toleranz')
    ]
    
    ax_legende.legend(
        handles=legend_handles, 
        loc='upper left', 
        frameon=True, 
        facecolor='#f9f9f9', 
        edgecolor='#cccccc', 
        fontsize=8.5, 
        labelspacing=1.1
    )

    # Initialer Aufruf mit Grad 1
    update_fit("1")

    plt.show()