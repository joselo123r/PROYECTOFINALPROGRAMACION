import requests
import pandas as pd
import os
import urllib
from sqlalchemy import create_engine

# =======================================================================
# 1. CONFIGURACIÓN DEL PROYECTO
# =======================================================================

# Token proporcionado por INEGI
API_TOKEN = "58cab149-c8ec-2bdc-929c-d198018a7215"

# IDs de los indicadores a consultar
INDICATOR_ID_LISTA = "8999998853,6206972696,6206972691,6206972692,8999998854,6207129517,6207131411"

# Parámetros de la API
GEOGRAFIA = "00"  # 00 = Nacional
PARAMETRO_TIEMPO = "false"  # false = todos los periodos disponibles

# Mapeo de IDs a Nombres Legibles (Para que la BD tenga nombres claros)
NOMBRES_INDICADORES = {
    "6206972696": "Hogares_con_Streaming",
    "6206972691": "Hogares_con_TV_Paga",
    "6206972692": "Hogares_con_Internet",
    "8999998853": "Hogares_con_IoT",
    "8999998854": "Usuarios_IoT",
    "6207129517": "Usuarios_Transacciones_Web",
    "6207131411": "Usuarios_Celular"
}

# URL final de la API
URL_BASE = (
    f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{INDICATOR_ID_LISTA}/es/"
    f"{GEOGRAFIA}/{PARAMETRO_TIEMPO}/BISE/2.0/{API_TOKEN}?type=json"
)

# =======================================================================
# 2. CONFIGURACIÓN DE BASE DE DATOS (SQL SERVER)
# =======================================================================

# Nombre exacto de tu servidor (La 'r' al inicio es vital para evitar errores con '\')
SERVER_NAME = r'GABRIEL_PC\SQLEXPRESS'
DATABASE_NAME = 'inegi_db'

# Configuración de la cadena de conexión para Autenticación de Windows
params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER_NAME};"
    f"DATABASE={DATABASE_NAME};"
    f"Trusted_Connection=yes;"
)

CONNECTION_STRING = f"mssql+pyodbc:///?odbc_connect={params}"

# Intentamos crear el motor de conexión
db_engine = None
try:
    db_engine = create_engine(CONNECTION_STRING)
    # Prueba rápida de conexión
    with db_engine.connect() as conn:
        print(f"[SQL] Conexión exitosa a: {SERVER_NAME} -> {DATABASE_NAME}")
except Exception as e:
    print(f"\n[ERROR CRÍTICO] No se pudo conectar a SQL Server.")
    print(f"Detalle del error: {e}")
    print("Asegúrate de tener instalado el 'ODBC Driver 17 for SQL Server'.")


# =======================================================================
# 3. FUNCIONES (ETL)
# =======================================================================

def obtener_datos_inegi(url):
    """
    Realiza la petición GET a la API del INEGI.

    Args:
        url (str): URL formateada con token e indicadores.

    Returns:
        dict: Objeto JSON con la respuesta si es exitosa, None si falla.
    """
    try:
        print(f"Conectando a API INEGI...")
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[Error API] Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"[Error Conexión] {e}")
        return None


def procesar_y_guardar_series(datos_json, carpeta_salida, nombres_map, engine):
    """
    Procesa el JSON, limpia los datos, genera CSVs y carga a SQL Server.

    Args:
        datos_json (dict): JSON crudo del INEGI.
        carpeta_salida (str): Ruta donde se guardarán los CSV.
        nombres_map (dict): Diccionario para renombrar IDs a texto legible.
        engine (sqlalchemy.engine): Motor de conexión a SQL Server.
    """
    if 'Series' not in datos_json:
        print("[Error] El JSON no contiene la clave 'Series'.")
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

        # --- LIMPIEZA DE DATOS ---
        df = df.rename(columns={'TIME_PERIOD': 'Fecha', 'OBS_VALUE': nombre_amigable})

        if nombre_amigable in df.columns and 'Fecha' in df.columns:
            df = df[['Fecha', nombre_amigable]]

            # Convertir a numérico y limpiar errores
            df[nombre_amigable] = pd.to_numeric(df[nombre_amigable], errors='coerce')
            df[nombre_amigable] = df[nombre_amigable].round(0)
            df = df.dropna(subset=[nombre_amigable])

            if df.empty:
                print(f"[Info] {nombre_amigable} vacío tras limpieza.")
                continue

            # --- GUARDAR CSV ---
            path_csv = os.path.join(carpeta_salida, f'{nombre_amigable}.csv')
            df.to_csv(path_csv, index=False)

            # --- GUARDAR EN SQL SERVER ---
            try:
                df.to_sql(name=nombre_amigable, con=engine, if_exists='replace', index=False)
                msg_sql = "Cargado en SQL Server OK"
            except Exception as e:
                msg_sql = f"Error SQL: {e}"

            print(f"-> {nombre_amigable}: {len(df)} regs. | {msg_sql}")


# =======================================================================
# 4. MAIN
# =======================================================================

if __name__ == "__main__":
    # Verificación de seguridad antes de empezar
    if db_engine is None:
        print("\n[ALERTA] Deteniendo el programa porque no hay conexión a la Base de Datos.")
        print("Revisa la configuración de SERVER_NAME o instala el driver ODBC.")
        exit()

    CARPETA_SALIDA = 'api_inegi'
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)

    datos = obtener_datos_inegi(URL_BASE)

    if datos:
        procesar_y_guardar_series(datos, CARPETA_SALIDA, NOMBRES_INDICADORES, db_engine)
        print("\n[LISTO] Proceso finalizado correctamente.")
    else:
        print("\n[FALLO] No se pudo completar el proceso.")
