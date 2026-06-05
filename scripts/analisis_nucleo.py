# -*- coding: utf-8 -*-
"""
Analisis exploratorio (EDA) del nucleo de accidentes — Movilidad Segura.

Fuentes:
  01 incidentes_viales_c5  (CSV, fuente C5 / call center, filtrado a atropello/ciclista/moto)
  02 puntos_accidentes_ciclistas (shapefile, registro SSC ciclista)
  03 puntos_accidentes_peatones  (shapefile, registro SSC peaton)
  04 hechos_transito_ssc (CSV, registro SSC todos los modos) -- comparativo + check de folios

Las CIFRAS las saca este script, no se inventan. Salidas:
  - tablas impresas en consola
  - CSV resumen en data/processed/analisis/
  - graficas PNG en data/processed/analisis/

Reglas: cobertura toda CDMX; se marca cuantos accidentes caen cerca de zonas
universitarias (enfasis del proyecto). Encoding de los CSV/dbf: UTF-8.
"""

import os
import io
import json
import zipfile
import math
import unicodedata

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # sin ventana, solo guarda PNG
import matplotlib.pyplot as plt
import shapefile  # pyshp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "1_nucleo")
OUT = os.path.join(ROOT, "data", "processed", "analisis")
os.makedirs(OUT, exist_ok=True)

# Bounding box CDMX (descartar coords basura / 0,0)
LON_MIN, LON_MAX = -99.40, -98.90
LAT_MIN, LAT_MAX = 19.00, 19.60

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
RADIO_UNI_KM = 1.5  # un accidente "cerca de uni" si cae a <=1.5 km de algun campus

# Mapeo de categorias EXACTAS de C5 (incidente_c4, sin acentos/lower) -> modo.
# C5 SI separa los modos; antes los juntaba todos en una bolsa (bug).
MODO_C5 = {
    "atropellado": "peaton",
    "persona atropellada": "peaton",
    "ciclista": "ciclista",
    "motociclista": "motociclista",
    "monopatin": "scooter",
}

ANIO_MIN, ANIO_MAX = 2010, 2025  # descartar anios basura

# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------

def haversine_km_vec(lat, lon, lat0, lon0):
    """Distancia haversine (km) de arrays (lat,lon) a un punto (lat0,lon0)."""
    R = 6371.0
    lat = np.radians(lat); lon = np.radians(lon)
    lat0 = math.radians(lat0); lon0 = math.radians(lon0)
    dphi = lat - lat0
    dl = lon - lon0
    a = np.sin(dphi / 2) ** 2 + np.cos(lat) * math.cos(lat0) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def hora_a_num(v):
    """'13:51', '13:51:20', 13.0 -> entero 0..23 o NaN (descarta fuera de rango)."""
    if pd.isna(v):
        return np.nan
    s = str(v).strip()
    if ":" in s:
        try:
            h = int(s.split(":")[0])
        except Exception:
            return np.nan
    else:
        try:
            h = int(float(s))
        except Exception:
            return np.nan
    return h if 0 <= h <= 23 else np.nan


def sin_acentos(s):
    """quita acentos de forma robusta: miércoles->miercoles, sábado->sabado."""
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def limpia_txt(serie):
    """Normaliza texto: strip + upper + convierte 'NAN'/'NONE'/'' en cadena vacia."""
    s = serie.astype(str).str.strip().str.upper()
    return s.where(~s.isin(["NAN", "NONE", "<NA>", ""]), "")


def normaliza_dia(v):
    if pd.isna(v):
        return np.nan
    s = sin_acentos(str(v).strip().lower()).replace("�", "")
    for d in ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]:
        if s.startswith(d[:4]):
            return d
    return s


ORDEN_DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


# ----------------------------------------------------------------------------
# Lectores -> DataFrame normalizado
# columnas estandar: fuente, no_folio, anio, dia, hora, lon, lat, alcaldia, colonia, tipo, occisos, lesionados
# ----------------------------------------------------------------------------

