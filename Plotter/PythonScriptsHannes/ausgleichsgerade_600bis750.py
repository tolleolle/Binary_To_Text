import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox

# ==========================================
# HIER DEINE DATEN EINTRAGEN:
# ==========================================
# 1. Die gemessenen Pixel-Nummern deiner Peaks
pixel_werte = np.array([
    2479, 2488, 2502, 2597, 2633, 
    2702, 2763, 2776, 2993, 3022, 3084, 
    3184, 3239, 3263, 3316, 3347, 3414, 3464, 3520, 3586, 3602, 3612
], dtype=float)

# 2. Die exakten Literaturwerte in nm (in genau derselben Reihenfolge!)
wellenlaengen_lit = np.array([
    603.21, 604.32, 605.94, 617.31, 621.60, 
    629.69, 636.96, 638.47, 664.37, 667.73, 
    675.28, 687.13, 693.77, 696.54, 703.03, 706.72, 714.71, 720.70, 727.29, 735.33, 
    737.21, 738.40
], dtype=float)
# ==========================================

# Liste der Pixel, die als Kreuz dargestellt werden sollen
spezielle_pixel = [3022, 3263, 3347, 3612]

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

        # Oberer Plot aktualisieren (Einheitliche Punkte, keine Kreuze)
        ax1.clear()
        ax1.plot(pixel_werte, wellenlaengen_lit, 'ko', markersize=5, label='Zuordnungen')
        ax1.plot(x_lin, fit_kurve, 'r-', linewidth=1.5, label=f'Fit (Grad {grad})')
        ax1.set_ylabel('Wellenlänge (nm)')
        ax1.set_title('Wellenlängen-Kalibrierung des Spektrometers')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')

        # Unterer Plot aktualisieren (Verbundene Linie, Standard-Punkte, spezielle Kreuze, Toleranzlinien)
        ax2.clear()
        ax2.plot(pixel_werte, residuen, 'g-', linewidth=1, alpha=0.5)
        ax2.plot(pixel_werte[maske_normal], residuen[maske_normal], 'go', markersize=5, label='Standard')
        ax2.plot(pixel_werte[maske_spezial], residuen[maske_spezial], 'rx', markersize=7, markeredgewidth=1.5, label='Hervorgehobene Peaks')
        ax2.axhline(0, color='black', linestyle='--', linewidth=0.8)
        
        # Toleranzlinien basierend auf der lokalen Steigung des Fits für ±1 Pixel
        mittlere_steigung = np.mean(np.gradient(fit_kurve, x_lin))
        toleranz_1_pixel = abs(mittlere_steigung)
        ax2.axhline(toleranz_1_pixel, color='orange', linestyle=':', linewidth=1.2, label='±1 Pixel Toleranz')
        ax2.axhline(-toleranz_1_pixel, color='orange', linestyle=':', linewidth=1.2)

        ax2.set_xlabel('Pixel')
        ax2.set_ylabel('Residuen (nm)')
        ax2.set_title('Abweichungen der Literaturwerte vom Fit')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper left')

        fig.canvas.draw_idle()

    # UI-Elemente rechts platzieren
    ax_box_label = fig.add_axes([0.77, 0.55, 0.18, 0.04])
    ax_box_label.axis("off")
    ax_box_label.text(0, 0.5, "Polynom-Grad eingeben\n(und Enter drücken):", fontsize=9, fontweight="bold")

    ax_box = fig.add_axes([0.77, 0.45, 0.18, 0.06])
    text_box = TextBox(ax_box, "", initial="1")
    text_box.on_submit(update_fit)

    # Initialer Aufruf mit Grad 1
    update_fit("1")

    plt.show()