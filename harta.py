import pandas as pd
import plotly.graph_objects as go
import json

# --- LINK-UL TĂU GOOGLE SHEETS ---
URL_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGWQb5ZLpLGDwl6mjeNAfzhUrl3GShXab_ePVSU8tj-9aOAwStGMjEutsErHnezkOpIaGA4maO_HYU/pub?output=csv"

# 1. Incarcare date (acum din Link)
df = pd.read_csv(URL_SHEETS)

def parse_coords(coord_str):
    try:
        # Curățăm string-ul în caz că are spații sau caractere ciudate de la importul CSV
        coord_str = str(coord_str).strip()
        if "," in coord_str:
            lat, lon = map(float, coord_str.split(','))
        else:
            lon, lat = map(float, coord_str.split())
        return lon, lat
    except:
        return None, None

# Verificăm coloanele Coord_Start și Coord_Ziel din Sheets
df['start_lon'], df['start_lat'] = zip(*df['Coord_Start'].apply(parse_coords))
df['ziel_lon'], df['ziel_lat'] = zip(*df['Coord_Ziel'].apply(parse_coords))
df = df.dropna(subset=['start_lon', 'start_lat', 'ziel_lon', 'ziel_lat'])

# Dicționar centralizat
locations_data = {}
for i, row in df.iterrows():
    idx_str = str(i)
    locations_data[idx_str] = {
        'id_afisat': str(row['#ID']),
        'pret': str(row['Listen Preis']),
        'ag': str(row['Auftraggeber (AG)']).replace('\n', ' '),
        'startort': str(row['Startort']).replace('\n', '<br>'),
        'zielort': str(row['Zielort']).replace('\n', '<br>'),
        'livrare': str(row['Ankunftszeit']),
        'start': [row['start_lon'], row['start_lat']], 
        'ziel': [row['ziel_lon'], row['ziel_lat']]
    }

# --- GRUPARE START ---
grouped_starts = df.groupby(['start_lat', 'start_lon'])
s_lons, s_lats, s_texts, s_ids = [], [], [], []
for (lat, lon), group in grouped_starts:
    loc_name = str(group.iloc[0]['Startort']).split(',')[0]
    s_lons.append(lon)
    s_lats.append(lat)
    s_texts.append(f"<b>Punct Start: {loc_name}</b><br>Curse care pleacă de aici: {len(group)}")
    s_ids.append(list(map(str, group.index.tolist())))

# --- GRUPARE ZIEL ---
grouped_ziels = df.groupby(['ziel_lat', 'ziel_lon'])
z_lons, z_lats, z_texts, z_ids = [], [], [], []
for (lat, lon), group in grouped_ziels:
    loc_name = str(group.iloc[0]['Zielort']).split(',')[0]
    z_lons.append(lon)
    z_lats.append(lat)
    z_texts.append(f"<b>Punct Destinație: {loc_name}</b><br>Curse care sosesc aici: {len(group)}")
    z_ids.append(list(map(str, group.index.tolist())))

fig = go.Figure()
fig.add_trace(go.Scattermapbox(
    mode="markers", lon=s_lons, lat=s_lats,
    marker={'size': 14, 'color': 'black', 'opacity': 0.9},
    text=s_texts, hoverinfo='text', customdata=s_ids, name="Locații Start"
))
fig.add_trace(go.Scattermapbox(
    mode="markers", lon=z_lons, lat=z_lats,
    marker={'size': 12, 'color': 'red', 'opacity': 0.8},
    text=z_texts, hoverinfo='text', customdata=z_ids, name="Locații Destinație"
))

fig.update_layout(
    mapbox={'style': "carto-positron", 'center': {'lon': 10.45, 'lat': 51.16}, 'zoom': 6},
    showlegend=True, margin={'l': 0, 'r': 0, 'b': 0, 't': 0}, clickmode='event'
)

# Schimbat numele fișierului în index.html pentru ca GitHub să îl poată afișa pe link
html_content = fig.to_html(include_plotlyjs='cdn', full_html=True, config={'scrollZoom': True})
json_coords = json.dumps(locations_data)

