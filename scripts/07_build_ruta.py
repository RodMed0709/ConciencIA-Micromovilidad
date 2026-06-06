# -*- coding: utf-8 -*-
"""
Genera un visor LOCAL (MapLibre GL, sin token) con un CONSTRUCTOR DE RUTAS.

Panel derecho: el usuario elige modo (peaton/bici/carro), escribe origen y
destino (autocompletar via OpenRouteService Pelias) o los pica/arrastra en el
mapa, y se traza la LINEA AZUL de la ruta con su distancia y tiempo estimado.

El ruteo es EN VIVO contra OpenRouteService (ORS). La API key NO se guarda en
el repo: el HTML la pide la primera vez y la guarda en localStorage.

Las capas de burbujas de riesgo van embebidas pero APAGADAS por defecto (toggle)
-> contexto visual; el riesgo aun NO altera la ruta (se cablea despues).

Salida: data/processed/ruta_segura.html  (abrir con doble clic)
"""

import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, "data", "processed", "geojson")
OUT_HTML = os.path.join(ROOT, "data", "processed", "ruta_segura.html")

# Capas de riesgo de fondo (mismas que el mapa de burbujas). Toggle, off por defecto.
CAPAS = [
    {"id": "peaton",   "label": "Peatones",  "archivo": "burbujas_peaton.geojson"},
    {"id": "ciclista", "label": "Ciclistas", "archivo": "burbujas_ciclista.geojson"},
    {"id": "moto",     "label": "Motos",     "archivo": "burbujas_moto.geojson"},
    {"id": "coches",   "label": "Coches",    "archivo": "burbujas_coches.geojson"},
]

# Zonas universitarias (campus principales) -> (lat, lon). Enfasis del proyecto.
UNIVERSIDADES = {
    "CU - UNAM": (19.3320, -99.1870),
    "IPN Zacatenco": (19.5040, -99.1340),
    "IPN Santo Tomas": (19.4560, -99.1530),
    "UAM Iztapalapa": (19.3600, -99.0740),
    "UAM Xochimilco": (19.3030, -99.1030),
    "UAM Azcapotzalco": (19.5030, -99.1860),
    "Tlalpan centro (zona uni/salud)": (19.2900, -99.1620),
}


