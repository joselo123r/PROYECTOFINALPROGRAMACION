import requests
import pandas as pd
import os
import pydoc
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

# Mapeo de IDs a Nombres Legibles
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

SERVER_NAME = r'GABRIEL_PC\SQLEXPRESS'
DATABASE_NAME = 'inegi_db'


# =======================================================================
# 2. CLASE PARA GESTIÓN DE BASE DE DATOS (CUMPLE REQUISITO QUINTO)
# =======================================================================

class ManejadorSQL:
    def __init__(self, server, database):
        self.server = server
        self.database = database
        self.engine = None
        self._crear_conexion()

    def _crear_conexion(self):
        """Configura la conexión usando autenticación de Windows."""
        params = urllib.parse.quote_plus(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"Trusted_Connection=yes;"
        )
        connection_string = f"mssql+pyodbc:///?odbc_connect={params}"

        try:
            self.engine = create_engine(connection_string)
            # Prueba rápida de conexión
            with self.engine.connect() as conn:
                print(f"[SQL] Conexión exitosa a: {self.server} -> {self.database}")
        except Exception as e:
            print(f"\n[ERROR CRÍTICO] No se pudo conectar a SQL Server.")
            print(f"Detalle del error: {e}")
            self.engine = None

    def guardar_tabla(self, df, nombre_tabla):
        """Guarda un DataFrame en la base de datos."""
        if self.engine is None:
            return "Sin conexión a BD"

        try:
            df.to_sql(name=nombre_tabla, con=self.engine, if_exists='replace', index=False)
            return "Cargado en SQL Server OK"
        except Exception as e:
            return f"Error SQL: {e}"


# =======================================================================
# 3. FUNCIONES (ETL)
# =======================================================================

def obtener_datos_inegi(url):
    """Realiza la petición GET a la API del INEGI."""
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


def procesar_y_guardar_series(datos_json, carpeta_salida, nombres_map, db_class_instance):
    """
    Procesa el JSON, limpia los datos, genera CSVs y usa la CLASE para guardar en SQL.
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

            # --- GUARDAR EN SQL SERVER USANDO LA CLASE ---
            msg_sql = db_class_instance.guardar_tabla(df, nombre_amigable)

            print(f"-> {nombre_amigable}: {len(df)} regs. | {msg_sql}")


# =======================================================================
# 4. MAIN
# =======================================================================

if __name__ == "__main__":

    db_manager = ManejadorSQL(SERVER_NAME, DATABASE_NAME)

    # Verificación de seguridad antes de empezar
    if db_manager.engine is None:
        print("\n[ALERTA] Deteniendo el programa porque no hay conexión a la Base de Datos.")
        exit()

    CARPETA_SALIDA = 'api_inegi'
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)

    datos = obtener_datos_inegi(URL_BASE)

    if datos:
        # Pasamos la instancia de la clase 'db_manager' en lugar del engine crudo
        procesar_y_guardar_series(datos, CARPETA_SALIDA, NOMBRES_INDICADORES, db_manager)
        print("\n[LISTO] Proceso finalizado correctamente.")
    else:
        print("\n[FALLO] No se pudo completar el proceso.")