script_inject = f"""
<style>
    #custom-route-panel {{
        display: none; position: absolute; top: 20px; right: 20px; width: 340px;
        background: white; border: 2px solid #2c3e50; border-radius: 8px;
        padding: 15px; z-index: 10000; box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    .panel-header {{ font-weight: bold; font-size: 14px; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
    .panel-body {{ font-size: 13px; line-height: 1.5; color: #444; }}
    .panel-footer {{ display: flex; justify-content: space-between; align-items: center; margin-top: 15px; }}
    .panel-btn {{ cursor: pointer; padding: 5px 12px; background: #2c3e50; color: white; border: none; border-radius: 4px; }}
    .panel-btn:disabled {{ background: #ccc; }}
    .undo-btn {{ background: #e67e22 !important; margin-right: 5px; }}
    .close-btn {{ float: right; cursor: pointer; font-weight: bold; color: #e74c3c; margin-left: 10px; }}
    .highlight {{ color: #00cc44; font-weight: bold; }}
    .ag-style {{ color: #2980b9; font-weight: bold; }}
</style>

<div id="custom-route-panel">
    <span class="close-btn" onclick="closePanel()">✖</span>
    <button class="panel-btn undo-btn" style="float:right; font-size:10px;" onclick="undoLastLine()">UNDO LINE</button>
    <div class="panel-header" id="panel-title">Detalii Locație</div>
    <div class="panel-body" id="panel-content"></div>
    <div class="panel-footer">
        <button class="panel-btn" id="btn-prev" onclick="prevRoute()">&#8592; Prev</button>
        <strong id="panel-counter">1/1</strong>
        <button class="panel-btn" id="btn-next" onclick="nextRoute()">Next &#8594;</button>
    </div>
</div>

<script>
    var coords = {json_coords};
    var plot = document.getElementsByClassName('plotly-graph-div')[0];
    var currentGroup = [];
    var currentIndex = 0;
    var lineTraces = []; 

    function drawLine() {{
        var id_cursa = currentGroup[currentIndex];
        var route = coords[id_cursa];

        var newLine = {{
            type: 'scattermapbox', mode: 'lines+markers',
            lon: [route.start[0], route.ziel[0]], lat: [route.start[1], route.ziel[1]],
            line: {{width: 4, color: '#00cc44'}},
            marker: {{size: 8, color: '#00cc44'}},
            hoverinfo: 'none',
            name: 'Ruta ' + route.id_afisat
        }};
        
        Plotly.addTraces(plot, newLine);
        lineTraces.push(plot.data.length - 1);
    }}

    function undoLastLine() {{
        if(lineTraces.length > 0) {{
            var lastIdx = lineTraces.pop();
            Plotly.deleteTraces(plot, lastIdx);
            lineTraces = lineTraces.map(idx => idx > lastIdx ? idx - 1 : idx);
        }}
    }}

    function updatePanel() {{
        var id_cursa = currentGroup[currentIndex];
        var route = coords[id_cursa];
        
        document.getElementById('panel-content').innerHTML = 
            "<b>ID Cursă:</b> <span class='highlight'>" + route.id_afisat + "</span><br>" +
            "<b>AG:</b> <span class='ag-style'>" + route.ag + "</span><br>" + 
            "<b>De la:</b> " + route.startort + "<br>" +
            "<b>Către:</b> " + route.zielort + "<br>" +
            "<b>Preț:</b> " + route.pret + "<br>" +
            "<b>Livrare:</b> " + route.livrare;

        document.getElementById('panel-counter').innerText = (currentIndex + 1) + " / " + currentGroup.length;
        document.getElementById('btn-prev').disabled = (currentIndex === 0);
        document.getElementById('btn-next').disabled = (currentIndex === currentGroup.length - 1);
        
        drawLine();
    }}

    function nextRoute() {{ if(currentIndex < currentGroup.length - 1) {{ currentIndex++; updatePanel(); }} }}
    function prevRoute() {{ if(currentIndex > 0) {{ currentIndex--; updatePanel(); }} }}
    
    function closePanel() {{ 
        document.getElementById('custom-route-panel').style.display = 'none'; 
    }}

    plot.on('plotly_click', function(data){{
        var ids = data.points[0].customdata;
        if (Array.isArray(ids)) {{
            currentGroup = ids;
            currentIndex = 0;
            document.getElementById('custom-route-panel').style.display = 'block';
            updatePanel();
        }}
    }});
</script>
"""

# GitHub Pages are nevoie de index.html
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content.replace('</body>', script_inject + '</body>'))

print("Succes! Harta cu sistemul tau de UNDE si trasee a fost generata.")