def cargar(archivo):
    ruta = os.path.join(GEO, archivo)
    if not os.path.exists(ruta):
        print(f"  AVISO: no existe {archivo}, se omite esa capa de fondo.")
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def main():
    datos, maxes, capas_ok = {}, {}, []
    for c in CAPAS:
        gj = cargar(c["archivo"])
        if gj is None:
            continue
        datos[c["id"]] = gj
        maxes[c["id"]] = gj.get("metadata", {}).get("max_accidentes_en_burbuja", 1) or 1
        capas_ok.append(c)

    # universidades -> lista [{nombre, lon, lat}] para marcadores
    unis = [{"nombre": n, "lat": v[0], "lon": v[1]} for n, v in UNIVERSIDADES.items()]

    datos_js = json.dumps(datos, ensure_ascii=False)
    maxes_js = json.dumps(maxes)
    capas_js = json.dumps(capas_ok, ensure_ascii=False)
    unis_js = json.dumps(unis, ensure_ascii=False)

    html = HTML_TEMPLATE
    html = (html.replace("__DATOS__", datos_js)
                .replace("__MAXES__", maxes_js)
                .replace("__CAPAS__", capas_js)
                .replace("__UNIS__", unis_js))

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    kb = os.path.getsize(OUT_HTML) / 1024
    print(f"Constructor de rutas generado: {OUT_HTML}  ({kb:.0f} KB)")
    print("Abrelo con doble clic (Chrome). Pega tu API key gratis de OpenRouteService")
    print("(openrouteservice.org/dev) la primera vez; se guarda en el navegador.")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<title>Movilidad Segura - Constructor de rutas</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<style>
  html,body{margin:0;height:100%;font-family:system-ui,Segoe UI,Roboto,sans-serif}
  #map{position:absolute;top:0;bottom:0;left:0;right:340px}
  #panel{position:absolute;top:0;bottom:0;right:0;width:340px;background:#fff;
    box-shadow:-2px 0 12px rgba(0,0,0,.18);overflow-y:auto;padding:16px 18px;box-sizing:border-box}
  #panel h1{font-size:17px;margin:0 0 2px}
  #panel .lead{font-size:12px;color:#666;margin:0 0 14px}
  .modos{display:flex;gap:6px;margin-bottom:12px}
  .modo{flex:1;text-align:center;padding:8px 0;border:1.5px solid #d0d0d0;border-radius:9px;
    cursor:pointer;font-size:13px;user-select:none;background:#fafafa}
  .modo.activo{border-color:#2563eb;background:#eaf1ff;color:#1d4ed8;font-weight:600}
  .modo .ic{display:block;font-size:18px;line-height:1.1}
  .campo{position:relative;margin-bottom:10px}
  .campo label{display:block;font-size:11px;color:#555;margin-bottom:3px;text-transform:uppercase;letter-spacing:.03em}
  .campo input{width:100%;box-sizing:border-box;padding:9px 10px;border:1.5px solid #d0d0d0;
    border-radius:8px;font-size:13px}
  .campo input:focus{outline:none;border-color:#2563eb}
  .sugerencias{position:absolute;z-index:5;left:0;right:0;background:#fff;border:1px solid #ddd;
    border-radius:0 0 8px 8px;max-height:200px;overflow-y:auto;box-shadow:0 6px 14px rgba(0,0,0,.12)}
  .sugerencias div{padding:8px 10px;font-size:12.5px;cursor:pointer;border-top:1px solid #f0f0f0}
  .sugerencias div:hover{background:#eaf1ff}
  .acciones{display:flex;gap:8px;margin:6px 0 12px}
  .btn{flex:1;padding:10px 0;border:none;border-radius:9px;font-size:13.5px;cursor:pointer;font-weight:600}
  .btn-primary{background:#2563eb;color:#fff}
  .btn-primary:disabled{background:#9db8ee;cursor:default}
  .btn-ghost{background:#f0f0f0;color:#333}
  .resultado{background:#f6f9ff;border:1px solid #d8e3fb;border-radius:10px;padding:12px;font-size:13px;display:none}
  .resultado.show{display:block}
  .resultado .big{font-size:22px;font-weight:700;color:#1d4ed8}
  .resultado .row{display:flex;justify-content:space-between;margin-top:6px;color:#444}
  .msg{font-size:12.5px;padding:9px 11px;border-radius:8px;margin-bottom:10px;display:none}
  .msg.show{display:block}
  .msg.err{background:#fdecec;color:#b3261e;border:1px solid #f5c2c0}
  .msg.info{background:#fff7e6;color:#92600a;border:1px solid #f3dca0}
  .ayuda{font-size:11px;color:#888;line-height:1.4;margin-top:6px}
  .ayuda a{color:#2563eb;cursor:pointer}
  .seccion{border-top:1px solid #eee;margin-top:14px;padding-top:12px}
  .seccion h2{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#777;margin:0 0 8px}
  .capa-row{display:block;font-size:13px;margin:4px 0;cursor:pointer}
  .leyenda .barra{height:10px;border-radius:5px;margin:6px 0 2px;
    background:linear-gradient(90deg,#ffffb2,#fed976,#feb24c,#fd8d3c,#fc4e2a,#e31a1c,#b10026)}
  .leyenda small{font-size:10.5px;color:#888}
  .maplibregl-popup-content{font-size:13px;line-height:1.4}
  .pin{font-size:26px;line-height:1;cursor:grab;filter:drop-shadow(0 2px 2px rgba(0,0,0,.35))}
  .uni-dot{width:11px;height:11px;border-radius:50%;background:#7c3aed;border:2px solid #fff;
    box-shadow:0 1px 3px rgba(0,0,0,.4);cursor:pointer}
</style>
</head>
<body>
<div id="map"></div>
<div id="panel">
  <h1>Constructor de ruta</h1>
  <p class="lead">Elige modo, marca origen y destino. Trazamos tu ruta estimada.</p>

  <div class="modos" id="modos">
    <div class="modo activo" data-perfil="foot-walking"><span class="ic">&#128694;</span>Peaton</div>
    <div class="modo" data-perfil="cycling-regular"><span class="ic">&#128690;</span>Bici</div>
    <div class="modo" data-perfil="driving-car"><span class="ic">&#128663;</span>Carro/Moto</div>
  </div>

  <div id="msg" class="msg"></div>

  <div class="campo">
    <label>Origen</label>
    <input id="in-origen" type="text" placeholder="Escribe una direccion o pica el mapa" autocomplete="off" />
    <div id="sug-origen" class="sugerencias" style="display:none"></div>
  </div>
  <div class="campo">
    <label>Destino</label>
    <input id="in-destino" type="text" placeholder="A donde vas" autocomplete="off" />
    <div id="sug-destino" class="sugerencias" style="display:none"></div>
  </div>

  <div class="acciones">
    <button id="btn-trazar" class="btn btn-primary" disabled>Trazar ruta</button>
    <button id="btn-limpiar" class="btn btn-ghost">Limpiar</button>
  </div>

  <div id="resultado" class="resultado">
    <div><span class="big" id="r-tiempo">--</span> <span style="color:#1d4ed8">min aprox</span></div>
    <div class="row"><span>Distancia</span><b id="r-dist">-- km</b></div>
    <div class="row"><span>Modo</span><b id="r-modo">--</b></div>
  </div>

  <div class="ayuda">
    Tip: clic en el mapa fija origen y luego destino. Arrastra los pines para reajustar.
    <br><a id="link-key">Cambiar API key</a>
  </div>

  <div class="seccion">
    <h2>Capas de riesgo (contexto)</h2>
    <div id="capas"></div>
    <div class="leyenda" id="leyenda" style="display:none">
      <div class="barra"></div>
      <small>Menos &rarr; mas siniestros por esquina (~50 m). SSC 2018-2019.</small>
    </div>
  </div>
</div>

<script>
const DATOS = __DATOS__;
const MAXES = __MAXES__;
const CAPAS = __CAPAS__;
const UNIS  = __UNIS__;

const ORS_BASE = "https://api.openrouteservice.org";
const FOCO = {lon:-99.1332, lat:19.4326}; // CDMX, sesgo de geocoding

// ---- API key (localStorage, nunca en repo) -------------------------------
function getKey(force){
  let k = localStorage.getItem("ors_key");
  if(!k || force){
    k = (prompt("Pega tu API key gratis de OpenRouteService\\n(openrouteservice.org/dev):", k || "") || "").trim();
    if(k) localStorage.setItem("ors_key", k);
  }
  return k;
}

// ---- estado --------------------------------------------------------------
let perfil = "foot-walking";
let origen = null;   // {lon, lat, label}
let destino = null;
let mkOrigen = null, mkDestino = null;

// ---- mapa ----------------------------------------------------------------
const map = new maplibregl.Map({
  container:'map',
  style:{ version:8,
    sources:{ base:{ type:'raster',
      tiles:['https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
             'https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'],
      tileSize:256, attribution:'&copy; OpenStreetMap &copy; CARTO' } },
    layers:[{ id:'base', type:'raster', source:'base' }] },
  center:[-99.13,19.40], zoom:10.5
});
map.addControl(new maplibregl.NavigationControl(), 'top-right');

function colorRamp(maxv){
  return ['interpolate',['linear'],['get','accidentes'],
    1,'#ffffb2', Math.max(2,maxv*0.25),'#fed976', Math.max(3,maxv*0.45),'#feb24c',
    Math.max(4,maxv*0.6),'#fd8d3c', Math.max(5,maxv*0.75),'#fc4e2a',
    Math.max(6,maxv*0.9),'#e31a1c', Math.max(7,maxv),'#b10026'];
}
function radioRamp(maxv){
  return ['interpolate',['linear'],['get','accidentes'], 1,2.5, Math.max(2,maxv),13];
}

const msg = document.getElementById('msg');
function showMsg(txt, tipo){ msg.textContent = txt; msg.className = 'msg show ' + (tipo||'info'); }
function hideMsg(){ msg.className = 'msg'; }

map.on('load', () => {
  // capas de riesgo (apagadas)
  CAPAS.forEach(c => {
    map.addSource(c.id, { type:'geojson', data: DATOS[c.id] });
    map.addLayer({ id:c.id, type:'circle', source:c.id,
      layout:{ visibility:'none' },
      paint:{ 'circle-radius':radioRamp(MAXES[c.id]), 'circle-color':colorRamp(MAXES[c.id]),
        'circle-opacity':0.8, 'circle-stroke-width':0.4, 'circle-stroke-color':'#7a0010' } });
  });

  // fuente + capa de la RUTA (linea azul, con casing)
  map.addSource('ruta', { type:'geojson', data:{ type:'FeatureCollection', features:[] } });
  map.addLayer({ id:'ruta-casing', type:'line', source:'ruta',
    layout:{ 'line-cap':'round','line-join':'round' },
    paint:{ 'line-color':'#1e3a8a','line-width':8,'line-opacity':0.55 } });
  map.addLayer({ id:'ruta', type:'line', source:'ruta',
    layout:{ 'line-cap':'round','line-join':'round' },
    paint:{ 'line-color':'#2563eb','line-width':5 } });

  // marcadores de universidades
  UNIS.forEach(u => {
    const el = document.createElement('div'); el.className = 'uni-dot';
    new maplibregl.Marker({element:el})
      .setLngLat([u.lon,u.lat])
      .setPopup(new maplibregl.Popup({offset:12}).setHTML('<b>'+u.nombre+'</b><br><small>zona universitaria</small>'))
      .addTo(map);
  });

  // controles de capa
  const cont = document.getElementById('capas');
  CAPAS.forEach(c => {
    const id='ck_'+c.id;
    cont.innerHTML += '<label class="capa-row"><input type="checkbox" id="'+id+'" value="'+c.id+'"> '+
      c.label+' ('+DATOS[c.id].features.length+')</label>';
  });
  cont.addEventListener('change', e => {
    map.setLayoutProperty(e.target.value,'visibility', e.target.checked?'visible':'none');
    const algun = CAPAS.some(c => document.getElementById('ck_'+c.id).checked);
    document.getElementById('leyenda').style.display = algun ? 'block':'none';
  });
});

// ---- clic en mapa fija origen -> destino ---------------------------------
map.on('click', (e) => {
  const p = { lon:e.lngLat.lng, lat:e.lngLat.lat, label:'(punto en mapa)' };
  if(!origen){ setPunto('origen', p); }
  else if(!destino){ setPunto('destino', p); }
  else { setPunto('origen', p); setPunto('destino', null); }
});

// ---- pines ---------------------------------------------------------------
function pinEl(emoji){ const d=document.createElement('div'); d.className='pin'; d.textContent=emoji; return d; }

function setPunto(cual, p){
  if(cual==='origen'){
    origen = p;
    document.getElementById('in-origen').value = p ? p.label : '';
    if(mkOrigen) mkOrigen.remove();
    if(p){ mkOrigen = new maplibregl.Marker({element:pinEl('\\uD83D\\uDFE2'),draggable:true,anchor:'bottom'})
      .setLngLat([p.lon,p.lat]).addTo(map);
      mkOrigen.on('dragend',()=>onDrag('origen',mkOrigen)); }
  } else {
    destino = p;
    document.getElementById('in-destino').value = p ? p.label : '';
    if(mkDestino) mkDestino.remove();
    if(p){ mkDestino = new maplibregl.Marker({element:pinEl('\\uD83D\\uDD34'),draggable:true,anchor:'bottom'})
      .setLngLat([p.lon,p.lat]).addTo(map);
      mkDestino.on('dragend',()=>onDrag('destino',mkDestino)); }
  }
  actualizarBoton();
  if(origen && destino) trazar();
}

async function onDrag(cual, mk){
  const ll = mk.getLngLat();
  const p = { lon:ll.lng, lat:ll.lat, label:'(punto en mapa)' };
  const lbl = await reverse(p.lon, p.lat);
  if(lbl) p.label = lbl;
  if(cual==='origen'){ origen=p; document.getElementById('in-origen').value=p.label; }
  else { destino=p; document.getElementById('in-destino').value=p.label; }
  if(origen && destino) trazar();
}

function actualizarBoton(){
  document.getElementById('btn-trazar').disabled = !(origen && destino);
}

// ---- autocompletar (ORS Pelias) ------------------------------------------
function bindAuto(inputId, sugId, cual){
  const input = document.getElementById(inputId);
  const sug = document.getElementById(sugId);
  let t = null;
  input.addEventListener('input', () => {
    clearTimeout(t);
    const q = input.value.trim();
    if(q.length < 3){ sug.style.display='none'; return; }
    t = setTimeout(() => autocompletar(q, sug, cual), 350);
  });
  input.addEventListener('blur', () => setTimeout(()=>{ sug.style.display='none'; }, 180));
}

async function autocompletar(q, sug, cual){
  const key = getKey(); if(!key) return;
  const url = ORS_BASE+"/geocode/autocomplete?api_key="+encodeURIComponent(key)+
    "&text="+encodeURIComponent(q)+"&focus.point.lon="+FOCO.lon+"&focus.point.lat="+FOCO.lat+
    "&boundary.country=MX&size=5";
  try{
    const r = await fetch(url); if(!r.ok) throw new Error('geocode '+r.status);
    const j = await r.json();
    const items = (j.features||[]);
    if(!items.length){ sug.style.display='none'; return; }
    sug.innerHTML = '';
    items.forEach(f => {
      const c = f.geometry.coordinates; // [lon,lat]
      const label = f.properties.label;
      const div = document.createElement('div');
      div.textContent = label;
      div.addEventListener('mousedown', () => {
        setPunto(cual, {lon:c[0], lat:c[1], label});
        sug.style.display='none';
        map.flyTo({center:c, zoom:14});
      });
      sug.appendChild(div);
    });
    sug.style.display='block';
  }catch(err){ showMsg('No se pudo autocompletar: '+err.message,'err'); }
}

async function reverse(lon, lat){
  const key = getKey(); if(!key) return null;
  try{
    const r = await fetch(ORS_BASE+"/geocode/reverse?api_key="+encodeURIComponent(key)+
      "&point.lon="+lon+"&point.lat="+lat+"&size=1");
    if(!r.ok) return null;
    const j = await r.json();
    return (j.features && j.features[0]) ? j.features[0].properties.label : null;
  }catch(e){ return null; }
}

// ---- trazar ruta (ORS Directions) ----------------------------------------
async function trazar(){
  if(!(origen && destino)) return;
  const key = getKey(); if(!key){ showMsg('Necesitas una API key de ORS para trazar.','info'); return; }
  showMsg('Trazando ruta...','info');
  try{
    const r = await fetch(ORS_BASE+"/v2/directions/"+perfil+"/geojson", {
      method:'POST',
      headers:{ 'Authorization':key, 'Content-Type':'application/json' },
      body: JSON.stringify({ coordinates:[[origen.lon,origen.lat],[destino.lon,destino.lat]] })
    });
    if(!r.ok){
      const txt = await r.text();
      throw new Error(r.status+' '+txt.slice(0,120));
    }
    const j = await r.json();
    const feat = j.features[0];
    map.getSource('ruta').setData(j);
    const sum = feat.properties.summary;
    mostrarResultado(sum.distance, sum.duration);
    ajustarVista(feat.geometry.coordinates);
    hideMsg();
  }catch(err){
    showMsg('No se pudo trazar la ruta: '+err.message,'err');
  }
}

function mostrarResultado(distM, durS){
  document.getElementById('r-dist').textContent = (distM/1000).toFixed(1)+' km';
  document.getElementById('r-tiempo').textContent = Math.max(1, Math.round(durS/60));
  const nombres = {'foot-walking':'Peaton','cycling-regular':'Bici','driving-car':'Carro/Moto'};
  document.getElementById('r-modo').textContent = nombres[perfil] || perfil;
  document.getElementById('resultado').classList.add('show');
}

function ajustarVista(coords){
  let minX=180,minY=90,maxX=-180,maxY=-90;
  coords.forEach(c=>{ if(c[0]<minX)minX=c[0]; if(c[0]>maxX)maxX=c[0];
    if(c[1]<minY)minY=c[1]; if(c[1]>maxY)maxY=c[1]; });
  map.fitBounds([[minX,minY],[maxX,maxY]], {padding:{top:60,bottom:60,left:60,right:380}});
}

// ---- modos ----------------------------------------------------------------
document.getElementById('modos').addEventListener('click', e => {
  const m = e.target.closest('.modo'); if(!m) return;
  document.querySelectorAll('.modo').forEach(x=>x.classList.remove('activo'));
  m.classList.add('activo');
  perfil = m.dataset.perfil;
  if(origen && destino) trazar();
});

// ---- botones --------------------------------------------------------------
document.getElementById('btn-trazar').addEventListener('click', trazar);
document.getElementById('btn-limpiar').addEventListener('click', () => {
  setPunto('origen', null); setPunto('destino', null);
  map.getSource('ruta').setData({ type:'FeatureCollection', features:[] });
  document.getElementById('resultado').classList.remove('show');
  hideMsg();
});
document.getElementById('link-key').addEventListener('click', () => getKey(true));

// ---- init -----------------------------------------------------------------
bindAuto('in-origen','sug-origen','origen');
bindAuto('in-destino','sug-destino','destino');
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
