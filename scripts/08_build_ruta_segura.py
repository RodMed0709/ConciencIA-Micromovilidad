# -*- coding: utf-8 -*-
"""
ruta_segurav2.html — Constructor de RUTA SEGURA (motor de riesgo real).

Diferencia con ruta_segura (v1): aqui el riesgo SI altera la ruta.
- Ruta CORTA = ORS sin restriccion (la mas corta, roja).
- Ruta SEGURA = ORS con options.avoid_polygons: las peores burbujas del modo en el
  corredor O->D se mandan como zonas a evitar; ORS rerutea esquivandolas.
  (peaton/bici incluyen robos; coche/moto van juntos en una capa.)
- Puntua ambas por # de incidentes cercanos (≤120 m) para el velocimetro.
- Muestra % de riesgo mitigado (incidentes esquivados) en un gauge.
- El selector de modo (arriba) controla: perfil de ruteo + datos de riesgo +
  burbujas de fondo.

Key ORS: igual que v1, desde ruta_key.js (gitignored) o prompt.
Salida: data/processed/ruta_segurav2.html
"""

import os
import json
import unicodedata

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, "data", "processed", "geojson")
UNI_CSV = os.path.join(ROOT, "data", "raw", "9_universidad_directorio.csv")
OUT_HTML = os.path.join(ROOT, "data", "processed", "ruta_segurav2.html")

# modo -> perfil ORS + capa de burbujas (datos del modo)
MODOS = [
    {"id": "peaton", "label": "Peaton", "emoji": "\U0001F6B6", "perfil": "foot-walking",   "capa": "peaton"},
    {"id": "bici",   "label": "Bici",   "emoji": "\U0001F6B2", "perfil": "cycling-regular", "capa": "ciclista"},
    {"id": "coches", "label": "Coche/Moto", "emoji": "\U0001F697", "perfil": "driving-car", "capa": "cochemoto"},
]

# Universidades curadas (~30 importantes, publicas + privadas). (patron, cuantas)
# Las coords salen del directorio real (9_universidad_directorio.csv).
UNIS_CURADAS = [
    ("nacional autonoma", 1), ("politecnico", 1), ("autonoma metropolitana", 5),
    ("docencia economicas", 1), ("pedagogica nacional", 1), ("claustro de sor juana", 1),
    ("tecnologico de monterrey", 9), ("iberoamericana", 1),
    ("instituto tecnologico autonomo", 2), ("la salle", 2), ("anahuac", 2),
    ("panamericana", 2), ("del valle de mexico", 3), ("marista", 1),
    ("westhill", 1), ("intercontinental", 2), ("tecnologica de mexico", 2),
    ("latinoamericana (ula)", 2), ("insurgentes", 1),
]
# Tec de Monterrey CDMX no esta en el directorio -> se agrega a mano.
UNIS_MANUAL = [{"nombre": "Tecnologico de Monterrey, Campus Ciudad de Mexico",
                "lat": 19.2849, "lon": -99.1380}]


def _na(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s).lower())
                   if not unicodedata.combining(c))


def cargar_unis_curadas():
    df = pd.read_csv(UNI_CSV, encoding="latin-1", low_memory=False)
    df["lon"] = pd.to_numeric(df["gmaps_longitud"], errors="coerce")
    df["lat"] = pd.to_numeric(df["gmaps_latitud"], errors="coerce")
    df = df[df["lon"].between(-99.4, -98.9) & df["lat"].between(19.0, 19.6)].copy()
    df["_n"] = df["universidad_nombre"].map(_na)
    unis, vistos = [], set()
    for patron, n in UNIS_CURADAS:
        sub = df[df["_n"].str.contains(patron, na=False, regex=False)]
        agregadas = 0
        for _, r in sub.iterrows():
            k = (round(r["lat"], 4), round(r["lon"], 4))
            if k in vistos:
                continue
            vistos.add(k)
            unis.append({"nombre": str(r["universidad_nombre"]).strip(),
                         "lat": round(float(r["lat"]), 5), "lon": round(float(r["lon"]), 5)})
            agregadas += 1
            if agregadas >= n:
                break
    unis.extend(UNIS_MANUAL)
    return unis


