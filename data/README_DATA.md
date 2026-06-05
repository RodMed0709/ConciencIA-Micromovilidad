# Diccionario de datos — Movilidad Segura

Datos abiertos del **Portal de Datos Abiertos CDMX** (CKAN), grupo movilidad:
https://datos.cdmx.gob.mx/group/movilidad

- **Descargado:** 2026-06-05 (vía `scripts/download_data.py`).
- **Cobertura:** toda la CDMX (el modelo dará más peso a zonas universitarias).
- **Estructura:** `data/raw/{N_categoria}/{NN_dataset}/<recursos>`. Categorías y datasets numerados por prioridad; cada dataset trae TODOS sus recursos (data + diccionario + notas).

```
data/raw/
  1_nucleo/        01..06  (base del peligro)
  2_transporte/    07..09  (gtfs, rutas, metrobus)
  3_bici/          10..13  (ecobici, biciestacionamientos, afluencia)
  4_accesibilidad/ 14      (banquetas y rampas)
```
- **Procesado:** `data/processed/` (vacío por ahora; aquí irán los GeoJSON/JSON limpios que consume el frontend).

> **Privacidad:** solo datos abiertos y agregados. La ubicación del usuario vive en su navegador, no se almacena ni se rastrea. Cero PII.

---

## ⚠️ Notas técnicas para quien procese

- **Encoding: todos los CSV y dbf están en UTF-8.** Leer con `encoding='utf-8'` (pandas y pyshp). OJO: si lees como latin-1, los acentos se corrompen (miércoles/sábado se pierden). pyshp default ya es utf-8.
- **`incidentes-viales-c5`** (los 4 CSV grandes): columnas clave `folio, fecha_creacion, hora_creacion, dia_semana, tipo_incidente_c4, incidente_c4, alcaldia_*, latitud, longitud`. El campo `incidente_c4` trae "Atropellado", "Choque...", etc. → de aquí salen moto/atropellos.
- Los `.zip` de "puntos de accidentes", "infraestructura ciclista", "ciclovías 500m", "rutas", "metrobús", "biciestacionamientos", "banquetas-rampas" son **shapefiles (SHP)**. Descomprimir y leer con geopandas.
- Los `.kmz` y `.json/.geojson` son alternativas de la misma geometría (más fáciles para el mapa web).
- Archivos `diccionario_*.csv/.xlsx` = describen columnas del dataset, NO son la data.

---

## NIVEL 1 — Núcleo del peligro → `data/raw/1_nucleo/`

### `incidentes-viales-c5`
- **Qué es:** incidentes viales reportados por C5 (2014–2024), georreferenciados.
- **Uso:** base madre de dónde/cuándo ocurren incidentes. Filtrar atropellos y moto.
- **Recursos:** `inViales_2014_2015.csv`, `inViales_2016_2018.csv`, `inViales_2019_2021.csv`, `inViales_2022_2024.csv` (~437 MB total), `diccionario-incidentes-viales-c5.xlsx`.
- **Nota:** los CSV viven en `archivo.datos.cdmx.gob.mx` con cert SSL caducado; el script reintenta sin verificar (data pública legítima).

### `puntos-de-accidentes-de-ciclistas`
- **Qué es:** ubicaciones donde se accidentan ciclistas. **ORO** del mapa de peligro.
- **Uso:** núcleo de puntos rojos para ciclistas.
- **Recursos:** `puntos-de-accidentes-de-ciclistas.zip` (SHP), `diccionario_datos_accidentado_ciclista.csv`.

### `puntos-de-accidentes-a-peatones`
- **Qué es:** ubicaciones de accidentes de peatones. Capa peatonal del mapa de peligro.
- **Uso:** puntos rojos a pie.
- **Recursos:** `puntos-de-accidentes-de-peatones.zip` (SHP), `diccionario_datos_accidentado_peaton.csv`.

### `hechos-de-transito-reportados-por-ssc-base-comparativa`
- **Qué es:** hechos de tránsito reportados por la SSC (base comparativa).
- **Uso:** capa extra de accidentes para robustecer el modelo de riesgo.
- **Recursos:** `hechos-de-transito-reportados-por-ssc-base-comparativa.csv` (~9.8 MB) + nota informativa PDF.

### `infraestructura-vial-ciclista`
- **Qué es:** ciclovías y ciclocarriles reales de la CDMX.
- **Uso:** por dónde SÍ es seguro pedalear → baja el costo de ruta.
- **Recursos:** `.zip` (SHP), `.json`, `.kmz`, diccionario xlsx, nota PDF.

