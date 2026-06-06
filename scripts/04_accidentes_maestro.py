# -*- coding: utf-8 -*-
"""
Construye el DATASET MAESTRO de accidentes: une 01 C5 + 04 SSC en UN solo CSV
normalizado, etiquetado por fuente y modo. Sale FUERA de 1_nucleo.

Salida: data/processed/accidentes_maestro.csv
Columnas: fuente, modo, fecha, anio, dia, hora, lat, lon, alcaldia, colonia,
          tipo_original, occisos, lesionados

Reglas:
- NUNCA se suman las fuentes: van etiquetadas (filtra por 'fuente').
- Solo filas con coords validas dentro de CDMX (es para mapa/riesgo/ruteo).
- Encoding UTF-8 en ambas fuentes.
"""

import os
import unicodedata
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "1_nucleo")
OUT = os.path.join(ROOT, "data", "processed", "accidentes_maestro.csv")

LON_MIN, LON_MAX = -99.40, -98.90
LAT_MIN, LAT_MAX = 19.00, 19.60
ANIO_MIN, ANIO_MAX = 2010, 2025

COLS = ["fuente", "modo", "fecha", "anio", "dia", "hora", "lat", "lon",
        "alcaldia", "colonia", "tipo_original", "occisos", "lesionados"]

MAPEO_C5 = {
    "choque sin lesionados": "coches", "choque con lesionados": "coches",
    "volcadura": "coches", "accidente automovilistico": "coches",
    "choque con prensados": "coches", "atropellado": "peaton",
    "persona atropellada": "peaton", "motociclista": "moto",
    "ciclista": "ciclista", "monopatin": "scooter",
}


def na(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s).strip().lower())
                   if not unicodedata.combining(c))


def hora_num(v):
    s = str(v).strip()
    h = None
    if ":" in s:
        try: h = int(s.split(":")[0])
        except: return np.nan
    else:
        try: h = int(float(s))
        except: return np.nan
    return h if 0 <= h <= 23 else np.nan


def dia_norm(v):
    s = na(v)
    for d in ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]:
        if s.startswith(d[:4]):
            return d
    return ""


def limpia(serie):
    s = serie.astype(str).str.strip().str.upper()
    return s.where(~s.isin(["NAN", "NONE", "<NA>", ""]), "")


def valida(df):
    df = df[df["lon"].between(LON_MIN, LON_MAX) & df["lat"].between(LAT_MIN, LAT_MAX)].copy()
    df = df[df["anio"].isna() | df["anio"].between(ANIO_MIN, ANIO_MAX)]
    return df


def escribe(df, primero):
    df = df[COLS]
    df.to_csv(OUT, mode="w" if primero else "a", header=primero, index=False, encoding="utf-8")


def proc_c5(primero):
    """C5 por chunks -> filas normalizadas con modo (mapeo confirmado)."""
    carpeta = os.path.join(RAW, "01_incidentes_viales_c5")
    usecols = ["folio", "fecha_creacion", "hora_creacion", "dia_semana",
               "incidente_c4", "alcaldia_catalogo", "colonia_catalogo", "longitud", "latitud"]
    n = 0
    for a in sorted(os.listdir(carpeta)):
        if not a.endswith(".csv"):
            continue
        for ch in pd.read_csv(os.path.join(carpeta, a), encoding="utf-8",
                              encoding_errors="replace", usecols=usecols,
                              chunksize=200000, low_memory=False):
            modo = ch["incidente_c4"].map(lambda v: MAPEO_C5.get(na(v)))
            ch = ch[modo.notna()].copy()
            ch["modo"] = modo[modo.notna()].values
            out = pd.DataFrame({
                "fuente": "01 C5",
                "modo": ch["modo"].values,
                "fecha": ch["fecha_creacion"].astype(str),
                "anio": pd.to_datetime(ch["fecha_creacion"], errors="coerce").dt.year,
                "dia": ch["dia_semana"].map(dia_norm),
                "hora": ch["hora_creacion"].map(hora_num),
                "lat": pd.to_numeric(ch["latitud"], errors="coerce"),
                "lon": pd.to_numeric(ch["longitud"], errors="coerce"),
                "alcaldia": limpia(ch["alcaldia_catalogo"]),
                "colonia": limpia(ch["colonia_catalogo"]),
                "tipo_original": ch["incidente_c4"].astype(str).str.strip(),
                "occisos": np.nan, "lesionados": np.nan,
            })
            out = valida(out)
            if len(out):
                escribe(out, primero); primero = False
                n += len(out)
    return n, primero


def proc_04(primero):
    p = os.path.join(RAW, "04_hechos_transito_ssc",
                     "hechos-de-transito-reportados-por-ssc-base-comparativa.csv")
    df = pd.read_csv(p, encoding="utf-8", low_memory=False)
    c = {x.lower(): x for x in df.columns}
    evento = df[c["tipo_de_evento"]].astype(str).str.upper()
    veh = [c[f"tipo_de_vehiculo_{k}"] for k in (1, 2, 3, 4) if f"tipo_de_vehiculo_{k}" in c]
    tiene = lambda pat: np.logical_or.reduce(
        [df[col].astype(str).str.upper().str.contains(pat, na=False) for col in veh])
    modo = np.full(len(df), "coches", dtype=object)
    modo[tiene("MONOPATIN")] = "scooter"
    modo[tiene("MOTO")] = "moto"
    modo[tiene("BICI")] = "ciclista"
    modo[evento.str.contains("ATROPELL", na=False).to_numpy()] = "peaton"
    out = pd.DataFrame({
        "fuente": "04 SSC",
        "modo": modo,
        "fecha": df[c["fecha_evento"]].astype(str) if "fecha_evento" in c else "",
        "anio": pd.to_numeric(df[c["ano_evento"]], errors="coerce") if "ano_evento" in c else np.nan,
        "dia": df[c["dia"]].map(dia_norm) if "dia" in c else "",
        "hora": df[c["hora"]].map(hora_num) if "hora" in c else np.nan,
        "lat": pd.to_numeric(df[c["coordenada_y"]], errors="coerce"),
        "lon": pd.to_numeric(df[c["coordenada_x"]], errors="coerce"),
        "alcaldia": limpia(df[c["alcaldia"]]) if "alcaldia" in c else "",
        "colonia": limpia(df[c["colonia"]]) if "colonia" in c else "",
        "tipo_original": evento.str.title(),
        "occisos": pd.to_numeric(df[c["total_occisos"]], errors="coerce") if "total_occisos" in c else np.nan,
        "lesionados": pd.to_numeric(df[c["total_lesionados"]], errors="coerce") if "total_lesionados" in c else np.nan,
    })
    out = valida(out)
    escribe(out, primero)
    return len(out)


def main():
    print("Construyendo maestro (01 C5 + 04 SSC)...")
    print("  - C5 (2.1M filas, por chunks)...")
    n_c5, primero = proc_c5(primero=True)
    print(f"    C5 escritas: {n_c5:,}")
    print("  - 04 SSC...")
    n_04 = proc_04(primero)
    print(f"    SSC escritas: {n_04:,}")
    total = n_c5 + n_04
    mb = os.path.getsize(OUT) / 1e6
    print(f"\nMAESTRO: {OUT}")
    print(f"  filas: {total:,}  | tamano: {mb:.0f} MB")
    print(f"  C5: {n_c5:,}  | SSC: {n_04:,}")
    print("  NUNCA sumar fuentes: filtra por columna 'fuente'.")


if __name__ == "__main__":
    main()
