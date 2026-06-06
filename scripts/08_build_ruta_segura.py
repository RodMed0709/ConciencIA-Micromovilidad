# -*- coding: utf-8 -*-
"""
ruta_segurav2.html — Constructor de RUTA SEGURA (motor de riesgo real).

Diferencia con ruta_segura (v1): aqui el riesgo SI altera la ruta.
- Pide a ORS varias rutas alternativas.
- Puntua cada una por # de incidentes cercanos (usando las burbujas del modo
  activo: peaton/bici incluyen robos; moto/coches solo accidentes).
- Dibuja la ruta CORTA en gris transparente y la ruta SEGURA en verde.
- Muestra % de riesgo mitigado (incidentes esquivados).
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
    {"id": "peaton",   "label": "Peaton",  "emoji": "\U0001F6B6", "perfil": "foot-walking",   "capa": "peaton"},
    {"id": "bici",     "label": "Bici",    "emoji": "\U0001F6B2", "perfil": "cycling-regular", "capa": "ciclista"},
    {"id": "moto",     "label": "Moto",    "emoji": "\U0001F3CD",  "perfil": "driving-car",     "capa": "moto"},
    {"id": "coches",   "label": "Coches",  "emoji": "\U0001F697", "perfil": "driving-car",     "capa": "coches"},
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
        sub = df[df["_n"].str.contains(patron, na=False)]
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
    unis = [{"nombre": n, "lat": v[0], "lon": v[1]} for n, v in UNIVERSIDADES.items()]

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
  .modo.activo{border-color:#16a34a;background:#e9f9ef;color:#15803d;font-weight:600}
  .modo .ic{display:block;font-size:17px;line-height:1.1}
  .campo{position:relative;margin-bottom:10px}
  .campo label{display:block;font-size:11px;color:#555;margin-bottom:3px;text-transform:uppercase;letter-spacing:.03em}
  .campo input{width:100%;box-sizing:border-box;padding:9px 10px;border:1.5px solid #d0d0d0;border-radius:8px;font-size:13px}
  .campo input:focus{outline:none;border-color:#16a34a}
  .sugerencias{position:absolute;z-index:5;left:0;right:0;background:#fff;border:1px solid #ddd;
    border-radius:0 0 8px 8px;max-height:200px;overflow-y:auto;box-shadow:0 6px 14px rgba(0,0,0,.12)}
  .sugerencias div{padding:8px 10px;font-size:12.5px;cursor:pointer;border-top:1px solid #f0f0f0}
  .sugerencias div:hover{background:#e9f9ef}
  .acciones{display:flex;gap:8px;margin:6px 0 12px}
  .btn{flex:1;padding:10px 0;border:none;border-radius:9px;font-size:13.5px;cursor:pointer;font-weight:600}
  .btn-primary{background:#16a34a;color:#fff}
  .btn-primary:disabled{background:#a7d7b9;cursor:default}
  .btn-ghost{background:#f0f0f0;color:#333}
  .resultado{background:#f3fbf5;border:1px solid #cdeed7;border-radius:10px;padding:12px;font-size:13px;display:none}
  .resultado.show{display:block}
  .resultado .big{font-size:22px;font-weight:700;color:#15803d}
  .resultado .row{display:flex;justify-content:space-between;margin-top:6px;color:#444}
  .mitiga{margin-top:10px;padding:9px 11px;background:#16a34a;color:#fff;border-radius:8px;font-size:13px}
  .mitiga b{font-size:18px}
  .leg{display:flex;align-items:center;gap:7px;margin-top:8px;font-size:12px;color:#555}
  .sw{width:22px;height:0;border-top:4px solid}
  .msg{font-size:12.5px;padding:9px 11px;border-radius:8px;margin-bottom:10px;display:none}
  .msg.show{display:block}
  .msg.err{background:#fdecec;color:#b3261e;border:1px solid #f5c2c0}
  .msg.info{background:#fff7e6;color:#92600a;border:1px solid #f3dca0}
  .ayuda{font-size:11px;color:#888;line-height:1.4;margin-top:10px}
  .ayuda a{color:#16a34a;cursor:pointer}
  .seccion{border-top:1px solid #eee;margin-top:14px;padding-top:12px}
  .seccion h2{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#777;margin:0 0 6px}
  .leyenda .barra{height:10px;border-radius:5px;margin:6px 0 2px;
    background:linear-gradient(90deg,#ffffb2,#fed976,#feb24c,#fd8d3c,#fc4e2a,#e31a1c,#b10026)}
  .leyenda small{font-size:10.5px;color:#888}
  .pin{font-size:26px;line-height:1;cursor:grab;filter:drop-shadow(0 2px 2px rgba(0,0,0,.35))}
  .uni-dot{width:11px;height:11px;border-radius:50%;background:#7c3aed;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.4)}
</style>
</head>
<body>
<div id="map"></div>
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
    <div><span class="big" id="r-tiempo">--</span> <span style="color:#15803d">min aprox</span></div>
    <div class="row"><span>Distancia</span><b id="r-dist">-- km</b></div>
    <div class="row"><span>Modo</span><b id="r-modo">--</b></div>
    <div class="mitiga" id="mitiga"></div>
    <div class="leg"><span class="sw" style="border-color:#16a34a"></span> Ruta segura</div>
    <div class="leg"><span class="sw" style="border-color:#94a3b8;border-top-style:dashed"></span> Ruta corta (mas riesgo)</div>
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
const map=new maplibregl.Map({container:'map',
  style:{version:8,sources:{base:{type:'raster',
    tiles:['https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png','https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'],
    tileSize:256,attribution:'&copy; OpenStreetMap &copy; CARTO'}},
    layers:[{id:'base',type:'raster',source:'base'}]},
  center:[-99.13,19.40],zoom:10.5});
map.addControl(new maplibregl.NavigationControl(),'top-right');
window.__map=map;

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
  // rutas: corta (gris discontinua) abajo, segura (verde) arriba
  map.addSource('r-corta',{type:'geojson',data:vacio()});
  map.addLayer({id:'r-corta',type:'line',source:'r-corta',layout:{'line-cap':'round','line-join':'round'},
    paint:{'line-color':'#94a3b8','line-width':5,'line-opacity':0.55,'line-dasharray':[2,2]}});
  map.addSource('r-segura',{type:'geojson',data:vacio()});
  map.addLayer({id:'r-segura-casing',type:'line',source:'r-segura',layout:{'line-cap':'round','line-join':'round'},
    paint:{'line-color':'#14532d','line-width':9,'line-opacity':0.6}});
  map.addLayer({id:'r-segura',type:'line',source:'r-segura',layout:{'line-cap':'round','line-join':'round'},
    paint:{'line-color':'#16a34a','line-width':5.5}});
  // universidades
  UNIS.forEach(u=>{ const el=document.createElement('div'); el.className='uni-dot';
    new maplibregl.Marker({element:el}).setLngLat([u.lon,u.lat])
      .setPopup(new maplibregl.Popup({offset:12}).setHTML('<b>'+u.nombre+'</b>')).addTo(map); });
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

// ---------- trazar: pide alternativas, puntua riesgo, elige la mas segura ----
async function rutas(key){
  const body={coordinates:[[origen.lon,origen.lat],[destino.lon,destino.lat]],
    alternative_routes:{target_count:3,weight_factor:1.7,share_factor:0.5},instructions:false};
  let r=await fetch(ORS_BASE+"/v2/directions/"+modo.perfil+"/geojson",
    {method:'POST',headers:{'Authorization':key,'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!r.ok){ // reintento sin alternativas (algunos perfiles no las soportan)
    r=await fetch(ORS_BASE+"/v2/directions/"+modo.perfil+"/geojson",
      {method:'POST',headers:{'Authorization':key,'Content-Type':'application/json'},
       body:JSON.stringify({coordinates:body.coordinates,instructions:false})});
    if(!r.ok){ const t=await r.text(); throw new Error(r.status+' '+t.slice(0,120)); }
  }
  const j=await r.json(); return j.features||[];
}
async function trazar(){
  if(!(origen&&destino))return; const key=getKey();
  if(!key){ showMsg('Necesitas tu API key de ORS.','info'); return; }
  showMsg('Calculando ruta segura...','info');
  try{
    const fs=await rutas(key);
    if(!fs.length) throw new Error('sin rutas');
    // puntuar cada alternativa
    const evaluadas=fs.map(f=>({f,
      dist:f.properties.summary.distance, dur:f.properties.summary.duration,
      riesgo:riesgoRuta(f.geometry.coordinates, modo.capa)}));
    const corta = evaluadas.reduce((a,b)=> b.dur<a.dur?b:a);      // mas rapida = "corta"
    const segura= evaluadas.reduce((a,b)=> b.riesgo<a.riesgo?b:a); // menos riesgo
    // dibujar
    map.getSource('r-corta').setData(corta===segura?vacio():corta.f);
    map.getSource('r-segura').setData(segura.f);
    // resultado
    document.getElementById('r-dist').textContent=(segura.dist/1000).toFixed(1)+' km';
    document.getElementById('r-tiempo').textContent=Math.max(1,Math.round(segura.dur/60));
    document.getElementById('r-modo').textContent=modo.label;
    const mit=document.getElementById('mitiga');
    if(corta===segura || corta.riesgo<=segura.riesgo){
      mit.innerHTML='La ruta mas corta ya es la mas segura para '+modo.label.toLowerCase()+'.';
    }else{
      const pct=Math.round(100*(corta.riesgo-segura.riesgo)/Math.max(1,corta.riesgo));
      const dif=corta.riesgo-segura.riesgo;
      mit.innerHTML='Riesgo mitigado <b>'+pct+'%</b><br><small>esquiva ~'+dif.toLocaleString()+
        ' incidentes vs la ruta corta ('+segura.riesgo.toLocaleString()+' vs '+corta.riesgo.toLocaleString()+')</small>';
    }
    document.getElementById('resultado').classList.add('show');
    ajustar(segura.f.geometry.coordinates);
    hideMsg();
  }catch(err){ showMsg('No se pudo trazar: '+err.message,'err'); }
}
function ajustar(coords){ let a=180,b=90,c=-180,d=-90;
  coords.forEach(p=>{ if(p[0]<a)a=p[0]; if(p[0]>c)c=p[0]; if(p[1]<b)b=p[1]; if(p[1]>d)d=p[1]; });
  map.fitBounds([[a,b],[c,d]],{padding:{top:60,bottom:60,left:60,right:380}}); }

document.getElementById('btn-trazar').addEventListener('click',trazar);
document.getElementById('btn-limpiar').addEventListener('click',()=>{
  setPunto('origen',null); setPunto('destino',null);
  map.getSource('r-corta').setData(vacio()); map.getSource('r-segura').setData(vacio());
  document.getElementById('resultado').classList.remove('show'); hideMsg(); });
document.getElementById('link-key').addEventListener('click',()=>getKey(true));
bindAuto('in-origen','sug-origen','origen');
bindAuto('in-destino','sug-destino','destino');
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
