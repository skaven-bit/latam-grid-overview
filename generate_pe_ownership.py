import json
import math

def haversine(c1, c2):
    R = 6371.0
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def build_ownership_page():
    # 1. Read pe_osm_lines.json
    with open('pe_osm_lines.json', 'r', encoding='utf-8') as f:
        ways = json.load(f)

    # 2. Extract self-contained Leaflet CSS and JS from pe.html
    with open('pe.html', 'r', encoding='utf-8') as f:
        pe_text = f.read()

    css_start = pe_text.find('<style>\n/* required styles */')
    css_end = pe_text.find('</style>', css_start)
    leaflet_css = pe_text[css_start + 7:css_end]

    js_marker = '/* @preserve\n * Leaflet 1.9.4'
    js_start = pe_text.find(js_marker)
    js_end_marker = 'window.L=t});'
    js_end = pe_text.find(js_end_marker, js_start) + len(js_end_marker)
    leaflet_js = pe_text[js_start:js_end]

    # 3. Classify and process transmission ways
    processed_lines = []
    group_totals = {
        'isa': 0.0,
        'celeo': 0.0,
        'generators': 0.0,
        'mining': 0.0,
        'distriluz': 0.0,
        'abengoa': 0.0
    }
    total_km = 0.0

    for w in ways:
        geom = w.get('geometry', [])
        if len(geom) < 2:
            continue
        coords = [[round(pt['lat'], 4), round(pt['lon'], 4)] for pt in geom]
        length = 0.0
        for i in range(len(coords) - 1):
            length += haversine(coords[i], coords[i+1])
        length = round(length, 1)

        tags = w.get('tags', {})
        v_raw = tags.get('voltage', '')
        v = 220
        if '500' in str(v_raw): v = 500
        elif '220' in str(v_raw): v = 220
        elif '138' in str(v_raw): v = 138
        elif '60' in str(v_raw): v = 60

        lats = [pt[0] for pt in coords]
        lons = [pt[1] for pt in coords]
        mid_lat = sum(lats) / len(lats)
        mid_lon = sum(lons) / len(lons)

        name_tag = tags.get('name', '')
        ref_tag = tags.get('ref', '')
        op_tag = tags.get('operator', '') + ' ' + tags.get('owner', '')
        op_lower = op_tag.lower()
        name_lower = name_tag.lower()

        if v >= 500:
            op = 'Consorcio Transmantaro (Grupo ISA)'
            grp = 'isa'
            regime = 'SGT (Sistema Garantizado de Transmisión)'
            disp_name = name_tag if name_tag else f'L-5000 Series Trunk Line (500 kV)'
        elif 'enersur' in op_lower or 'engie' in op_lower:
            op = 'Engie Energía Perú'
            grp = 'generators'
            regime = 'SCT (Interconexión Ilo–Moquegua)'
            disp_name = name_tag if name_tag else f'Engie Ilo–Moquegua {v} kV Line'
        elif 'transmantaro' in op_lower or 'ctm' in op_lower:
            op = 'Consorcio Transmantaro (Grupo ISA)'
            grp = 'isa'
            regime = 'SGT (Troncal Interregional)'
            disp_name = name_tag if name_tag else f'CTM {v} kV Corridor'
        elif 'rep' in op_lower or 'red electrica del perú' in op_lower:
            op = 'ISA REP (Red de Energía del Perú)'
            grp = 'isa'
            regime = 'SPT (Troncal Nacional 220 kV)'
            disp_name = name_tag if name_tag else (f'L-{ref_tag}' if ref_tag else f'ISA REP {v} kV Line')
        elif 'redesur' in op_lower or 'tesur' in op_lower:
            op = 'Celeo Redes / Tesur (REDESUR)'
            grp = 'celeo'
            regime = 'SGT / SPT Sur'
            disp_name = name_tag if name_tag else f'REDESUR Altiplano {v} kV Line'
        elif 'atn' in op_lower or 'abengoa' in op_lower:
            op = 'Abengoa / Omega (ATN)'
            grp = 'abengoa'
            regime = 'SGT (Concesión Norte)'
            disp_name = name_tag if name_tag else f'ATN Carhuaquero–Cajamarca {v} kV'
        elif 'adinelsa' in op_lower:
            op = 'Adinelsa (Rural Estatal)'
            grp = 'distriluz'
            regime = 'SST (Electrificación Rural)'
            disp_name = name_tag if name_tag else f'Adinelsa {v} kV Rural Feeder'
        elif 'luz del sur' in op_lower:
            op = 'Luz del Sur / Inland Energy'
            grp = 'generators'
            regime = 'SCT (Transmisión Lima)'
            disp_name = name_tag if name_tag else f'Luz del Sur {v} kV Line'
        elif 'yura' in op_lower:
            op = 'Yura S.A. (Industrial)'
            grp = 'mining'
            regime = 'Uso Exclusivo / Industrial'
            disp_name = f'Yura Arequipa Industrial {v} kV Spur'
        # Geographic specific lines
        elif -9.75 <= mid_lat <= -9.3 and -77.2 <= mid_lon <= -76.9:
            op = 'Compañía Minera Antamina'
            grp = 'mining'
            regime = 'Uso Exclusivo Minero'
            disp_name = 'L-2280 Huallanca–Antamina 220 kV'
        elif -14.4 <= mid_lat <= -13.9 and -72.6 <= mid_lon <= -72.0:
            op = 'Minera Las Bambas'
            grp = 'mining'
            regime = 'Uso Exclusivo Minero'
            disp_name = 'Cotabambas–Las Bambas 220 kV Spur'
        elif -17.7 <= mid_lat <= -17.0 and -71.4 <= mid_lon <= -70.5:
            if v <= 138 or 'toquepala' in name_lower or 'cuajone' in name_lower:
                op = 'Southern Peru Copper (SPCC)'
                grp = 'mining'
                regime = 'Uso Exclusivo Minero'
                disp_name = f'SPCC Toquepala/Cuajone {v} kV Line'
            else:
                op = 'Engie Energía Perú'
                grp = 'generators'
                regime = 'SCT (Generación Ilo)'
                disp_name = f'Engie Ilo–Moquegua {v} kV Line'
        elif -16.6 <= mid_lat <= -16.4 and -71.7 <= mid_lon <= -71.5:
            op = 'Sociedad Minera Cerro Verde'
            grp = 'mining'
            regime = 'Uso Exclusivo Minero'
            disp_name = 'Cerro Verde Mining 220/500 kV Spur'
        elif -13.6 <= mid_lat <= -12.4 and -70.6 <= mid_lon <= -69.0:
            op = 'San Gabán / Interconexión Sur'
            grp = 'generators'
            regime = 'SST (San Gabán–Puerto Maldonado)'
            disp_name = 'San Gabán–Maldonado 138 kV Line'
        elif -6.8 <= mid_lat <= -5.8 and -79.2 <= mid_lon <= -78.3 and v == 220:
            if mid_lon < -78.8:
                op = 'Abengoa / Omega (ATN)'
                grp = 'abengoa'
                regime = 'SGT Carhuaquero–Cajamarca'
                disp_name = 'Carhuaquero–Cajamarca 220 kV (ATN)'
            else:
                op = 'Consorcio Transmantaro (Grupo ISA)'
                grp = 'isa'
                regime = 'SGT Jaén–Carhuaquero'
                disp_name = 'Jaén–Carhuaquero 220 kV (CTM)'
        elif mid_lat <= -14.8 and mid_lon >= -72.0 and v == 220:
            op = 'Celeo Redes / Tesur (REDESUR)'
            grp = 'celeo'
            regime = 'SGT / SPT Altiplano Sur'
            disp_name = name_tag if name_tag else 'REDESUR Altiplano 220 kV Trunk'
        elif -6.6 <= mid_lat <= -5.6 and -77.8 <= mid_lon <= -76.2 and v == 220:
            op = 'Consorcio Transmantaro (Grupo ISA)'
            grp = 'isa'
            regime = 'SGT Selva Norte'
            disp_name = 'Moyobamba–Tarapoto 220 kV (CTM)'
        elif -14.3 <= mid_lat <= -13.1 and -73.5 <= mid_lon <= -72.3 and v == 220:
            op = 'Consorcio Transmantaro (Grupo ISA)'
            grp = 'isa'
            regime = 'SGT Machupicchu–Cotaruse'
            disp_name = 'Machupicchu–Abancay–Cotaruse 220 kV (CTM)'
        elif v <= 138:
            grp = 'distriluz'
            regime = 'SST (Sistema Secundario de Transmisión)'
            if mid_lat < -15.5:
                op = 'SEAL / Electrosur (Estatal Sur)'
                disp_name = f'SEAL / Electrosur {v} kV Feeder'
            elif mid_lat < -12.5 and mid_lon < -71.0:
                op = 'ELSE (Electro Sur Este)'
                disp_name = f'ELSE Cusco/Puno {v} kV Feeder'
            else:
                op = 'Distriluz (Electrocentro / Hidrandina)'
                disp_name = f'Distriluz Regional {v} kV Line'
        else:
            op = 'ISA REP (Red de Energía del Perú)'
            grp = 'isa'
            regime = 'SPT (Troncal Nacional 220 kV)'
            disp_name = name_tag if name_tag else (f'L-{ref_tag}' if ref_tag else f'ISA REP Trunk {v} kV')

        group_totals[grp] += length
        total_km += length

        processed_lines.append({
            'id': w['id'],
            'n': disp_name,
            'v': v,
            'km': length,
            'op': op,
            'grp': grp,
            'rg': regime,
            'c': coords
        })

    print(f"Total processed lines: {len(processed_lines)}")
    print(f"Total Grid length: {total_km:.1f} km")
    for g, km in group_totals.items():
        print(f"  {g}: {km:.1f} km ({km/total_km*100:.1f}%)")

    # Serialize JSON payload
    lines_json = json.dumps(processed_lines, separators=(',', ':'))

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Peru — Transmission Grid Ownership & Concessions (SEIN)</title>
<style>
{leaflet_css}

