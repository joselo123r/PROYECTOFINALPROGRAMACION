import requests
import pandas as pd
import json
import os

# =======================================================================
# CONFIGURACIÓN CRÍTICA
# =======================================================================

API_TOKEN = "58cab149-c8ec-2bdc-929c-d198018a7215"

# LISTA DE INDICADORES (¡Solución Final!)
INDICATOR_ID_LISTA = "8999998853,6206972692,6206972693,6206972689"

GEOGRAFIA = "00"
PARAMETRO_TIEMPO = "false"  # Pedir serie histórica

# =======================================================================
# ¡NUEVO! DICCIONARIO DE NOMBRES DE INDICADORES
# =======================================================================
# Traduce los IDs de la API a nombres legibles para los archivos y columnas.
NOMBRES_INDICADORES = {
    "8999998853": "PIB_Nacional_Incompleto",
    "6206972692": "Hogares_con_Internet",
    "6206972693": "Usuarios_de_Internet",
    "6206972689": "Hogares_con_Televisor"
}
# =======================================================================

# Verificación de seguridad
assert API_TOKEN not in ["[Aquí va tu Token]", ""], "¡ERROR CRÍTICO! Reemplace la variable API_TOKEN."

# URL FINAL Multi-Indicador (Formato BISE 2.0)
URL_BASE = (
    f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{INDICATOR_ID_LISTA}/es/"
    f"{GEOGRAFIA}/{PARAMETRO_TIEMPO}/BISE/2.0/{API_TOKEN}?type=json"
)


# =======================================================================
# FUNCIONES DE EXTRACCIÓN Y PROCESAMIENTO
# =======================================================================

