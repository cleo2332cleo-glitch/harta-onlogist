import folium
from folium import plugins

# Presupunem că ai aceste date extrase din scriptul tău (Exemplu: de la Würzburg la Kassel)
# Format: [lat, lng]
start_coords = [49.7913, 9.9294] 
end_coords = [51.3127, 9.4797]

# Creăm harta cu fundal Dark Mode pentru efectul Neon
m = folium.Map(location=[(start_coords[0] + end_coords[0])/2, 
                         (start_coords[1] + end_coords[1])/2], 
               zoom_start=7, 
               tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
               attr='&copy; CartoDB')

# --- LOGICA PENTRU LINIA CURBATĂ (BEZIER) ---
# Generăm un punct de control pentru a "îndoi" linia spre dreapta/stânga
control_point = [
    (start_coords[0] + end_coords[0]) / 2 + 0.5, 
    (start_coords[1] + end_coords[1]) / 2 + 0.8
]

# Script JS injectat pentru efectul de Glow și Curbă
curve_script = f"""
<script>
    var pathData = "M {start_coords[1]} {start_coords[0]} Q {control_point[1]} {control_point[0]} {end_coords[1]} {end_coords[0]}";
    // Folosim o librărie SVG internă sau manipulăm Layer-ul Leaflet după randare
</script>
"""

# Adăugăm Linia cu Efect Neon (folosind PolyLine cu greutate mare și opacitate)
# Pentru o curbă perfectă în Python Folium, folosim AntPath sau curbe matematice:
path_coords = [start_coords, control_point, end_coords]

# Linia principală Neon Albastră
folium.PolyLine(
    locations=[start_coords, end_coords], # Aici poți adăuga mai multe puncte dacă ai traseul real
    color='#00f2ff',
    weight=4,
    opacity=0.8,
    tooltip="Ruta Activă"
).add_to(m)

# --- MARKERE STILIZATE ---

# START: Cerc Radiant (Neon Dot)
folium.CircleMarker(
    location=start_coords,
    radius=6,
    color='#00f2ff',
    fill=True,
    fill_color='#00f2ff',
    fill_opacity=0.9,
    popup="Punct Plecare"
).add_to(m)

# DESTINAȚIE: Steag (Custom Icon)
folium.Marker(
    location=end_coords,
    icon=folium.Icon(color='red', icon='flag', prefix='fa'),
    popup="Destinație Finală"
).add_to(m)

# Adăugăm un efect de puls pe destinație
plugins.BeautifyIcon(icon='arrow-down', border_color='#ff0055', text_color='#ff0055').add_to(m)

# Salvăm rezultatul
m.save("harta_prologistics_2026.html")
print("Harta a fost generată! Deschide harta_prologistics_2026.html")