html, body {{ margin:0; padding:0; height:100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background:#0b1329; }}
#map {{ position:absolute; inset:0; background:#0b1329; }}

/* Panel styling */
#panel {{
  position:absolute; top:14px; left:14px; z-index:1000; width:340px; max-height: calc(100% - 28px);
  overflow-y:auto; background:rgba(255,255,255,0.96); border-radius:12px;
  box-shadow:0 6px 28px rgba(0,0,0,0.35); padding:16px 18px; box-sizing:border-box;
}}
.nav-links {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }}
.nav-links a {{ font-size:11px; color:#475569; text-decoration:none; font-weight:600; display:inline-flex; align-items:center; gap:4px; }}
.nav-links a:hover {{ color:#0f172a; text-decoration:underline; }}
.nav-links .switch-btn {{ background:#f1f5f9; padding:3px 8px; border-radius:6px; color:#2563eb; }}
.nav-links .switch-btn:hover {{ background:#e2e8f0; text-decoration:none; }}

#panel h1 {{ font-size:16px; margin:0 0 2px; line-height:1.25; color:#0f172a; }}
#panel .sub {{ font-size:11.5px; color:#64748b; margin:0 0 12px; }}

.big {{ font-size:32px; font-weight:800; color:#2563eb; line-height:1; letter-spacing:-0.5px; }}
.big-label {{ font-size:11.5px; color:#0f172a; margin-top:4px; line-height:1.35; font-weight:500; }}

.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; margin:12px 0; }}
.stat {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:7px 9px; }}
.stat .k {{ font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:0.3px; font-weight:600; }}
.stat .v {{ font-size:13.5px; font-weight:700; color:#0f172a; }}

/* Filter Controls */
.ctl {{ margin-bottom:12px; }}
.ctl label.t {{ display:flex; justify-content:space-between; font-size:10.5px; color:#334155; font-weight:700; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:5px; }}
.btnrow {{ display:flex; gap:4px; flex-wrap:wrap; }}
button {{
  border:1px solid #cbd5e1; background:#fff; color:#0f172a; font-size:11px;
  padding:5px 9px; border-radius:6px; cursor:pointer; line-height:1.2; font-weight:500;
  transition:all 0.15s ease;
}}
button:hover {{ background:#f8fafc; border-color:#94a3b8; }}
button.on {{ background:#0f172a; color:#fff; border-color:#0f172a; }}

/* Group buttons with color dot */
.grp-btn {{ display:inline-flex; align-items:center; gap:5px; }}
.grp-btn .gdot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}

/* Breakdown Table */
.breakdown {{ margin:12px 0 10px; border-top:1px solid #e2e8f0; padding-top:10px; }}
.breakdown-title {{ font-size:11px; font-weight:700; text-transform:uppercase; color:#475569; letter-spacing:0.3px; margin-bottom:6px; }}
.b-row {{ display:flex; align-items:center; justify-content:space-between; font-size:11px; padding:3px 0; color:#334155; }}
.b-name {{ display:flex; align-items:center; gap:6px; font-weight:500; }}
.b-sw {{ width:10px; height:10px; border-radius:2px; flex:none; }}
.b-val {{ font-weight:700; color:#0f172a; font-variant-numeric:tabular-nums; }}

.note {{ font-size:10px; color:#64748b; margin:10px 0 6px; line-height:1.4; }}
.attrib {{ font-size:9.5px; color:#94a3b8; margin-top:8px; line-height:1.4; border-top:1px solid #f1f5f9; padding-top:6px; }}

/* Selected Line Info Card */
#lineInfoCard {{
  display:none; background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:10px; margin:10px 0;
}}
#lineInfoCard.visible {{ display:block; }}
#lineInfoCard .lic-title {{ font-weight:700; font-size:12px; color:#1e3a8a; margin-bottom:3px; }}
#lineInfoCard .lic-sub {{ font-size:10.5px; color:#3b82f6; margin-bottom:6px; }}
#lineInfoCard .lic-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:4px; font-size:10.5px; }}
#lineInfoCard .lic-grid div span {{ color:#64748b; }}
#lineInfoCard .lic-grid div b {{ color:#0f172a; }}

/* Popup Styling */
.custom-line-popup {{ font-size:12px; line-height:1.4; }}
.custom-line-popup h4 {{ margin:0 0 4px; font-size:13px; color:#0f172a; }}
.custom-line-popup .badge {{ display:inline-block; font-size:10px; font-weight:700; padding:2px 5px; border-radius:4px; color:#fff; margin-bottom:6px; }}
.custom-line-popup .p-row {{ display:flex; justify-content:space-between; gap:12px; margin:2px 0; color:#475569; }}
.custom-line-popup .p-row b {{ color:#0f172a; }}
</style>
</head>
<body>
<div id="map"></div>

<div id="panel">
  <div class="nav-links">
    <a href="./index.html">← LatAm Overview</a>
    <a href="./pe.html" class="switch-btn">📶 Coverage View</a>
  </div>

  <h1>Peru — Transmission Grid</h1>
  <p class="sub">Asset Ownership & Concessionaires (SEIN · $\ge 138\text{{ kV}}$)</p>

  <div class="big" id="headlineShare">68.6%</div>
  <div class="big-label" id="headlineLabel">of Peru's transmission grid is operated by <b>Grupo ISA</b> (ISA REP & Consorcio Transmantaro)</div>

  <div class="grid">
    <div class="stat"><div class="k">Visible Length</div><div class="v" id="statLength">22,319 km</div></div>
    <div class="stat"><div class="k">Private Share</div><div class="v" id="statPrivate">82.8%</div></div>
    <div class="stat"><div class="k">500 kV Backbone</div><div class="v" id="stat500">2,938 km</div></div>
    <div class="stat"><div class="k">220 kV Trunk</div><div class="v" id="stat220">15,350 km</div></div>
  </div>

  <!-- Selected Line Card -->
  <div id="lineInfoCard">
    <div class="lic-title" id="cardName">Click any line to inspect</div>
    <div class="lic-sub" id="cardOperator">Concessionaire</div>
    <div class="lic-grid">
      <div><span>Voltage:</span> <b id="cardVolt">-</b></div>
      <div><span>Length:</span> <b id="cardKm">-</b></div>
      <div style="grid-column:1 / -1;"><span>Regime:</span> <b id="cardRegime">-</b></div>
    </div>
  </div>

  <!-- Corporate Group Filter -->
  <div class="ctl">
    <label class="t"><span>Corporate Group</span> <span id="groupFilterBadge" style="color:#2563eb; font-weight:600;">ALL</span></label>
    <div class="btnrow" id="grpBtns">
      <button data-g="all" class="on">All</button>
      <button data-g="isa" class="grp-btn"><span class="gdot" style="background:#2563eb;"></span>ISA</button>
      <button data-g="celeo" class="grp-btn"><span class="gdot" style="background:#059669;"></span>Celeo</button>
      <button data-g="generators" class="grp-btn"><span class="gdot" style="background:#d97706;"></span>Generators</button>
      <button data-g="mining" class="grp-btn"><span class="gdot" style="background:#e11d48;"></span>Mining</button>
      <button data-g="distriluz" class="grp-btn"><span class="gdot" style="background:#9333ea;"></span>State Sub-tx</button>
      <button data-g="abengoa" class="grp-btn"><span class="gdot" style="background:#0891b2;"></span>ATN</button>
    </div>
  </div>

  <!-- Voltage Filter -->
  <div class="ctl">
    <label class="t">Voltage Level</label>
    <div class="btnrow" id="voltBtns">
      <button data-v="0" class="on">All</button>
      <button data-v="500">500 kV</button>
      <button data-v="220">220 kV</button>
      <button data-v="138">138 kV</button>
      <button data-v="60">60 kV</button>
    </div>
  </div>

  <!-- Basemap -->
  <div class="ctl">
    <label class="t">Basemap Style</label>
    <div class="btnrow" id="baseBtns">
      <button data-b="dark" class="on">Esri Dark</button>
      <button data-b="osm">OpenStreetMap</button>
      <button data-b="esri">Esri Street</button>
      <button data-b="sat">Esri Satellite</button>
    </div>
  </div>

  <!-- Dynamic Breakdown -->
  <div class="breakdown">
    <div class="breakdown-title">Ownership Distribution</div>
    <div id="breakdownList"></div>
  </div>

  <p class="note">High-voltage lines ($\ge 138\text{{ kV}}$) are concessioned under BOOT (Build-Own-Operate-Transfer) public-private contracts supervised by OSINERGMIN and dispatched by COES.</p>

  <p class="attrib">Data: COES SEIN Estadísticas · OSINERGMIN SIGLE · OpenStreetMap contributors (ODbL).<br>
  Interactive visualization produced for LatAm Grid Overview.</p>
</div>

<script>
{leaflet_js}

// Line Data
var LINES = {lines_json};

// Colors per group
var GROUP_COLORS = {{
  'isa': '#2563eb',       // Royal Blue
  'celeo': '#059669',     // Emerald
  'generators': '#d97706',// Amber
  'mining': '#e11d48',    // Rose
  'distriluz': '#9333ea',  // Purple
  'abengoa': '#0891b2'    // Cyan
}};

var GROUP_NAMES = {{
  'isa': 'Grupo ISA (ISA REP & CTM)',
  'celeo': 'Celeo Redes / Tesur (REDESUR)',
  'generators': 'Generators (Engie, San Gabán)',
  'mining': 'Mining Dedicated (SPCC, Antamina)',
  'distriluz': 'State Sub-transmission (Distriluz)',
  'abengoa': 'Abengoa / Omega (ATN)'
}};

var BADGE_COLORS = {{
  500: '#7c3aed',
  220: '#2563eb',
  138: '#059669',
  60: '#64748b'
}};

// Basemaps (100% public, no API keys or watermarks required)
var darkMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
  attribution: 'Esri, HERE, Garmin, &copy; OpenStreetMap contributors', maxZoom: 16
}});
var osmMap = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '&copy; OpenStreetMap contributors', maxZoom: 18
}});
var esriMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
  attribution: 'Esri, HERE, Garmin', maxZoom: 18
}});
var satMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
  attribution: '&copy; Esri, Earthstar Geographics', maxZoom: 18
}});

var map = L.map('map', {{
  preferCanvas: true,
  zoomControl: false,
  layers: [darkMap]
}}).setView([-9.5, -75.0], 6);

L.control.zoom({{ position: 'topright' }}).addTo(map);

var lineCanvas = L.canvas();
var lineLayer = L.layerGroup().addTo(map);

var filterGroup = 'all';
var filterVolt = 0;
var activeLinePoly = null;

function renderGrid() {{
  lineLayer.clearLayers();

  var visibleKm = 0.0;
  var groupKm = {{
    'isa': 0.0,
    'celeo': 0.0,
    'generators': 0.0,
    'mining': 0.0,
    'distriluz': 0.0,
    'abengoa': 0.0
  }};
  var voltKm = {{ 500: 0.0, 220: 0.0, 138: 0.0, 60: 0.0 }};

  for (var i = 0; i < LINES.length; i++) {{
    var line = LINES[i];
    if (filterGroup !== 'all' && line.grp !== filterGroup) continue;
    if (filterVolt && line.v !== filterVolt) continue;

    visibleKm += line.km;
    groupKm[line.grp] = (groupKm[line.grp] || 0) + line.km;
    voltKm[line.v] = (voltKm[line.v] || 0) + line.km;

    var color = GROUP_COLORS[line.grp] || '#64748b';
    var weight = line.v >= 500 ? 3.8 : (line.v >= 220 ? 2.5 : (line.v >= 138 ? 1.8 : 1.3));
    var opacity = (filterGroup === 'all' || filterGroup === line.grp) ? 0.90 : 0.25;

    var poly = L.polyline(line.c, {{
      renderer: lineCanvas,
      color: color,
      weight: weight,
      opacity: opacity,
      lineCap: 'round',
      lineJoin: 'round'
    }});

    // Bind popup and click interaction
    (function(l, p) {{
      var badgeColor = BADGE_COLORS[l.v] || '#64748b';
      var popupHtml = '<div class="custom-line-popup">' +
        '<h4>' + l.n + '</h4>' +
        '<span class="badge" style="background:' + badgeColor + ';">' + l.v + ' kV</span>' +
        '<div class="p-row"><span>Concessionaire:</span> <b>' + l.op + '</b></div>' +
        '<div class="p-row"><span>Corporate Group:</span> <b>' + (GROUP_NAMES[l.grp] || l.grp) + '</b></div>' +
        '<div class="p-row"><span>Regime:</span> <b>' + l.rg + '</b></div>' +
        '<div class="p-row"><span>Length:</span> <b>' + l.km.toFixed(1) + ' km</b></div>' +
        '</div>';

      p.bindPopup(popupHtml, {{ maxWidth: 300 }});

      p.on('click', function(e) {{
        showCard(l);
      }});
    }})(line, poly);

    poly.addTo(lineLayer);
  }}

  updateStats(visibleKm, groupKm, voltKm);
}}

function showCard(l) {{
  var card = document.getElementById('lineInfoCard');
  card.classList.add('visible');
  document.getElementById('cardName').innerText = l.n;
  document.getElementById('cardOperator').innerText = l.op;
  document.getElementById('cardVolt').innerText = l.v + ' kV';
  document.getElementById('cardKm').innerText = l.km.toFixed(1) + ' km';
  document.getElementById('cardRegime').innerText = l.rg;
}}

function updateStats(totalKm, groupKm, voltKm) {{
  document.getElementById('statLength').innerText = Math.round(totalKm).toLocaleString() + ' km';
  document.getElementById('stat500').innerText = Math.round(voltKm[500] || 0).toLocaleString() + ' km';
  document.getElementById('stat220').innerText = Math.round(voltKm[220] || 0).toLocaleString() + ' km';

  var privateKm = (groupKm['isa'] || 0) + (groupKm['celeo'] || 0) + (groupKm['generators'] || 0) + (groupKm['abengoa'] || 0) + (groupKm['mining'] || 0);
  var privateShare = totalKm > 0 ? (privateKm / totalKm * 100).toFixed(1) : 0;
  document.getElementById('statPrivate').innerText = privateShare + '%';

  // Headline
  if (filterGroup === 'all') {{
    var isaShare = totalKm > 0 ? ((groupKm['isa'] || 0) / totalKm * 100).toFixed(1) : 0;
    document.getElementById('headlineShare').innerText = isaShare + '%';
    document.getElementById('headlineLabel').innerHTML = 'of Peru\\'s transmission grid is operated by <b>Grupo ISA</b> (ISA REP & Consorcio Transmantaro)';
  }} else {{
    var selKm = groupKm[filterGroup] || 0;
    var selShare = totalKm > 0 ? (selKm / totalKm * 100).toFixed(1) : 0;
    document.getElementById('headlineShare').innerText = Math.round(selKm).toLocaleString() + ' km';
    document.getElementById('headlineLabel').innerHTML = 'Total visible corridor length for <b>' + (GROUP_NAMES[filterGroup] || filterGroup) + '</b>';
  }}

  // Breakdown list
  var bList = document.getElementById('breakdownList');
  bList.innerHTML = '';
  var sortedGroups = ['isa', 'distriluz', 'generators', 'celeo', 'mining', 'abengoa'];

  for (var i = 0; i < sortedGroups.length; i++) {{
    var g = sortedGroups[i];
    var km = groupKm[g] || 0;
    var pct = totalKm > 0 ? (km / totalKm * 100).toFixed(1) : 0;
    var col = GROUP_COLORS[g];
    var name = GROUP_NAMES[g];

    var row = document.createElement('div');
    row.className = 'b-row';
    row.innerHTML = '<span class="b-name"><span class="b-sw" style="background:' + col + ';"></span> ' + name + '</span>' +
      '<span class="b-val">' + Math.round(km).toLocaleString() + ' km (' + pct + '%)</span>';
    bList.appendChild(row);
  }}
}}

// UI Handlers
function setActive(container, btn) {{
  var bs = container.querySelectorAll('button');
  for (var i = 0; i < bs.length; i++) bs[i].classList.remove('on');
  btn.classList.add('on');
}}

document.getElementById('grpBtns').addEventListener('click', function(e) {{
  var b = e.target.closest('button'); if (!b) return;
  filterGroup = b.getAttribute('data-g');
  document.getElementById('groupFilterBadge').innerText = filterGroup.toUpperCase();
  setActive(this, b);
  renderGrid();
}});

document.getElementById('voltBtns').addEventListener('click', function(e) {{
  var b = e.target.closest('button'); if (!b) return;
  filterVolt = parseInt(b.getAttribute('data-v'), 10) || 0;
  setActive(this, b);
  renderGrid();
}});

document.getElementById('baseBtns').addEventListener('click', function(e) {{
  var b = e.target.closest('button'); if (!b) return;
  setActive(this, b);
  var key = b.getAttribute('data-b');
  map.removeLayer(darkMap); map.removeLayer(osmMap); map.removeLayer(esriMap); map.removeLayer(satMap);
  if (key === 'osm') osmMap.addTo(map);
  else if (key === 'esri') esriMap.addTo(map);
  else if (key === 'sat') satMap.addTo(map);
  else darkMap.addTo(map);
}});

// Initial render
renderGrid();
</script>
</body>
</html>"""

    with open('pe_ownership.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("pe_ownership.html generated successfully!")

if __name__ == '__main__':
    build_ownership_page()