def obtener_datos_inegi(url):
    """
    Realiza la solicitud HTTP a la API del INEGI.
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

        if 'Header' not in datos_json or 'Series' not in datos_json:
            print("\n[DEBUG] Alerta Estructural: El JSON no contiene 'Header' o 'Series'.")
            return None

        return datos_json

    except requests.exceptions.RequestException:
        print("\n[DEBUG] Error de Conexión. Verifique su conexión.")
        return None


def procesar_y_guardar_series(datos_json, carpeta_salida, nombres_map):
    """
    Itera sobre CADA serie en el JSON, la limpia y la guarda en un CSV individual
    usando los nombres amigables del diccionario 'nombres_map'.
    """
    if 'Series' not in datos_json:
        print("[DEBUG] No se encontró la clave 'Series' en el JSON.")
        return

    print(f"\nSe encontraron {len(datos_json['Series'])} indicadores en la respuesta.")

    for serie in datos_json['Series']:

        current_id = serie.get('INDICADOR')
        if not current_id:
            print("[WARN] Se encontró una serie sin INDICADOR ID.")
            continue

        observaciones = serie.get('OBSERVATIONS')
        if not observaciones:
            print(f"[INFO] Indicador {current_id} no tiene 'OBSERVATIONS'.")
            continue

        # --- LÓGICA DE RENOMBRADO ---
        nombre_amigable = nombres_map.get(
            current_id,
            serie.get('INDICADOR_DESCRIPCION', f'Valor_{current_id}')
        )

        df = pd.DataFrame(observaciones)

        # Renombrar columnas usando el nombre amigable
        df = df.rename(columns={
            'TIME_PERIOD': 'Fecha',
            'OBS_VALUE': nombre_amigable
        })

        if nombre_amigable not in df.columns or 'Fecha' not in df.columns:
            print(f"[DEBUG] Error de columnas para Indicador {current_id}.")
            continue

        # Seleccionar, limpiar y guardar
        df = df[['Fecha', nombre_amigable]]
        df[nombre_amigable] = pd.to_numeric(df[nombre_amigable], errors='coerce')

        # LIMPIEZA: Eliminar filas con valores NaN (como los del PIB 2015-2022)
        df = df.dropna()

        if df.empty:
            print(f"\n[INFO] Indicador {current_id} ({nombre_amigable}) no tiene datos válidos después de la limpieza.")
            continue

        # --- GUARDADO CON NOMBRE AMIGABLE ---
        archivo_salida = os.path.join(carpeta_salida, f'{nombre_amigable}.csv')
        df.to_csv(archivo_salida, index=False)

        print(f"\n=========================================")
        print(f" DATOS GUARDADOS: {nombre_amigable} ")
        print(f"=========================================")
        print(f"Total de filas limpias: {len(df)}")
        print(df.head())
        print(f"Archivo: {archivo_salida}")


# =======================================================================
# NUEVAS FUNCIONES: CARGA Y GRAFICADO
# =======================================================================

# carga_series_desde_csv: carga todos los CSVs guardados en una carpeta y devuelve un dict.
def cargar_series_desde_csv(carpeta_salida):
    """
    Carga todos los CSV en 'carpeta_salida' y devuelve un diccionario {nombre_indicador: df}.
    Espera archivos con dos columnas: 'Fecha' y '<NombreIndicador>'.
    """
    series = {}
    if not os.path.isdir(carpeta_salida):
        print(f"[WARN] Carpeta no encontrada: {carpeta_salida}")
        return series

    for fname in os.listdir(carpeta_salida):
        if not fname.lower().endswith('.csv'):
            continue
        path = os.path.join(carpeta_salida, fname)
        try:
            df = pd.read_csv(path)
            # Normalizar nombres: asumir que la segunda columna es el valor
            if 'Fecha' not in df.columns:
                print(f"[WARN] Archivo sin columna 'Fecha': {path}")
                continue
            # Renombrar segunda columna a su nombre (si viene con otro nombre)
            cols = df.columns.tolist()
            if len(cols) >= 2:
                valor_col = cols[1]
                df = df[['Fecha', valor_col]].rename(columns={valor_col: valor_col})
                series[os.path.splitext(fname)[0]] = df
            else:
                print(f"[WARN] Archivo con menos de 2 columnas: {path}")
        except Exception as ex:
            print(f"[WARN] No se pudo leer {path}: {ex}")
    return series


# graficar_series: toma un dict de DataFrames y grafica series de tiempo juntas.
def graficar_series(series_dict, indicadores=None, guardar=False, carpeta_plots='plots'):
    """
    Grafica las series de tiempo presentes en 'series_dict'.
    - indicadores: lista de nombres (keys del dict) a graficar. Si None, grafica todas.
    - guardar: si True, guarda la imagen en 'carpeta_plots'.
    Devuelve el path del archivo guardado si se guarda, o None.
    """
    import matplotlib.pyplot as plt

    if not series_dict:
        print("[INFO] No hay series para graficar.")
        return None

    # Filtrar series solicitadas
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
        # Intentar convertir Fecha a datetime; si falla, intentar año '%Y'
        df['Fecha_dt'] = pd.to_datetime(df['Fecha'], errors='coerce', infer_datetime_format=True)
        if df['Fecha_dt'].isna().all():
            try:
                df['Fecha_dt'] = pd.to_datetime(df['Fecha'].astype(str).str.extract(r'(\d{4})')[0], format='%Y', errors='coerce')
            except Exception:
                pass
        # Si aún no hay datetime, usar índice numérico
        if df['Fecha_dt'].isna().all():
            df['Fecha_dt'] = range(len(df))
        # Asegurar la columna de valor (segunda columna)
        val_col = [c for c in df.columns if c not in ('Fecha', 'Fecha_dt')][0]
        df = df[['Fecha_dt', val_col]].rename(columns={'Fecha_dt': 'Fecha', val_col: k})
        dfs.append(df.set_index('Fecha'))

    # Unir todas por índice (Fecha)
    df_master = pd.concat(dfs, axis=1).sort_index()

    # Graficado
    plt.figure(figsize=(10, 6))
    for col in df_master.columns:
        plt.plot(df_master.index, df_master[col], marker='o', label=col)

    plt.legend()
    plt.grid(True)
    plt.title('Series de tiempo: ' + ', '.join(keys))
    plt.xlabel('Fecha')
    plt.ylabel('Valor')
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


# combinar_y_graficar: carga CSVs desde carpeta y grafica un subconjunto (alta-nivel).
def combinar_y_graficar(carpeta_salida='api_inegi', indicadores=None, guardar=False):
    """
    Función de alto nivel: carga los CSV desde 'carpeta_salida' y grafica las series
    especificadas en 'indicadores' (o todas si None). Si guardar True, guarda la imagen.
    """
    series = cargar_series_desde_csv(carpeta_salida)
    if not series:
        print("[INFO] No se encontraron series para combinar/graficar.")
        return
    return graficar_series(series, indicadores=indicadores, guardar=guardar)


# =======================================================================
# PUNTO DE ENTRADA DEL SCRIPT
# =======================================================================

if __name__ == "__main__":

    print(f"\n[DIAGNÓSTICO] Solicitando {len(INDICATOR_ID_LISTA.split(','))} indicadores...")
    print(URL_BASE)
    print("--------------------------------------------------------------------------")

    CARPETA_SALIDA = 'api_inegi'
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)

    datos_json = obtener_datos_inegi(URL_BASE)

    if datos_json:
        # Pasamos el diccionario de nombres a la función de procesamiento
        procesar_y_guardar_series(datos_json, CARPETA_SALIDA, NOMBRES_INDICADORES)
        print("\n\n[ÉXITO] Proceso completado. Se han guardado los archivos CSV en la carpeta 'api_inegi'.")
    else:
        print("\n[FALLO] No se recibieron datos de la API.")

    # EJEMPLOS DE USO DE LAS FUNCIONES DE GRAFICADO:
    # 1) Graficar todas las series en pantalla:
    # combinar_y_graficar(CARPETA_SALIDA, indicadores=None, guardar=False)
    #
    # 2) Graficar solo indicadores específicos (usar nombres de archivo sin .csv):
    # combinar_y_graficar(CARPETA_SALIDA, indicadores=['Hogares_con_Internet','Usuarios_de_Internet'], guardar=True)
    #
    # Descomente la línea que necesite ejecutar automáticamente al correr el script.
    #
    # Por defecto no se generan gráficas para evitar abrir ventanas en entornos no interactivos.

    print("\n--- Ejecución finalizada. ---")