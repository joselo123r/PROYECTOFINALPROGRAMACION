import requests
import pandas as pd
import os
from sqlalchemy import create_engine, text

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

# =======================================================================
# 2. CONFIGURACIÓN DE BASE DE DATOS (CUMPLE RÚBRICA: MySQL)
# =======================================================================
# IMPORTANTE PARA EL EQUIPO:
# Se requiere instalar el driver: pip install pymysql
# Deben crear una base de datos vacía llamada 'inegi_db' en su MySQL local.

# Formato: mysql+pymysql://usuario:contraseña@host:puerto/nombre_base_datos
# NOTA: Cambia 'root' y 'password' por tus credenciales reales de MySQL
DB_USER = 'root'
DB_PASS = '1234'  # <--- COLOCA TU CONTRASEÑA AQUÍ
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'inegi_db'

CONNECTION_STRING = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Creamos el motor de conexión
try:
    db_engine = create_engine(CONNECTION_STRING)
    print(f"[SQL] Motor configurado para conectar a: {DB_NAME}")
except Exception as e:
    print(f"[SQL Error] No se pudo configurar el motor: {e}")

# URL final de la API
URL_BASE = (
    f"https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{INDICATOR_ID_LISTA}/es/"
    f"{GEOGRAFIA}/{PARAMETRO_TIEMPO}/BISE/2.0/{API_TOKEN}?type=json"
)

# =======================================================================
# 3. FUNCIONES DE EXTRACCIÓN Y TRANSFORMACIÓN
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
    Procesa el JSON, limpia los datos, genera CSVs y carga a SQL.
    
    Args:
        datos_json (dict): JSON crudo del INEGI.
        carpeta_salida (str): Ruta donde se guardarán los CSV.
        nombres_map (dict): Diccionario para renombrar IDs a texto legible.
        engine (sqlalchemy.engine): Motor de conexión a MySQL.
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

        # Obtener nombre legible del diccionario, o usar descripción por defecto
        nombre_amigable = nombres_map.get(
            current_id,
            serie.get('INDICADOR_DESCRIPCION', f'Valor_{current_id}')
        )

        # Crear DataFrame
        df = pd.DataFrame(observaciones)

        # --- LIMPIEZA DE DATOS ---
        # 1. Renombrar columnas clave
        df = df.rename(columns={'TIME_PERIOD': 'Fecha', 'OBS_VALUE': nombre_amigable})

        if nombre_amigable in df.columns and 'Fecha' in df.columns:
            # 2. Filtrar solo columnas útiles
            df = df[['Fecha', nombre_amigable]]

            # 3. Transformación numérica (Manejo de errores y redondeo)
            df[nombre_amigable] = pd.to_numeric(df[nombre_amigable], errors='coerce')
            df[nombre_amigable] = df[nombre_amigable].round(0) # Eliminar decimales innecesarios

            # 4. Eliminar filas vacías resultantes de la conversión
            df = df.dropna(subset=[nombre_amigable])

            if df.empty:
                print(f"[Info] {nombre_amigable} vacío tras limpieza.")
                continue

            # --- GUARDADO EN CSV (Respaldo local) ---
            path_csv = os.path.join(carpeta_salida, f'{nombre_amigable}.csv')
            df.to_csv(path_csv, index=False)

            # --- CARGA A BASE DE DATOS (MySQL) ---
            try:
                # if_exists='replace' borra la tabla si existe y la crea de nuevo
                df.to_sql(name=nombre_amigable, con=engine, if_exists='replace', index=False)
                msg_sql = "Cargado en MySQL correctamente"
            except Exception as e:
                msg_sql = f"Error al cargar en SQL: {e}"

            print(f"-> {nombre_amigable}: {len(df)} registros. | {msg_sql}")

# =======================================================================
# 4. EJECUCIÓN PRINCIPAL
# =======================================================================

if __name__ == "__main__":
    # Carpeta para archivos locales
    CARPETA_SALIDA = 'api_inegi'
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)

    # 1. Extracción
    datos = obtener_datos_inegi(URL_BASE)

    # 2. Procesamiento y Carga
    if datos:
        procesar_y_guardar_series(datos, CARPETA_SALIDA, NOMBRES_INDICADORES, db_engine)
        print("\n[ÉXITO] Proceso de ETL (Extracción, Transformación y Carga) finalizado.")
        print("Las tablas ya están disponibles en MySQL para su visualización.")
    else:
        print("\n[FALLO] No se pudo completar el proceso.")
