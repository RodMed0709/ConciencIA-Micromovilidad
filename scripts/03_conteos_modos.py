# -*- coding: utf-8 -*-
"""
Cuenta accidentes por MODO en cada fuente y guarda el tamano en CSV.
- C5 (01): clasifica por incidente_c4 (mapeo confirmado por el usuario).
- SSC (04): clasifica por evento + vehiculo involucrado (prioridad).
Salidas:
  data/processed/analisis/clasificacion_modos.csv  (el mapeo: categoria -> modo)
  data/processed/analisis/conteos_modos.csv         (los tamanos: fuente, modo, conteo)
Las cifras las calcula este script (no se inventan).
"""

import os
import unicodedata
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "1_nucleo")
OUT = os.path.join(ROOT, "data", "processed", "analisis")
os.makedirs(OUT, exist_ok=True)


def na(s):
    return "".join(c for c in unicodedata.normalize("NFKD", str(s).strip().lower())
                   if not unicodedata.combining(c))


# Mapeo CONFIRMADO C5: incidente_c4 -> modo (claves normalizadas sin acentos)
MAPEO_C5 = {
    "choque sin lesionados": "coches",
    "choque con lesionados": "coches",
    "volcadura": "coches",
    "accidente automovilistico": "coches",
    "choque con prensados": "coches",
    "atropellado": "peaton",
    "persona atropellada": "peaton",
    "motociclista": "moto",
    "ciclista": "bici",
    "monopatin": "scooter",
}


def cuenta_c5():
    carpeta = os.path.join(RAW, "01_incidentes_viales_c5")
    from collections import Counter
    c = Counter()
    total = 0
    for a in os.listdir(carpeta):
        if not a.endswith(".csv"):
            continue
        for ch in pd.read_csv(os.path.join(carpeta, a), encoding="utf-8",
                              usecols=["incidente_c4"], chunksize=300000, low_memory=False):
            total += len(ch)
            modo = ch["incidente_c4"].map(lambda v: MAPEO_C5.get(na(v)))
            c.update(modo.dropna().tolist())
    filas = [{"fuente": "01 C5", "modo": m, "conteo": int(n)} for m, n in c.items()]
    clasificados = sum(c.values())
    filas.append({"fuente": "01 C5", "modo": "(sin modo/otros)", "conteo": int(total - clasificados)})
    return filas, total


def cuenta_04():
    p = os.path.join(RAW, "04_hechos_transito_ssc",
                     "hechos-de-transito-reportados-por-ssc-base-comparativa.csv")
    df = pd.read_csv(p, encoding="utf-8", low_memory=False)
    total = len(df)
    evento = df["tipo_de_evento"].astype(str).str.upper()
    veh = [f"tipo_de_vehiculo_{k}" for k in (1, 2, 3, 4) if f"tipo_de_vehiculo_{k}" in df.columns]
    tiene = lambda pat: np.logical_or.reduce(
        [df[c].astype(str).str.upper().str.contains(pat, na=False) for c in veh])
    es_atrop = evento.str.contains("ATROPELL", na=False).to_numpy()
    es_bici = tiene("BICI")
    es_moto = tiene("MOTO")
    es_scoot = tiene("MONOPATIN")
    modo = np.full(total, "coches", dtype=object)
    modo[es_scoot] = "scooter"
    modo[es_moto] = "moto"
    modo[es_bici] = "ciclista"
    modo[es_atrop] = "peaton"
    vc = pd.Series(modo).value_counts()
    filas = [{"fuente": "04 SSC", "modo": m, "conteo": int(n)} for m, n in vc.items()]
    return filas, total


def main():
    print("Contando C5 (2.1M filas, tarda)...")
    filas_c5, tot_c5 = cuenta_c5()
    print("Contando 04 SSC...")
    filas_04, tot_04 = cuenta_04()

    # guardar el mapeo (clasificacion)
    clasif = ([{"fuente": "01 C5 (incidente_c4)", "categoria": k, "modo": v}
               for k, v in MAPEO_C5.items()] +
              [{"fuente": "04 SSC (evento+vehiculo)", "categoria": "ATROPELLADO", "modo": "peaton"},
               {"fuente": "04 SSC (evento+vehiculo)", "categoria": "vehiculo=BICICLETA", "modo": "ciclista"},
               {"fuente": "04 SSC (evento+vehiculo)", "categoria": "vehiculo=MOTOCICLETA", "modo": "moto"},
               {"fuente": "04 SSC (evento+vehiculo)", "categoria": "vehiculo=MONOPATIN", "modo": "scooter"},
               {"fuente": "04 SSC (evento+vehiculo)", "categoria": "resto", "modo": "coches"}])
    pd.DataFrame(clasif).to_csv(os.path.join(OUT, "clasificacion_modos.csv"),
                                index=False, encoding="utf-8")

    # guardar conteos
    df = pd.DataFrame(filas_c5 + filas_04)
    orden = {"peaton": 0, "ciclista": 1, "moto": 2, "scooter": 3, "coches": 4, "(sin modo/otros)": 5}
    df["_o"] = df["modo"].map(lambda m: orden.get(m, 9))
    df = df.sort_values(["fuente", "_o"]).drop(columns="_o")
    df.to_csv(os.path.join(OUT, "conteos_modos.csv"), index=False, encoding="utf-8")

    print("\n== 04 SSC — total:", f"{tot_04:,}", "==")
    for f in sorted(filas_04, key=lambda x: -x["conteo"]):
        print(f"  {f['conteo']:>7,}  {f['modo']}")
    print("\n== 01 C5 — total:", f"{tot_c5:,}", "==")
    for f in sorted(filas_c5, key=lambda x: -x["conteo"]):
        print(f"  {f['conteo']:>9,}  {f['modo']}")
    print("\nGuardado:")
    print("  ", os.path.join(OUT, "clasificacion_modos.csv"))
    print("  ", os.path.join(OUT, "conteos_modos.csv"))


if __name__ == "__main__":
    main()
