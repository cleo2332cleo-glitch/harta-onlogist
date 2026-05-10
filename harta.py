import pandas as pd
import plotly.graph_objects as go
import json

# 1. Incarcare date din Google Sheets
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

# Verificare coloane coordonate
df['start_lon'], df['start_lat'] = zip(*df['Coord_Start'].apply(parse_coords))
df['ziel_lon'], df['ziel_lat'] = zip(*df['Coord_Ziel'].apply(parse_coords))
df = df.dropna(subset=['start_lon', 'start_lat', 'ziel_lon', 'ziel_lat'])

# Dicționarul tău
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

# --- GRUPARE (Codul tău) ---
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
fig.add_trace(go.Scattermapbox(
    mode="markers", lon=s_lons, lat=s_lats,
    marker={'size': 14, 'color': 'black'},
    text=s_texts, hoverinfo='text', customdata=s_ids
))
fig.add_trace(go.Scattermapbox(
    mode="markers", lon=z_lons, lat=z_lats,
    marker={'size': 12, 'color': 'red'},
    text=z_texts, hoverinfo='text', customdata=z_ids
))

fig.update_layout(
    mapbox={'style': "carto-positron", 'center': {'lon': 10, 'lat': 51}, 'zoom': 5},
    margin={'l': 0, 'r': 0, 'b': 0, 't': 0}, clickmode='event'
)

# AICI E CHEIA: Fortam Plotly sa incarce scriptul de baza
html_content = fig.to_html(include_plotlyjs=True, full_html=True)
json_coords = json.dumps(locations_data)

# Injectam stilul si panoul tau
script_inject = f"""
<style>
    #custom-route-panel {{
        display: none; position: absolute; top: 10px; right: 10px; width: 300px;
        background: white; border: 2px solid #2c3e50; border-radius: 8px;
        padding: 10px; z-index: 99999; box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
    }}
    .panel-btn {{ cursor: pointer; padding: 5px; background: #2c3e50; color: white; border: none; }}
</style>
<div id="custom-route-panel">
    <span style="float:right; cursor:pointer;" onclick="closePanel()">✖</span>
    <button class="panel-btn" onclick="undoLastLine()">UNDO</button>
    <div id="panel-content" style="margin-top:10px;"></div>
    <div style="margin-top:10px;">
        <button class="panel-btn" onclick="prevRoute()">PREV</button>
        <span id="panel-counter"></span>
        <button class="panel-btn" onclick="nextRoute()">NEXT</button>
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
            Plotly.addTraces(plot, {{
                type: 'scattermapbox', mode: 'lines+markers',
                lon: [r.start[0], r.ziel[0]], lat: [r.start[1], r.ziel[1]],
                line: {{width: 4, color: '#00cc44'}}, marker: {{size: 8, color: '#00cc44'}}
            }});
            lineTraces.push(plot.data.length - 1);
        }};

        window.undoLastLine = function() {{
            if(lineTraces.length > 0) {{
                var last = lineTraces.pop();
                Plotly.deleteTraces(plot, last);
            }}
        }};

        window.updatePanel = function() {{
            var id = currentGroup[currentIndex];
            var r = coords[id];
            document.getElementById('panel-content').innerHTML = "<b>ID:</b> "+r.id_afisat+"<br><b>Pret:</b> "+r.pret+"<br><b>De la:</b> "+r.startort;
            document.getElementById('panel-counter').innerText = (currentIndex+1)+"/"+currentGroup.length;
            drawLine();
        }};

        window.nextRoute = function() {{ if(currentIndex < currentGroup.length-1) {{currentIndex++; updatePanel();}} }};
        window.prevRoute = function() {{ if(currentIndex > 0) {{currentIndex--; updatePanel();}} }};
        window.closePanel = function() {{ document.getElementById('custom-route-panel').style.display='none'; }};

        plot.on('plotly_click', function(data){{
            var ids = data.points[0].customdata;
            if(ids) {{
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
