# -*- coding: utf-8 -*-
"""
Descarga de datasets del Portal de Datos Abiertos CDMX (CKAN) para el proyecto
"Movilidad Segura". NO inventa datos: solo baja lo que el portal entrega.

Estructura: data/raw/{categoria}/{slug}/<todos los recursos del dataset>
Cada dataset = su propia carpeta nombrada como su slug.
Recursos: baja TODOS (CSV, SHP/zip, GeoJSON, dicc.) para no perder la data real.

Si un dataset no se puede bajar -> crea _PENDIENTE.txt con slug + URL y sigue.
"""

import os
import sys
import json
import requests

API = "https://datos.cdmx.gob.mx/api/3/action"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
TIMEOUT = 60

# Datasets a atacar. type=slug -> package_show directo. type=search -> package_search.
DATASETS = [
    # NIVEL 1 — nucleo del peligro
    {"cat": "1_nucleo", "dir": "01_incidentes_viales_c5", "type": "slug", "id": "incidentes-viales-c5"},
    {"cat": "1_nucleo", "dir": "02_puntos_accidentes_ciclistas", "type": "slug", "id": "puntos-de-accidentes-de-ciclistas"},
    {"cat": "1_nucleo", "dir": "03_puntos_accidentes_peatones", "type": "slug", "id": "puntos-de-accidentes-a-peatones"},
    {"cat": "1_nucleo", "dir": "04_hechos_transito_ssc", "type": "slug", "id": "hechos-de-transito-reportados-por-ssc-base-comparativa"},
    {"cat": "1_nucleo", "dir": "05_infraestructura_vial_ciclista", "type": "slug", "id": "infraestructura-vial-ciclista"},
    {"cat": "1_nucleo", "dir": "06_area_influencia_ciclovias_500m", "type": "slug", "id": "area-de-influencia-de-ciclovias-500-mts"},
    # NIVEL 2 — transporte / multimodal
    {"cat": "2_transporte", "dir": "07_gtfs", "type": "search", "q": "GTFS"},
    {"cat": "2_transporte", "dir": "08_rutas_corredores_transporte", "type": "slug", "id": "rutas-y-corredores-del-transporte-publico-concesionado"},
    {"cat": "2_transporte", "dir": "09_geolocalizacion_metrobus", "type": "slug", "id": "geolocalizacion-metrobus"},
    # NIVEL 3 — bici
    {"cat": "3_bici", "dir": "10_biciestacionamientos", "type": "slug", "id": "biciestacionamientos"},
    {"cat": "3_bici", "dir": "11_datos_bicicletas_ecobici", "type": "slug", "id": "datos-de-bicicletas-ecobici"},
    {"cat": "3_bici", "dir": "12_cicloestaciones_ecobici", "type": "slug", "id": "cicloestaciones-ecobici-nuevo-sistema"},
    # NIVEL 4 — flujos (analisis)
    {"cat": "3_bici", "dir": "13_afluencia_ecobici", "type": "search", "q": "viajes Ecobici"},
    # NIVEL 5 — accesibilidad (carta secreta)
    {"cat": "4_accesibilidad", "dir": "14_banquetas_rampas_manzana", "type": "slug", "id": "banquetas-y-rampas-por-manzana"},
]

resultados = []  # {cat, slug, status, detalle}


def get_package(slug):
    r = requests.get(f"{API}/package_show", params={"id": slug}, timeout=TIMEOUT)
    r.raise_for_status()
    d = r.json()
    if not d.get("success"):
        raise RuntimeError("package_show success=False")
    return d["result"]


def search_package(q):
    r = requests.get(f"{API}/package_search", params={"q": q, "rows": 5}, timeout=TIMEOUT)
    r.raise_for_status()
    d = r.json()
    if not d.get("success"):
        raise RuntimeError("package_search success=False")
    results = d["result"]["results"]
    if not results:
        raise RuntimeError(f"sin resultados para q='{q}'")
    return results[0]  # mejor match por score


def safe_name(s):
    keep = [c if (c.isalnum() or c in "._-") else "_" for c in s]
    return "".join(keep).strip("_") or "recurso"


def _stream_to_file(url, dest_path, verify):
    with requests.get(url, stream=True, timeout=TIMEOUT, verify=verify) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return os.path.getsize(dest_path)


