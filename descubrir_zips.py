"""
FASE 1 — descubrimiento. La Comisión Administradora del Río de la
Plata (CARP) publica en comisionriodelaplata.org datos observados
(sin procesar) de viento y marea de 4 estaciones del Canal Martín
García: Pilote Norden, Puerto de Colonia, Puerto de Conchillas,
Puerto de Carmelo. Cada una tiene un ZIP de viento y uno de marea
en https://www.comisionriodelaplata.org/historicos/.

No sabemos todavía qué hay adentro de esos ZIP (¿un CSV por año? ¿
todo junto? ¿desde qué fecha?), así que este script solo:
  1. Baja los 8 ZIP.
  2. Los abre y lista qué archivos tienen adentro (nombre, tamaño).
  3. Para cada archivo de texto que encuentra, imprime las primeras
     y últimas líneas (para ver el formato y el rango de fechas)
     sin volcar el archivo entero.

Con esto decidimos si conviene guardar todo el histórico en el repo
tal cual, o primero recortarlo/convertirlo a algo más liviano.
"""
import zipfile
from io import BytesIO
from pathlib import Path

import requests

BASE = "https://www.comisionriodelaplata.org/historicos/"
ESTACIONES = ["Norden", "Colonia", "Conchillas", "Carmelo"]
VARIABLES = ["wind", "tide"]

DATA_DIR = Path(__file__).parent / "data" / "discovery"


def inspeccionar_zip(nombre: str, contenido: bytes) -> None:
    print(f"\n--- {nombre}: {len(contenido) / 1024:.1f} KB ---")
    try:
        zf = zipfile.ZipFile(BytesIO(contenido))
    except zipfile.BadZipFile:
        print("  No es un ZIP válido. Primeros 200 bytes:")
        print(" ", contenido[:200])
        return

    for info in zf.infolist():
        print(f"  {info.filename}  ({info.file_size} bytes)")

    # Para cada archivo que parezca texto, mostramos una muestra
    for info in zf.infolist():
        if info.file_size == 0 or info.filename.endswith("/"):
            continue
        with zf.open(info) as f:
            crudo = f.read()
        try:
            texto = crudo.decode("utf-8")
        except UnicodeDecodeError:
            try:
                texto = crudo.decode("latin-1")
            except Exception:
                print(f"    [{info.filename}] no pude decodificar como texto, salto muestra")
                continue

        lineas = texto.splitlines()
        print(f"    [{info.filename}] {len(lineas)} líneas")
        print("    Primeras 5:")
        for linea in lineas[:5]:
            print(f"      {linea}")
        print("    Últimas 5:")
        for linea in lineas[-5:]:
            print(f"      {linea}")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for estacion in ESTACIONES:
        for variable in VARIABLES:
            nombre = f"{estacion}_{variable}.zip"
            url = BASE + nombre
            print(f"\n=== Bajando {url} ===")
            try:
                resp = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
            except Exception as e:
                print(f"  Error de red: {e}")
                continue
            print(f"  HTTP {resp.status_code}, content-type={resp.headers.get('content-type')}")
            if resp.status_code != 200:
                continue
            inspeccionar_zip(nombre, resp.content)
            # Guardamos el ZIP crudo en el repo para no tener que
            # rebajarlo si hace falta mirarlo de nuevo.
            (DATA_DIR / nombre).write_bytes(resp.content)

    print("\nListo. Mandame este log completo (o subí el resultado y avisame).")


if __name__ == "__main__":
    main()
