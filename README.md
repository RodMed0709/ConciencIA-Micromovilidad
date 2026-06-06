# ConciencIA — Micromovilidad Segura (CDMX)

Proyecto de hackathon: analiza siniestros viales y crimen en la Ciudad de México
para (1) mostrar **mapas de riesgo** por zona y (2) ofrecer un **constructor de
rutas** que estima un trayecto entre dos puntos por modo de viaje.

Datos abiertos del Portal CDMX (CKAN) + FGJ. **Ningún número se inventa**: los
scripts de Python leen los datos crudos y producen las cifras y los GeoJSON.

---

## TL;DR — abrir la demo sin programar

Los visores ya están generados en `data/processed/`. Ábrelos con doble clic (Chrome):

- **`mapa_riesgo.html`** — mapa de burbujas de riesgo (peatón / ciclista / moto / coches / crimen).
- **`ruta_segura.html`** — constructor de rutas: escribe origen y destino (o pica el mapa) y traza la ruta.

> El constructor de rutas necesita una **API key gratis de OpenRouteService**
> (ver sección [Constructor de rutas](#constructor-de-rutas)).

---

## Estructura

```
data/
  raw/        datos crudos descargados (1_nucleo = lo que usa el pipeline)
  processed/  salidas: CSV, PNG, GeoJSON y los .html (visores)
    geojson/  capas del mapa (riesgo_*.geojson, burbujas_*.geojson)
scripts/      pipeline de Python, numerado por orden de ejecución
requirements.txt
```

## Pipeline de scripts (orden)

| # | Script | Qué hace | Entrada → Salida |
|---|--------|----------|------------------|
| 00 | `00_data_downloader.py` | Descarga datasets de `1_nucleo` del Portal CDMX (CKAN) | API → `data/raw/1_nucleo/` |
| 01 | `01_analisis_nucleo.py` | Motor de análisis: clasifica por modo, hotspots, tablas/PNG y GeoJSON de riesgo + burbujas. Marca cercanía a universidades | `data/raw/1_nucleo` → `data/processed/` |
| 02 | `02_build_mapa.py` | Genera el visor del mapa de riesgo | `geojson/burbujas_*` → `mapa_riesgo.html` |
| 03 | `03_conteos_modos.py` | Cuenta accidentes por modo en cada fuente (cifras duras) | → `processed/analisis/conteos_modos.csv` |
| 04 | `04_accidentes_maestro.py` | Dataset maestro: une C5 + SSC en un CSV etiquetado por fuente y modo | `1_nucleo` → `accidentes_maestro.csv` |
| 05 | `05_seguridad.py` | Capa de crimen (robo a transeúnte) desde FGJ | `5_seguridad/...FGJ.csv` → `crimen_maestro.csv` |
| 06 | `06_burbujas_crimen.py` | Burbujas de crimen para el mapa | `crimen_maestro.csv` → `burbujas_crimen.geojson` |
| 07 | `07_burbujas_mapa.py` | Regenera las 5 capas de burbujas (acc + crimen) | maestros → `geojson/burbujas_*` |
| 07 | `07_build_ruta.py` | Genera el constructor de rutas | `geojson/burbujas_*` → `ruta_segura.html` |

> Hay dos scripts con prefijo `07` (mapa de burbujas y constructor de rutas);
> son independientes.

## Cómo correr el pipeline

```bash
pip install -r requirements.txt
python scripts/00_data_downloader.py     # baja data de 1_nucleo (~ varios cientos de MB)
python scripts/01_analisis_nucleo.py     # análisis + geojson base
python scripts/02_build_mapa.py          # mapa_riesgo.html
python scripts/07_build_ruta.py          # ruta_segura.html
```

(03–06 alimentan el dataset maestro y la capa de crimen; córrelos si vas a
regenerar todas las burbujas con `07_burbujas_mapa.py`.)

## Datos (importante)

- **CSV de C5 (>100 MB)** se versionan con **Git LFS**. Para clonarlos:
  ```bash
  git lfs install
  git clone https://github.com/RodMed0709/ConciencIA-Micromovilidad.git
  # si ya clonaste sin LFS:  git lfs pull
  ```
- Algunos CSV crudos/derivados **muy grandes** NO están en el repo (ver
  `.gitignore`); se **regeneran** corriendo los scripts (`00`, `04`, `05`).
- Encoding **UTF-8** en CSV/dbf (NO latin-1; latin-1 corrompe acentos).
  Excepción: el directorio de universidades sí viene en latin-1.
- **Las fuentes no se suman**: cada fila va etiquetada por `fuente`
  (C5 ≠ SSC ≠ FGJ). Filtra por fuente; no mezcles totales.

## Constructor de rutas

`ruta_segura.html` rutea en vivo contra **OpenRouteService (ORS)**.

1. Saca una API key gratis en <https://openrouteservice.org/dev> (2000 req/día).
2. Crea el archivo **`data/processed/ruta_key.js`** (está en `.gitignore`, nunca
   se sube) con:
   ```js
   window.ORS_KEY = "TU_API_KEY_AQUI";
   ```
3. Abre `data/processed/ruta_segura.html`. Si no existe `ruta_key.js`, el HTML te
   pide la key y la guarda en `localStorage` del navegador.

Modos: peatón (`foot-walking`), bici (`cycling-regular`), carro/moto
(`driving-car`). Entrada por texto con autocompletar (ORS Pelias, sesgado a CDMX)
o picando/arrastrando pines en el mapa.

> El riesgo (burbujas) aún **no** altera la ruta — va como capa de contexto
> apagable. Cablearlo es el siguiente paso.

## Notas

- Las capas de burbujas son por intensidad relativa a su propia capa; no compares
  el rojo entre capas como magnitud absoluta.
- Repo: <https://github.com/RodMed0709/ConciencIA-Micromovilidad>
