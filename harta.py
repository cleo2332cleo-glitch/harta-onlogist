import folium
import numpy as np

# Coordonate de test (Würzburg -> Kassel)
start = [49.7913, 9.9294]
end = [51.3127, 9.4797]

# 1. CREĂM HARTA (Ultra Dark Mode)
m = folium.Map(
    location=[(start[0] + end[0])/2, (start[1] + end[1])/2],
    zoom_start=7,
    tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attr='&copy; CartoDB'
)

# 2. FUNCȚIE PENTRU CURBĂ (Arc Digital)
def create_arc(p1, p2, n_points=30):
    # Generăm o curbă tip parabolă între puncte
    lats = np.linspace(p1[0], p2[0], n_points)
    lngs = np.linspace(p1[1], p2[1], n_points)
    
    # Adăugăm "burta" curbei (offset)
    dist = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
    offset = np.sin(np.linspace(0, np.pi, n_points)) * (dist * 0.2)
    
    return [[lats[i], lngs[i] + offset[i]] for i in range(n_points)]

arc_points = create_arc(start, end)

# 3. EFECTUL NEON (Stratificare)
# Strat 1: Glow-ul (Linia de fundal, lată și transparentă)
folium.PolyLine(
    arc_points, 
    color='#00f2ff', 
    weight=12, 
    opacity=0.2
).add_to(m)

# Strat 2: Linia principală (Miezul luminos)
folium.PolyLine(
    arc_points, 
    color='#00f2ff', 
    weight=3, 
    opacity=1,
    tooltip="Livrare Activă"
).add_to(m)

# 4. MARKERE MODERNE
# Start: Punct de lumină
folium.CircleMarker(
    location=start,
    radius=5,
    color='#00f2ff',
    fill=True,
    fill_opacity=1
).add_to(m)

# Destinație: Steag (Custom Icon)
folium.Marker(
    location=end,
    icon=folium.Icon(color='red', icon='flag', prefix='fa'),
).add_to(m)

# 5. SALVARE
m.save("harta_prologistics_2026.html")
