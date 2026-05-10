import pandas as pd
import plotly.graph_objects as go
import json

# 1. Incarcare date din Google Sheets
URL_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQGWQb5ZLpLGDwl6mjeNAfzhUrl3GShXab_ePVSU8tj-9aOAwStGMjEutsErHnezkOpIaGA4maO_HYU/pub?output=csv"

def parse_coords(coord_str):
    try:
        coord_str = str(coord_str).strip()
        if "," in coord_str:
            parts = coord_str.split(',')
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
        else:
            parts = coord_str.split()
            lon, lat = float(parts[0].strip()), float(parts[1].strip())
        return lon, lat
    except:
        return None, None

df = pd.read_csv(URL_SHEETS)

# Verificăm coloanele Coord_Start și Coord_Ziel
df['start_lon'], df['start_lat'] = zip(*df['Coord_Start'].apply(parse_coords))
df['ziel_lon'], df['ziel_lat'] = zip(*df['Coord_Ziel'].apply(parse_coords))
df = df.dropna(subset=['start_lon', 'start_lat', 'ziel_lon', 'ziel_lat'])

# Dicționarul tău (PĂSTRAT EXACT)
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

# --- GRUPARE ---
grouped_starts = df.groupby(['start_lat', 'start_lon'])
s_lons, s_lats, s_texts, s_ids = [], [], [], []
for (lat, lon), group in grouped_starts:
    loc_name = str(group.iloc[0]['Startort']).split(',')[0]
    s_lons.append(lon)
    s_lats.append(lat)
    s_texts.append(f"<b>Punct Start: {loc_name}</b><br>Curse: {len(group)}")
    s_ids.append(list(map(str, group.index.tolist())))

grouped_ziels = df.groupby(['ziel_lat', 'ziel_lon'])
z_lons, z_lats, z_texts, z_ids = [], [], [], []
for (lat, lon), group in grouped_ziels:
    loc_name = str(group.iloc[0]['Zielort']).split(',')[0]
    z_lons.append(lon)
    z_lats.append(lat)
    z_texts.append(f"<b>Destinatie: {loc_name}</b><br>Curse: {len(group)}")
    z_ids.append(list(map(str, group.index.tolist())))

fig = go.Figure()
# AM MICȘORAT BULINELE (Negru la 22, Roșu la 18)
fig.add_trace(go.Scattermapbox(
    mode="markers", lon=s_lons, lat=s_lats,
    marker={'size': 22, 'color': 'black', 'opacity': 0.85},
    text=s_texts, hoverinfo='text', customdata=s_ids
))
fig.add_trace(go.Scattermapbox(
    mode="markers", lon=z_lons, lat=z_lats,
    marker={'size': 18, 'color': 'red', 'opacity': 0.75},
    text=z_texts, hoverinfo='text', customdata=z_ids
))

fig.update_layout(
    mapbox={'style': "carto-positron", 'center': {'lon': 10.45, 'lat': 51.16}, 'zoom': 6},
    margin={'l': 0, 'r': 0, 'b': 0, 't': 0}, clickmode='event'
)

# Viewport și config păstrate
html_content = fig.to_html(include_plotlyjs=True, full_html=True, config={'scrollZoom': True, 'responsive': True})
json_coords = json.dumps(locations_data)

