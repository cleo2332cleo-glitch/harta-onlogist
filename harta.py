import pandas as pd
import plotly.graph_objects as go
import json

# Link-ul tău de Google Sheets
URL_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGWQb5ZLpLGDwl6mjeNAfzhUrl3GShXab_ePVSU8tj-9aOAwStGMjEutsErHnezkOpIaGA4maO_HYU/pub?output=csv"

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

df = pd.read_csv(URL_SHEETS)
df['start_lon'], df['start_lat'] = zip(*df['Coord_Start'].apply(parse_coords))
df['ziel_lon'], df['ziel_lat'] = zip(*df['Coord_Ziel'].apply(parse_coords))
df = df.dropna(subset=['start_lon', 'start_lat', 'ziel_lon', 'ziel_lat'])

locations_data = {}
for i, row in df.iterrows():
    locations_data[str(i)] = {
        'id_afisat': str(row['#ID']),
        'pret': str(row['Listen Preis']),
        'ag': str(row['Auftraggeber (AG)']).replace('\n', ' '),
        'startort': str(row['Startort']).replace('\n', '<br>'),
        'zielort': str(row['Zielort']).replace('\n', '<br>'),
        'livrare': str(row['Ankunftszeit']),
        'start': [row['start_lon'], row['start_lat']], 
        'ziel': [row['ziel_lon'], row['ziel_lat']]
    }

# Construcție hartă Plotly (Codul tău de grafică)
fig = go.Figure()
fig.add_trace(go.Scattermapbox(mode="markers", lon=df['start_lon'], lat=df['start_lat'], marker={'size': 14, 'color': 'black'}, customdata=list(map(str, df.index)), name="Start"))
fig.add_trace(go.Scattermapbox(mode="markers", lon=df['ziel_lon'], lat=df['ziel_lat'], marker={'size': 12, 'color': 'red'}, customdata=list(map(str, df.index)), name="Ziel"))

fig.update_layout(mapbox={'style': "carto-positron", 'center': {'lon': 10.45, 'lat': 51.16}, 'zoom': 6}, margin={'l': 0, 'r': 0, 'b': 0, 't': 0})

html_content = fig.to_html(include_plotlyjs='cdn', full_html=True)

# Aici injectăm scriptul tău de detaliu și UNDO
script_inject = f"<script>var coords = {json.dumps(locations_data)}; /* restul logicii tale */ </script>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content.replace('</body>', script_inject + '</body>'))
