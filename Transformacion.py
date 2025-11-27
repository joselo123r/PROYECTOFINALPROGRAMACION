
import os
import sys
import json
import argparse
from pathlib import Path
import requests
import pandas as pd
import matplotlib.pyplot as plt

API_TOKEN = "58cab149-c8ec-2bdc-929c-d198018a7215"

# LISTA DE INDICADORES (¡Solución Final!)
INDICATOR_ID_LISTA = "8999998853,6206972692,6206972693,6206972689"
GEOGRAFIA = "00"
PARAMETRO_TIEMPO = "false"  # Pedir serie histórica

# Traduce los IDs de la API a nombres legibles para archivos/columnas.
NOMBRES_INDICADORES = {
    "8999998853": "PIB_Nacional_Incompleto",
    "6206972692": "Hogares_con_Internet",
    "6206972693": "Usuarios_de_Internet",
    "6206972689": "Hogares_con_Televisor",
}

# URL FINAL Multi-Indicador (Formato BISE 2.0)
URL_BASE = (
    f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{INDICATOR_ID_LISTA}/es/"
    f"{GEOGRAFIA}/{PARAMETRO_TIEMPO}/BISE/2.0/{API_TOKEN}?type=json"
)

# (Sigue existiendo la verificación, pero solo se evaluará
# si llegas a usar la API en alguna función que la requiera.)
assert API_TOKEN not in ["[Aquí va tu Token]", ""], "¡ERROR CRÍTICO! Reemplace la variable API_TOKEN."

# ======================================================================
# FUNCIONES MODO LOCAL (TRABAJO CON CSVs YA GENERADOS)
# ======================================================================

def listar_csvs(carpeta: str):
    """
    Lista los archivos CSV en una carpeta dada.
    Devuelve una lista de rutas (Path) ordenadas alfabéticamente.
    """
    p = Path(carpeta)
    if not p.exists() or not p.is_dir():
        print(f"[ERROR] Carpeta no encontrada: {carpeta}")
        return []
    return sorted([f for f in p.iterdir() if f.suffix.lower() == ".csv"])


def cargar_csvs_basico(carpeta: str):
    """
    Carga CSVs en un dict {nombre_sin_ext: DataFrame} esperando al menos dos columnas.
    No realiza limpiezas agresivas: deja la responsabilidad al usuario.
    La primera columna se toma como 'Fecha' y la segunda como 'Valor'.
    """
    resultados = {}
    for path in listar_csvs(carpeta):
        try:
            df = pd.read_csv(path)
            if df.shape[1] < 2:
                print(f"[WARN] {path.name} tiene menos de 2 columnas, se omite.")
                continue

            cols = df.columns.tolist()
            df2 = df[[cols[0], cols[1]]].copy()
            df2.columns = ["Fecha", "Valor"]

            # Intento conservador de parseo de Fecha
            df2["Fecha"] = pd.to_datetime(df2["Fecha"], errors="ignore")
            resultados[path.stem] = df2

        except Exception as e:
            print(f"[WARN] No se pudo leer {path.name}: {e}")
    return resultados


def graficar_basico(dfs_dict, nombres=None, guardar=False, carpeta_plots="plots"):
    """
    Grafica las series contenidas en dfs_dict (dict de DataFrames con columnas Fecha y Valor).
    - nombres: lista opcional de claves a graficar; si None, grafica todas.
    - guardar: si True guarda PNG en carpeta_plots y devuelve ruta; si False, muestra la gráfica.
    """
    if not dfs_dict:
        print("[INFO] No hay datos para graficar.")
        return None

    to_plot = nombres if nombres else list(dfs_dict.keys())
    to_plot = [n for n in to_plot if n in dfs_dict]

    if not to_plot:
        print("[WARN] No se encontraron nombres solicitados en los datos.")
        return None

    plt.figure(figsize=(10, 6))

    for nombre in to_plot:
        df = dfs_dict[nombre]
        x = df["Fecha"]
        y = pd.to_numeric(df["Valor"], errors="coerce")
        plt.plot(x, y, marker="o", label=nombre)

    plt.legend()
    plt.grid(True)
    plt.xlabel("Fecha")
    plt.ylabel("Valor")
    plt.title("Series de tiempo (modo local)")
    plt.tight_layout()

    if guardar:
        os.makedirs(carpeta_plots, exist_ok=True)
        safe_name = "_".join(to_plot).replace(" ", "_")
        ruta = os.path.join(carpeta_plots, f"series_{safe_name}.png")
        plt.savefig(ruta, dpi=150)
        plt.close()
        print(f"[INFO] Gráfica guardada en: {ruta}")
        return ruta
    else:
        plt.show()
        return None


