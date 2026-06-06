# VíaVital.ai — App (landing + demo)

Frontend hecho en **Lovable** (TanStack Start + React 19 + Tailwind v4).
Landing pública + demo interactivo de 5 pantallas (login → chat IA → mapa → mobility pool → rating).

## Cómo se conecta con los mapas

El demo (`src/components/DemoModal.tsx`) ya enlaza a los mapas estáticos:

- `/ruta_segurav2.html` — ruta segura con motor de riesgo (MapLibre + ruteo OpenRouteService)
- `/mapa_riesgo.html` — mapa de burbujas de riesgo

Ambos viven en `public/` y se sirven como estáticos. **Las API keys (ORS + Mapbox)
van inline dentro de `ruta_segurav2.html`** — el archivo es autónomo, funciona para
cualquiera que abra la URL, sin pedir key.

> Las keys son demo: ORS free (rate-limited) y token público de Mapbox (`pk.`),
> el mismo que ya usa el demo. Para producción, restringe el token por URL en mapbox.com.

## Correr local

```bash
cd app
npm install --legacy-peer-deps   # npm es estricto con el peer de nitro; bun no lo necesita
npm run dev                      # http://localhost:3000  (o el puerto que imprima)
```

Verifica el mapa directo: `http://localhost:3000/ruta_segurav2.html`

## Publicar (que cualquiera le pique y funcione)

El build usa **nitro con target Cloudflare** (default de Lovable). Tres caminos:

1. **Lovable Publish (lo más rápido).** Si este código está en tu proyecto Lovable
   (Lovable ↔ GitHub sync), abre Lovable y dale **Publish**. Te da una URL
   `*.lovable.app` pública. Asegúrate de que `public/ruta_segurav2.html` y
   `public/mapa_riesgo.html` estén en el proyecto (si no, en el chat de Lovable:
   "agrega estos archivos a public").
2. **Cloudflare Pages.** Conecta el repo, build `npm run build`, output `.output`.
3. **Local para jueces en vivo:** `npm run build && npm run preview`.

## Estructura

```
app/
  src/routes/index.tsx        landing
  src/components/DemoModal.tsx demo 5 pantallas (login → ... → enlaza ruta/mapa)
  public/ruta_segurav2.html   mapa ruta segura (keys inline, autónomo)
  public/mapa_riesgo.html     mapa de riesgo (autónomo)
```
