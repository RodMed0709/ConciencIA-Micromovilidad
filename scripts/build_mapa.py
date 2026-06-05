# -*- coding: utf-8 -*-
"""
Genera un visor de mapa LOCAL (MapLibre GL, sin token) con las burbujas de
riesgo. Embebe los GeoJSON dentro del HTML -> se abre con doble clic, sin
servidor ni internet (salvo el basemap de calles).

Salida: data/processed/mapa_riesgo.html
"""

import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, "data", "processed", "geojson")
OUT_HTML = os.path.join(ROOT, "data", "processed", "mapa_riesgo.html")

CAPAS = [
    {"id": "peaton",   "label": "Peatones",  "archivo": "burbujas_peaton.geojson"},
    {"id": "ciclista", "label": "Ciclistas", "archivo": "burbujas_ciclista.geojson"},
    {"id": "moto",     "label": "Motos",     "archivo": "burbujas_moto.geojson"},
    {"id": "coches",   "label": "Coches",    "archivo": "burbujas_coches.geojson"},
]


def cargar(archivo):
    with open(os.path.join(GEO, archivo), encoding="utf-8") as f:
        return json.load(f)


def main():
    datos = {}
    maxes = {}
    for c in CAPAS:
        gj = cargar(c["archivo"])
        datos[c["id"]] = gj
        maxes[c["id"]] = gj.get("metadata", {}).get("max_accidentes_en_burbuja", 1) or 1

    datos_js = json.dumps(datos, ensure_ascii=False)
    maxes_js = json.dumps(maxes)
    capas_js = json.dumps(CAPAS, ensure_ascii=False)

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
  <div class="leyenda">
    <div>Menos &rarr; mas accidentes</div>
    <div class="barra"></div>
    <div>burbuja: tamano + color por # de siniestros en esa esquina (~50 m)</div>
  </div>
  <div class="sub">Clic en una burbuja para ver detalle. Fuente: SSC 2018-2019 (un solo registro, modo por vehiculo involucrado).</div>
</div>
<script>
const DATOS = __DATOS__;
const MAXES = __MAXES__;
const CAPAS = __CAPAS__;

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
  center: [-99.13, 19.40],
  zoom: 10.5
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
        .setHTML('<b>'+(p.accidentes)+' siniestros</b><br>'+(p.colonia||'')+
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
});
</script>
</body>
</html>
"""
    html = (html.replace("__DATOS__", datos_js)
                .replace("__MAXES__", maxes_js)
                .replace("__CAPAS__", capas_js))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    kb = os.path.getsize(OUT_HTML) / 1024
    print(f"Mapa generado: {OUT_HTML}  ({kb:.0f} KB)")
    print("Abrelo con doble clic (Chrome). Necesita internet solo para el mapa de calles.")


if __name__ == "__main__":
    main()