# ======================================================================
# FUNCIONES API INEGI (NO SE EJECUTAN POR DEFECTO)
# ======================================================================

def obtener_datos_inegi(url: str):
    """
    Realiza la solicitud HTTP a la API del INEGI.
    Devuelve el JSON como dict o None en caso de error.
    """
    try:
        response = requests.get(url)

        if response.status_code != 200:
            try:
                error_json = response.json()
                print(f"\n[DEBUG] Error HTTP: {response.status_code}")
                print(json.dumps(error_json, indent=4))
            except json.JSONDecodeError:
                print(f"\n[DEBUG] Error HTTP: {response.status_code}. La respuesta no es JSON.")
            return None

        datos_json = response.json()

        if "Header" not in datos_json or "Series" not in datos_json:
            print("\n[DEBUG] Alerta Estructural: El JSON no contiene 'Header' o 'Series'.")
            return None

        return datos_json

    except requests.exceptions.RequestException:
        print("\n[DEBUG] Error de Conexión. Verifique su conexión.")
        return None


def procesar_y_guardar_series(datos_json, carpeta_salida: str, nombres_map: dict):
    """
    Itera sobre CADA serie en el JSON, la limpia y la guarda en un CSV individual
    usando los nombres amigables del diccionario 'nombres_map'.
    """
    if "Series" not in datos_json:
        print("[DEBUG] No se encontró la clave 'Series' en el JSON.")
        return

    print(f"\nSe encontraron {len(datos_json['Series'])} indicadores en la respuesta.")

    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    for serie in datos_json["Series"]:
        current_id = serie.get("INDICADOR")
        if not current_id:
            print("[WARN] Se encontró una serie sin INDICADOR ID.")
            continue

        observaciones = serie.get("OBSERVATIONS")
        if not observaciones:
            print(f"[INFO] Indicador {current_id} no tiene 'OBSERVATIONS'.")
            continue

        # Nombre amigable del indicador
        nombre_amigable = nombres_map.get(
            current_id,
            serie.get("INDICADOR_DESCRIPCION", f"Valor_{current_id}")
        )

        df = pd.DataFrame(observaciones)

        # Renombrar columnas usando el nombre amigable
        df = df.rename(columns={
            "TIME_PERIOD": "Fecha",
            "OBS_VALUE": nombre_amigable
        })

        if nombre_amigable not in df.columns or "Fecha" not in df.columns:
            print(f"[DEBUG] Error de columnas para Indicador {current_id}.")
            continue

        # Seleccionar, limpiar y guardar
        df = df[["Fecha", nombre_amigable]]
        df[nombre_amigable] = pd.to_numeric(df[nombre_amigable], errors="coerce")
        df = df.dropna()

        if df.empty:
            print(f"\n[INFO] Indicador {current_id} ({nombre_amigable}) no tiene datos válidos después de la limpieza.")
            continue

        archivo_salida = os.path.join(carpeta_salida, f"{nombre_amigable}.csv")
        df.to_csv(archivo_salida, index=False)

        print("\n=========================================")
        print(f" DATOS GUARDADOS: {nombre_amigable} ")
        print("=========================================")
        print(f"Total de filas limpias: {len(df)}")
        print(df.head())
        print(f"Archivo: {archivo_salida}")


def cargar_series_desde_csv(carpeta_salida: str):
    """
    Carga todos los CSV en 'carpeta_salida' y devuelve un dict {nombre_indicador: df}.
    Espera archivos con dos columnas: 'Fecha' y '<NombreIndicador>'.
    """
    series = {}
    if not os.path.isdir(carpeta_salida):
        print(f"[WARN] Carpeta no encontrada: {carpeta_salida}")
        return series

    for fname in os.listdir(carpeta_salida):
        if not fname.lower().endswith(".csv"):
            continue

        path = os.path.join(carpeta_salida, fname)
        try:
            df = pd.read_csv(path)
            if "Fecha" not in df.columns:
                print(f"[WARN] Archivo sin columna 'Fecha': {path}")
                continue

            cols = df.columns.tolist()
            if len(cols) >= 2:
                valor_col = cols[1]
                df = df[["Fecha", valor_col]].rename(columns={valor_col: valor_col})
                series[os.path.splitext(fname)[0]] = df
            else:
                print(f"[WARN] Archivo con menos de 2 columnas: {path}")
        except Exception as ex:
            print(f"[WARN] No se pudo leer {path}: {ex}")

    return series


