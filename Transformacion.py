from pathlib import Path
import pandas as pd
import streamlit as st

# ============================================================
# FUNCIONES SIMPLES (MISMAS IDEAS QUE USASTE ANTES)
# ============================================================

def leer_csv(ruta):
    df = pd.read_csv(ruta)
    return df


def limpieza_basica(df):
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = df[col].astype(str).str.strip()
            except:
                pass

    if "Fecha" in df.columns:
        try:
            df["Fecha"] = pd.to_datetime(df["Fecha"])
        except:
            pass

    return df


def reemplazar_nulos(df):
    df = df.copy()
    for col in df.columns:
        if df[col].dtype in ["float64", "int64"]:
            df[col] = df[col].fillna(df[col].median())
        else:
            try:
                df[col] = df[col].fillna(df[col].mode()[0])
            except:
                pass
    return df


def normalizacion_minmax(df, columna):
    if columna not in df.columns:
        return df

    col = df[columna]
    if col.dtype not in ["float64", "int64"]:
        return df

    minimo = col.min()
    maximo = col.max()
    if maximo - minimo == 0:
        return df

    df[columna + "_norm"] = (col - minimo) / (maximo - minimo)
    return df


# ============================================================
# APP DE STREAMLIT
# ============================================================

def app():
    st.title("📊 Tablero de transformación de datos (CSV INEGI)")

    carpeta = Path("api_inegi")
    if not carpeta.exists():
        st.error("No se encontró la carpeta 'api_inegi' en este proyecto.")
        return

    archivos = list(carpeta.glob("*.csv"))
    if not archivos:
        st.error("No hay archivos CSV en la carpeta 'api_inegi'.")
        return

    # Seleccionar archivo
    nombre_archivo = st.selectbox(
        "Selecciona un archivo CSV:",
        [f.name for f in archivos]
    )

    ruta_archivo = carpeta / nombre_archivo

    df = leer_csv(ruta_archivo)
    df = limpieza_basica(df)
    df = reemplazar_nulos(df)

    # Normalizar primera columna numérica (solo como ejemplo)
    columnas_num = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
    if columnas_num:
        df = normalizacion_minmax(df, columnas_num[0])

    st.subheader("Vista previa de los datos")
    st.dataframe(df.head())

    if not columnas_num:
        st.warning("El archivo no tiene columnas numéricas para graficar.")
        return

    # Elegir X, Y y tipo de gráfica
    col_x_default = "Fecha" if "Fecha" in df.columns else df.columns[0]

    col_x = st.selectbox("Columna para eje X:", df.columns, index=list(df.columns).index(col_x_default))
    col_y = st.selectbox("Columna numérica para eje Y:", columnas_num)

    tipo = st.radio("Tipo de gráfica:", ["Línea", "Barras"])

    st.subheader("Gráfica")

    df_plot = df.set_index(col_x, drop=False)[col_y]

    if tipo == "Línea":
        st.line_chart(df_plot)
    else:
        st.bar_chart(df_plot)


if __name__ == "__main__":
    app()

#copiar y pegar en la terminal
 #cd "C:\Users\OVER POWERED GAMER\PycharmProjects\PROYECTOFINALPROGRAMACION"
# py -m streamlit run Transformacion.py