def cargar(capa):
    ruta = os.path.join(GEO, f"burbujas_{capa}.geojson")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def main():
    datos, maxes = {}, {}
    for m in MODOS:
        gj = cargar(m["capa"])
        datos[m["capa"]] = gj
        maxes[m["capa"]] = gj.get("metadata", {}).get("max_accidentes_en_burbuja", 1) or 1
    unis = cargar_unis_curadas()
    print(f"Universidades curadas: {len(unis)}")

    html = (HTML_TEMPLATE
            .replace("__DATOS__", json.dumps(datos, ensure_ascii=False))
            .replace("__MAXES__", json.dumps(maxes))
            .replace("__MODOS__", json.dumps(MODOS, ensure_ascii=False))
            .replace("__UNIS__", json.dumps(unis, ensure_ascii=False)))
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    kb = os.path.getsize(OUT_HTML) / 1024
    print(f"Ruta segura v2 generada: {OUT_HTML}  ({kb:.0f} KB)")
    print("Doble clic. Usa tu key ORS (ruta_key.js). Elige modo, origen y destino.")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<title>Movilidad Segura - Ruta segura v2</title>
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
    cursor:pointer;font-size:12px;user-select:none;background:#fafafa}
  .modo.activo{border-color:#2563eb;background:#eaf1ff;color:#1d4ed8;font-weight:600}
  .modo .ic{display:block;font-size:17px;line-height:1.1}
  .campo{position:relative;margin-bottom:10px}
  .campo label{display:block;font-size:11px;color:#555;margin-bottom:3px;text-transform:uppercase;letter-spacing:.03em}
  .campo input{width:100%;box-sizing:border-box;padding:9px 10px;border:1.5px solid #d0d0d0;border-radius:8px;font-size:13px}
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
  .mitiga{margin-top:10px;padding:9px 11px;background:#2563eb;color:#fff;border-radius:8px;font-size:13px}
  .mitiga b{font-size:18px}
  .leg{display:flex;align-items:center;gap:7px;margin-top:8px;font-size:12px;color:#555}
  .sw{width:22px;height:0;border-top:4px solid}
  .msg{font-size:12.5px;padding:9px 11px;border-radius:8px;margin-bottom:10px;display:none}
  .msg.show{display:block}
  .msg.err{background:#fdecec;color:#b3261e;border:1px solid #f5c2c0}
  .msg.info{background:#fff7e6;color:#92600a;border:1px solid #f3dca0}
  .ayuda{font-size:11px;color:#888;line-height:1.4;margin-top:10px}
  .ayuda a{color:#2563eb;cursor:pointer}
  .seccion{border-top:1px solid #eee;margin-top:14px;padding-top:12px}
  .seccion h2{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#777;margin:0 0 6px}
  .leyenda .barra{height:10px;border-radius:5px;margin:6px 0 2px;
    background:linear-gradient(90deg,#ffffb2,#fed976,#feb24c,#fd8d3c,#fc4e2a,#e31a1c,#b10026)}
  .leyenda small{font-size:10.5px;color:#888}
  .pin{font-size:26px;line-height:1;cursor:grab;filter:drop-shadow(0 2px 2px rgba(0,0,0,.35))}
  .uni-dot{width:11px;height:11px;border-radius:50%;background:#7c3aed;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.4)}
  /* velocimetro de riesgo, sobre el mapa abajo-derecha */
  #gauge{position:absolute;right:356px;bottom:18px;z-index:3;background:#fff;border-radius:14px;
    box-shadow:0 4px 18px rgba(0,0,0,.22);padding:12px 14px 10px;width:210px;text-align:center;display:none}
  #gauge.show{display:block}
  #gauge .titulo{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#777;margin-bottom:2px}
  #gauge .pct{font-size:30px;font-weight:800;color:#16a34a;line-height:1}
  #gauge .pct small{font-size:13px;font-weight:700}
  #gauge .sub{font-size:12px;color:#444;margin-top:4px}
  #gauge .sub b{font-weight:700}
  #gauge .vs{display:flex;justify-content:center;gap:8px;margin-top:6px;font-size:11px}
  #gauge .vs span{padding:3px 7px;border-radius:6px;font-weight:700}
  #gauge .vs .nueva{background:#dcfce7;color:#15803d}
  #gauge .vs .peli{background:#fee2e2;color:#b91c1c}
</style>
</head>
<body>
<div id="map"></div>
<div id="gauge">
  <div class="titulo">Riesgo mitigado</div>
  <svg id="g-svg" width="186" height="104" viewBox="0 0 186 104"></svg>
  <div class="pct" id="g-pct">--<small>%</small></div>
  <div class="sub" id="g-sub"></div>
  <div class="vs"><span class="nueva" id="g-nueva">--</span><span class="peli" id="g-peli">--</span></div>
</div>
<div id="panel">
  <h1>Ruta segura</h1>
  <p class="lead">Elige modo, origen y destino. Te damos la ruta que <b>esquiva el riesgo</b>.</p>

  <div class="modos" id="modos"></div>
  <div id="msg" class="msg"></div>

  <div class="campo">
    <label>Origen</label>
    <input id="in-origen" type="text" placeholder="Direccion o pica el mapa" autocomplete="off" />
    <div id="sug-origen" class="sugerencias" style="display:none"></div>
  </div>
  <div class="campo">
    <label>Destino</label>
    <input id="in-destino" type="text" placeholder="A donde vas" autocomplete="off" />
    <div id="sug-destino" class="sugerencias" style="display:none"></div>
  </div>

  <div class="acciones">
    <button id="btn-trazar" class="btn btn-primary" disabled>Trazar ruta segura</button>
    <button id="btn-limpiar" class="btn btn-ghost">Limpiar</button>
  </div>

  <div id="resultado" class="resultado">
    <div><span class="big" id="r-tiempo">--</span> <span style="color:#1d4ed8">min aprox</span></div>
    <div class="row"><span>Distancia</span><b id="r-dist">-- km</b></div>
    <div class="row"><span>Modo</span><b id="r-modo">--</b></div>
    <div class="leg"><span class="sw" style="border-color:#1d4ed8"></span> Ruta segura (recomendada)</div>
    <div class="leg"><span class="sw" style="border-color:#fca5a5"></span> Ruta corta (mas riesgo)</div>
  </div>

  <div class="seccion">
    <h2>Riesgo del modo (fondo)</h2>
    <div class="leyenda"><div class="barra"></div>
      <small>Menos &rarr; mas incidentes por zona. Peaton/bici incluyen robos.</small></div>
  </div>
  <div class="ayuda">Clic en mapa: 1er pico = origen, 2o = destino. Arrastra los pines.
    <br><a id="link-key">Cambiar API key ORS</a></div>
</div>

<script src="ruta_key.js"></script>
<script>
const DATOS = __DATOS__;
const MAXES = __MAXES__;
const MODOS = __MODOS__;
const UNIS  = __UNIS__;
const ORS_BASE = "https://api.openrouteservice.org";
const FOCO = {lon:-99.1332, lat:19.4326};

let modo = MODOS[0];           // {id,label,perfil,capa,emoji}
let origen=null, destino=null, mkO=null, mkD=null;
let indices = {};              // cache de indices espaciales por capa

function getKey(force){
  if(!force && window.ORS_KEY) return window.ORS_KEY;
  let k = localStorage.getItem("ors_key");
  if(!k || force){ k=(prompt("Pega tu API key gratis de OpenRouteService (openrouteservice.org/dev):", k||"")||"").trim();
    if(k) localStorage.setItem("ors_key", k); }
  return k;
}
const msg=document.getElementById('msg');
function showMsg(t,c){ msg.textContent=t; msg.className='msg show '+(c||'info'); }
function hideMsg(){ msg.className='msg'; }

// ---------- indice espacial de burbujas (grid ~220 m) para puntuar riesgo ----
const CELL = 0.002; // ~220 m
function ckey(lon,lat){ return Math.round(lon/CELL)+'_'+Math.round(lat/CELL); }
function indiceDe(capa){
  if(indices[capa]) return indices[capa];
  const idx = new Map();
  (DATOS[capa].features||[]).forEach(f=>{
    const c=f.geometry.coordinates, k=ckey(c[0],c[1]);
    if(!idx.has(k)) idx.set(k,[]);
    idx.get(k).push({lon:c[0],lat:c[1],n:f.properties.accidentes||1});
  });
  indices[capa]=idx; return idx;
}
function metros(aLon,aLat,bLon,bLat){
  const R=6371000, dLat=(bLat-aLat)*Math.PI/180, dLon=(bLon-aLon)*Math.PI/180;
  const la1=aLat*Math.PI/180, la2=bLat*Math.PI/180;
  const x=Math.sin(dLat/2)**2+Math.cos(la1)*Math.cos(la2)*Math.sin(dLon/2)**2;
  return 2*R*Math.asin(Math.sqrt(x));
}
// riesgo de una ruta = suma de incidentes de burbujas a <=120 m de la linea
// (cada burbuja cuenta una vez).
function riesgoRuta(coords, capa){
  const idx=indiceDe(capa), vistos=new Set(); let total=0;
  // submuestreo: 1 de cada 2 puntos para ir rapido
  for(let i=0;i<coords.length;i+=2){
    const [lon,lat]=coords[i];
    const ci=Math.round(lon/CELL), cj=Math.round(lat/CELL);
    for(let a=-1;a<=1;a++) for(let b=-1;b<=1;b++){
      const arr=idx.get((ci+a)+'_'+(cj+b)); if(!arr) continue;
      for(const p of arr){
        const id=p.lon+','+p.lat;
        if(vistos.has(id)) continue;
        if(metros(lon,lat,p.lon,p.lat)<=120){ vistos.add(id); total+=p.n; }
      }
    }
  }
  return total;
}

// ---------- mapa -------------------------------------------------------------
// basemap: Mapbox (bonito) si hay token; si no, CARTO gratis
const baseTiles = window.MAPBOX_KEY
  ? ['https://api.mapbox.com/styles/v1/mapbox/light-v11/tiles/{z}/{x}/{y}?access_token='+window.MAPBOX_KEY]
  : ['https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png','https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'];
const baseSize = window.MAPBOX_KEY ? 512 : 256;
const baseAttr = window.MAPBOX_KEY ? '&copy; Mapbox &copy; OpenStreetMap' : '&copy; OpenStreetMap &copy; CARTO';
const map=new maplibregl.Map({container:'map',
  style:{version:8,sources:{base:{type:'raster',tiles:baseTiles,tileSize:baseSize,attribution:baseAttr}},
    layers:[{id:'base',type:'raster',source:'base'}]},
  center:[-99.13,19.40],zoom:10.5});
map.addControl(new maplibregl.NavigationControl(),'top-right');
window.__map=map;
// promesa que resuelve cuando el mapa termino de cargar (evita carrera con trazar)
let _ready; const mapReady=new Promise(r=>{_ready=r;});

function colorRamp(m){ return ['interpolate',['linear'],['get','accidentes'],
  1,'#ffffb2',Math.max(2,m*0.25),'#fed976',Math.max(3,m*0.45),'#feb24c',
  Math.max(4,m*0.6),'#fd8d3c',Math.max(5,m*0.75),'#fc4e2a',Math.max(6,m*0.9),'#e31a1c',Math.max(7,m),'#b10026']; }
function radioRamp(m){ return ['interpolate',['linear'],['get','accidentes'],1,2.5,Math.max(2,m),12]; }

map.on('load',()=>{
  // burbujas de cada modo (solo la activa visible)
  MODOS.forEach(mo=>{
    map.addSource('b_'+mo.capa,{type:'geojson',data:DATOS[mo.capa]});
    map.addLayer({id:'b_'+mo.capa,type:'circle',source:'b_'+mo.capa,
      layout:{visibility: mo.capa===modo.capa?'visible':'none'},
      paint:{'circle-radius':radioRamp(MAXES[mo.capa]),'circle-color':colorRamp(MAXES[mo.capa]),
        'circle-opacity':0.5,'circle-stroke-width':0.3,'circle-stroke-color':'#7a0010'}});
  });
  // halo morado translucido de universidades (zona) -> mas entendimiento
  map.addSource('uni-halo',{type:'geojson',data:{type:'FeatureCollection',
    features:UNIS.map(u=>({type:'Feature',geometry:{type:'Point',coordinates:[u.lon,u.lat]},properties:{nombre:u.nombre}}))}});
  map.addLayer({id:'uni-halo',type:'circle',source:'uni-halo',
    paint:{'circle-radius':['interpolate',['linear'],['zoom'],10,8,13,26,16,70],
      'circle-color':'#7c3aed','circle-opacity':0.16,
      'circle-stroke-color':'#7c3aed','circle-stroke-opacity':0.4,'circle-stroke-width':1}});
  // ruta CORTA: roja translucida solida (la mas corta = mas riesgo), siempre visible
  map.addSource('r-corta',{type:'geojson',data:vacio()});
  map.addLayer({id:'r-corta',type:'line',source:'r-corta',layout:{'line-cap':'round','line-join':'round'},
    paint:{'line-color':'#f87171','line-width':7,'line-opacity':0.5}});
  // ruta SEGURA: solida con casing, color segun su riesgo (azul seguro -> rojo riesgoso)
  map.addSource('r-segura',{type:'geojson',data:vacio()});
  map.addLayer({id:'r-segura-casing',type:'line',source:'r-segura',layout:{'line-cap':'round','line-join':'round'},
    paint:{'line-color':'#0b2a6b','line-width':9,'line-opacity':0.5}});
  map.addLayer({id:'r-segura',type:'line',source:'r-segura',layout:{'line-cap':'round','line-join':'round'},
    paint:{'line-color':'#2563eb','line-width':5.5}});
  // universidades (punto morado encima del halo)
  UNIS.forEach(u=>{ const el=document.createElement('div'); el.className='uni-dot';
    new maplibregl.Marker({element:el}).setLngLat([u.lon,u.lat])
      .setPopup(new maplibregl.Popup({offset:12}).setHTML('<b>'+u.nombre+'</b>')).addTo(map); });
  _ready();
});
function vacio(){ return {type:'FeatureCollection',features:[]}; }

// ---------- modos ------------------------------------------------------------
const cont=document.getElementById('modos');
MODOS.forEach((mo,i)=>{ const d=document.createElement('div');
  d.className='modo'+(i===0?' activo':''); d.dataset.id=mo.id;
  d.innerHTML='<span class="ic">'+mo.emoji+'</span>'+mo.label; cont.appendChild(d); });
cont.addEventListener('click',e=>{
  const el=e.target.closest('.modo'); if(!el) return;
  modo=MODOS.find(m=>m.id===el.dataset.id);
  document.querySelectorAll('.modo').forEach(x=>x.classList.remove('activo'));
  el.classList.add('activo');
  MODOS.forEach(mo=> map.setLayoutProperty('b_'+mo.capa,'visibility', mo.capa===modo.capa?'visible':'none'));
  if(origen&&destino) trazar();
});

// ---------- clic / pines -----------------------------------------------------
map.on('click',e=>{ const p={lon:e.lngLat.lng,lat:e.lngLat.lat,label:'(punto en mapa)'};
  if(!origen) setPunto('origen',p); else if(!destino) setPunto('destino',p);
  else { setPunto('origen',p); setPunto('destino',null); } });
function pinEl(em){ const d=document.createElement('div'); d.className='pin'; d.textContent=em; return d; }
function setPunto(cual,p){
  if(cual==='origen'){ origen=p; document.getElementById('in-origen').value=p?p.label:'';
    if(mkO)mkO.remove(); if(p){ mkO=new maplibregl.Marker({element:pinEl('🟢'),draggable:true,anchor:'bottom'})
      .setLngLat([p.lon,p.lat]).addTo(map); mkO.on('dragend',()=>onDrag('origen',mkO)); } }
  else { destino=p; document.getElementById('in-destino').value=p?p.label:'';
    if(mkD)mkD.remove(); if(p){ mkD=new maplibregl.Marker({element:pinEl('🔴'),draggable:true,anchor:'bottom'})
      .setLngLat([p.lon,p.lat]).addTo(map); mkD.on('dragend',()=>onDrag('destino',mkD)); } }
  document.getElementById('btn-trazar').disabled=!(origen&&destino);
  if(origen&&destino) trazar();
}
async function onDrag(cual,mk){ const ll=mk.getLngLat(); const p={lon:ll.lng,lat:ll.lat,label:'(punto en mapa)'};
  const l=await reverse(p.lon,p.lat); if(l)p.label=l;
  if(cual==='origen'){origen=p;document.getElementById('in-origen').value=p.label;}
  else{destino=p;document.getElementById('in-destino').value=p.label;}
  if(origen&&destino) trazar(); }

// ---------- geocode ----------------------------------------------------------
function bindAuto(inId,sugId,cual){ const input=document.getElementById(inId),sug=document.getElementById(sugId); let t=null;
  input.addEventListener('input',()=>{ clearTimeout(t); const q=input.value.trim();
    if(q.length<3){sug.style.display='none';return;} t=setTimeout(()=>autocompletar(q,sug,cual),350); });
  input.addEventListener('blur',()=>setTimeout(()=>{sug.style.display='none';},180)); }
async function autocompletar(q,sug,cual){ const key=getKey(); if(!key)return;
  const url=ORS_BASE+"/geocode/autocomplete?api_key="+encodeURIComponent(key)+"&text="+encodeURIComponent(q)+
    "&focus.point.lon="+FOCO.lon+"&focus.point.lat="+FOCO.lat+"&boundary.country=MX&size=5";
  try{ const r=await fetch(url); if(!r.ok)throw new Error('geocode '+r.status); const j=await r.json();
    const items=j.features||[];
    if(!items.length){ sug.innerHTML='<div style="color:#999;cursor:default">Sin resultados. Prueba calle + colonia, o pica el mapa.</div>'; sug.style.display='block'; return; }
    sug.innerHTML=''; items.forEach(f=>{ const c=f.geometry.coordinates,label=f.properties.label;
      const div=document.createElement('div'); div.textContent=label;
      div.addEventListener('mousedown',()=>{ setPunto(cual,{lon:c[0],lat:c[1],label}); sug.style.display='none'; map.flyTo({center:c,zoom:14}); });
      sug.appendChild(div); }); sug.style.display='block';
  }catch(err){ showMsg('No se pudo autocompletar: '+err.message,'err'); } }
async function reverse(lon,lat){ const key=getKey(); if(!key)return null;
  try{ const r=await fetch(ORS_BASE+"/geocode/reverse?api_key="+encodeURIComponent(key)+"&point.lon="+lon+"&point.lat="+lat+"&size=1");
    if(!r.ok)return null; const j=await r.json(); return (j.features&&j.features[0])?j.features[0].properties.label:null; }catch(e){return null;} }

// ---------- ruteo: corta (sin evitar) vs segura (ORS evita zonas peligrosas) --
async function rutaUna(key, avoid){
  const body={coordinates:[[origen.lon,origen.lat],[destino.lon,destino.lat]],instructions:false};
  if(avoid) body.options={avoid_polygons:avoid};
  const r=await fetch(ORS_BASE+"/v2/directions/"+modo.perfil+"/geojson",
    {method:'POST',headers:{'Authorization':key,'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!r.ok){ const t=await r.text(); throw new Error(r.status+' '+t.slice(0,100)); }
  const j=await r.json(); if(!j.features||!j.features.length) throw new Error('sin ruta');
  return j.features[0];
}
// poligonos de las PEORES burbujas en el corredor O->D (para que ORS las evite)
function zonasEvitar(capa, maxN){
  const pad=0.012;
  const a=Math.min(origen.lon,destino.lon)-pad, c=Math.max(origen.lon,destino.lon)+pad;
  const b=Math.min(origen.lat,destino.lat)-pad, d=Math.max(origen.lat,destino.lat)+pad;
  let fs=(DATOS[capa].features||[]).filter(f=>{const g=f.geometry.coordinates;
    return g[0]>=a&&g[0]<=c&&g[1]>=b&&g[1]<=d;});
  fs.sort((p,q)=>q.properties.accidentes-p.properties.accidentes);
  fs=fs.slice(0,maxN);
  const h=0.0013; // ~130 m medio lado del cuadrito
  const polys=fs.map(f=>{const [x,y]=f.geometry.coordinates;
    return [[[x-h,y-h],[x+h,y-h],[x+h,y+h],[x-h,y+h],[x-h,y-h]]];});
  return polys.length? {type:'MultiPolygon',coordinates:polys} : null;
}
async function trazar(){
  if(!(origen&&destino))return; const key=getKey();
  if(!key){ showMsg('Necesitas tu API key de ORS.','info'); return; }
  showMsg('Calculando ruta segura...','info');
  try{
    await mapReady;                                   // espera a que el mapa cargue (evita carrera)
    const corta=await rutaUna(key,null);              // sin evitar = la mas corta
    let segura=corta;
    // intentar que ORS EVITE las peores zonas (top 30 -> 12 -> nada)
    for(const n of [30,12]){
      const avoid=zonasEvitar(modo.capa,n);
      if(!avoid) break;
      try{ segura=await rutaUna(key,avoid); break; }catch(e){ /* zona muy grande, reintenta con menos */ }
    }
    const rC=riesgoRuta(corta.geometry.coordinates, modo.capa);
    const rS=riesgoRuta(segura.geometry.coordinates, modo.capa);
    const igual = (segura===corta) || rS>=rC;          // no logro una mas segura
    map.getSource('r-corta').setData(igual?vacio():corta);
    map.getSource('r-segura').setData(segura);
    const nivel = rC>0 ? Math.min(1, rS/rC) : 0;
    map.setPaintProperty('r-segura','line-color', colorNivel(igual?0.15:nivel));
    const sum=segura.properties.summary;
    document.getElementById('r-dist').textContent=(sum.distance/1000).toFixed(1)+' km';
    document.getElementById('r-tiempo').textContent=Math.max(1,Math.round(sum.duration/60));
    document.getElementById('r-modo').textContent=modo.label;
    document.getElementById('resultado').classList.add('show');
    dibujarGauge(rS, rC, igual);
    ajustar(segura.geometry.coordinates);
    hideMsg();
  }catch(err){ showMsg('No se pudo trazar: '+err.message,'err'); }
}

// ---------- color y velocimetro ---------------------------------------------
function lerp(a,b,t){ return Math.round(a+(b-a)*t); }
function col3(t,c1,c2,c3){ let a,b,u;
  if(t<0.5){a=c1;b=c2;u=t*2;}else{a=c2;b=c3;u=(t-0.5)*2;}
  return 'rgb('+lerp(a[0],b[0],u)+','+lerp(a[1],b[1],u)+','+lerp(a[2],b[2],u)+')'; }
function colorNivel(t){ return col3(t,[37,99,235],[245,158,11],[220,38,38]); }   // azul->ambar->rojo
function colorGauge(t){ return col3(t,[250,204,21],[249,115,22],[220,38,38]); }  // amarillo->naranja->rojo
function polar(cx,cy,r,deg){ const a=deg*Math.PI/180; return [cx+r*Math.cos(a), cy-r*Math.sin(a)]; }
function arco(cx,cy,r,d1,d2){ const p1=polar(cx,cy,r,d1),p2=polar(cx,cy,r,d2);
  const large=Math.abs(d1-d2)>180?1:0;
  return 'M '+p1[0].toFixed(1)+' '+p1[1].toFixed(1)+' A '+r+' '+r+' 0 '+large+' 1 '+p2[0].toFixed(1)+' '+p2[1].toFixed(1); }
function dibujarGauge(seg,cor,igual){
  const f = cor>0? Math.min(1,seg/cor):0;          // fraccion de riesgo que queda
  const pct = cor>0? Math.max(0,Math.round(100*(cor-seg)/cor)):0;
  const cx=93,cy=92,r=72, endDeg=180-f*180;
  const [nx,ny]=polar(cx,cy,r*0.72,endDeg);
  document.getElementById('g-svg').innerHTML=
    '<path d="'+arco(cx,cy,r,180,0)+'" fill="none" stroke="#eee" stroke-width="13" stroke-linecap="round"/>'+
    (f>0?'<path d="'+arco(cx,cy,r,180,endDeg)+'" fill="none" stroke="'+colorGauge(f)+'" stroke-width="13" stroke-linecap="round"/>':'')+
    '<line x1="'+cx+'" y1="'+cy+'" x2="'+nx.toFixed(1)+'" y2="'+ny.toFixed(1)+'" stroke="#333" stroke-width="3"/>'+
    '<circle cx="'+cx+'" cy="'+cy+'" r="5" fill="#333"/>';
  document.getElementById('g-pct').innerHTML=pct+'<small>%</small>';
  document.getElementById('g-sub').innerHTML= (igual||pct<=0)?'La ruta corta ya es la mas segura'
    :'esquiva ~'+(cor-seg).toLocaleString()+' incidentes';
  document.getElementById('g-nueva').textContent='nueva: '+seg.toLocaleString();
  document.getElementById('g-peli').textContent='peligrosa: '+cor.toLocaleString();
  document.getElementById('gauge').classList.add('show');
}
function ajustar(coords){ let a=180,b=90,c=-180,d=-90;
  coords.forEach(p=>{ if(p[0]<a)a=p[0]; if(p[0]>c)c=p[0]; if(p[1]<b)b=p[1]; if(p[1]>d)d=p[1]; });
  map.fitBounds([[a,b],[c,d]],{padding:{top:60,bottom:60,left:60,right:380}}); }

document.getElementById('btn-trazar').addEventListener('click',trazar);
document.getElementById('btn-limpiar').addEventListener('click',()=>{
  setPunto('origen',null); setPunto('destino',null);
  map.getSource('r-corta').setData(vacio()); map.getSource('r-segura').setData(vacio());
  document.getElementById('resultado').classList.remove('show');
  document.getElementById('gauge').classList.remove('show'); hideMsg(); });
document.getElementById('link-key').addEventListener('click',()=>getKey(true));
bindAuto('in-origen','sug-origen','origen');
bindAuto('in-destino','sug-destino','destino');
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
