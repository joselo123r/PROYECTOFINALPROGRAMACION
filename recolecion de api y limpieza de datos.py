import requests
import pandas as pd
import json
import os
from sqlalchemy import create_engine

# =======================================================================
# CONFIGURACIÓN CRÍTICA
# =======================================================================

API_TOKEN = "58cab149-c8ec-2bdc-929c-d198018a7215"

# LISTA DE INDICADORES (Streaming, IoT, Pagos, Celular, etc.)
INDICATOR_ID_LISTA = "8999998853,6206972696,6206972691,6206972692,8999998854,6207129517,6207131411"

GEOGRAFIA = "00"
PARAMETRO_TIEMPO = "false"

# =======================================================================
# CONFIGURACIÓN BASE DE DATOS (SQL)
# =======================================================================
CONNECTION_STRING = "sqlite:///inegi_datos.db"
db_engine = create_engine(CONNECTION_STRING)

# =======================================================================
# DICCIONARIO DE NOMBRES
# =======================================================================
NOMBRES_INDICADORES = {
    "6206972696": "Hogares_con_Streaming",
    "6206972691": "Hogares_con_TV_Paga",
    "6206972692": "Hogares_con_Internet",
    "8999998853": "Hogares_con_IoT",
    "8999998854": "Usuarios_IoT",
    "6207129517": "Usuarios_Transacciones_Web",
    "6207131411": "Usuarios_Celular"
}
# =======================================================================


URL_BASE = (
    f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{INDICATOR_ID_LISTA}/es/"
    f"{GEOGRAFIA}/{PARAMETRO_TIEMPO}/BISE/2.0/{API_TOKEN}?type=json"
)


# =======================================================================
# FUNCIONES
# =======================================================================

def obtener_datos_inegi(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"[Error] HTTP: {response.status_code}")
            return None
        return response.json()
    except Exception as e:
        print(f"[Error] Conexión: {e}")
        return None


def procesar_y_guardar_series(datos_json, carpeta_salida, nombres_map, engine):
    if 'Series' not in datos_json:
        return

    print(f"\nProcesando {len(datos_json['Series'])} indicadores...")

    for serie in datos_json['Series']:
        current_id = serie.get('INDICADOR')
        observaciones = serie.get('OBSERVATIONS')

        if not current_id or not observaciones:
            continue

        nombre_amigable = nombres_map.get(
            current_id,
            serie.get('INDICADOR_DESCRIPCION', f'Valor_{current_id}')
        )

        df = pd.DataFrame(observaciones)

        # Estandarizar columnas
        df = df.rename(columns={'TIME_PERIOD': 'Fecha', 'OBS_VALUE': nombre_amigable})

        if nombre_amigable in df.columns and 'Fecha' in df.columns:
            # Seleccionar solo lo necesario
            df = df[['Fecha', nombre_amigable]]

            # 1. Convertir a numérico (errores se vuelven NaN)
            df[nombre_amigable] = pd.to_numeric(df[nombre_amigable], errors='coerce')

            # 2. SIN DECIMALES: Redondear a 0
            df[nombre_amigable] = df[nombre_amigable].round(0)

            # (Opcional) Intentar convertir a Int64 para soportar enteros con nulos
            try:
                df[nombre_amigable] = df[nombre_amigable].astype('Int64')
            except:
                pass

            if df.empty:
                print(f"[Info] {nombre_amigable} totalmente vacío.")
                continue

            # --- GUARDAR CSV (Datos crudos, mantiene formato numérico correcto) ---
            path_csv = os.path.join(carpeta_salida, f'{nombre_amigable}.csv')
            df.to_csv(path_csv, index=False)

            # --- GUARDAR SQL (Datos crudos) ---
            try:
                df.to_sql(name=nombre_amigable, con=engine, if_exists='replace', index=False)
                msg = "SQL OK"
            except Exception as e:
                msg = f"SQL Error: {e}"

            print(f"\n-> {nombre_amigable}: Guardado ({len(df)} regs) | {msg}")

            # --- VISUALIZACIÓN LIMPIA (CORREGIDO AQUÍ) ---
            print("   Vista previa de datos:")

            # 1. Creamos copia
            df_visual = df.copy()

            # 2. LA SOLUCIÓN: Convertimos a 'object' para permitir texto mezclado con números
            df_visual = df_visual.astype(object)

            # 3. Ahora sí podemos rellenar con "N/D" sin error
            df_visual = df_visual.fillna("N/D")

            print(df_visual.head(10))
            print("-" * 40)


# =======================================================================
# MAIN
# =======================================================================

if __name__ == "__main__":
    CARPETA_SALIDA = 'api_inegi'
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)

    datos = obtener_datos_inegi(URL_BASE)

    if datos:
        procesar_y_guardar_series(datos, CARPETA_SALIDA, NOMBRES_INDICADORES, db_engine)
        print("\n[LISTO] Datos procesados sin errores.")
    else:
        print("\n[ERROR] No se obtuvieron datos.")

