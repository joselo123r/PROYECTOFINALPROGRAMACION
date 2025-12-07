import os
import sys
import subprocess

# ======================================================
# AUTO-LANZADOR STREAMLIT (SIN BUCLES)
# ======================================================

def ejecutar_streamlit():
    archivo = os.path.abspath(__file__)
    subprocess.run([sys.executable, "-m", "streamlit", "run", archivo])

if __name__ == "__main__":
    # Evita que se lance más de una vez
    if os.environ.get("STREAMLIT_ALREADY_RUNNING") != "1":
        os.environ["STREAMLIT_ALREADY_RUNNING"] = "1"
        ejecutar_streamlit()
        sys.exit()

# ======================================================
# APP STREAMLIT
# ======================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ======================================================
# CONFIG
# ======================================================

CARPETA_DATOS = "api_inegi"

st.set_page_config(page_title="Dashboard INEGI", layout="wide")

st.title("📊 Dashboard de Indicadores - INEGI")
st.write("Datos limpios generados automáticamente por recoleccion.py")

# ======================================================
# FUNCIONES
# ======================================================

def listar_csvs(carpeta):
    return [f for f in os.listdir(carpeta) if f.endswith(".csv")]

def leer_csv(ruta):
    return pd.read_csv(ruta)

# ======================================================
# VALIDACIONES
# ======================================================

if not os.path.exists(CARPETA_DATOS):
    st.error("❌ No se encuentra la carpeta api_inegi")
    st.stop()

archivos = listar_csvs(CARPETA_DATOS)

if not archivos:
    st.error("❌ No hay archivos CSV")
    st.stop()

# ======================================================
# INTERFAZ
# ======================================================

archivo_seleccionado = st.selectbox("Selecciona un indicador:", archivos)

ruta_archivo = os.path.join(CARPETA_DATOS, archivo_seleccionado)
df = leer_csv(ruta_archivo)

st.subheader("📄 Datos")
st.dataframe(df, use_container_width=True)

# ======================================================
# GRÁFICOS
# ======================================================

st.subheader("📈 Gráfica")

col_fecha = df.columns[0]
col_valor = df.columns[1]

df[col_valor] = pd.to_numeric(df[col_valor], errors="coerce")
df = df.dropna()

fig, ax = plt.subplots()
ax.plot(df[col_fecha], df[col_valor])
ax.set_xlabel("Fecha")
ax.set_ylabel(col_valor)
ax.set_title(archivo_seleccionado.replace(".csv", ""))

st.pyplot(fig)


import os
import sys
import subprocess

# ======================================================
# AUTO-LANZADOR STREAMLIT (SIN BUCLES)
# ======================================================

def ejecutar_streamlit():
    archivo = os.path.abspath(__file__)
    subprocess.run([sys.executable, "-m", "streamlit", "run", archivo])

if __name__ == "__main__":
    # Evita que se lance más de una vez
    if os.environ.get("STREAMLIT_ALREADY_RUNNING") != "1":
        os.environ["STREAMLIT_ALREADY_RUNNING"] = "1"
        ejecutar_streamlit()
        sys.exit()

# ======================================================
# APP STREAMLIT
# ======================================================

import streamlit as st
import pandas as pd

# ======================================================
# FUNCIONES
# ======================================================

def listar_csvs(carpeta):
    return [f for f in os.listdir(carpeta) if f.endswith(".csv")]

def leer_csv(ruta):
    return pd.read_csv(ruta)


# ======================================================
# 🧠 ANÁLISIS GENERAL DE LA GRÁFICA (SECCIÓN NUEVA)
# ======================================================

st.subheader("📌 Análisis General del Indicador")

if len(df) > 1:
    valor_inicial = df[col_valor].iloc[0]
    valor_final = df[col_valor].iloc[-1]
    maximo = df[col_valor].max()
    minimo = df[col_valor].min()
    promedio = df[col_valor].mean()

    tendencia = "estable"
    if valor_final > valor_inicial:
        tendencia = "alcista (tendencia al alza)"
    elif valor_final < valor_inicial:
        tendencia = "bajista (tendencia a la baja)"

    st.markdown(f"""
    📝 **Resumen del comportamiento del indicador:**

    - Valor inicial: **{valor_inicial:,.2f}**
    - Valor final: **{valor_final:,.2f}**
    - Valor máximo: **{maximo:,.2f}**
    - Valor mínimo: **{minimo:,.2f}**
    - Promedio general: **{promedio:,.2f}**
    - Tendencia general: **{tendencia}**

    💡 *Interpretación:*  
    El indicador muestra una tendencia **{tendencia}** a lo largo del periodo analizado, con fluctuaciones entre **{minimo:,.2f}** y **{maximo:,.2f}**, lo que sugiere un comportamiento relativamente {"estable" if tendencia == "estable" else "variable"} en el tiempo.
    """)
else:
    st.info("ℹ️ No hay suficientes datos para generar el análisis.")
