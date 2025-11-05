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
        # 1. Usar el nombre del diccionario.
        # 2. Si no está en el diccionario, usar la descripción de la API.
        # 3. Si no hay descripción, usar el ID como último recurso.
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
        # Guardar el archivo CSV usando el nombre amigable
        archivo_salida = os.path.join(carpeta_salida, f'{nombre_amigable}.csv')
        df.to_csv(archivo_salida, index=False)

        print(f"\n=========================================")
        print(f" DATOS GUARDADOS: {nombre_amigable} ")
        print(f"=========================================")
        print(f"Total de filas limpias: {len(df)}")
        print(df.head())
        print(f"Archivo: {archivo_salida}")


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

    print("\n--- Ejecución finalizada. ---")