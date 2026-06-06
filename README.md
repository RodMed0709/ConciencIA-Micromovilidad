# ConciencIA — Micromovilidad Segura (CDMX)

Proyecto de hackathon: analiza siniestros viales y crimen en la Ciudad de México
para (1) mostrar **mapas de riesgo** por zona y (2) ofrecer una **ruta segura**
que, entre varias opciones, elige la que **esquiva más incidentes** por modo de viaje.

Datos abiertos del Portal CDMX (CKAN) + FGJ. **Ningún número se inventa**: los
scripts de Python leen los datos crudos y producen las cifras y los GeoJSON.

---

## 🌐 Sitio web (landing + demo)

La página está en **`app/`** (React + Vite). Landing + demo de celular:
login → chat IA → mapa → **ruta segura real** (motor de riesgo).

**Verla en vivo:** _(deploy en Vercel — pega la URL aquí cuando esté lista)_

**Correrla en local:**
```bash
cd app
npm install
npm run dev        # abre http://localhost:8080
```

> ⚠️ Abrir este repo en GitHub **no** ejecuta la página — GitHub solo muestra el
> código. Para verla funcionando: usa el link de Vercel de arriba, o córrela local
> con los dos comandos de arriba.

---

## TL;DR — abrir la demo sin programar

Los visores ya están generados en `data/processed/`. Ábrelos con doble clic (Chrome):

- ⭐ **`ruta_segurav2.html`** — **la demo principal.** Ruta segura con motor de
  riesgo real: eliges modo (peatón / bici / coche-moto), origen y destino, y traza
  **dos rutas** — la más corta (roja, más riesgo) y la **recomendada** (esquiva
  zonas de accidentes y robos). Velocímetro abajo-derecha con el **% de riesgo
  mitigado** (verde) y los incidentes de cada ruta. Universidades marcadas con
  halo morado.
- **`mapa_riesgo.html`** — mapa de burbujas de riesgo (peatón / ciclista / moto /
  coches / crimen) + pines de universidades. Para explorar dónde pega más fuerte.
- `ruta_segura.html` — versión básica del constructor de rutas (solo traza, **no**
  evalúa riesgo). Quedó como base; usa la v2.

