# -*- coding: utf-8 -*-
"""
Capa de PELIGRO por CRIMEN (robo a transeunte) -> peaton/bici.
Filtra el FGJ a 'ROBO A TRANSEUNTE' y normaliza a un CSV limpio.

Entrada: data/raw/5_seguridad/15_carpetas_investigacion_fgj/carpetasFGJ_acumulado_2025_01.csv
Salida:  data/processed/crimen_maestro.csv
Columnas: fuente, tipo, con_violencia, fecha, anio, dia, hora, lat, lon, alcaldia, colonia
"""

import os
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "raw", "5_seguridad",
                   "15_carpetas_investigacion_fgj", "carpetasFGJ_acumulado_2025_01.csv")
OUT = os.path.join(ROOT, "data", "processed", "crimen_maestro.csv")

LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = -99.40, -98.90, 19.00, 19.60
DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
USECOLS = ["fecha_hecho", "anio_hecho", "hora_hecho", "delito",
           "alcaldia_hecho", "colonia_hecho", "latitud", "longitud"]


def hora_num(v):
    s = str(v)
    try:
        h = int(s.split(":")[0])
        return h if 0 <= h <= 23 else np.nan
    except Exception:
        return np.nan


def main():
    partes = []
    for ch in pd.read_csv(SRC, encoding="utf-8", usecols=USECOLS,
                          chunksize=300000, low_memory=False):
        d = ch["delito"].astype(str).str.upper()
        ch = ch[d.str.startswith("ROBO A TRANSEUNTE")].copy()
        if len(ch):
            partes.append(ch)
    df = pd.concat(partes, ignore_index=True)

    fecha = pd.to_datetime(df["fecha_hecho"], errors="coerce")
    out = pd.DataFrame({
        "fuente": "FGJ",
        "tipo": "robo_transeunte",
        "con_violencia": df["delito"].astype(str).str.upper().str.contains("CON VIOLENCIA"),
        "fecha": df["fecha_hecho"].astype(str),
        "anio": pd.to_numeric(df["anio_hecho"], errors="coerce"),
        "dia": fecha.dt.dayofweek.map(lambda i: DIAS[int(i)] if pd.notna(i) else ""),
        "hora": df["hora_hecho"].map(hora_num),
        "lat": pd.to_numeric(df["latitud"], errors="coerce"),
        "lon": pd.to_numeric(df["longitud"], errors="coerce"),
        "alcaldia": df["alcaldia_hecho"].astype(str).str.strip().str.upper(),
        "colonia": df["colonia_hecho"].astype(str).str.strip().str.upper(),
    })
    out = out[out["lon"].between(LON_MIN, LON_MAX) & out["lat"].between(LAT_MIN, LAT_MAX)]
    # clamp anios: el registro georreferenciado FGJ arranca 2016; fechas viejas = ruido
    out = out[out["anio"].between(2016, 2025)]
    out.to_csv(OUT, index=False, encoding="utf-8")

    print(f"Crimen (robo a transeunte) -> {OUT}")
    print(f"  filas: {len(out):,}  | con violencia: {int(out['con_violencia'].sum()):,}")
    if out["anio"].notna().any():
        print(f"  anios: {int(out['anio'].min())}-{int(out['anio'].max())}")


if __name__ == "__main__":
    main()
