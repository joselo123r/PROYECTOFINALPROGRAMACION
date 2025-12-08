import os
import sys
import subprocess

# ========================================
# AUTO LANZADOR STREAMLIT
# ========================================

def ejecutar_streamlit():
    archivo = os.path.abspath(__file__)
    subprocess.run([sys.executable, "-m", "streamlit", "run", archivo])

if __name__ == "__main__":
    if os.environ.get("STREAMLIT_ALREADY_RUNNING") != "1":
        os.environ["STREAMLIT_ALREADY_RUNNING"] = "1"
        ejecutar_streamlit()
        sys.exit()

# ========================================
# APP STREAMLIT
# ========================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ========================================
# CONFIG
# ========================================

st.set_page_config(page_title="INEGI Dashboard", layout="wide")

CARPETA = "api_inegi"

st.title("📊 Dashboard de Transformación Digital en Hogares Mexicanos")
st.markdown("Análisis visual del impacto del streaming en la economía digital 📡")

# ========================================
# FUNCIONES
# ========================================

def cargar_csv(nombre):
    ruta = os.path.join(CARPETA, nombre)
    if os.path.exists(ruta):
        df = pd.read_csv(ruta)
        return limpiar_df(df)
    return None

def limpiar_df(df):
    df[df.columns[1]] = pd.to_numeric(df[df.columns[1]], errors="coerce")
    return df.dropna()

def grafica_lineas_comparativa(df1, df2, titulo, etiqueta1, etiqueta2):
    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(df1.iloc[:,0], df1.iloc[:,1], marker="o", label=etiqueta1)
    ax.plot(df2.iloc[:,0], df2.iloc[:,1], marker="o", label=etiqueta2)
    ax.set_title(titulo)
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

def grafica_barras(df, titulo):
    fig, ax = plt.subplots(figsize=(9,4))
    ax.bar(df.iloc[:,0], df.iloc[:,1])
    ax.set_title(titulo)
    ax.grid(axis="y")
    st.pyplot(fig)

def grafica_pastel(valor, titulo):
    fig, ax = plt.subplots()
    ax.pie([valor,100-valor], labels=["Participación","Resto"], autopct="%1.1f%%")
    ax.set_title(titulo)
    st.pyplot(fig)

# ========================================
# CARGA DE DATOS
# ========================================

streaming = cargar_csv("Hogares_con_Streaming.csv")
tv_paga = cargar_csv("Hogares_con_TV_Paga.csv")
internet = cargar_csv("Hogares_con_Internet.csv")
iot = cargar_csv("Hogares_con_IoT.csv")
pagos = cargar_csv("Usuarios_Transacciones_Web.csv")
celular = cargar_csv("Usuarios_Celular.csv")

# ========================================
# FILA 1 - CHOQUE DE MERCADOS
# ========================================

st.header("🧩 Fila 1: Choque de Mercados")

if streaming is not None and tv_paga is not None:
    grafica_lineas_comparativa(
        streaming, tv_paga,
        "Streaming vs TV de Paga",
        "Streaming Digital",
        "TV Tradicional"
    )

# ========================================
# FILA 2 - CAPACIDAD DE PAGO
# ========================================

st.header("💳 Fila 2: Capacidad de Pago")

col1, col2 = st.columns(2)

if internet is not None:
    with col1:
        grafica_barras(internet, "Acceso a Internet")

if pagos is not None:
    with col2:
        grafica_barras(pagos, "Transacciones en Línea")

# ========================================
# FILA 3 - ECOSISTEMA DE HARDWARE
# ========================================

st.header("📱 Fila 3: Ecosistema de Hardware")

col3, col4, col5 = st.columns(3)

if celular is not None:
    with col3:
        grafica_lineas_comparativa(celular, iot, "Smartphones vs IoT",
                                   "Smartphones", "IoT")

if celular is not None:
    with col4:
        ultimo = celular.iloc[-1,1]
        grafica_pastel(ultimo, "Penetración de Smartphones")

if iot is not None:
    with col5:
        ultimo_iot = iot.iloc[-1,1]
        grafica_pastel(ultimo_iot, "Penetración de IoT")

# ========================================
# ANÁLISIS INTELIGENTE
# ========================================

st.header("🧠 Interpretación Automática")

if streaming is not None:
    ini = streaming.iloc[0,1]
    fin = streaming.iloc[-1,1]
    crecimiento = fin - ini

    st.markdown(f"""
    - Valor inicial Streaming: **{ini}**
    - Valor final Streaming: **{fin}**
    - Crecimiento total: **{crecimiento} puntos**

    El crecimiento de las plataformas digitales muestra una transformación clara
    en la economía de los hogares mexicanos.
    """)