def leer_shapefile_zip(zip_path):
    z = zipfile.ZipFile(zip_path)
    def member(ext):
        for n in z.namelist():
            if n.endswith(ext) and "__MACOSX" not in n:
                return n
        return None
    miembros = {e: member(e) for e in (".shp", ".dbf", ".shx")}
    faltan = [e for e, m in miembros.items() if m is None]
    if faltan:
        raise FileNotFoundError(f"Shapefile incompleto en {zip_path}: faltan {faltan}")
    r = shapefile.Reader(
        shp=io.BytesIO(z.read(miembros[".shp"])),
        dbf=io.BytesIO(z.read(miembros[".dbf"])),
        shx=io.BytesIO(z.read(miembros[".shx"])),
        encoding="utf-8",
    )
    flds = [f[0] for f in r.fields[1:]]
    rows = []
    for sr in r.iterShapeRecords():
        d = dict(zip(flds, sr.record))
        pts = sr.shape.points
        lon, lat = (pts[0][0], pts[0][1]) if pts else (np.nan, np.nan)
        rows.append({"rec": d, "lon": lon, "lat": lat})
    return rows


def df_ciclista_peaton(zip_path, fuente):
    rows = leer_shapefile_zip(zip_path)
    out = []
    for x in rows:
        d = x["rec"]
        out.append({
            "fuente": fuente,
            "no_folio": d.get("no_folio"),
            "anio": pd.to_numeric(d.get("ano_evento"), errors="coerce"),
            "dia": normaliza_dia(d.get("dia")),
            "hora": hora_a_num(d.get("hora")),
            "lon": x["lon"], "lat": x["lat"],
            "alcaldia": str(d.get("alcaldia") or "").strip().upper(),
            "colonia": str(d.get("colonia") or "").strip().upper(),
            "tipo": str(d.get("tipo_de_ev") or "").strip(),
            "occisos": pd.to_numeric(d.get("total_occi"), errors="coerce"),
            "lesionados": pd.to_numeric(d.get("total_lesi"), errors="coerce"),
        })
    return pd.DataFrame(out)


def df_ssc_csv(csv_path, fuente):
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    cols = {c.lower(): c for c in df.columns}
    def col(name):
        return cols.get(name)
    out = pd.DataFrame({
        "fuente": fuente,
        "no_folio": df[col("no_folio")] if col("no_folio") else np.nan,
        "anio": pd.to_numeric(df[col("ano_evento")], errors="coerce") if col("ano_evento") else np.nan,
        "dia": df[col("dia")].map(normaliza_dia) if col("dia") else np.nan,
        "hora": df[col("hora")].map(hora_a_num) if col("hora") else np.nan,
        "lon": pd.to_numeric(df[col("coordenada_x")], errors="coerce") if col("coordenada_x") else np.nan,
        "lat": pd.to_numeric(df[col("coordenada_y")], errors="coerce") if col("coordenada_y") else np.nan,
        "alcaldia": limpia_txt(df[col("alcaldia")]) if col("alcaldia") else "",
        "colonia": limpia_txt(df[col("colonia")]) if col("colonia") else "",
        "tipo": df[col("tipo_de_evento")].astype(str).str.strip() if col("tipo_de_evento") else "",
        "occisos": pd.to_numeric(df[col("total_occisos")], errors="coerce") if col("total_occisos") else np.nan,
        "lesionados": pd.to_numeric(df[col("total_lesionados")], errors="coerce") if col("total_lesionados") else np.nan,
    })
    return out


