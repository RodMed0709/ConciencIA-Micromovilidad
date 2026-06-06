# -*- coding: utf-8 -*-
"""
Genera un visor de mapa LOCAL (MapLibre GL, sin token) con las burbujas de
riesgo. Embebe los GeoJSON dentro del HTML -> se abre con doble clic, sin
servidor ni internet (salvo el basemap de calles).

Salida: data/processed/mapa_riesgo.html
"""

import os
import json

import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, "data", "processed", "geojson")
UNI_CSV = os.path.join(ROOT, "data", "raw", "9_universidad_directorio.csv")
OUT_HTML = os.path.join(ROOT, "data", "processed", "mapa_riesgo.html")

# bbox CDMX para descartar coords basura del directorio
LON_MIN, LON_MAX = -99.40, -98.90
LAT_MIN, LAT_MAX = 19.00, 19.60

CAPAS = [
    {"id": "peaton",   "label": "Peatones",  "archivo": "burbujas_peaton.geojson"},
    {"id": "ciclista", "label": "Ciclistas", "archivo": "burbujas_ciclista.geojson"},
    {"id": "moto",     "label": "Motos",     "archivo": "burbujas_moto.geojson"},
    {"id": "coches",   "label": "Coches",    "archivo": "burbujas_coches.geojson"},
    {"id": "crimen",   "label": "Crimen (robo)", "archivo": "burbujas_crimen.geojson"},
]


def cargar(archivo):
    with open(os.path.join(GEO, archivo), encoding="utf-8") as f:
        return json.load(f)


def cargar_unis():
    """Lee el directorio (latin-1), filtra a CDMX con coords validas."""
    df = pd.read_csv(UNI_CSV, encoding="latin-1", low_memory=False)
    df["lon"] = pd.to_numeric(df["gmaps_longitud"], errors="coerce")
    df["lat"] = pd.to_numeric(df["gmaps_latitud"], errors="coerce")
    m = (df["lon"].between(LON_MIN, LON_MAX) & df["lat"].between(LAT_MIN, LAT_MAX))
    df = df[m]
    unis = []
    for _, r in df.iterrows():
        unis.append({
            "nombre": str(r.get("universidad_nombre", "")).strip(),
            "adscripcion": str(r.get("universidad_adscripcion", "")).strip(),
            "alcaldia": str(r.get("nom_mun", "")).strip(),
            "lon": round(float(r["lon"]), 5),
            "lat": round(float(r["lat"]), 5),
        })
    return unis


def foco_universidades(unis, celda_km=2.0):
    """
    Centro/zoom inicial: donde se CONCENTRAN mas universidades. Cuenta unis por
    celda de ~celda_km y centra en el centroide del vecindario mas denso.
    """
    if not unis:
        return [-99.13, 19.40], 10.5
    lat = np.array([u["lat"] for u in unis])
    lon = np.array([u["lon"] for u in unis])
    dlat = celda_km / 111.0
    dlon = celda_km / 105.0
    gi = np.floor(lat / dlat).astype(int)
    gj = np.floor(lon / dlon).astype(int)
    from collections import Counter
    cnt = Counter(zip(gi, gj))
    (bi, bj), _ = cnt.most_common(1)[0]
    # promedio de las unis en la celda mas densa y sus vecinas (3x3)
    sel = np.array([(abs(i - bi) <= 1 and abs(j - bj) <= 1) for i, j in zip(gi, gj)])
    return [float(lon[sel].mean()), float(lat[sel].mean())], 12.5