# CSS Radical - Versiunea MICȘORATĂ
script_inject = f"""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
<style>
    /* Panoul tip "Bottom Sheet" MICȘORAT */
    #custom-route-panel {{
        display: none; position: fixed; 
        bottom: 0; left: 2.5%; /* Mai aproape de margini */
        width: 95%; max-width: 420px; /* Panou mai ingust */
        background: white; border-top: 3px solid #2c3e50; border-radius: 15px 15px 0 0; /* Mai putin rotunjit */
        padding: 12px; /* Mai putin padding */
        z-index: 999999; box-shadow: 0px -8px 25px rgba(0,0,0,0.4);
        font-family: 'Segoe UI', system-ui, sans-serif;
        box-sizing: border-box;
    }}
    /* Header MICȘORAT */
    .panel-header-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #eee; }}
    
    /* BUTOANE MAI MICI PENTRU MOBILE */
    .mob-btn {{ 
        cursor: pointer; 
        padding: 12px 18px; /* Padding mai mic (era 16x24) */
        background: #2c3e50; color: white; border: none; 
        border-radius: 8px; font-weight: bold; 
        font-size: 14px; /* Font mai mic (era 16) */
        min-width: 70px; text-align: center;
    }}
    .close-btn {{ color: red; font-size: 28px; font-weight: bold; cursor: pointer; padding: 0 8px; }}
    
    /* Text MICȘORAT pentru detalii */
    #panel-content {{ 
        margin: 15px 0; font-size: 15px; /* Font mai mic (era 17) */
        line-height: 1.5; color: #111; 
    }}
    #panel-content b {{ font-weight: 700; color: #444; }}
    .highlight-id {{ color: #00cc44; font-weight: 900; font-size: 1.05em; }}
    .undo-mob {{ background: #e67e22 !important; }}
    
    /* Footer MICȘORAT */
    .panel-footer-row {{ display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }}
</style>

<div id="custom-route-panel">
    <div class="panel-header-row">
        <button class="mob-btn undo-mob" onclick="undoLastLine()">UNDO LINE</button>
        <span class="close-btn" onclick="closePanel()">✖</span>
    </div>
    <div id="panel-content"></div>
    <div class="panel-footer-row">
        <button class="mob-btn" onclick="prevRoute()">PREV</button>
        <strong id="panel-counter" style="font-size: 16px;"></strong>
        <button class="mob-btn" onclick="nextRoute()">NEXT</button>
    </div>
</div>

<script>
    var coords = {json_coords};
    
    window.onload = function() {{
        var plot = document.getElementsByClassName('plotly-graph-div')[0];
        var currentGroup = [];
        var currentIndex = 0;
        var lineTraces = [];

        window.drawLine = function() {{
            var id = currentGroup[currentIndex];
            var r = coords[id];
            // Linii puțin mai subțiri și markere de linie mai mici
            var newLine = {{
                type: 'scattermapbox', mode: 'lines+markers',
                lon: [r.start[0], r.ziel[0]], lat: [r.start[1], r.ziel[1]],
                line: {{width: 5, color: '#00cc44'}}, marker: {{size: 10, color: '#00cc44'}},
                hoverinfo: 'none'
            }};
            Plotly.addTraces(plot, newLine);
            lineTraces.push(plot.data.length - 1);
        }};

        window.undoLastLine = function() {{
            if(lineTraces.length > 0) {{
                var last = lineTraces.pop();
                Plotly.deleteTraces(plot, last);
                lineTraces = lineTraces.map(idx => idx > last ? idx - 1 : idx);
            }}
        }};

        window.updatePanel = function() {{
            var id = currentGroup[currentIndex];
            var r = coords[id];
            document.getElementById('panel-content').innerHTML = 
                "<b>ID:</b> <span class='highlight-id'>" + r.id_afisat + "</span><br>" +
                "<b>AG:</b> " + r.ag + "<br>" + 
                "<b>De la:</b> " + r.startort + "<br>" +
                "<b>Către:</b> " + r.zielort + "<br>" +
                "<b>Preț:</b> <b>" + r.pret + "</b><br>" +
                "<b>Livrare:</b> " + r.livrare;
            document.getElementById('panel-counter').innerText = (currentIndex + 1) + " / " + currentGroup.length;
            drawLine();
        }};

        window.nextRoute = function() {{ if(currentIndex < currentGroup.length-1) {{currentIndex++; updatePanel();}} }};
        window.prevRoute = function() {{ if(currentIndex > 0) {{currentIndex--; updatePanel();}} }};
        window.closePanel = function() {{ document.getElementById('custom-route-panel').style.display='none'; }};

        plot.on('plotly_click', function(data){{
            var ids = data.points[0].customdata;
            if(Array.isArray(ids)) {{
                currentGroup = ids; currentIndex = 0;
                document.getElementById('custom-route-panel').style.display = 'block';
                updatePanel();
            }}
        }});
    }};
</script>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content.replace('</body>', script_inject + '</body>'))