def df_modos_04(csv_path):
    """
    Una sola fuente (04 SSC, 2018-2019) clasificada por MODO de la victima/actor,
    sin doble conteo. Prioridad por evento+vehiculo involucrado:
      1) peaton   = tipo_de_evento ATROPELLADO
      2) ciclista = bicicleta involucrada (y no atropellado)
      3) moto     = motocicleta involucrada (y no bici/atropello)
      4) coches   = el resto (choques de auto, etc.)
    Devuelve DataFrame normalizado con columna 'modo'.
    """
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
    cols = {c.lower(): c for c in df.columns}
    def col(n):
        return cols.get(n)

    evento = df[col("tipo_de_evento")].astype(str).str.upper() if col("tipo_de_evento") else pd.Series([""] * len(df))
    veh_cols = [col(f"tipo_de_vehiculo_{k}") for k in (1, 2, 3, 4) if col(f"tipo_de_vehiculo_{k}")]
    tiene = lambda pat: np.logical_or.reduce(
        [df[c].astype(str).str.upper().str.contains(pat, na=False) for c in veh_cols]) \
        if veh_cols else np.zeros(len(df), dtype=bool)

    es_atrop = evento.str.contains("ATROPELL", na=False).to_numpy()
    es_bici = tiene("BICI")
    es_moto = tiene("MOTO")

    modo = np.full(len(df), "coches", dtype=object)
    modo[es_moto] = "moto"
    modo[es_bici] = "ciclista"     # bici pisa moto (bici+moto raro -> cuenta ciclista)
    modo[es_atrop] = "peaton"      # atropello manda

    out = pd.DataFrame({
        "fuente": "04 ssc",
        "no_folio": df[col("no_folio")] if col("no_folio") else np.nan,
        "anio": pd.to_numeric(df[col("ano_evento")], errors="coerce") if col("ano_evento") else np.nan,
        "dia": df[col("dia")].map(normaliza_dia) if col("dia") else np.nan,
        "hora": df[col("hora")].map(hora_a_num) if col("hora") else np.nan,
        "lon": pd.to_numeric(df[col("coordenada_x")], errors="coerce") if col("coordenada_x") else np.nan,
        "lat": pd.to_numeric(df[col("coordenada_y")], errors="coerce") if col("coordenada_y") else np.nan,
        "alcaldia": limpia_txt(df[col("alcaldia")]) if col("alcaldia") else "",
        "colonia": limpia_txt(df[col("colonia")]) if col("colonia") else "",
        "tipo": evento.str.title(),
        "modo": modo,
        "occisos": pd.to_numeric(df[col("total_occisos")], errors="coerce") if col("total_occisos") else np.nan,
        "lesionados": pd.to_numeric(df[col("total_lesionados")], errors="coerce") if col("total_lesionados") else np.nan,
    })
    return out


def df_c5():
    """
    Lee los 4 CSV de C5 por chunks. C5 SI trae categorias separadas en
    incidente_c4 (Atropellado, Motociclista, Ciclista, Monopatin...), asi que
    asigna columna 'modo' con el mapeo exacto MODO_C5 (NO subcadenas).
    Devuelve un solo DataFrame con columna 'modo'; el caller lo separa por modo.
    C5 no tiene severidad -> occisos/lesionados = NaN (sin dato, no 0).
    """
    carpeta = os.path.join(RAW, "01_incidentes_viales_c5")
    archivos = [f for f in os.listdir(carpeta) if f.lower().endswith(".csv")]
    usecols = ["folio", "fecha_creacion", "hora_creacion", "dia_semana",
               "incidente_c4", "alcaldia_catalogo", "colonia_catalogo",
               "longitud", "latitud"]
    partes = []
    for a in archivos:
        try:
            for chunk in pd.read_csv(os.path.join(carpeta, a), encoding="utf-8",
                                     encoding_errors="replace", usecols=usecols,
                                     chunksize=200_000, low_memory=False):
                clave = chunk["incidente_c4"].map(
                    lambda v: sin_acentos(str(v).strip().lower()))
                modo = clave.map(MODO_C5)
                sub = chunk[modo.notna()].copy()
                sub["modo"] = modo[modo.notna()].values
                partes.append(sub)
        except Exception as e:
            print(f"    [AVISO] fallo al leer C5 '{a}': {e} (se omite ese archivo)")
    if not partes:
        return pd.DataFrame()
    df = pd.concat(partes, ignore_index=True)
    anio = pd.to_datetime(df["fecha_creacion"], errors="coerce").dt.year
    out = pd.DataFrame({
        "fuente": "01 c5",
        "no_folio": df["folio"],
        "anio": anio,
        "dia": df["dia_semana"].map(normaliza_dia),
        "hora": df["hora_creacion"].map(hora_a_num),
        "lon": pd.to_numeric(df["longitud"], errors="coerce"),
        "lat": pd.to_numeric(df["latitud"], errors="coerce"),
        "alcaldia": limpia_txt(df["alcaldia_catalogo"]),
        "colonia": limpia_txt(df["colonia_catalogo"]),
        "tipo": df["incidente_c4"].astype(str).str.strip(),
        "modo": df["modo"].values,
        "occisos": np.nan,
        "lesionados": np.nan,
    })
    return out


# ----------------------------------------------------------------------------
# Analisis sobre un DataFrame normalizado
# ----------------------------------------------------------------------------

def coords_validas(df):
    m = (df["lon"].between(LON_MIN, LON_MAX) & df["lat"].between(LAT_MIN, LAT_MAX))
    return df[m].copy()


