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
        'km': str(row['Entfernung']).replace('\n', ' '),
        'ag': str(row['Auftraggeber (AG)']).replace('\n', ' '),
        'startort': str(row['Startort']).replace('\n', '<br>'),
        'zielort': str(row['Zielort']).replace('\n', '<br>'),
        'abholzeit': str(row['Abholzeit']),
        'livrare': str(row['Ankunftszeit']),
        'start': [row['start_lon'], row['start_lat']], 
        'ziel': [row['ziel_lon'], row['ziel_lat']]
    }

# --- GRUPARE PUNCTE PE HARTA ---
grouped_starts = df.groupby(['start_lat', 'start_lon'])
s_lons, s_lats, s_texts, s_ids = [], [], [], []
for (lat, lon), group in grouped_starts:
    loc_name = str(group.iloc[0]['Startort']).split(',')[0]
    s_lons.append(lon)
    s_lats.append(lat)
    s_texts.append(f"<b>{loc_name}</b>")
    s_ids.append(list(map(str, group.index.tolist())))

grouped_ziels = df.groupby(['ziel_lat', 'ziel_lon'])
z_lons, z_lats, z_texts, z_ids = [], [], [], []
for (lat, lon), group in grouped_ziels:
    loc_name = str(group.iloc[0]['Zielort']).split(',')[0]
    z_lons.append(lon)
    z_lats.append(lat)
    z_texts.append(f"<b>{loc_name}</b>")
    z_ids.append(list(map(str, group.index.tolist())))

fig = go.Figure()
fig.add_trace(go.Scattermapbox(mode="markers", lon=s_lons, lat=s_lats, marker={'size': 10, 'color': 'black', 'opacity': 0.8}, text=s_texts, hoverinfo='text', customdata=s_ids))
fig.add_trace(go.Scattermapbox(mode="markers", lon=z_lons, lat=z_lats, marker={'size': 8, 'color': 'red', 'opacity': 0.7}, text=z_texts, hoverinfo='text', customdata=z_ids))

fig.update_layout(
    mapbox={'style': "carto-positron", 'center': {'lon': 10.45, 'lat': 51.16}, 'zoom': 6},
    margin={'l': 0, 'r': 0, 'b': 0, 't': 0}, clickmode='event', showlegend=False
)

html_content = fig.to_html(include_plotlyjs=True, full_html=True, config={'scrollZoom': True, 'responsive': True, 'displayModeBar': False})
json_coords = json.dumps(locations_data)

script_inject = f"""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<style>
    #search-box {{
        position: fixed; top: 10px; left: 10px; z-index: 999999;
        background: white; padding: 8px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        display: flex; gap: 5px;
    }}
    #search-input {{ padding: 6px; border: 1px solid #ccc; border-radius: 4px; width: 120px; font-size: 14px; }}
    #custom-route-panel {{
        display: none; position: fixed; bottom: 5px; left: 5px; right: 5px;
        background: white; border: 1px solid #ccc; border-radius: 8px;
        padding: 8px; z-index: 999999; box-shadow: 0px 2px 10px rgba(0,0,0,0.2);
        font-family: sans-serif;
    }}
    .panel-header {{ display: flex; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
    .mob-btn {{ cursor: pointer; padding: 6px 10px; background: #2c3e50; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 11px; }}
    .undo-mob {{ background: #e67e22 !important; }}
    .clear-mob {{ background: #d9534f !important; margin-left: 15px; }}
    .delete-mob {{ background: #ff4d4d !important; margin-left: auto; }}
    .close-btn {{ color: #999; font-size: 22px; font-weight: bold; cursor: pointer; margin-left: 10px; }}
    #panel-content {{ margin: 8px 0; font-size: 13px; line-height: 1.3; color: #333; }}
    .highlight-id {{ color: #00cc44; font-weight: bold; }}
    .highlight-km {{ color: #e67e22; font-weight: bold; }}
    .panel-footer {{ display: flex; justify-content: space-between; align-items: center; }}
</style>

<div id="search-box">
    <input type="number" id="search-input" placeholder="ID Cursă...">
    <button class="mob-btn" onclick="searchByID()">🔍</button>
</div>

<div id="custom-route-panel">
    <div class="panel-header">
        <button class="mob-btn undo-mob" onclick="undoLastLine()">UNDO</button>
        <button class="mob-btn clear-mob" onclick="clearAllLines()">CLEAR</button>
        <button class="mob-btn delete-mob" onclick="askDelete()">DELETE</button>
        <span class="close-btn" onclick="closePanel()">×</span>
    </div>
    <div id="panel-content"></div>
    <div class="panel-footer">
        <button class="mob-btn" onclick="prevRoute()">PREV</button>
        <span id="panel-counter" style="font-size: 12px; font-weight: bold;"></span>
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
                    Plotly.relayout(plot, {{ 'mapbox.center.lon': coords[key].start[0], 'mapbox.center.lat': coords[key].start[1], 'mapbox.zoom': 9 }});
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
            if(confirm("Ștergi vizual cursa " + coords[id].id_afisat + "?")) {{
                deletedIds.push(id);
                localStorage.setItem('deletedRoutes', JSON.stringify(deletedIds));
                undoLastLine();
                nextRoute();
            }}
        }};

        window.undoLastLine = function() {{
            if(lineTraces.length > 0) {{
                var last = lineTraces.pop();
                Plotly.deleteTraces(plot, last);
                lineTraces = lineTraces.map(idx => idx > last ? idx - 1 : idx);
            }}
        }};

        window.clearAllLines = function() {{
            if(lineTraces.length > 0) {{ Plotly.deleteTraces(plot, lineTraces); lineTraces = []; }}
        }};

        window.updatePanel = function() {{
            var id = currentGroup[currentIndex];
            var r = coords[id];
            document.getElementById('panel-content').innerHTML = 
                "<b>ID:</b> <span class='highlight-id'>" + r.id_afisat + "</span> | <span class='highlight-km'>" + r.km + "</span><br>" +
                "<b>AG:</b> " + r.ag + "<br><b>Pick-up:</b> " + r.abholzeit + "<br>" +
                "<b>Start:</b> " + r.startort + "<br><b>Dest:</b> " + r.zielort;
            
            let activeInGroup = currentGroup.filter(idx => !deletedIds.includes(idx));
            document.getElementById('panel-counter').innerText = (activeInGroup.indexOf(id) + 1) + "/" + activeInGroup.length;
            drawLine();
        }};

        window.nextRoute = function() {{ currentIndex = (currentIndex + 1) % currentGroup.length; updatePanel(); }};
        window.prevRoute = function() {{ currentIndex = (currentIndex - 1 + currentGroup.length) % currentGroup.length; updatePanel(); }};
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