### `area-de-influencia-de-ciclovias-500-mts`
- **Qué es:** buffer de 500 m alrededor de ciclovías.
- **Uso:** qué tan cerca de una ciclovía estás → premia rutas protegidas.
- **Recursos:** `.zip` (SHP), diccionario csv.

---

## NIVEL 2 — Transporte / multimodal → `data/raw/2_transporte/`

### `gtfs` (búsqueda `q=GTFS`)
- **Qué es:** GTFS estático — estándar de transporte público (rutas, paradas, horarios, geometría).
- **Uso:** AVANZADO. Solo bajado por ahora; sirve para ruteo multimodal con tiempos.
- **Recursos:** `gtfs.zip` (~2.4 MB).

### `rutas-y-corredores-del-transporte-publico-concesionado`
- **Qué es:** geometría de rutas y corredores del transporte concesionado.
- **Uso:** mostrar conexiones de transporte en el mapa.
- **Recursos:** `concesionado_shp.zip`, `concesionado_kmz.zip`, descriptor xlsx.

### `geolocalizacion-metrobus`
- **Qué es:** líneas y estaciones del Metrobús.
- **Uso:** nodos de transbordo en el mapa multimodal.
- **Recursos:** `mb_shp.zip`, `mb_kmz.zip`, descriptor xlsx.

---

## NIVEL 3 — Bici → `data/raw/3_bici/`

### `biciestacionamientos`
- **Qué es:** biciestacionamientos públicos.
- **Uso:** dónde dejar/tomar bici (cierre multimodal).
- **Recursos:** `biciestacionamientos.zip` (SHP), `biciestacionamientos.json`, diccionario xlsx.

### `datos-de-bicicletas-ecobici`
- **Qué es:** datos de bicicletas Ecobici.
- **Uso:** componente del cierre multimodal en bici.
- **Recursos:** `ecobicis_20230430.csv` (~2 MB).

### `cicloestaciones-ecobici-nuevo-sistema`
- **Qué es:** cicloestaciones del nuevo sistema Ecobici.
- **Uso:** estaciones Ecobici para origen/destino multimodal.
- **Recursos:** `cicloestaciones_ecobici.zip` (SHP), `cicloestaciones_ecobici.csv`, diccionario xlsx.

---

## NIVEL 4 — Flujos (análisis) → `data/raw/3_bici/`

### `afluencia-diaria-del-sistema-ecobici` (búsqueda `q=viajes Ecobici`)
- **Qué es:** afluencia/viajes acumulados del sistema Ecobici (2024-07).
- **Uso:** patrones reales de uso de bici. Análisis, NO seguridad directa.
- **Recursos:** `afluencia_simple_acumulada_2024_07_.csv`, `afluencia_desglosada_acumulada_2024_07.csv` (~7.7 MB).
- **Nota:** la búsqueda devolvió afluencia/viajes; es el dato de flujos buscado.

---

## NIVEL 5 — Accesibilidad (carta secreta) → `data/raw/4_accesibilidad/`

### `banquetas-y-rampas-por-manzana`
- **Qué es:** inventario de banquetas y rampas por manzana.
- **Uso:** rutas accesibles (silla de ruedas, muletas). Diferenciador del proyecto.
- **Recursos:** `banquetas-y-rampas-por-manzana.zip` (~18 MB, SHP), diccionario csv.

---

## Estado de descarga (2026-06-05)

**14 / 14 datasets descargados.** 0 pendientes.

| Categoría | Dataset | Estado |
|---|---|---|
| nucleo | incidentes-viales-c5 | ✅ (4 CSV vía reintento SSL) |
| nucleo | puntos-de-accidentes-de-ciclistas | ✅ |
| nucleo | puntos-de-accidentes-a-peatones | ✅ |
| nucleo | hechos-de-transito-reportados-por-ssc-base-comparativa | ✅ |
| nucleo | infraestructura-vial-ciclista | ✅ |
| nucleo | area-de-influencia-de-ciclovias-500-mts | ✅ |
| transporte | gtfs | ✅ |
| transporte | rutas-y-corredores-del-transporte-publico-concesionado | ✅ |
| transporte | geolocalizacion-metrobus | ✅ |
| bici | biciestacionamientos | ✅ |
| bici | datos-de-bicicletas-ecobici | ✅ |
| bici | cicloestaciones-ecobici-nuevo-sistema | ✅ |
| bici | afluencia-diaria-del-sistema-ecobici | ✅ |
| accesibilidad | banquetas-y-rampas-por-manzana | ✅ |

Para re-descargar: `python scripts/download_data.py`