def marca_universidad(df):
    """
    Agrega cerca_uni (bool) y campus_cercano (el campus MAS cercano dentro del
    radio, no el primero del dict). Distancia haversine real.
    """
    df = df.copy()
    if len(df) == 0:
        df["cerca_uni"] = []
        df["campus_cercano"] = []
        return df
    lats = df["lat"].to_numpy(dtype=float)
    lons = df["lon"].to_numpy(dtype=float)
    nombres = list(UNIVERSIDADES.keys())
    # matriz distancias [n_puntos x n_campus]
    dists = np.column_stack([
        haversine_km_vec(lats, lons, UNIVERSIDADES[n][0], UNIVERSIDADES[n][1])
        for n in nombres
    ])
    idx_min = np.argmin(dists, axis=1)
    dist_min = dists[np.arange(len(df)), idx_min]
    cerca = dist_min <= RADIO_UNI_KM
    campus = np.where(cerca, np.array(nombres, dtype=object)[idx_min], "")
    df["cerca_uni"] = cerca
    df["campus_cercano"] = campus
    return df


def guarda_barras(serie, titulo, archivo, xlabel=""):
    plt.figure(figsize=(8, 4.5))
    serie.plot(kind="bar", color="#c0392b")
    plt.title(titulo)
    plt.xlabel(xlabel)
    plt.ylabel("accidentes")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, archivo), dpi=110)
    plt.close()


def analiza(df, fuente):
    print("\n" + "=" * 70)
    print(f"FUENTE: {fuente}")
    print("=" * 70)
    n_total = len(df)
    df = coords_validas(df)
    n_geo = len(df)
    print(f"Registros totales: {n_total:,}  | con coords validas: {n_geo:,}")
    if n_geo == 0:
        print("Sin coords validas, se omite analisis espacial.")
        return None
    # anios validos (descarta basura tipo 1900/2099)
    df = df[df["anio"].isna() | df["anio"].between(ANIO_MIN, ANIO_MAX)].copy()
    anios = df["anio"].dropna().astype(int)
    if len(anios):
        print(f"Rango de anios: {anios.min()} - {anios.max()}")

    df = marca_universidad(df)
    cerca = int(df["cerca_uni"].sum())
    print(f"Accidentes cerca de zona universitaria (<= {RADIO_UNI_KM} km): "
          f"{cerca:,}  ({100*cerca/n_geo:.1f}%)")

    # severidad: si la fuente NO trae el dato (toda la columna NaN) -> "sin dato",
    # NO reportar 0 (eso seria inventar un cero que no existe).
    if df["occisos"].notna().any() or df["lesionados"].notna().any():
        occ = int(df["occisos"].sum(skipna=True))
        les = int(df["lesionados"].sum(skipna=True))
        print(f"Occisos: {occ:,}  | Lesionados: {les:,}")
    else:
        print("Severidad (occisos/lesionados): sin dato en esta fuente")

    pre = fuente.replace(" ", "_").replace("/", "_")

    # temporal: hora
    por_hora = df["hora"].dropna().astype(int).value_counts().reindex(range(24), fill_value=0)
    por_hora.to_csv(os.path.join(OUT, f"{pre}_por_hora.csv"), header=["accidentes"])
    guarda_barras(por_hora, f"{fuente}: accidentes por hora del dia",
                  f"{pre}_por_hora.png", "hora (0-23)")
    h_pico = por_hora.idxmax()
    print(f"Hora pico: {h_pico}:00 hrs ({por_hora.max():,} accidentes)")

    # temporal: dia de semana
    por_dia = df["dia"].value_counts().reindex(ORDEN_DIAS, fill_value=0)
    por_dia.to_csv(os.path.join(OUT, f"{pre}_por_dia.csv"), header=["accidentes"])
    guarda_barras(por_dia, f"{fuente}: accidentes por dia de semana",
                  f"{pre}_por_dia.png", "dia")
    print(f"Dia mas peligroso: {por_dia.idxmax()} ({por_dia.max():,})")

    # temporal: anio
    por_anio = df["anio"].dropna().astype(int).value_counts().sort_index()
    por_anio.to_csv(os.path.join(OUT, f"{pre}_por_anio.csv"), header=["accidentes"])

    # espacial: alcaldia
    por_alc = df["alcaldia"].value_counts().head(16)
    por_alc.to_csv(os.path.join(OUT, f"{pre}_por_alcaldia.csv"), header=["accidentes"])
    print("\nTop alcaldias:")
    for alc, c in por_alc.head(5).items():
        print(f"  {c:>6,}  {alc}")

    # espacial: colonia
    top_col = df["colonia"].value_counts().head(20)
    top_col.to_csv(os.path.join(OUT, f"{pre}_top_colonias.csv"), header=["accidentes"])

    # HOTSPOTS: celda de rejilla ~111 m (redondeo a 3 decimales). OJO: es una
    # celda de rejilla con fronteras fijas, NO un radio centrado en cada punto.
    df["celda_lat"] = df["lat"].round(3)
    df["celda_lon"] = df["lon"].round(3)
    hs = (df.groupby(["celda_lat", "celda_lon"])
            .agg(accidentes=("no_folio", "size"),
                 alcaldia=("alcaldia", lambda s: s.mode().iat[0] if len(s.mode()) else ""),
                 colonia=("colonia", lambda s: s.mode().iat[0] if len(s.mode()) else ""),
                 cerca_uni=("cerca_uni", "max"),
                 campus=("campus_cercano", lambda s: next((x for x in s if x), "")))
            .reset_index()
            .sort_values("accidentes", ascending=False))
    hs["google_maps"] = ("https://www.google.com/maps?q="
                         + hs["celda_lat"].astype(str) + "," + hs["celda_lon"].astype(str))
    hs.head(40).to_csv(os.path.join(OUT, f"{pre}_hotspots.csv"), index=False)
    print("\nTop 8 hotspots (celda de rejilla ~111 m):")
    for _, r in hs.head(8).iterrows():
        u = " [CERCA UNI: %s]" % r["campus"] if r["cerca_uni"] else ""
        print(f"  {int(r['accidentes']):>4} acc | {r['colonia'][:28]:28} {r['alcaldia'][:14]:14}"
              f" ({r['celda_lat']},{r['celda_lon']}){u}")

    return df