def graficar_series(series_dict, indicadores=None, guardar=False, carpeta_plots="plots"):
    """
    Grafica múltiples series de tiempo presentes en 'series_dict'.
    - indicadores: lista de nombres (keys del dict) a graficar. Si None, grafica todas.
    - guardar: si True, guarda la imagen en 'carpeta_plots'.
    Devuelve el path del archivo si se guarda, o None.
    """
    if not series_dict:
        print("[INFO] No hay series para graficar.")
        return None

    keys = list(series_dict.keys())
    if indicadores:
        keys = [k for k in indicadores if k in series_dict]
        if not keys:
            print("[WARN] Ningún indicador solicitado se encontró en los datos.")
            return None

    # Preparar DataFrame maestro por unión en Fecha
    dfs = []
    for k in keys:
        df = series_dict[k].copy()
        df["Fecha_dt"] = pd.to_datetime(df["Fecha"], errors="coerce", infer_datetime_format=True)

        if df["Fecha_dt"].isna().all():
            # Intentar interpretar solo el año si viene así
            try:
                df["Fecha_dt"] = pd.to_datetime(
                    df["Fecha"].astype(str).str.extract(r"(\d{4})")[0],
                    format="%Y",
                    errors="coerce"
                )
            except Exception:
                pass

        if df["Fecha_dt"].isna().all():
            df["Fecha_dt"] = range(len(df))

        val_col = [c for c in df.columns if c not in ("Fecha", "Fecha_dt")][0]
        df = df[["Fecha_dt", val_col]].rename(columns={"Fecha_dt": "Fecha", val_col: k})
        dfs.append(df.set_index("Fecha"))

    df_master = pd.concat(dfs, axis=1).sort_index()

    plt.figure(figsize=(10, 6))
    for col in df_master.columns:
        plt.plot(df_master.index, df_master[col], marker="o", label=col)

    plt.legend()
    plt.grid(True)
    plt.title("Series de tiempo: " + ", ".join(keys))
    plt.xlabel("Fecha")
    plt.ylabel("Valor")
    plt.tight_layout()

    if guardar:
        if not os.path.exists(carpeta_plots):
            os.makedirs(carpeta_plots)
        archivo = os.path.join(carpeta_plots, f"series_{'_'.join(keys)}.png")
        plt.savefig(archivo, dpi=150)
        plt.close()
        print(f"[INFO] Gráfica guardada en: {archivo}")
        return archivo
    else:
        plt.show()
        return None


def combinar_y_graficar(carpeta_salida="api_inegi", indicadores=None, guardar=False):
    """
    Función de alto nivel: carga los CSV desde 'carpeta_salida' y grafica las series
    especificadas en 'indicadores' (o todas si None). Si guardar es True, guarda la imagen.
    """
    series = cargar_series_desde_csv(carpeta_salida)
    if not series:
        print("[INFO] No se encontraron series para combinar/graficar.")
        return None
    return graficar_series(series, indicadores=indicadores, guardar=guardar)


# ======================================================================
# PUNTO DE ENTRADA DEL SCRIPT: MODO LOCAL POR DEFECTO
# ======================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Modo local: cargar CSVs ya generados y graficar (evita recolección API)."
    )
    parser.add_argument(
        "--carpeta",
        "-c",
        default="api_inegi",
        help="Carpeta donde buscar CSVs (por defecto: api_inegi)."
    )
    parser.add_argument(
        "--indicadores",
        "-i",
        nargs="*",
        default=None,
        help="Lista de indicadores (nombres de archivo sin .csv) a graficar. "
             "Si no se especifica, se grafican todos."
    )
    parser.add_argument(
        "--guardar",
        "-g",
        action="store_true",
        help="Guardar la imagen en lugar de mostrarla."
    )
    parser.add_argument(
        "--plots",
        "-p",
        default="plots",
        help="Carpeta donde guardar las imágenes si --guardar está activo."
    )

    args = parser.parse_args()

    print(f"[INFO] Modo local activado. Buscando CSVs en: {args.carpeta}")
    dfs = cargar_csvs_basico(args.carpeta)

    if not dfs:
        print("[INFO] No se encontraron CSVs válidos. Saliendo.")
        sys.exit(0)

    print(f"[INFO] Series cargadas: {list(dfs.keys())}")
    graficar_basico(
        dfs,
        nombres=args.indicadores,
        guardar=args.guardar,
        carpeta_plots=args.plots
    )

    # Salimos explícitamente. La lógica de API queda disponible
    # pero NO se ejecuta de forma automática.
    sys.exit(0)