def download_resource(url, dest_path):
    # Algunos recursos viven en archivo.datos.cdmx.gob.mx con cert SSL caducado
    # (problema del lado del gobierno). Si falla por SSL, reintentar sin verificar:
    # es data abierta publica, el archivo es legitimo.
    try:
        return _stream_to_file(url, dest_path, verify=True)
    except requests.exceptions.SSLError:
        import urllib3
        urllib3.disable_warnings()
        print(f"    (SSL caducado en host, reintento sin verificar: {url})")
        return _stream_to_file(url, dest_path, verify=False)


def write_pendiente(carpeta, slug, motivo, url=""):
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, "_PENDIENTE.txt"), "w", encoding="utf-8") as f:
        f.write(f"Dataset: {slug}\n")
        f.write(f"Motivo no descarga: {motivo}\n")
        f.write(f"URL pagina dataset: {url or ('https://datos.cdmx.gob.mx/dataset/' + slug)}\n")
        f.write("Descargar a mano y colocar aqui.\n")


def procesar(item):
    cat = item["cat"]
    folder = item["dir"]
    try:
        if item["type"] == "slug":
            slug = item["id"]
            pkg = get_package(slug)
        else:  # search
            pkg = search_package(item["q"])
            slug = pkg.get("name", safe_name(item["q"]))
    except Exception as e:
        slug = item.get("id") or safe_name(item.get("q", "desconocido"))
        carpeta = os.path.join(RAW, cat, folder)
        write_pendiente(carpeta, slug, f"No se resolvio el dataset: {e}")
        resultados.append({"cat": cat, "slug": slug, "status": "PENDIENTE", "detalle": str(e)})
        print(f"  [PENDIENTE] {slug}: {e}")
        return

    carpeta = os.path.join(RAW, cat, folder)
    os.makedirs(carpeta, exist_ok=True)
    recursos = pkg.get("resources", [])
    if not recursos:
        write_pendiente(carpeta, slug, "Dataset sin recursos descargables",
                        f"https://datos.cdmx.gob.mx/dataset/{slug}")
        resultados.append({"cat": cat, "slug": slug, "status": "PENDIENTE", "detalle": "sin recursos"})
        print(f"  [PENDIENTE] {slug}: sin recursos")
        return

    bajados, fallidos = [], []
    for i, res in enumerate(recursos):
        url = res.get("url")
        fmt = (res.get("format") or "bin").lower()
        nombre = res.get("name") or f"recurso_{i}"
        # nombre de archivo: tomar el del url si trae extension, si no construir
        base = url.split("/")[-1].split("?")[0] if url else ""
        if not base or "." not in base:
            base = f"{safe_name(nombre)}.{safe_name(fmt)}"
        dest = os.path.join(carpeta, safe_name(base))
        if not url:
            fallidos.append(f"{nombre} (sin url)")
            continue
        try:
            size = download_resource(url, dest)
            bajados.append(f"{base} ({size} bytes)")
            print(f"  [OK] {slug} -> {base} ({size} bytes)")
        except Exception as e:
            fallidos.append(f"{base}: {e}")
            print(f"  [FALLO recurso] {slug} -> {base}: {e}")

    if bajados and not fallidos:
        status = "OK"
    elif bajados:
        status = "PARCIAL"
    else:
        status = "PENDIENTE"
        write_pendiente(carpeta, slug, "Todos los recursos fallaron al descargar",
                        f"https://datos.cdmx.gob.mx/dataset/{slug}")
    resultados.append({"cat": cat, "slug": slug, "status": status,
                       "detalle": f"bajados={len(bajados)} fallidos={len(fallidos)}"})


def main():
    print(f"Raiz datos: {RAW}\n")
    for item in DATASETS:
        etq = item.get("id") or f"search:{item.get('q')}"
        print(f"-> {item['cat']}/{etq}")
        procesar(item)

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    ok = [r for r in resultados if r["status"] == "OK"]
    parc = [r for r in resultados if r["status"] == "PARCIAL"]
    pend = [r for r in resultados if r["status"] == "PENDIENTE"]
    for r in resultados:
        print(f"  [{r['status']:9}] {r['cat']:13} {r['slug']:55} {r['detalle']}")
    print(f"\nOK: {len(ok)}  PARCIAL: {len(parc)}  PENDIENTE: {len(pend)}")
    if pend or parc:
        print("\nNO descargados / incompletos (revisar _PENDIENTE.txt):")
        for r in pend + parc:
            print(f"  - {r['slug']} ({r['status']}): {r['detalle']}")


if __name__ == "__main__":
    main()
