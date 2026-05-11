import pandas as pd
import plotly.graph_objects as go
import json

# 1. Incarcare date din Google Sheets
URL_SHEETS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnlLZB2PnX1qXG80tK5TiHakYMd_Xdq_BrOd-PgsTNj7LYDbS83rD5TLATZl9_HsWNvD2cqReQnjQt/pub?output=csv"

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
df.columns = df.columns.str.strip()

df['start_lon'], df['start_lat'] = zip(*df['Coord_Start'].apply(parse_coords))
df['ziel_lon'], df['ziel_lat'] = zip(*df['Coord_Ziel'].apply(parse_coords))
df = df.dropna(subset=['start_lon', 'start_lat', 'ziel_lon', 'ziel_lat'])

locations_data = {}
for i, row in df.iterrows():
    idx_str = str(i)
    locations_data[idx_str] = {
        'id_afisat': str(row['#ID']),
        'pret': str(row['Listen Preis']),
        'ag': str(row['Auftraggeber (AG)']).replace('\n', ' '),
        'startort': str(row['Startort']).replace('\n', '<br>'),
        'zielort': str(row['Zielort']).replace('\n', '<br>'),
        'abholzeit': str(row['Abholzeit']),
        'livrare': str(row['Ankunftszeit']),
        'start': [row['start_lon'], row['start_lat']], 
        'ziel': [row['ziel_lon'], row['ziel_lat']]
    }

# --- Hartă ---
fig = go.Figure()
fig.add_trace(go.Scattermapbox(mode="markers", lon=df['start_lon'], lat=df['start_lat'], marker={'size': 10, 'color': 'black'}, customdata=df.index))
fig.add_trace(go.Scattermapbox(mode="markers", lon=df['ziel_lon'], lat=df['ziel_lat'], marker={'size': 8, 'color': 'red'}, customdata=df.index))

fig.update_layout(
    mapbox={'style': "carto-positron", 'center': {'lon': 10.45, 'lat': 51.16}, 'zoom': 6},
    margin={'l': 0, 'r': 0, 'b': 0, 't': 0}, clickmode='event', showlegend=False
)

html_content = fig.to_html(include_plotlyjs=True, full_html=True, config={'scrollZoom': True, 'responsive': True, 'displayModeBar': False})
json_coords = json.dumps(locations_data)

script_inject = f"""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<style>
    /* STIL LUPA CAUTARE */
    #search-container {{
        position: fixed; top: 10px; left: 10px; z-index: 999999;
        display: flex; gap: 5px; background: white; padding: 5px;
        border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }}
    #search-input {{ padding: 8px; border: 1px solid #ccc; border-radius: 4px; width: 130px; font-size: 14px; }}
    
    /* STIL PANEL DETALII */
    #custom-route-panel {{
        display: none; position: fixed; bottom: 5px; left: 5px; right: 5px;
        background: white; border: 1px solid #ccc; border-radius: 8px;
        padding: 8px; z-index: 999999; font-family: sans-serif;
    }}
    .panel-header {{ display: flex; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
    .mob-btn {{ cursor: pointer; padding: 6px 10px; background: #2c3e50; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 11px; }}
    .delete-mob {{ background: #ff4d4d !important; margin-left: auto; }}
    .close-btn {{ color: #999; font-size: 22px; font-weight: bold; cursor: pointer; margin-left: 10px; }}
</style>

<div id="search-container">
    <input type="number" id="search-input" placeholder="ID Cursă...">
    <button class="mob-btn" onclick="searchByID()">🔍</button>
</div>

<div id="custom-route-panel">
    <div class="panel-header">
        <button class="mob-btn" style="background:#e67e22" onclick="undoLastLine()">UNDO</button>
        <button class="mob-btn" style="background:#d9534f; margin-left:10px;" onclick="clearAllLines()">CLEAR</button>
        <button class="mob-btn delete-mob" onclick="askDelete()">DELETE</button>
        <span class="close-btn" onclick="closePanel()">×</span>
    </div>
    <div id="panel-content" style="margin:8px 0; font-size:13px;"></div>
    <div style="display:flex; justify-content: space-between;">
        <button class="mob-btn" onclick="prevRoute()">PREV</button>
        <span id="panel-counter" style="font-weight:bold"></span>
        <button class="mob-btn" onclick="nextRoute()">NEXT</button>
    </div>
</div>

<script>
    var coords = {json_coords};
    var deletedIds = JSON.parse(localStorage.getItem('deletedRoutes') || '[]');
    var plot, currentGroup = [], currentIndex = 0, lineTraces = [];

    window.onload = function() {{
        plot = document.getElementsByClassName('plotly-graph-div')[0];

        window.searchByID = function() {{
            var val = document.getElementById('search-input').value.trim();
            for (var key in coords) {{
                if (coords[key].id_afisat === val) {{
                    currentGroup = [key]; currentIndex = 0;
                    document.getElementById('custom-route-panel').style.display = 'block';
                    updatePanel();
                    Plotly.relayout(plot, {{
                        'mapbox.center.lon': coords[key].start[0],
                        'mapbox.center.lat': coords[key].start[1],
                        'mapbox.zoom': 10
                    }});
                    return;
                }}
            }}
            alert("ID negăsit!");
        }};

        window.drawLine = function() {{
            var id = currentGroup[currentIndex];
            if (deletedIds.includes(id)) return;
            var r = coords[id];
            var newLine = {{
                type: 'scattermapbox', mode: 'lines+markers',
                lon: [r.start[0], r.ziel[0]], lat: [r.start[1], r.ziel[1]],
                line: {{width: 3, color: '#00cc44'}}, marker: {{size: 6, color: '#00cc44'}},
                hoverinfo: 'none', showlegend: false
            }};
            Plotly.addTraces(plot, newLine);
            lineTraces.push(plot.data.length - 1);
        }};

        window.askDelete = function() {{
            var id = currentGroup[currentIndex];
            if(confirm("Ștergi vizual " + coords[id].id_afisat + "?")) {{
                deletedIds.push(id);
                localStorage.setItem('deletedRoutes', JSON.stringify(deletedIds));
                undoLastLine();
                nextRoute();
            }}
        }};

        window.updatePanel = function() {{
            var id = currentGroup[currentIndex];
            var r = coords[id];
            document.getElementById('panel-content').innerHTML = 
                "<b>ID:</b> " + r.id_afisat + " | <b>Preț:</b> " + r.pret + "<br>" +
                "<b>AG:</b> " + r.ag + "<br><b>Start:</b> " + r.startort + "<br><b>Dest:</b> " + r.zielort;
            drawLine();
        }};

        window.undoLastLine = function() {{ if(lineTraces.length > 0) {{ var last = lineTraces.pop(); Plotly.deleteTraces(plot, last); }} }};
        window.clearAllLines = function() {{ while(plot.data.length > 2) {{ Plotly.deleteTraces(plot, plot.data.length - 1); }} lineTraces = []; }};
        window.nextRoute = function() {{ currentIndex = (currentIndex + 1) % currentGroup.length; updatePanel(); }};
        window.prevRoute = function() {{ currentIndex = (currentIndex - 1 + currentGroup.length) % currentGroup.length; updatePanel(); }};
        window.closePanel = function() {{ document.getElementById('custom-route-panel').style.display='none'; }};

        plot.on('plotly_click', function(data){{
            currentGroup = data.points[0].customdata; currentIndex = 0;
            document.getElementById('custom-route-panel').style.display = 'block';
            updatePanel();
        }});
    }};
</script>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content.replace('</body>', script_inject + '</body>'))