> Las rutas necesitan una **API key gratis de OpenRouteService**
> (ver sección [Rutas](#rutas-ors)).

---

## Estructura

```
data/
  raw/        datos crudos descargados (1_nucleo = accidentes/ciclovías, 5_seguridad = crimen)
  processed/  salidas: CSV, PNG, GeoJSON y los .html (visores)
    geojson/  capas del mapa (riesgo_*.geojson, burbujas_*.geojson)
    analisis/ tablas CSV + PNG de patrones
scripts/      pipeline de Python, numerado por orden de ejecución
requirements.txt
```

## Pipeline de scripts (orden)

| # | Script | Qué hace | Entrada → Salida |
|---|--------|----------|------------------|
| 00 | `00_data_downloader.py` | Descarga datasets (núcleo + crimen FGJ) del Portal CDMX | API → `data/raw/` |
| 01 | `01_analisis_nucleo.py` | Motor de análisis: clasifica por modo, hotspots, tablas/PNG y GeoJSON de riesgo + burbujas. Marca cercanía a universidades | `data/raw/1_nucleo` → `data/processed/` |
| 02 | `02_build_mapa.py` | Visor del mapa de riesgo (5 capas + unis) | `geojson/burbujas_*` → `mapa_riesgo.html` |
| 03 | `03_conteos_modos.py` | Cuenta accidentes por modo en cada fuente (cifras duras) | → `analisis/conteos_modos.csv` |
| 04 | `04_accidentes_maestro.py` | Dataset maestro: une C5 + SSC, etiquetado por fuente y modo | `1_nucleo` → `accidentes_maestro.csv` |
| 05 | `05_seguridad.py` | Capa de crimen (robo a transeúnte) desde FGJ | `5_seguridad/...FGJ.csv` → `crimen_maestro.csv` |
| 06 | `06_burbujas_crimen.py` | Burbujas de crimen para el mapa | `crimen_maestro.csv` → `burbujas_crimen.geojson` |
| 07 | `07_burbujas_mapa.py` | Genera las capas de burbujas del mapa/rutas (acc por modo desde C5 + robos en peatón/bici + capa `cochemoto`) | maestros → `geojson/burbujas_*` |
| 07 | `07_build_ruta.py` | Constructor de rutas básico (sin riesgo) | `geojson/burbujas_*` → `ruta_segura.html` |
| 08 | `08_build_ruta_segura.py` | **Ruta segura v2** (motor de riesgo, gauge, unis curadas) | `geojson/burbujas_*` + directorio unis → `ruta_segurav2.html` |

> Hay dos scripts con prefijo `07` (mapa de burbujas y ruta básica); son
> independientes. El `08` es el bueno para rutas.

## Cómo correr el pipeline

```bash
pip install -r requirements.txt
python scripts/00_data_downloader.py     # baja data núcleo + crimen FGJ (~cientos de MB)
python scripts/01_analisis_nucleo.py     # análisis + geojson base
python scripts/04_accidentes_maestro.py  # maestro C5+SSC
python scripts/05_seguridad.py           # crimen_maestro.csv (robo a transeúnte)
python scripts/06_burbujas_crimen.py     # burbujas de crimen
python scripts/07_burbujas_mapa.py       # capas de burbujas (acc por modo + robos + cochemoto)
python scripts/02_build_mapa.py          # mapa_riesgo.html
python scripts/08_build_ruta_segura.py   # ruta_segurav2.html  <- la demo principal
```

## Modos y capas de riesgo

- **Un modo por viaje**: peatón, bici, coche/moto. (Coche y moto van juntos en
  una capa de vehículos.)
- **Capa de peligro = accidentes + crimen**:
  - Accidentes desde **C5** (11 años de volumen) clasificados por modo.
  - **Robo a transeúnte (FGJ, ~148k)** se suma al riesgo de **peatón y bici**
    (a quien va a pie o en bici lo asaltan igual). Solo en el mapa/ruteo; en los
    datos duros las fuentes quedan separadas.
- **Burbujas**: agrupan incidentes por cercanía; tamaño y color (amarillo→rojo)
  crecen con el número de siniestros.

## Rutas (ORS)

`ruta_segurav2.html` y `ruta_segura.html` rutean en vivo contra
**OpenRouteService (ORS)**.

1. Saca una API key gratis en <https://openrouteservice.org/dev> (2000 req/día).
2. Crea **`data/processed/ruta_key.js`** (está en `.gitignore`, nunca se sube):
   ```js
   window.ORS_KEY = "TU_API_KEY_AQUI";
   ```
3. Abre el `.html`. Si no existe `ruta_key.js`, el HTML te pide la key y la guarda
   en `localStorage`.

**Cómo funciona la v2 (motor de riesgo):**
1. Pide a ORS la ruta sin restricción = la **más corta** (roja, aunque cruce rojo).
2. Toma las **peores burbujas** del modo activo en el corredor origen→destino y las
   manda como `options.avoid_polygons` (cuadritos ~130 m). ORS **rerutea sobre su
   grafo evitando esas zonas** → la ruta **recomendada** (no es rankeo, la API
   esquiva de verdad). Si rechaza por tamaño, baja el # de zonas (30→12) y, en
   último caso, cae al método de comparar.
3. Puntúa ambas por # de incidentes cercanos (≤120 m, índice espacial de rejilla +
   haversine) para el velocímetro: **% mitigado** e incidentes `nueva` vs `peligrosa`.

El color de la recomendada va azul→rojo según su riesgo. Si la más corta ya es la
más segura, muestra una sola y lo dice.

> Nota: el pathfinding (grafo + Dijkstra/CH) lo hace ORS. Nosotros aportamos las
> zonas a evitar (datos de riesgo) y la puntuación. El "grafo propio con costo =
> distancia + α·riesgo sobre OSM" sería el siguiente nivel.

Entrada por texto con autocompletar (ORS Pelias, sesgado a CDMX) o picando/
arrastrando pines en el mapa.

## Datos (importante)

- **CSV de C5 (>100 MB)** se versionan con **Git LFS**:
  ```bash
  git lfs install
  git clone https://github.com/RodMed0709/ConciencIA-Micromovilidad.git
  # si ya clonaste sin LFS:  git lfs pull
  ```
- CSV crudos/derivados **muy grandes** NO están en el repo (ver `.gitignore`); se
  **regeneran** corriendo los scripts (`00`, `04`, `05`).
- Encoding **UTF-8** en CSV/dbf (NO latin-1; latin-1 corrompe acentos).
  Excepción: el directorio de universidades sí viene en latin-1.
- **Las fuentes no se suman**: cada fila va etiquetada por `fuente`
  (C5 ≠ SSC ≠ FGJ). Filtra por fuente; no mezcles totales.

## Notas

- Las burbujas son por intensidad relativa a su propia capa; no compares el rojo
  entre capas como magnitud absoluta.
- Repo: <https://github.com/RodMed0709/ConciencIA-Micromovilidad>