def main():
    datos = {}
    maxes = {}
    for c in CAPAS:
        gj = cargar(c["archivo"])
        datos[c["id"]] = gj
        maxes[c["id"]] = gj.get("metadata", {}).get("max_accidentes_en_burbuja", 1) or 1

    unis = cargar_unis()
    centro, zoom = foco_universidades(unis)

    datos_js = json.dumps(datos, ensure_ascii=False)
    maxes_js = json.dumps(maxes)
    capas_js = json.dumps(CAPAS, ensure_ascii=False)
    unis_js = json.dumps(unis, ensure_ascii=False)
    centro_js = json.dumps(centro)

    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<title>Movilidad Segura - Mapa de riesgo</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<style>
  html,body{margin:0;height:100%;font-family:system-ui,Segoe UI,Roboto,sans-serif}
  #map{position:absolute;top:0;bottom:0;left:0;right:0}
  .panel{position:absolute;top:12px;left:12px;z-index:1;background:#fff;
    padding:12px 14px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,.25);font-size:14px;max-width:240px}
  .panel h1{font-size:15px;margin:0 0 8px}
  .panel label{display:block;margin:4px 0;cursor:pointer}
  .leyenda{margin-top:10px;font-size:12px;color:#333}
  .barra{height:12px;border-radius:6px;margin:4px 0;
    background:linear-gradient(90deg,#ffffb2,#fed976,#feb24c,#fd8d3c,#fc4e2a,#e31a1c,#b10026)}
  .sub{font-size:11px;color:#666;margin-top:8px;line-height:1.35}
  .maplibregl-popup-content{font-size:13px;line-height:1.4}
</style>
</head>
<body>
<div id="map"></div>
<div class="panel">
  <h1>Riesgo vial - CDMX</h1>
  <div id="capas"></div>
  <hr style="border:none;border-top:1px solid #eee;margin:8px 0">
  <label><input type="checkbox" id="chk_unis" checked> <span style="color:#8e44ad">&#9679;</span> Universidades (<span id="nuni"></span>)</label>
  <div class="leyenda">
    <div>Menos &rarr; mas accidentes</div>
    <div class="barra"></div>
    <div>burbuja: tamano + color por # de siniestros en esa esquina (~50 m)</div>
  </div>
  <div class="sub">Clic en una burbuja o pin para ver detalle. Accidentes: SSC 2018-2019. Universidades: directorio SIC. Mapa centrado donde hay mas universidades.</div>
</div>
<script>
const DATOS = __DATOS__;
const MAXES = __MAXES__;
const CAPAS = __CAPAS__;
const UNIS = __UNIS__;

const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {
      base: {
        type: 'raster',
        tiles: ['https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
                'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '&copy; OpenStreetMap &copy; CARTO'
      }
    },
    layers: [{ id: 'base', type: 'raster', source: 'base' }]
  },
  center: __CENTRO__,
  zoom: __ZOOM__
});
map.addControl(new maplibregl.NavigationControl(), 'top-right');

function colorRamp(maxv){
  // interpola color por # accidentes (YlOrRd)
  return ['interpolate',['linear'],['get','accidentes'],
    1,'#ffffb2',
    Math.max(2, maxv*0.25),'#fed976',
    Math.max(3, maxv*0.45),'#feb24c',
    Math.max(4, maxv*0.6),'#fd8d3c',
    Math.max(5, maxv*0.75),'#fc4e2a',
    Math.max(6, maxv*0.9),'#e31a1c',
    Math.max(7, maxv),'#b10026'];
}
function radioRamp(maxv){
  // burbujas chicas: 2.5 px (1 acc) -> 13 px (maximo)
  return ['interpolate',['linear'],['get','accidentes'], 1,2.5, Math.max(2,maxv),13];
}

map.on('load', () => {
  CAPAS.forEach((c, i) => {
    map.addSource(c.id, { type:'geojson', data: DATOS[c.id] });
    map.addLayer({
      id: c.id, type:'circle', source:c.id,
      layout:{ visibility: i===0 ? 'visible':'none' },
      paint:{
        'circle-radius': radioRamp(MAXES[c.id]),
        'circle-color': colorRamp(MAXES[c.id]),
        'circle-opacity': 0.82,
        'circle-stroke-width': 0.4,
        'circle-stroke-color': '#7a0010'
      }
    });
    map.on('click', c.id, (e) => {
      const p = e.features[0].properties;
      const uni = p.cerca_universidad === 'true' || p.cerca_universidad === true
        ? '<br><b>Cerca de:</b> '+(p.campus_cercano||'zona uni') : '';
      new maplibregl.Popup()
        .setLngLat(e.lngLat)
        .setHTML('<b>'+(p.accidentes)+' registros</b><br>'+(p.colonia||'')+
                 '<br><small>'+(p.alcaldia||'')+'</small>'+uni)
        .addTo(map);
    });
    map.on('mouseenter', c.id, ()=> map.getCanvas().style.cursor='pointer');
    map.on('mouseleave', c.id, ()=> map.getCanvas().style.cursor='');
  });

  // controles de capa (radio: una capa a la vez)
  const cont = document.getElementById('capas');
  CAPAS.forEach((c,i)=>{
    const id='r_'+c.id;
    cont.innerHTML += '<label><input type="radio" name="capa" id="'+id+'" value="'+c.id+'" '+
      (i===0?'checked':'')+'> '+c.label+' ('+DATOS[c.id].features.length+')</label>';
  });
  cont.addEventListener('change', (e)=>{
    CAPAS.forEach(c=> map.setLayoutProperty(c.id,'visibility', c.id===e.target.value?'visible':'none'));
  });

  // UNIVERSIDADES: pines morados estilo Google Maps con popup
  const marcadores = UNIS.map(u=>{
    const pop = new maplibregl.Popup({offset:24})
      .setHTML('<b>'+u.nombre+'</b><br><small>'+(u.adscripcion||'')+
               '</small><br><small>'+(u.alcaldia||'')+'</small>');
    return new maplibregl.Marker({color:'#8e44ad'})
      .setLngLat([u.lon,u.lat]).setPopup(pop).addTo(map);
  });
  document.getElementById('nuni').textContent = marcadores.length;
  document.getElementById('chk_unis').addEventListener('change', (e)=>{
    const vis = e.target.checked ? '' : 'none';
    marcadores.forEach(m=> m.getElement().style.display = vis);
  });
});
</script>
</body>
</html>
"""
    html = (html.replace("__DATOS__", datos_js)
                .replace("__MAXES__", maxes_js)
                .replace("__CAPAS__", capas_js)
                .replace("__UNIS__", unis_js)
                .replace("__CENTRO__", centro_js)
                .replace("__ZOOM__", str(zoom)))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    kb = os.path.getsize(OUT_HTML) / 1024
    print(f"Mapa generado: {OUT_HTML}  ({kb:.0f} KB)")
    print("Abrelo con doble clic (Chrome). Necesita internet solo para el mapa de calles.")


if __name__ == "__main__":
    main()
