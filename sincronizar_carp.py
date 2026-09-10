"""
Sincronización real (no descubrimiento) de los históricos de CARP.

Por cada una de las 4 estaciones del Canal Martín García (Pilote
Norden, Puerto de Colonia, Puerto de Conchillas, Puerto de Carmelo)
baja los ZIP de viento y marea, junta todos los años en un solo CSV
por estación/variable, limpio y ordenado, y lo deja en data/.

Cosas del formato de origen que este script corrige (confirmadas
2026-09-10 mirando los datos reales):
  - Filas duplicadas exactas (se repiten).
  - Alguna coma decimal rota: valores como "25/87" en vez de "25.87"
    (se corrige antes de convertir a número; si igual no se puede
    parsear, se descarta esa fila y se cuenta como descartada).
  - Las filas NO siempre vienen ordenadas por fecha dentro del
    archivo — se ordena todo al final.
  - Los archivos "por año" no siempre arrancan el 1/1 ni terminan el
    31/12 (son más bien "tandas" que calendario estricto) y a veces
    no traen la fila de encabezado — no importa, se concatena todo
    y se ordena por fecha real.

Como CARP sigue actualizando estos ZIP con el tiempo, este script
está pensado para correr solo, todos los días (ver el workflow).
Cada corrida vuelve a bajar TODO el histórico y regenera los CSV
limpios — no hace falta guardar los ZIP crudos en el repo.

Estaciones conocidas por tener huecos largos (no es un error del
script, es la fuente): Conchillas (2015/2018/2019 vacíos, 2017 casi
vacío), Colonia (2019 sin viento), Carmelo (prácticamente sin datos
entre 2025-03 y 2026-05).
"""
import csv
import io
import re
import zipfile
from datetime import datetime
from pathlib import Path

import requests

BASE = "https://www.comisionriodelaplata.org/historicos/"
ESTACIONES = ["Norden", "Colonia", "Conchillas", "Carmelo"]
VARIABLES = {
    "wind": ["date_time", "wind_speed", "wind_direction", "max_gust"],
    "tide": ["date_time", "tide_height"],
}
DATA_DIR = Path(__file__).parent / "data"

RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


def _arreglar_numero(campo: str) -> str:
    """Corrige el típico typo de origen donde un '/' aparece en vez
    de un '.' en un número decimal (ej '25/87' -> '25.87')."""
    campo = campo.strip()
    if re.match(r"^-?\d+/\d+$", campo):
        campo = campo.replace("/", ".")
    return campo


def procesar_estacion_variable(estacion: str, variable: str) -> None:
    columnas = VARIABLES[variable]
    n_columnas = len(columnas)

    url = f"{BASE}{estacion}_{variable}.zip"
    print(f"\n=== {estacion} / {variable}: bajando {url} ===")
    resp = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        print(f"  HTTP {resp.status_code}, salto esta estación/variable")
        return

    try:
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
    except zipfile.BadZipFile:
        print("  No es un ZIP válido, salto")
        return

    filas_por_clave = {}  # (fecha_str, *valores) -> fila cruda, para dedupe exacto
    descartadas = 0
    total_leidas = 0

    for info in sorted(zf.infolist(), key=lambda i: i.filename):
        if info.file_size == 0 or info.filename.endswith("/"):
            continue
        with zf.open(info) as f:
            crudo = f.read()
        try:
            texto = crudo.decode("utf-8")
        except UnicodeDecodeError:
            texto = crudo.decode("latin-1", errors="replace")

        for linea in texto.splitlines():
            linea = linea.strip()
            if not linea:
                continue
            if linea.lower().startswith("date_time"):
                continue  # encabezado, puede aparecer o no en cada archivo
            celdas = [c.strip() for c in linea.split(",")]
            if len(celdas) != n_columnas:
                descartadas += 1
                continue
            fecha_str = celdas[0]
            if not RE_FECHA.match(fecha_str):
                descartadas += 1
                continue

            valores_ok = True
            valores_num = []
            for celda in celdas[1:]:
                celda_arreglada = _arreglar_numero(celda)
                try:
                    valores_num.append(float(celda_arreglada))
                except ValueError:
                    valores_ok = False
                    break
            if not valores_ok:
                descartadas += 1
                continue

            total_leidas += 1
            clave = tuple(celdas)  # dedupe exacto de la fila cruda
            filas_por_clave[clave] = (fecha_str, valores_num)

    if not filas_por_clave:
        print("  No quedaron filas válidas, no escribo nada.")
        return

    filas_final = list(filas_por_clave.values())
    filas_final.sort(key=lambda t: datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S"))

    DATA_DIR.mkdir(exist_ok=True)
    salida = DATA_DIR / f"{estacion.lower()}_{variable}.csv"
    with salida.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        for fecha_str, valores_num in filas_final:
            w.writerow([fecha_str] + valores_num)

    primero = filas_final[0][0]
    ultimo = filas_final[-1][0]
    print(
        f"  {len(filas_final)} filas finales (de {total_leidas} leídas, "
        f"{descartadas} descartadas por formato). Rango: {primero} a {ultimo}."
    )
    print(f"  Guardado: {salida}")


def main():
    for estacion in ESTACIONES:
        for variable in VARIABLES:
            procesar_estacion_variable(estacion, variable)
    print("\nListo.")


if __name__ == "__main__":
    main()
