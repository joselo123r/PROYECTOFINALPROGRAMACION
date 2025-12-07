import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

st.set_page_config(
    page_title="Dashboard INEGI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown('''
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 {
        color: #1f2937;
        padding-bottom: 20px;
    }
    </style>
''', unsafe_allow_html=True)

INDICADORES = {
    'Hogares_con_Streaming': {'emoji': '🎬', 'color': '#3b82f6'},
    'Hogares_con_TV_Paga': {'emoji': '📺', 'color': '#8b5cf6'},
    'Hogares_con_Internet': {'emoji': '🌐', 'color': '#10b981'},
    'Hogares_con_IoT': {'emoji': '🔌', 'color': '#f59e0b'},
    'Usuarios_IoT': {'emoji': '📱', 'color': '#ef4444'},
    'Usuarios_Transacciones_Web': {'emoji': '💳', 'color': '#06b6d4'},
    'Usuarios_Celular': {'emoji': '📞', 'color': '#ec4899'}
}

@st.cache_data
def cargar_datos(carpeta='api_inegi'):
    datos = {}
    if not os.path.exists(carpeta):
        st.error(f"❌ No se encuentra la carpeta '{carpeta}'.")
        return None

    for nombre_indicador in INDICADORES.keys():
        archivo = os.path.join(carpeta, f'{nombre_indicador}.csv')
        if os.path.exists(archivo):
            try:
                df = pd.read_csv(archivo)
                if nombre_indicador in df.columns:
                    df[nombre_indicador] = pd.to_numeric(df[nombre_indicador], errors='coerce')
                    df = df.dropna(subset=[nombre_indicador])
                    datos[nombre_indicador] = df
            except Exception as e:
                st.warning(f"⚠️ Error cargando {nombre_indicador}: {e}")
    return datos if datos else None

def calcular_estadisticas(df, columna):
    if df is None or df.empty or columna not in df.columns:
        return None
    valores = df[columna].dropna()
    if len(valores) < 2:
        return None
    ultimo_valor = valores.iloc[-1]
    primer_valor = valores.iloc[0]
    crecimiento = ((ultimo_valor - primer_valor) / primer_valor * 100)
    return {
        'ultimo': ultimo_valor,
        'crecimiento': crecimiento,
        'promedio': valores.mean(),
        'maximo': valores.max(),
        'minimo': valores.min()
    }

def formatear_numero(num):
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    return f"{num:,.0f}"

st.title("📊 Dashboard INEGI - Indicadores Tecnológicos")
st.markdown("### Análisis de Adopción Tecnológica en México")
st.markdown("---")

with st.spinner('Cargando datos...'):
    datos = cargar_datos()

if datos is None or len(datos) == 0:
    st.error("❌ No se pudieron cargar los datos.")
    st.info("💡 Ejecuta primero el script de Python para descargar los datos de INEGI.")
    st.stop()

st.sidebar.header("🎛️ Controles")
indicadores_disponibles = list(datos.keys())
indicador_seleccionado = st.sidebar.selectbox(
    "Selecciona un indicador:",
    options=['Todos'] + indicadores_disponibles,
    format_func=lambda x: x.replace('_', ' ') if x != 'Todos' else x
)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Filtro de Fechas")

todas_fechas = []
for df in datos.values():
    if 'Fecha' in df.columns:
        todas_fechas.extend(df['Fecha'].tolist())

if todas_fechas:
    todas_fechas = sorted(set(todas_fechas))
    fecha_inicio = st.sidebar.selectbox("Fecha inicial:", options=todas_fechas, index=0)
    fecha_fin = st.sidebar.selectbox("Fecha final:", options=todas_fechas, index=len(todas_fechas)-1)

st.sidebar.markdown("---")
st.sidebar.info(f"📁 **Indicadores cargados:** {len(datos)}")
st.sidebar.success(f"✅ Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.subheader("📈 Métricas Principales")
cols = st.columns(4)

for idx, (nombre, info) in enumerate(list(INDICADORES.items())[:4]):
    if nombre in datos:
        stats = calcular_estadisticas(datos[nombre], nombre)
        if stats:
            with cols[idx % 4]:
                delta_color = "normal" if stats['crecimiento'] >= 0 else "inverse"
                st.metric(
                    label=f"{info['emoji']} {nombre.replace('_', ' ')}",
                    value=formatear_numero(stats['ultimo']),
                    delta=f"{stats['crecimiento']:.1f}%",
                    delta_color=delta_color
                )

st.markdown("---")

def combinar_datos_filtrados(datos_dict, fecha_inicio, fecha_fin):
    df_combinado = None
    for nombre, df in datos_dict.items():
        if 'Fecha' in df.columns and nombre in df.columns:
            df_temp = df[['Fecha', nombre]].copy()
            df_temp = df_temp[(df_temp['Fecha'] >= fecha_inicio) & (df_temp['Fecha'] <= fecha_fin)]
            if df_combinado is None:
                df_combinado = df_temp
            else:
                df_combinado = pd.merge(df_combinado, df_temp, on='Fecha', how='outer')
    if df_combinado is not None:
        df_combinado = df_combinado.sort_values('Fecha')
    return df_combinado

df_grafico = combinar_datos_filtrados(datos, fecha_inicio, fecha_fin)

tab1, tab2, tab3, tab4 = st.tabs(["📈 Evolución Temporal", "📊 Comparativa", "📉 Tendencias", "📋 Datos"])

with tab1:
    st.subheader("Evolución Temporal de Indicadores")
    if df_grafico is not None and not df_grafico.empty:
        fig = go.Figure()
        if indicador_seleccionado == 'Todos':
            for nombre in indicadores_disponibles:
                if nombre in df_grafico.columns:
                    fig.add_trace(go.Scatter(
                        x=df_grafico['Fecha'], y=df_grafico[nombre],
                        mode='lines+markers', name=nombre.replace('_', ' '),
                        line=dict(color=INDICADORES[nombre]['color'], width=2),
                        marker=dict(size=6)
                    ))
        else:
            if indicador_seleccionado in df_grafico.columns:
                fig.add_trace(go.Scatter(
                    x=df_grafico['Fecha'], y=df_grafico[indicador_seleccionado],
                    mode='lines+markers', name=indicador_seleccionado.replace('_', ' '),
                    line=dict(color=INDICADORES[indicador_seleccionado]['color'], width=3),
                    marker=dict(size=8), fill='tozeroy',
                    fillcolor=INDICADORES[indicador_seleccionado]['color'] + '20'
                ))
        fig.update_layout(
            height=500, hovermode='x unified',
            xaxis_title="Fecha", yaxis_title="Valor",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor='white', paper_bgcolor='white'
        )
        fig.update_xaxis(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxis(showgrid=True, gridwidth=1, gridcolor='LightGray')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos disponibles.")

with tab2:
    st.subheader("Comparación de Últimos Valores")
    ultimos_valores = []
    nombres_indicadores = []
    colores = []
    for nombre in indicadores_disponibles:
        if nombre in datos:
            stats = calcular_estadisticas(datos[nombre], nombre)
            if stats:
                ultimos_valores.append(stats['ultimo'])
                nombres_indicadores.append(nombre.replace('_', ' '))
                colores.append(INDICADORES[nombre]['color'])
    if ultimos_valores:
        fig_bar = go.Figure(data=[go.Bar(
            x=nombres_indicadores, y=ultimos_valores, marker_color=colores,
            text=[formatear_numero(v) for v in ultimos_valores], textposition='auto'
        )])
        fig_bar.update_layout(
            height=500, xaxis_title="Indicador", yaxis_title="Valor",
            plot_bgcolor='white', paper_bgcolor='white', showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("### 📊 Estadísticas Detalladas")
        stats_data = []
        for nombre in indicadores_disponibles:
            if nombre in datos:
                stats = calcular_estadisticas(datos[nombre], nombre)
                if stats:
                    stats_data.append({
                        'Indicador': nombre.replace('_', ' '),
                        'Último Valor': formatear_numero(stats['ultimo']),
                        'Crecimiento (%)': f"{stats['crecimiento']:.2f}%",
                        'Promedio': formatear_numero(stats['promedio']),
                        'Máximo': formatear_numero(stats['maximo']),
                        'Mínimo': formatear_numero(stats['minimo'])
                    })
        if stats_data:
            st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Análisis de Tendencias 🖥")
    if indicador_seleccionado != 'Todos' and indicador_seleccionado in datos:
        df_indicador = datos[indicador_seleccionado]
        fig_trend = px.scatter(df_indicador, x='Fecha', y=indicador_seleccionado,
            trendline="lowess", title=f"Tendencia: {indicador_seleccionado.replace('_', ' ')}")
        fig_trend.update_traces(marker=dict(size=8, color=INDICADORES[indicador_seleccionado]['color']))
        fig_trend.update_layout(height=500)
        st.plotly_chart(fig_trend, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📊 Distribución de Valores")
            fig_hist = px.histogram(df_indicador, x=indicador_seleccionado, nbins=20,
                color_discrete_sequence=[INDICADORES[indicador_seleccionado]['color']])
            fig_hist.update_layout(height=350)
            st.plotly_chart(fig_hist, use_container_width=True)
        with col2:
            st.markdown("#### 📈 Box Plot")
            fig_box = px.box(df_indicador, y=indicador_seleccionado,
                color_discrete_sequence=[INDICADORES[indicador_seleccionado]['color']])
            fig_box.update_layout(height=350)
            st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("👈 Selecciona un indicador específico en el menú lateral.")

with tab4:
    st.subheader("📋 Datos Crudos")
    if indicador_seleccionado == 'Todos':
        if df_grafico is not None:
            st.dataframe(df_grafico, use_container_width=True, height=400)
            csv = df_grafico.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar datos combinados (CSV)",
                data=csv, file_name="inegi_datos_combinados.csv", mime="text/csv"
            )
    else:
        if indicador_seleccionado in datos:
            df_mostrar = datos[indicador_seleccionado]
            st.dataframe(df_mostrar, use_container_width=True, height=400)
            csv = df_mostrar.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Descargar {indicador_seleccionado} (CSV)",
                data=csv, file_name=f"{indicador_seleccionado}.csv", mime="text/csv"
            )

st.markdown("---")
st.markdown('''
    <div style='text-align: center; color: #6b7280;'>
        <p>📊 Dashboard desarrollado para visualización de datos INEGI</p>
        <p>Fuente: Instituto Nacional de Estadística y Geografía (INEGI)</p>
    </div>
''', unsafe_allow_html=True)
