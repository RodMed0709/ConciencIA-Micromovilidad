# -*- coding: utf-8 -*-
"""
Genera las burbujas del MAPA (5 capas) reusando el motor de 01_analisis_nucleo.
Fuente de accidentes: 04 SSC (la limpia). Robo a transeunte se SUMA al peligro
de peaton Y bici (se repite a proposito; solo para el mapa, no para datos duros).

  peaton   = accidentes peaton + robos
  ciclista = accidentes ciclista + robos
  moto     = accidentes moto
  coches   = accidentes coches
  crimen   = robos (capa propia)

Salida: data/processed/geojson/burbujas_*.geojson
"""

import os
import importlib.util
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
# Fuente de accidentes para el MAPA: C5 (01) = 11 anios, volumen completo
# (1.68M coches, 273k peaton, etc.). Bolas mas grandes donde mas pega.
FUENTE_MAPA = "01 C5"
# radio de agrupacion por capa (mas grande = bolas mas grandes juntando vecinos).
RADIOS = {"peaton": 150, "ciclista": 150, "moto": 150, "coches": 150, "crimen": 180}


def cargar_motor():
    ruta = os.path.join(ROOT, "scripts", "01_analisis_nucleo.py")
    spec = importlib.util.spec_from_file_location("an", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prep(df):
    """deja columnas minimas que espera export_burbujas."""
    d = df[["lat", "lon", "alcaldia", "colonia"]].copy()
    d["no_folio"] = range(len(d))
    return d


def main():
    an = cargar_motor()
    acc = pd.read_csv(os.path.join(PROC, "accidentes_maestro.csv"), low_memory=False)
    acc = acc[acc["fuente"] == FUENTE_MAPA]
    crimen = pd.read_csv(os.path.join(PROC, "crimen_maestro.csv"), low_memory=False)

    def modo(m):
        return prep(acc[acc["modo"] == m])
    crim = prep(crimen)

    capas = {
        "peaton": pd.concat([modo("peaton"), crim], ignore_index=True),
        "ciclista": pd.concat([modo("ciclista"), crim], ignore_index=True),
        "moto": modo("moto"),
        "coches": modo("coches"),
        "crimen": crim,
    }
    for nombre, df in capas.items():
        an.export_burbujas(df, nombre, radio_m=RADIOS[nombre])


if __name__ == "__main__":
    main()
