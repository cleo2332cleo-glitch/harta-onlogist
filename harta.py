import pandas as pd
import plotly.graph_objects as go
import json

# Link-ul tău de Google Sheets (format CSV public)
URL_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGWQb5ZLpLGDwl6mjeNAfzHUr13GShXAb_ePVSU8tj-9a0AwStGMjEutsErHnezKOpIaGA4maO_HYU/pub?output=csv"

def parse_coords(coord_str):
    try:
        coord_str = str(coord_str).strip()
        if "," in coord_str:
            lat, lon = map(float, coord_str.split(','))
        else:
            lon, lat = map(float, coord_str.split())
        return lon, lat
    except:
        return None, None

# Citire date
df = pd.read_csv(URL_SHEETS)

# Verificăm dacă există coloanele de coordonate (K și L din Sheets-ul tău)
# Am folosit numele pe care le-am stabilit: Coord_Start și Coord_Ziel
df['start_lon'], df['start_lat'] = zip(*df['Coord_Start'].apply(parse_coords))
df['ziel_lon'], df['ziel_lat'] = zip(*df['Coord_Ziel'].apply(parse_coords))
df = df.dropna(subset=['start_lon', 'start_lat', 'ziel_lon', 'ziel_lat'])

locations_data = {}
for i, row in df.iterrows():
    # Aici am pus exact numele coloanelor tale din screenshot: #ID, Listen Preis, etc.
    locations_data[str(i)] = {
        'id_afisat': str(row['#ID']),
        'pret': str(row['Listen Preis']),
        'ag': str(row['Auftraggeber (AG)']),
        'startort': str(row['Startort']),
        'zielort': str(row['Zielort']),
        'livrare': str(row['Ankunftszeit']),
        'start': [row['start_lon'], row['start_lat']], 
        'ziel': [row['ziel_lon'], row['ziel_lat']]
    }

# Construcție hartă
fig = go.Figure()
fig.add_trace(go.Scattermapbox(lat=df['start_lat'], lon=df['start_lon'], mode='markers', marker={'size': 14, 'color': 'black'}, name='Start'))
fig.add_trace(go.Scattermapbox(lat=df['ziel_lat'], lon=df['ziel_lon'], mode='markers', marker={'size': 12, 'color': 'red'}, name='Destinatie'))

fig.update_layout(mapbox={'style': "carto-positron", 'center': {'lat': 46, 'lon': 25}, 'zoom': 6}, margin={'l': 0, 'r': 0, 'b': 0, 't': 0})

html_content = fig.to_html(full_html=True, include_plotlyjs='cdn')

# Injectăm datele pentru interactivitate
script_inject = f"<script>var coords = {json.dumps(locations_data)};</script>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content.replace('</body>', script_inject + '</body>'))