# ----------------------------------------------------------------------------
# GeoJSON: circulos por afeccion, escala de rojo segun # de siniestros
# ----------------------------------------------------------------------------

GEO = os.path.join(ROOT, "data", "processed", "geojson")

# escala YlOrRd (ColorBrewer): pocos=amarillo claro -> muchos=rojo oscuro
ESCALA_ROJO = ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c",
               "#fc4e2a", "#e31a1c", "#b10026"]


def color_por_intensidad(t):
    """t en 0..1 -> color hex de la escala."""
    idx = min(int(t * len(ESCALA_ROJO)), len(ESCALA_ROJO) - 1)
    return ESCALA_ROJO[idx]


def export_geojson(df, nombre, precision=3, min_acc=1):
    """
    Agrupa accidentes en clusters (~111 m con precision=3) y exporta un GeoJSON
    de puntos. Cada punto = un circulo de afeccion: propiedades con # de
    accidentes, intensidad 0..1 y color en escala de rojo (mas rojo = mas peligro).
    """
    os.makedirs(GEO, exist_ok=True)
    g = coords_validas(df)
    g = marca_universidad(g)
    g["clat"] = g["lat"].round(precision)
    g["clon"] = g["lon"].round(precision)
    grp = (g.groupby(["clat", "clon"])
             .agg(accidentes=("no_folio", "size"),
                  occisos=("occisos", "sum"),
                  lesionados=("lesionados", "sum"),
                  alcaldia=("alcaldia", lambda s: s.mode().iat[0] if len(s.mode()) else ""),
                  colonia=("colonia", lambda s: s.mode().iat[0] if len(s.mode()) else ""),
                  cerca_uni=("cerca_uni", "max"),
                  campus=("campus_cercano", lambda s: next((x for x in s if x), "")))
             .reset_index())
    grp = grp[grp["accidentes"] >= min_acc]
    if grp.empty:
        return 0, 0
    cmax = grp["accidentes"].max()
    feats = []
    for _, r in grp.iterrows():
        t = r["accidentes"] / cmax  # 0..1
        occ = 0 if pd.isna(r["occisos"]) else int(r["occisos"])
        les = 0 if pd.isna(r["lesionados"]) else int(r["lesionados"])
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(r["clon"], precision),
                                                          round(r["clat"], precision)]},
            "properties": {
                "accidentes": int(r["accidentes"]),
                "occisos": occ,
                "lesionados": les,
                "intensidad": round(float(t), 3),
                "radio": round(4 + t * 26, 1),      # px sugeridos para el circulo
                "color": color_por_intensidad(t),    # escala de rojo
                "marker-color": color_por_intensidad(t),  # simplestyle (geojson.io)
                "alcaldia": r["alcaldia"],
                "colonia": r["colonia"],
                "cerca_universidad": bool(r["cerca_uni"]),
                "campus_cercano": r["campus"],
            },
        })
    fc = {"type": "FeatureCollection",
          "metadata": {"fuente": nombre, "clusters": len(feats),
                       "max_accidentes_en_un_punto": int(cmax),
                       "nota": "color/intensidad escalan con # de siniestros (mas rojo = mas peligro)"},
          "features": feats}
    path = os.path.join(GEO, f"riesgo_{nombre}.geojson")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    print(f"  GeoJSON: riesgo_{nombre}.geojson  ({len(feats)} circulos, max {int(cmax)} acc/punto)")
    return len(feats), int(cmax)


