import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import unicodedata
import re
import detail

# -----------------------
# STATE
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "reto"   # página principal

if "selected_sucursal" not in st.session_state:
    st.session_state.selected_sucursal = None


# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Riesgo - Sucursales",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================
# CSS 
# =========================================
st.markdown("""
<style>

/* Contenedor principal de la barra lateral con altura fija y scroll */
.sidebar-fixed-container {
    max-height: 80vh;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 10px;
    border-right: 1px solid #eee;
}
    
    
/* Fondo general */
.main .block-container {
    background-color: #f5f8f5;
}

/* Títulos */
h1 {
    color: #0A3D20;
    text-align: center;
    font-weight: 700;
    margin-bottom: 10px;
}

h2, h3 {
    color: #14532d;
    font-weight: 600;
}

/* KPI Cards */
.metric-card {
    background: #ffffff;
    padding: 18px 22px;
    border-radius: 14px;
    box-shadow: 0 2px 10px rgba(0, 60, 20, 0.08);
    border: 1px solid #e4eee4;
}

.metric-card h4 {
    color: #0A3D20;
    font-size: 15px;
    font-weight: 500;
    margin: 0;
}

.metric-card p {
    font-size: 24px;
    font-weight: bold;
    color: #14532d;
    margin: 5px 0 0;
}

/* Sidebar */
.sidebar .sidebar-content {
    background-color: #f0f3f0;
}

/* Badges de riesgo */
.risk-badge-high {
    background-color: #c62828;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-weight: bold;
}

.risk-badge-medium {
    background-color: #ef6c00;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-weight: bold;
}

.risk-badge-low {
    background-color: #2e7d32;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-weight: bold;
}

/* Estilo para tablas */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    background-color: #e4eee4;
    border-radius: 8px;
    padding: 8px 16px;
    color: #0A3D20;
}

.stTabs [aria-selected="true"] {
    background-color: #2e7d32;
    color: white;
}

/* Contenedor para controlar el tamaño relativo */
.button-container {
    width: 100%;
    display: justify;
    justify-content: center;
    margin: 0.2em 0;
}
    
/* Estilo para botones de Streamlit */
.stButton > button {
    width: 100%!important;
    min-width: 150px !important;
    max-width: 300px !important;
    height: 2em !important;
    border-radius: 0.5em !important;
    font-weight: bold !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
}

/* Ocultar los checkbox reales en la columna "Ver Detalle" */
div[data-testid="stDataEditor"] div[aria-colindex="5"] input[type="checkbox"] {
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
}

/* Mostrar ícono ➡️ en lugar del checkbox */
div[data-testid="stDataEditor"] div[aria-colindex="5"] div[role="checkbox"]::after {
    content: "➡️";
    font-size: 20px;
    cursor: pointer;
    position: relative;
    top: 2px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# Load Data
# -----------------------
@st.cache_data
def load_data():
    excel_file = 'analisis_completo_sucursales_20251127_031525.xlsx'    
    
    # Cargar datos principales
    df_clusters = pd.read_excel(excel_file, sheet_name='Clusters_S6')
    df_completos = pd.read_excel(excel_file, sheet_name='Datos_Completos')
    
    # Limpiar datos
    df_clusters = df_clusters.dropna(subset=['Región'])
    
    # Dejar solo sucursales únicas
    df_clusters = df_clusters.drop_duplicates(subset=['Sucursal'])
    
    # Calcular métricas de riesgo
    df_clusters['Tasa_Morosidad'] = (df_clusters['Saldo_Insoluto_Vencido_Actual'] / 
                                      df_clusters['Saldo_Insoluto_Total_Actual'] * 100).fillna(0)
    df_clusters['Tasa_Castigos'] = (df_clusters['Castigos_Actual'] / 
                                     df_clusters['Saldo_Insoluto_Total_Actual'] * 100).fillna(0)
    
    # Clasificación de riesgo mejorada
    def clasificar_riesgo(row):
        score = 0
        
        # FPD
        if row['FPD_Actual'] > 15:
            score += 3
        elif row['FPD_Actual'] > 8:
            score += 2
        elif row['FPD_Actual'] > 5:
            score += 1
            
        # ICV
        if row['ICV_Actual'] > 10:
            score += 3
        elif row['ICV_Actual'] > 6:
            score += 2
        elif row['ICV_Actual'] > 3:
            score += 1
            
        # Morosidad
        if row['Tasa_Morosidad'] > 10:
            score += 3
        elif row['Tasa_Morosidad'] > 5:
            score += 2
        elif row['Tasa_Morosidad'] > 2:
            score += 1
        
        if score >= 6:
            return 'Alto'
        elif score >= 3:
            return 'Medio'
        else:
            return 'Bajo'
    
    df_clusters['Nivel_Riesgo'] = df_clusters.apply(clasificar_riesgo, axis=1)
    
    # Score de riesgo (0-100)
    df_clusters['Score_Riesgo'] = (
        (df_clusters['FPD_Actual'] / (df_clusters['FPD_Actual'].max() + 1) * 40) +
        (df_clusters['Tasa_Morosidad'] / (df_clusters['Tasa_Morosidad'].max() + 1) * 30) +
        (df_clusters['ICV_Actual'] / (df_clusters['ICV_Actual'].max() + 1) * 30)
    )
    
    # Coordenadas aproximadas para mapa de México (simuladas por región)
    coords_region = {
        'Norte': {'lat': 28.6353, 'lon': -106.0889},
        'Sur': {'lat': 16.7569, 'lon': -93.1292},
        'Centro 1': {'lat': 19.0414, 'lon': -98.2063},
        'Centro 2': {'lat': 20.5888, 'lon': -100.3899},
        'Occidente': {'lat': 20.6597, 'lon': -103.3496},
        'Perla': {'lat': 21.1619, 'lon': -86.8515}
    }
    
    # Agregar coordenadas con variación aleatoria para cada sucursal
    np.random.seed(42)
    df_clusters['lat'] = df_clusters['Región'].map(lambda x: coords_region.get(x, {'lat': 19.4326})['lat']) + np.random.uniform(-1, 1, len(df_clusters))
    df_clusters['lon'] = df_clusters['Región'].map(lambda x: coords_region.get(x, {'lon': -99.1332})['lon']) + np.random.uniform(-1, 1, len(df_clusters))
    
    return df_clusters, df_completos

# -----------------------
# NAVIGATION
# -----------------------
def go_to_main():
    st.session_state.selected_sucursal = None
    st.session_state.page = "reto"
    st.rerun()
    
def go_to_detail(suc):
    st.session_state.selected_sucursal = suc
    st.session_state.page = "detail"
    for key in ["region_filter", "cluster_filter", "risk_filter"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# -----------------------
# MAIN PAGE
# -----------------------
def render_main_page():
    # Cargar datos
    df_clusters, df_completos = load_data()

    # ========================================
    # SIDEBAR - FILTROS
    # ========================================
    
    with st.sidebar:
        st.header("Filtros de Análisis")
        
        st.markdown('<div class="sidebar-fixed-container">', unsafe_allow_html=True)
        
        # Filtro de búsqueda por nombre de sucursal
        search_term = st.text_input("Buscar sucursal:")
        filtered_sucursales = []
        
        def normalize(text):
            if not isinstance(text, str):
                return ""
            text = unicodedata.normalize('NFKD', text)
            text = text.encode('ascii', 'ignore').decode("utf-8")
            return text.lower()
        
        if search_term:
            term_normalized = re.sub(r"[^a-z\s]", "", normalize(search_term))
            df_clusters["Sucursal_normalizada"] = df_clusters["Sucursal"].apply(normalize)
            filtered_df = df_clusters[df_clusters["Sucursal_normalizada"].str.contains(term_normalized, case=False)]
            if len(filtered_df) > 0:
                # Mostrar lista de sucursales filtradas
                filtered_sucursales = filtered_df['Sucursal'].tolist()
                st.write("Selecciona para ir al detalle")
                for i, suc in enumerate(filtered_sucursales):
                    if st.button(f"{suc} ▾", key=f"search_{i}_{suc}", type='secondary'):
                        go_to_detail(suc)
            else:
                st.warning("No se encontraron sucursales que coincidan con la búsqueda.")

        # Filtro de región
        regiones = ['Todas'] + sorted(df_clusters['Región'].unique().tolist())
        region_seleccionada = st.selectbox("Región", regiones, key=f"region_filter_{st.session_state.page}")

        # Filtro de cluster
        clusters = ['Todos'] + sorted(df_clusters['Cluster_KM'].unique().tolist())
        cluster_seleccionado = st.selectbox("Cluster", clusters, key='cluster_filter')

        # Filtro de nivel de riesgo
        nivel_riesgo_seleccionado = st.multiselect(
            "Nivel de Riesgo", 
            ['Alto', 'Medio', 'Bajo'],
            default=['Alto', 'Medio', 'Bajo'],
            key='risk_filter'
        )

        # Filtros adicionales de métricas
        st.markdown("---")
        st.subheader("Filtros por Métricas")

        fpd_range = st.slider(
            "FPD (%)",
            min_value=0.0,
            max_value=float(df_clusters['FPD_Actual'].max()),
            value=(0.0, float(df_clusters['FPD_Actual'].max())),
            key='fpd_slider'
        )

        icv_range = st.slider(
            "ICV (%)",
            min_value=0.0,
            max_value=float(df_clusters['ICV_Actual'].max()),
            value=(0.0, float(df_clusters['ICV_Actual'].max())),
            key='icv_slider'
        )

        morosidad_range = st.slider(
            "Morosidad (%)",
            min_value=0.0,
            max_value=float(df_clusters['Tasa_Morosidad'].max()),
            value=(0.0, float(df_clusters['Tasa_Morosidad'].max())),
            key='morosidad_slider'
        )
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Aplicar filtros
    df_filtered = df_clusters.copy()
    
    # Filtrar por nombre de sucursal si se encontraron coincidencias
    if len(filtered_sucursales) > 0:
        df_filtered = df_filtered[df_filtered['Sucursal'].isin(filtered_sucursales)]

    if region_seleccionada != 'Todas':
        df_filtered = df_filtered[df_filtered['Región'] == region_seleccionada]

    if cluster_seleccionado != 'Todos':
        df_filtered = df_filtered[df_filtered['Cluster_KM'] == cluster_seleccionado]

    if nivel_riesgo_seleccionado:
        df_filtered = df_filtered[df_filtered['Nivel_Riesgo'].isin(nivel_riesgo_seleccionado)]

    # Filtros de métricas
    df_filtered = df_filtered[
        (df_filtered['FPD_Actual'] >= fpd_range[0]) &
        (df_filtered['FPD_Actual'] <= fpd_range[1]) &
        (df_filtered['ICV_Actual'] >= icv_range[0]) &
        (df_filtered['ICV_Actual'] <= icv_range[1]) &
        (df_filtered['Tasa_Morosidad'] >= morosidad_range[0]) &
        (df_filtered['Tasa_Morosidad'] <= morosidad_range[1])
    ]
    
    # ========================================
    # Título principal
    # ========================================
    st.title("Dashboard de Análisis de Riesgo - Sucursales")
    st.markdown("---")

    # ========================================
    # KPIs PRINCIPALES
    # ========================================
    st.header("Indicadores Clave de Desempeño")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        icv_promedio = df_filtered['ICV_Actual'].mean()
        icv_global = df_clusters['ICV_Actual'].mean()
        delta_icv = icv_promedio - icv_global
        delta_color = "#c62828" if delta_icv > 0 else "#2e7d32"
        delta_text = f"+{delta_icv:.2f}%" if delta_icv > 0 else f"{delta_icv:.2f}%"
        st.markdown(f"""
        <div class='metric-card'>
            <h4>ICV Promedio</h4>
            <p>{icv_promedio:.2f}%</p>
            <small style='color: {delta_color}; font-weight: 600;'>{delta_text} vs promedio</small>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        capital_dispersado = df_filtered['Capital_Dispersado_Actual'].sum()
        capital_global = df_clusters['Capital_Dispersado_Actual'].sum()
        pct_capital = (capital_dispersado / capital_global * 100) if capital_global > 0 else 0
        st.markdown(f"""
        <div class='metric-card'>
            <h4>Capital Dispersado</h4>
            <p>${capital_dispersado:,.0f}</p>
            <small style='color: #14532d; font-weight: 600;'>{pct_capital:.1f}% del total</small>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        saldo_insoluto = df_filtered['Saldo_Insoluto_Total_Actual'].sum()
        saldo_global = df_clusters['Saldo_Insoluto_Total_Actual'].sum()
        pct_saldo = (saldo_insoluto / saldo_global * 100) if saldo_global > 0 else 0
        st.markdown(f"""
        <div class='metric-card'>
            <h4>Saldo Insoluto Total</h4>
            <p>${saldo_insoluto:,.0f}</p>
            <small style='color: #14532d; font-weight: 600;'>{pct_saldo:.1f}% del total</small>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        fpd_promedio = df_filtered['FPD_Actual'].mean()
        fpd_global = df_clusters['FPD_Actual'].mean()
        delta_fpd = fpd_promedio - fpd_global
        delta_color_fpd = "#c62828" if delta_fpd > 0 else "#2e7d32"
        delta_text_fpd = f"+{delta_fpd:.2f}%" if delta_fpd > 0 else f"{delta_fpd:.2f}%"
        st.markdown(f"""
        <div class='metric-card'>
            <h4>FPD Promedio</h4>
            <p>{fpd_promedio:.2f}%</p>
            <small style='color: {delta_color_fpd}; font-weight: 600;'>{delta_text_fpd} vs promedio</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ========================================
    # MAPA DE SUCURSALES EN RIESGO
    # ========================================
    st.header("Mapa de Sucursales por Nivel de Riesgo")

    if len(df_filtered) > 0:
        # Crear mapa con Plotly
        fig_map = px.scatter_mapbox(
            df_filtered,
            lat="lat",
            lon="lon",
            color="Nivel_Riesgo",
            size="Score_Riesgo",
            hover_name="Sucursal",
            hover_data={
                "Región": True,
                "Cluster_KM": True,
                "FPD_Actual": ":.2f",
                "ICV_Actual": ":.2f",
                "Tasa_Morosidad": ":.2f",
                "lat": False,
                "lon": False,
                "Score_Riesgo": ":.2f"
            },
            color_discrete_map={
                'Bajo': '#2e7d32',
                'Medio': '#ef6c00',
                'Alto': '#c62828'
            },
            zoom=4,
            height=500,
            title=f"Sucursales Filtradas: {len(df_filtered)}"
        )
        
        fig_map.update_layout(
            mapbox_style="carto-positron",
            mapbox_center={"lat": 23.6345, "lon": -102.5528},
            margin={"r":0,"t":40,"l":0,"b":0}
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
        
        # Contador de sucursales por región
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sucursales_alto_list = df_filtered[df_filtered['Nivel_Riesgo'] == 'Alto']['Sucursal'].tolist()
            st.markdown(f"<div class='risk-badge-high'>Alto Riesgo: {len(sucursales_alto_list)} sucursales</div>", unsafe_allow_html=True)
        with col2:
            sucursales_medio_list = df_filtered[df_filtered['Nivel_Riesgo'] == 'Medio']['Sucursal'].tolist()
            st.markdown(f"<div class='risk-badge-medium'>Medio Riesgo: {len(sucursales_medio_list)} sucursales</div>", unsafe_allow_html=True)
 
        with col3:
            sucursales_bajo_list = df_filtered[df_filtered['Nivel_Riesgo'] == 'Bajo']['Sucursal'].tolist()
            st.markdown(f"<div class='risk-badge-low'>Bajo Riesgo: {len(sucursales_bajo_list)} sucursales</div>", unsafe_allow_html=True)

    else:
        st.warning("⚠️ No hay sucursales que coincidan con los filtros seleccionados")

    st.markdown("---")

    # ========================================
    # MÉTRICAS GENERALES POR CLUSTER Y REGIÓN
    # ========================================
    st.header("Métricas Generales por Cluster y Región")

    tab1, tab2 = st.tabs(["Por Región", "Por Cluster"])

    with tab1:
        if len(df_filtered) > 0:
            # Agrupar por región
            metricas_region = df_filtered.groupby('Región').agg({
                'Sucursal': 'count',
                'Capital_Dispersado_Actual': 'sum',
                'Saldo_Insoluto_Total_Actual': 'sum',
                'Saldo_Insoluto_Vencido_Actual': 'sum',
                'FPD_Actual': 'mean',
                'ICV_Actual': 'mean',
                'Tasa_Morosidad': 'mean',
                'Score_Riesgo': 'mean'
            }).reset_index()
            
            metricas_region.columns = [
                'Región', 'Num_Sucursales', 'Capital_Dispersado', 'Saldo_Insoluto',
                'Saldo_Vencido', 'FPD_Promedio', 'ICV_Promedio', 'Morosidad_Promedio', 'Score_Riesgo'
            ]
            
            # Gráfico de métricas por región con Altair
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Capital Dispersado y Saldo Insoluto por Región")
                
                # Preparar datos para gráfico de barras agrupadas
                chart_data = metricas_region.melt(
                    id_vars=['Región'],
                    value_vars=['Capital_Dispersado', 'Saldo_Insoluto'],
                    var_name='Métrica',
                    value_name='Monto'
                )
                
                # Crear selección interactiva por leyenda
                selection = alt.selection_point(fields=['Métrica'], bind='legend')
                
                chart = alt.Chart(chart_data).mark_bar().encode(
                    x=alt.X('Región:N', title='Región'),
                    y=alt.Y('Monto:Q', title='Monto ($)', axis=alt.Axis(format='$,.0f')),
                    color=alt.Color('Métrica:N',
                                scale=alt.Scale(domain=['Capital_Dispersado', 'Saldo_Insoluto'],
                                                range=['#2e7d32', '#66bb6a']),
                                legend=alt.Legend(title='Métrica (Click para filtrar)')),
                    xOffset='Métrica:N',
                    opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
                    tooltip=[
                        alt.Tooltip('Región:N', title='Región'),
                        alt.Tooltip('Métrica:N', title='Métrica'),
                        alt.Tooltip('Monto:Q', title='Monto', format='$,.0f')
                    ]
                ).add_params(
                    selection
                ).properties(
                    height=400
                )
                
                st.altair_chart(chart, use_container_width=True)
            
            with col2:
                st.subheader("Indicadores de Riesgo por Región")
                
                # Preparar datos para gráfico de indicadores (solo FPD e ICV, no Morosidad)
                indicators_data = metricas_region.melt(
                    id_vars=['Región'],
                    value_vars=['FPD_Promedio', 'ICV_Promedio'],
                    var_name='Indicador',
                    value_name='Valor'
                )
                
                # Crear selección interactiva por leyenda
                selection2 = alt.selection_point(fields=['Indicador'], bind='legend')
                
                chart2 = alt.Chart(indicators_data).mark_bar().encode(
                    x=alt.X('Región:N', title='Región'),
                    y=alt.Y('Valor:Q', title='Valor'),
                    color=alt.Color('Indicador:N',
                                scale=alt.Scale(scheme='greens'),
                                legend=alt.Legend(title='Indicador (Click para filtrar)')),
                    xOffset='Indicador:N',
                    opacity=alt.condition(selection2, alt.value(1), alt.value(0.2)),
                    tooltip=[
                        alt.Tooltip('Región:N', title='Región'),
                        alt.Tooltip('Indicador:N', title='Indicador'),
                        alt.Tooltip('Valor:Q', title='Valor', format=',.2f')
                    ]
                ).add_params(
                    selection2
                ).properties(
                    height=400
                )
                
                st.altair_chart(chart2, use_container_width=True)
            
            # Tabla detallada de métricas por región
            st.subheader("Tabla Detallada de Métricas por Región")
            
            tabla_display = metricas_region.copy()
            tabla_display['Capital_Dispersado'] = tabla_display['Capital_Dispersado'].apply(lambda x: f"${x:,.0f}")
            tabla_display['Saldo_Insoluto'] = tabla_display['Saldo_Insoluto'].apply(lambda x: f"${x:,.0f}")
            tabla_display['Saldo_Vencido'] = tabla_display['Saldo_Vencido'].apply(lambda x: f"${x:,.0f}")
            tabla_display['FPD_Promedio'] = tabla_display['FPD_Promedio'].apply(lambda x: f"{x:.2f}%")
            tabla_display['ICV_Promedio'] = tabla_display['ICV_Promedio'].apply(lambda x: f"{x:.2f}%")
            tabla_display['Morosidad_Promedio'] = tabla_display['Morosidad_Promedio'].apply(lambda x: f"{x:.2f}%")
            tabla_display['Score_Riesgo'] = tabla_display['Score_Riesgo'].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(tabla_display, use_container_width=True, hide_index=True)

    with tab2:
        if len(df_filtered) > 0:
            # Agrupar por cluster
            metricas_cluster = df_filtered.groupby('Cluster_KM').agg({
                'Sucursal': 'count',
                'Capital_Dispersado_Actual': 'sum',
                'Saldo_Insoluto_Total_Actual': 'sum',
                'Saldo_Insoluto_Vencido_Actual': 'sum',
                'FPD_Actual': 'mean',
                'ICV_Actual': 'mean',
                'Tasa_Morosidad': 'mean',
                'Score_Riesgo': 'mean'
            }).reset_index()
            
            metricas_cluster.columns = [
                'Cluster', 'Num_Sucursales', 'Capital_Dispersado', 'Saldo_Insoluto',
                'Saldo_Vencido', 'FPD_Promedio', 'ICV_Promedio', 'Morosidad_Promedio', 'Score_Riesgo'
            ]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Distribución de Sucursales por Cluster y Riesgo")
                
                cluster_risk = df_filtered.groupby(['Cluster_KM', 'Nivel_Riesgo']).size().reset_index(name='Cantidad')
                
                chart3 = alt.Chart(cluster_risk).mark_bar().encode(
                    x=alt.X('Cluster_KM:N', title='Cluster'),
                    y=alt.Y('Cantidad:Q', title='Número de Sucursales'),
                    color=alt.Color('Nivel_Riesgo:N',
                                scale=alt.Scale(domain=['Bajo', 'Medio', 'Alto'],
                                                range=['#2e7d32', '#ef6c00', '#c62828']),
                                legend=alt.Legend(title='Nivel de Riesgo')),
                    tooltip=[
                        alt.Tooltip('Cluster_KM:N', title='Cluster'),
                        alt.Tooltip('Nivel_Riesgo:N', title='Nivel Riesgo'),
                        alt.Tooltip('Cantidad:Q', title='Sucursales')
                    ]
                ).properties(
                    height=400
                ).interactive()
                
                st.altair_chart(chart3, use_container_width=True)
            
            with col2:
                st.subheader("Score de Riesgo Promedio por Cluster")
                
                chart4 = alt.Chart(metricas_cluster).mark_bar(color='#2e7d32').encode(
                    x=alt.X('Cluster:N', title='Cluster'),
                    y=alt.Y('Score_Riesgo:Q', title='Score de Riesgo Promedio'),
                    tooltip=[
                        alt.Tooltip('Cluster:N', title='Cluster'),
                        alt.Tooltip('Score_Riesgo:Q', title='Score', format='.2f'),
                        alt.Tooltip('Num_Sucursales:Q', title='Sucursales')
                    ]
                ).properties(
                    height=400
                ).interactive()
                
                st.altair_chart(chart4, use_container_width=True)
            
            # Tabla detallada de métricas por cluster
            st.subheader("Tabla Detallada de Métricas por Cluster")
            
            tabla_cluster_display = metricas_cluster.copy()
            tabla_cluster_display['Capital_Dispersado'] = tabla_cluster_display['Capital_Dispersado'].apply(lambda x: f"${x:,.0f}")
            tabla_cluster_display['Saldo_Insoluto'] = tabla_cluster_display['Saldo_Insoluto'].apply(lambda x: f"${x:,.0f}")
            tabla_cluster_display['Saldo_Vencido'] = tabla_cluster_display['Saldo_Vencido'].apply(lambda x: f"${x:,.0f}")
            tabla_cluster_display['FPD_Promedio'] = tabla_cluster_display['FPD_Promedio'].apply(lambda x: f"{x:.2f}%")
            tabla_cluster_display['ICV_Promedio'] = tabla_cluster_display['ICV_Promedio'].apply(lambda x: f"{x:.2f}%")
            tabla_cluster_display['Morosidad_Promedio'] = tabla_cluster_display['Morosidad_Promedio'].apply(lambda x: f"{x:.2f}%")
            tabla_cluster_display['Score_Riesgo'] = tabla_cluster_display['Score_Riesgo'].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(tabla_cluster_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ========================================
    # TOP 10 SUCURSALES EN RIESGO - TABLA ÚNICA
    # ========================================
    st.header("Top 10 Sucursales en Riesgo")

    if len(df_filtered) > 0:
        # Obtener top 10 por score de riesgo
        top_10_riesgo = df_filtered.nlargest(10, 'Score_Riesgo')[
            ['Sucursal', 'Región', 'Cluster_KM', 'FPD_Actual', 'ICV_Actual',
            'Capital_Dispersado_Actual', 'Saldo_Insoluto_Total_Actual',
            'Castigos_Actual', 'Quitas_Actual', 'Score_Riesgo', 'Nivel_Riesgo']
        ].copy()
        
        # Tabla con todas las métricas
        # st.subheader("Top 10 Sucursales - Indicadores de Riesgo")
        
        tabla_top10 = top_10_riesgo.copy()
        tabla_top10['FPD_Actual'] = tabla_top10['FPD_Actual'].apply(lambda x: f"{x:.2f}%")
        tabla_top10['ICV_Actual'] = tabla_top10['ICV_Actual'].apply(lambda x: f"{x:.2f}%")
        tabla_top10['Capital_Dispersado_Actual'] = tabla_top10['Capital_Dispersado_Actual'].apply(lambda x: f"${x:,.0f}")
        tabla_top10['Saldo_Insoluto_Total_Actual'] = tabla_top10['Saldo_Insoluto_Total_Actual'].apply(lambda x: f"${x:,.0f}")
        tabla_top10['Castigos_Actual'] = tabla_top10['Castigos_Actual'].apply(lambda x: f"${x:,.0f}")
        tabla_top10['Quitas_Actual'] = tabla_top10['Quitas_Actual'].apply(lambda x: f"${x:,.0f}")
        tabla_top10['Score_Riesgo'] = tabla_top10['Score_Riesgo'].apply(lambda x: f"{x:.2f}")
        tabla_top10['Ver'] = False
        
        tabla_top10.columns = [
            'Sucursal', 'Región', 'Cluster', 'FPD %', 'ICV %',
            'Capital Dispersado', 'Saldo Insoluto', 'Castigos', 'Quitas', 'Score Riesgo', 'Nivel Riesgo', 'Ver Detalle'
        ]
        
        num_filas = min(len(tabla_top10), 10)
        alto_tabla_top = 35 + num_filas * 35 
        
        
        edited = st.data_editor(
            tabla_top10,
            use_container_width=True,
            height=alto_tabla_top,
            hide_index=True,
            column_config={
                "Ver Detalle": st.column_config.CheckboxColumn(
                    label="Ver",
                    help="Da clic para ver el detalle de una sucursal específica"
                )
            },
            disabled=[col for col in tabla_top10.columns if col != "Ver Detalle"]
        )

        # 🔹 Detectar cuál checkbox fue activado
        seleccionados = edited[edited["Ver Detalle"] == True]
        if not seleccionados.empty:
            sucursal = seleccionados.iloc[0]["Sucursal"]
            seleccionados = edited[edited["Ver Detalle"] == False]
            go_to_detail(sucursal)
        
        # ---------------------------
        
    else:
        st.warning("⚠️ No hay datos disponibles con los filtros actuales")

    st.markdown("---")

    # Footer con resumen
    st.header("Resumen Ejecutivo")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Datos Filtrados")
        st.info(f"""
        - **Sucursales analizadas**: {len(df_filtered)}
        - **Regiones**: {df_filtered['Región'].nunique() if len(df_filtered) > 0 else 0}
        - **Clusters**: {df_filtered['Cluster_KM'].nunique() if len(df_filtered) > 0 else 0}
        """)

    with col2:
        st.markdown("### Alertas de Riesgo")
        if len(df_filtered) > 0:
            pct_alto = len(df_filtered[df_filtered['Nivel_Riesgo'] == 'Alto']) / len(df_filtered) * 100
            st.warning(f"""
            - **Alto riesgo**: {len(df_filtered[df_filtered['Nivel_Riesgo'] == 'Alto'])} ({pct_alto:.1f}%)
            - **Medio riesgo**: {len(df_filtered[df_filtered['Nivel_Riesgo'] == 'Medio'])}
            - **Bajo riesgo**: {len(df_filtered[df_filtered['Nivel_Riesgo'] == 'Bajo'])}
            """)
        else:
            st.info("No hay datos para mostrar")

    with col3:
        st.markdown("### Recomendaciones")
        st.success("""
        - Revisar sucursales en alto riesgo
        - Analizar tendencias por región
        - Implementar medidas correctivas
        - Monitorear indicadores críticos
        """)

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p><strong>Dashboard de Análisis de Riesgo Crediticio</strong></p>
        <p style='font-size: 0.85em;'>Desarrollado con Streamlit, Altair y Plotly | Noviembre 2025</p>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.page == "reto":
    render_main_page()  
elif st.session_state.page == "detail":
    detail.render(go_to_main, load_data)     