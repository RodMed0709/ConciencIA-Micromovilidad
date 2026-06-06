# -*- coding: utf-8 -*-
"""
POST-PROCESADOR: inyecta un panel de CHAT con agente de IA en ruta_segurav2.html
SIN tocar el script que lo genera (08_build_ruta_segura.py, de otro autor).

El chat detecta "voy a tal lado / llevame a X / de A a B en bici" y dispara el
motor de ruta+riesgo que YA existe en v2, reusando sus funciones globales:
  setPunto(cual,{lon,lat,label})  -> fija origen/destino (auto-traza)
  getKey(), ORS_BASE, FOCO        -> geocoding ORS
  MODOS, #modos .modo (click)     -> cambiar modo (peaton/bici/coche-moto)

Deteccion de destino:
  1) Si hay window.OPENAI_KEY -> gpt-4o-mini con salida JSON (agente real).
  2) Si no -> parser por keywords (gratis, sin key).

Ejecutar DESPUES de 08:  python scripts/08_build_ruta_segura.py
                         python scripts/09_add_chat.py
Idempotente: re-ejecutar reemplaza el bloque inyectado.

Entrada/Salida (in-place): data/processed/ruta_segurav2.html
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "data", "processed", "ruta_segurav2.html")

START = "<!-- CHAT_AGENT_INJECTED:START -->"
END = "<!-- CHAT_AGENT_INJECTED:END -->"

BLOQUE = START + r"""
<style>
  #chat-fab{position:absolute;left:14px;bottom:14px;z-index:6;width:54px;height:54px;border:none;
    border-radius:50%;background:#2563eb;color:#fff;font-size:24px;cursor:pointer;
    box-shadow:0 4px 14px rgba(0,0,0,.3)}
  #chat-box{position:absolute;left:14px;bottom:14px;z-index:7;width:330px;max-width:calc(100vw - 28px);
    height:440px;max-height:70vh;background:#fff;border-radius:14px;display:none;flex-direction:column;
    box-shadow:0 8px 28px rgba(0,0,0,.3);overflow:hidden}
  #chat-box.abierto{display:flex}
  #chat-head{background:#2563eb;color:#fff;padding:10px 14px;font-size:14px;font-weight:600;
    display:flex;justify-content:space-between;align-items:center}
  #chat-head .x{cursor:pointer;font-size:18px;opacity:.9}
  #chat-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#f7f9fc}
  .cm{max-width:85%;padding:8px 11px;border-radius:12px;font-size:13px;line-height:1.4;white-space:pre-wrap}
  .cm.user{align-self:flex-end;background:#2563eb;color:#fff;border-bottom-right-radius:3px}
  .cm.bot{align-self:flex-start;background:#fff;border:1px solid #e4e9f2;color:#222;border-bottom-left-radius:3px}
  #chat-in{display:flex;border-top:1px solid #eee;padding:8px;gap:6px}
  #chat-in input{flex:1;border:1.5px solid #d0d0d0;border-radius:9px;padding:9px 10px;font-size:13px}
  #chat-in input:focus{outline:none;border-color:#2563eb}
  #chat-in button{border:none;background:#2563eb;color:#fff;border-radius:9px;padding:0 14px;cursor:pointer;font-size:15px}
  #chat-in button:disabled{background:#9db8ee}
</style>

<button id="chat-fab" title="Asistente de rutas">💬</button>
<div id="chat-box">
  <div id="chat-head"><span>🛡️ Asistente de Rutas</span><span class="x" id="chat-x">✕</span></div>
  <div id="chat-msgs"></div>
  <div id="chat-in">
    <input id="chat-txt" type="text" placeholder='Ej: "llévame a Coyoacán en bici"' autocomplete="off"/>
    <button id="chat-send">➤</button>
  </div>
</div>

<script>
(function(){
  // ---- helpers de UI -----------------------------------------------------
  const box=document.getElementById('chat-box');
  const fab=document.getElementById('chat-fab');
  const msgs=document.getElementById('chat-msgs');
  const txt=document.getElementById('chat-txt');
  const send=document.getElementById('chat-send');
  function abrir(v){ box.classList.toggle('abierto',v); fab.style.display=v?'none':'block';
    if(v && !msgs.childElementCount) pintar('Hola 👋 Dime a dónde vas y te trazo la ruta más segura. Ej: "voy a CU a pie" o "de Polanco a Coyoacán en coche".','bot'); }
  fab.onclick=()=>abrir(true);
  document.getElementById('chat-x').onclick=()=>abrir(false);
  function pintar(t,tipo){ const d=document.createElement('div'); d.className='cm '+tipo; d.textContent=t;
    msgs.appendChild(d); msgs.scrollTop=msgs.scrollHeight; return d; }

  // ---- mapeo de modo -> indice del boton ---------------------------------
  const MODO_IDX={peaton:0,bici:1,cochemoto:2,coches:2,moto:2,carro:2,coche:2};
  function setModo(modo){ const i=MODO_IDX[modo]; if(i==null) return;
    const b=document.querySelectorAll('#modos .modo'); if(b[i]) b[i].click(); }

  // ---- geocoding (reusa ORS de la pagina) --------------------------------
  async function geoUno(q){
    if(typeof getKey!=='function') return null;
    const key=getKey(); if(!key) return null;
    const base=(typeof ORS_BASE!=='undefined')?ORS_BASE:'https://api.openrouteservice.org';
    const foco=(typeof FOCO!=='undefined')?FOCO:{lon:-99.1332,lat:19.4326};
    const u=base+"/geocode/autocomplete?api_key="+encodeURIComponent(key)+"&text="+encodeURIComponent(q)+
      "&focus.point.lon="+foco.lon+"&focus.point.lat="+foco.lat+"&boundary.country=MX&size=1";
    try{ const r=await fetch(u); if(!r.ok) return null; const j=await r.json();
      const f=(j.features||[])[0]; if(!f) return null;
      return {lon:f.geometry.coordinates[0], lat:f.geometry.coordinates[1], label:f.properties.label};
    }catch(e){ return null; }
  }

  // ---- 1) agente OpenAI (estructurado) -----------------------------------
  const SYS=`Eres el asistente de "Rutas Seguras CDMX". Extrae la intencion de viaje del usuario.
Responde SOLO un JSON valido con esta forma exacta:
{"origen": string|null, "destino": string|null, "modo": "peaton"|"bici"|"cochemoto"|null, "respuesta": string}
- destino: a donde quiere ir (lugar/direccion en CDMX o Edomex). null si no lo dice.
- origen: de donde parte, solo si lo menciona; si no, null (se usa su punto actual).
- modo: peaton (a pie/caminando), bici (bicicleta), cochemoto (coche/auto/carro/moto/manejando). null si no lo dice.
- respuesta: 1-2 frases amables en español confirmando lo que haras (usa emojis).
No inventes coordenadas. Si no hay destino claro, pide la direccion en "respuesta" y deja destino null.`;
  async function extraerLLM(texto){
    const r=await fetch('https://api.openai.com/v1/chat/completions',{method:'POST',
      headers:{'Authorization':'Bearer '+window.OPENAI_KEY,'Content-Type':'application/json'},
      body:JSON.stringify({model:'gpt-4o-mini',temperature:0,response_format:{type:'json_object'},
        messages:[{role:'system',content:SYS},{role:'user',content:texto}]})});
    if(!r.ok){ throw new Error('openai '+r.status); }
    const j=await r.json();
    return JSON.parse(j.choices[0].message.content);
  }

  // ---- 2) fallback por keywords (sin IA) ---------------------------------
  function parseKW(t){
    const m=t.toLowerCase();
    let modo=null;
    if(/(a pie|caminando|caminar|peat[oó]n)/.test(m)) modo='peaton';
    else if(/(bici|bicicleta|ciclo)/.test(m)) modo='bici';
    else if(/(coche|carro|auto|moto|manej|conduc)/.test(m)) modo='cochemoto';
    let origen=null,destino=null,mm;
    if((mm=t.match(/\bde\s+(.+?)\s+a\s+(.+)$/i))){ origen=mm[1].trim(); destino=mm[2].trim(); }
    else if((mm=t.match(/(?:ir a|ruta a|ll[eé]v[ae]me a|llegar a|c[oó]mo llego a|voy a|hacia|hasta)\s+(.+)$/i))){ destino=mm[1].trim(); }
    const limpiar=s=>s&&s.replace(/\b(a pie|caminando|en bici|en bicicleta|en coche|en carro|en auto|en moto|manejando|por favor|porfa)\b/gi,'').replace(/[?.!]+$/,'').trim();
    return {origen:limpiar(origen)||null, destino:limpiar(destino)||null, modo, respuesta:null};
  }

  // ---- aplicar intencion al mapa -----------------------------------------
  async function aplicar(it){
    if(it.modo) setModo(it.modo);
    if(it.origen){ const o=await geoUno(it.origen); if(o && typeof setPunto==='function') setPunto('origen',o); }
    if(it.destino){ const d=await geoUno(it.destino); if(!d){ return {ok:false,motivo:'No encontré "'+it.destino+'".'}; }
      if(typeof setPunto==='function') setPunto('destino',d); return {ok:true,label:d.label}; }
    return {ok:false,motivo:'sin_destino'};
  }
  function resumenRuta(){
    const g=id=>{const e=document.getElementById(id); return e?e.textContent.trim():'';};
    const dist=g('r-dist'), t=g('r-tiempo'), pct=g('g-pct');
    if(!dist || dist==='-- km') return '';
    let s='✅ Listo: '+dist+', ~'+t+' min.';
    if(pct && /\d/.test(pct)) s+=' Evita ~'+pct+' del riesgo de la ruta corta. 🛡️';
    return s;
  }

  // ---- enviar ------------------------------------------------------------
  let ocupado=false;
  async function enviar(){
    const texto=txt.value.trim(); if(!texto || ocupado) return;
    txt.value=''; pintar(texto,'user'); ocupado=true; send.disabled=true;
    try{
      let it=null;
      if(window.OPENAI_KEY){ try{ it=await extraerLLM(texto); }catch(e){ console.warn('LLM falló, uso keywords:',e.message); } }
      if(!it || (!it.destino && !it.origen)){ const kw=parseKW(texto); if(!it) it=kw; else { it.origen=it.origen||kw.origen; it.destino=it.destino||kw.destino; it.modo=it.modo||kw.modo; } }
      if(it.respuesta) pintar(it.respuesta,'bot');
      if(!it.destino && !it.origen){ if(!it.respuesta) pintar('¿A dónde vas? Ej: "llévame a Coyoacán en bici".','bot'); return; }
      const esperando=pintar('🔎 Buscando y trazando ruta segura...','bot');
      const res=await aplicar(it);
      if(res && res.ok===false && res.motivo && res.motivo!=='sin_destino'){ esperando.textContent='❌ '+res.motivo+' Prueba calle + colonia.'; return; }
      // esperar (poll) a que el motor de v2 trace y rellene el resultado
      let resumen='';
      for(let i=0;i<40;i++){ await new Promise(r=>setTimeout(r,250)); resumen=resumenRuta(); if(resumen) break; }
      esperando.textContent = resumen || ('📍 Marqué '+((res&&res.label)||'el destino')+'. Si falta tu origen, márcalo en el mapa (clic).');
    } finally { ocupado=false; send.disabled=false; txt.focus(); }
  }
  send.onclick=enviar;
  txt.addEventListener('keydown',e=>{ if(e.key==='Enter') enviar(); });
})();
</script>
""" + END


def main():
    if not os.path.exists(HTML):
        raise SystemExit("No existe " + HTML + " (corre antes 08_build_ruta_segura.py)")
    html = open(HTML, encoding="utf-8").read()

    # quitar inyeccion previa (idempotente)
    html = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html, flags=re.S).rstrip()

    if "</body>" in html:
        html = html.replace("</body>", BLOQUE + "\n</body>", 1)
    else:
        html = html + BLOQUE

    open(HTML, "w", encoding="utf-8").write(html)
    print("Chat inyectado en:", HTML)
    print("Agente: OpenAI (window.OPENAI_KEY en ruta_key.js) o fallback por keywords.")


if __name__ == "__main__":
    main()
