import pandas as pd
import plotly.graph_objects as go
import json

# Link-ul tău actualizat de Google Sheets (format CSV)
URL_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGWQb5ZLpLGDwl6mjeNAfzhUrl3GShXab_ePVSU8tj-9aOAwStGMjEutsErHnezkOpIaGA4maO_HYU/pub?output=csv"

def parse_coords(coord_str):
    try:
        if pd.isna(coord_str): return None, None
        coord_str = str(coord_str).strip().replace('(', '').replace(')', '')
        if "," in coord_str:
            parts = coord_str.split(',')
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
        else:
            parts = coord_str.split()
            lon, lat = float(parts[0].strip()), float(parts[1].strip())
        return lon, lat
    except:
        return None, None

# 1. Citire date din link-ul tău
try:
    df = pd.read_csv(URL_SHEETS)
except Exception as e:
    print(f"Eroare la citirea tabelului: {e}")
    exit(1)

# 2. Procesare coordonate (Coloanele K și L din Sheets)
if 'Coord_Start' in df.columns and 'Coord_Ziel' in df.columns:
    df['start_lon'], df['start_lat'] = zip(*df['Coord_Start'].apply(parse_coords))
    df['ziel_lon'], df['ziel_lat'] = zip(*df['Coord_Ziel'].apply(parse_coords))
    df = df.dropna(subset=['start_lon', 'start_lat', 'ziel_lon', 'ziel_lat'])
else:
    print("EROARE: Nu am gasit coloanele Coord_Start si Coord_Ziel pe randul 1 in Sheets!")
    exit(1)

# 3. Pregătire date pentru ferestrele pop-up (exact cum apar în tabelul tău)
locations_data = {}
for i, row in df.iterrows():
    locations_data[str(i)] = {
        'id_afisat': str(row.get('#ID', 'N/A')),
        'pret': str(row.get('Listen Preis', 'N/A')),
        'ag': str(row.get('Auftraggeber (AG)', 'N/A')),
        'startort': str(row.get('Startort', 'N/A')),
        'zielort': str(row.get('Zielort', 'N/A')),
        'livrare': str(row.get('Ankunftszeit', 'N/A')),
        'start': [row['start_lon'], row['start_lat']], 
        'ziel': [row['ziel_lon'], row['ziel_lat']]
    }

# 4. Construcție hartă interactivă
fig = go.Figure()

# Puncte Negre (Start)
fig.add_trace(go.Scattermapbox(
    lat=df['start_lat'], lon=df['start_lon'],
    mode='markers',
    marker={'size': 14, 'color': 'black'},
    name='Punct Incarcare',
    customdata=df.index,
    hoverinfo='none'
))

# Puncte Roșii (Destinație)
fig.add_trace(go.Scattermapbox(
    lat=df['ziel_lat'], lon=df['ziel_lon'],
    mode='markers',
    marker={'size': 12, 'color': 'red'},
    name='Destinatie',
    customdata=df.index,
    hoverinfo='none'
))

fig.update_layout(
    mapbox={'style': "carto-positron", 'center': {'lat': 48, 'lon': 12}, 'zoom': 5},
    margin={'l': 0, 'r': 0, 'b': 0, 't': 0},
    showlegend=False
)

# 5. Generare fișier final
html_content = fig.to_html(full_html=True, include_plotlyjs='cdn')
script_inject = f"<script>var coords = {json.dumps(locations_data)};</script>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content.replace('</body>', script_inject + '</body>'))

print("Succes! Harta a fost generata in index.html")
