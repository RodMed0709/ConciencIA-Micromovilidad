# -*- coding: utf-8 -*-
"""
Burbujas de PELIGRO por crimen (robo a transeunte) para el mapa.
Reusa el motor de burbujas de 01_analisis_nucleo (no duplica codigo).

Entrada: data/processed/crimen_maestro.csv
Salida:  data/processed/geojson/burbujas_crimen.geojson
"""

import os
import importlib.util
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cargar_modulo():
    ruta = os.path.join(ROOT, "scripts", "01_analisis_nucleo.py")
    spec = importlib.util.spec_from_file_location("an", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    an = cargar_modulo()
    df = pd.read_csv(os.path.join(ROOT, "data", "processed", "crimen_maestro.csv"),
                     low_memory=False)
    # adaptar a lo que espera export_burbujas: necesita no_folio, lat, lon, alcaldia, colonia
    df["no_folio"] = range(len(df))
    # radio 120 m: zonas de robo (un poco mas grueso que accidentes por esquina)
    an.export_burbujas(df, "crimen", radio_m=120)


if __name__ == "__main__":
    main()