def color_continuo(t):
    """Interpola la escala YlOrRd de forma continua. t en 0..1 -> hex."""
    t = max(0.0, min(1.0, t))
    pos = t * (len(ESCALA_ROJO) - 1)
    i = int(np.floor(pos))
    if i >= len(ESCALA_ROJO) - 1:
        return ESCALA_ROJO[-1]
    frac = pos - i
    c1 = ESCALA_ROJO[i].lstrip("#")
    c2 = ESCALA_ROJO[i + 1].lstrip("#")
    rgb = [round(int(c1[k:k+2], 16) + frac * (int(c2[k:k+2], 16) - int(c1[k:k+2], 16)))
           for k in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(rgb)


def cluster_burbujas(g, radio_m, snap_m=50):
    """
    Clustering por CERCANIA REAL (no rejilla) para mapa de burbujas.
    Etapa 1: pre-agrega puntos a una malla fina (snap_m) -> centroides.
    Etapa 2: leader clustering con KD-tree: procesa centroides de mayor a menor
    densidad; cada uno absorbe a los vecinos a <= radio_m que sigan libres.
    Asi cada burbuja tiene diametro ~2*radio_m centrado en el punto mas denso.
    Devuelve lista de dicts (lat, lon, accidentes, cerca_uni, campus, alcaldia, colonia).
    """
    from scipy.spatial import cKDTree
    if len(g) == 0:
        return []
    lat = g["lat"].to_numpy(float)
    lon = g["lon"].to_numpy(float)
    lat0 = float(np.mean(lat))
    mlat = 110540.0
    mlon = 111320.0 * math.cos(math.radians(lat0))
    # etapa 1: snap a malla fina y agrega
    gx = np.round(lon * mlon / snap_m).astype(np.int64)
    gy = np.round(lat * mlat / snap_m).astype(np.int64)
    tmp = g.assign(_gx=gx, _gy=gy)
    cells = (tmp.groupby(["_gx", "_gy"])
                .agg(accidentes=("no_folio", "size"),
                     lat=("lat", "mean"), lon=("lon", "mean"),
                     cerca_uni=("cerca_uni", "max"),
                     campus=("campus_cercano", lambda s: next((x for x in s if x), "")),
                     alcaldia=("alcaldia", lambda s: s.mode().iat[0] if len(s.mode()) else ""),
                     colonia=("colonia", lambda s: s.mode().iat[0] if len(s.mode()) else ""))
                .reset_index(drop=True))
    n = len(cells)
    clat = cells["lat"].to_numpy(float)
    clon = cells["lon"].to_numpy(float)
    xy = np.column_stack([clon * mlon, clat * mlat])
    tree = cKDTree(xy)
    cnt = cells["accidentes"].to_numpy()
    orden = np.argsort(-cnt)  # mas denso primero -> es centro de burbuja
    asignado = np.zeros(n, dtype=bool)
    burbujas = []
    for idx in orden:
        if asignado[idx]:
            continue
        vecinos = tree.query_ball_point(xy[idx], radio_m)
        libres = [v for v in vecinos if not asignado[v]]
        if not libres:
            continue
        for v in libres:
            asignado[v] = True
        sub = cells.iloc[libres]
        total = int(sub["accidentes"].sum())
        # centroide ponderado por # de accidentes
        w = sub["accidentes"].to_numpy()
        lat_c = float(np.average(sub["lat"], weights=w))
        lon_c = float(np.average(sub["lon"], weights=w))
        lider = sub.loc[sub["accidentes"].idxmax()]
        burbujas.append({
            "lat": lat_c, "lon": lon_c, "accidentes": total,
            "cerca_uni": bool(sub["cerca_uni"].max()),
            "campus": next((x for x in sub["campus"] if x), ""),
            "alcaldia": lider["alcaldia"], "colonia": lider["colonia"],
        })
    return burbujas


def export_burbujas(df, nombre, radio_m=300):
    """
    Mapa de BURBUJAS: agrupa accidentes por cercania real (radio_m) y dibuja una
    burbuja por grupo. El TAMANO (radio_px, area proporcional al conteo) Y el
    COLOR (escala continua amarillo->rojo) crecen con el # de accidentes.
    """
    os.makedirs(GEO, exist_ok=True)
    g = coords_validas(df)
    g = marca_universidad(g)
    burbujas = cluster_burbujas(g, radio_m=radio_m)
    if not burbujas:
        return 0, 0
    cmax = max(b["accidentes"] for b in burbujas)
    feats = []
    for b in burbujas:
        t = math.sqrt(b["accidentes"] / cmax)  # area ~ conteo -> radio ~ sqrt
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(b["lon"], 5), round(b["lat"], 5)]},
            "properties": {
                "accidentes": b["accidentes"],
                "intensidad": round(float(t), 3),
                "radio_px": round(5 + 35 * t, 1),     # tamano de burbuja (area ~ conteo)
                "color": color_continuo(t),
                "marker-color": color_continuo(t),    # simplestyle geojson.io
                "alcaldia": b["alcaldia"],
                "colonia": b["colonia"],
                "cerca_universidad": b["cerca_uni"],
                "campus_cercano": b["campus"],
            },
        })
    feats.sort(key=lambda f: f["properties"]["accidentes"])  # grandes encima al pintar
    fc = {"type": "FeatureCollection",
          "metadata": {"fuente": nombre, "tipo": "burbujas",
                       "radio_agrupacion_m": radio_m, "burbujas": len(feats),
                       "max_accidentes_en_burbuja": int(cmax),
                       "nota": "burbuja: tamano y color crecen con # de accidentes; "
                               "agrupadas por cercania real <= %d m" % radio_m},
          "features": feats}
    path = os.path.join(GEO, f"burbujas_{nombre}.geojson")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    print(f"  GeoJSON: burbujas_{nombre}.geojson  ({len(feats)} burbujas, "
          f"max {int(cmax)} acc/burbuja, radio {radio_m} m)")
    return len(feats), int(cmax)


def check_folios(dfs):
    """Verifica solape de no_folio entre fuentes (detecta doble conteo)."""
    print("\n" + "=" * 70)
    print("CHECK DE FOLIOS (detecta si una fuente contiene a otra)")
    print("=" * 70)
    folios = {}
    for f, df in dfs.items():
        s = set(df["no_folio"].dropna().astype(str))
        folios[f] = s
        print(f"  {f}: {len(s):,} folios unicos")
    nombres = list(folios.keys())
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            a, b = nombres[i], nombres[j]
            inter = folios[a] & folios[b]
            if folios[a] and folios[b]:
                pa = 100 * len(inter) / len(folios[a])
                pb = 100 * len(inter) / len(folios[b])
                print(f"  {a} & {b}: {len(inter):,} folios comunes "
                      f"({pa:.1f}% de {a}, {pb:.1f}% de {b})")


# ----------------------------------------------------------------------------
def main():
    print("Cargando fuentes (las cifras las calcula este script)...")
    dfs_raw = {}

    print("  - 02 ciclistas (shapefile)")
    dfs_raw["02 ciclista"] = df_ciclista_peaton(
        os.path.join(RAW, "02_puntos_accidentes_ciclistas", "puntos-de-accidentes-de-ciclistas.zip"),
        "02 ciclista")

    print("  - 03 peatones (shapefile)")
    dfs_raw["03 peaton"] = df_ciclista_peaton(
        os.path.join(RAW, "03_puntos_accidentes_peatones", "puntos-de-accidentes-de-peatones.zip"),
        "03 peaton")

    print("  - 04 hechos SSC (csv, comparativo)")
    dfs_raw["04 ssc"] = df_ssc_csv(
        os.path.join(RAW, "04_hechos_transito_ssc",
                     "hechos-de-transito-reportados-por-ssc-base-comparativa.csv"),
        "04 ssc")

    print("  - 01 C5 (4 csv, separado por modo: peaton/ciclista/moto/scooter)")
    c5 = df_c5()
    # C5 separado por modo EXACTO (categorias reales de incidente_c4), no en una bolsa.
    for modo, etiqueta in [("peaton", "01c5 peaton"), ("ciclista", "01c5 ciclista"),
                           ("motociclista", "01c5 moto"), ("scooter", "01c5 scooter")]:
        sub = c5[c5["modo"] == modo].copy()
        sub["fuente"] = etiqueta
        if len(sub):
            dfs_raw[etiqueta] = sub

    # COCHES = 04 SSC quitando los folios de peaton(03) y ciclista(02).
    # Lo que queda = hechos de transito donde la victima NO fue peaton ni ciclista
    # (coches, motos, etc.). Asi NO hay doble conteo con 02/03.
    folios_02 = set(dfs_raw["02 ciclista"]["no_folio"].dropna().astype(str))
    folios_03 = set(dfs_raw["03 peaton"]["no_folio"].dropna().astype(str))
    folios_pc = folios_02 | folios_03
    ssc = dfs_raw["04 ssc"]
    coches = ssc[~ssc["no_folio"].astype(str).isin(folios_pc)].copy()
    coches["fuente"] = "04b coches"
    dfs_raw["04b coches"] = coches

    # analisis por fuente
    for fuente, df in dfs_raw.items():
        analiza(df, fuente)

    # check de folios (02/03 vs 04). C5 va aparte: su no_folio NO es comparable.
    check_folios({k: dfs_raw[k] for k in ["02 ciclista", "03 peaton", "04 ssc"]})
    # verificar que la resta de coches quedo limpia (0 folios de peaton/ciclista)
    f_coches = set(coches["no_folio"].dropna().astype(str))
    print(f"  verificacion coches: {len(f_coches & folios_pc)} folios de peaton/ciclista "
          f"dentro de coches (debe ser 0)")

    # GeoJSON 1: riesgo_* = puntos finos por afeccion (~111 m, escala de rojo)
    print("\n" + "=" * 70)
    print("GENERANDO GEOJSON")
    print("=" * 70)
    print("[riesgo_*] puntos finos ~111 m, escala de rojo:")
    export_geojson(dfs_raw["03 peaton"], "peaton")
    export_geojson(dfs_raw["02 ciclista"], "ciclista")
    export_geojson(dfs_raw["04b coches"], "coches")

    # GeoJSON 2: burbujas_* = clustering por cercania real (300 m); tamano y
    # color crecen con el # de accidentes (mapa de burbujas).
    # Burbujas desde 04 (UNA fuente, 2018-2019), clasificadas por modo de victima
    # con vehiculo involucrado. Sin doble conteo, sin contaminacion de coches.
    print("[burbujas_*] desde 04 por modo (peaton/ciclista/moto/coches), cercania 50 m:")
    modos04 = df_modos_04(os.path.join(
        RAW, "04_hechos_transito_ssc",
        "hechos-de-transito-reportados-por-ssc-base-comparativa.csv"))
    for modo in ["peaton", "ciclista", "moto", "coches"]:
        sub = modos04[modos04["modo"] == modo].copy()
        sub["fuente"] = f"04 {modo}"
        export_burbujas(sub, modo, radio_m=50)

    # AVISOS de interpretacion
    print("\n" + "=" * 70)
    print("AVISOS DE INTERPRETACION (leer antes de presentar)")
    print("=" * 70)
    print("- Mapa de burbujas: UNA sola fuente (04 SSC, 2018-2019). Modo asignado")
    print("  por prioridad atropello>bici>moto>coche -> cada siniestro cuenta 1 vez.")
    print("- El color/tamano de la burbuja es relativo a cada capa (su propio max);")
    print("  NO comparar el rojo de una capa contra otra en magnitud absoluta.")
    print("- C5 (01) es OTRA fuente (llamadas, 2013-2024, sin severidad) y NO se")
    print("  suma con 04. Sirve aparte para tendencia historica/volumen.")

    print("\nSalidas guardadas en:")
    print("  tablas/graficas:", OUT)
    print("  geojson:", GEO)
    print("Arrastra los *.geojson a https://geojson.io para verlos.")


if __name__ == "__main__":
    main()
