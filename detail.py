import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from geminiPrueba import analyze_branch_with_gemini
import chatWidget
    
def render(return_main, load_data):
    # Cargar datos
    df_clusters, df_completos = load_data()
    
    # Mostrar detalles de la sucursal seleccionada
    suc = st.session_state.selected_sucursal
    col1, col2 = st.columns([6,1])
    with col1: 
        st.header(f"Detalles de sucursal {suc}")
    with col2: 
        if st.button("Main"):
            return_main()
    
    # Cluster al que pertenece
    df_filtered_cluster = df_clusters[df_clusters['Sucursal'] == suc]
    cluster = df_filtered_cluster['Cluster_KM'].values[0]
    region = df_filtered_cluster['Región'].values[0]
    nivel_riesgo = df_filtered_cluster['Nivel_Riesgo'].values[0]
    
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        st.subheader(f"Cluster: {cluster}")
    with col2: 
        st.subheader(f"Región: {region}")
    with col3:
        risk_color = {
            'Alto': '#c62828',
            'Medio': '#ef6c00',
            'Bajo': '#2e7d32'
        }.get(nivel_riesgo, '#666')
        st.markdown(f"<h3 style='color: {risk_color};'>Riesgo: {nivel_riesgo}</h3>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # ANÁLISIS INTELIGENTE CON DIGIBOT
    # ========================================
    st.markdown("""
    <div style='background: linear-gradient(135deg, #0A3D20 0%, #14532d 100%); 
                padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
        <h2 style='color: white; margin: 0; display: flex; align-items: center;'>
            🤖 Análisis Inteligente DigiBot
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar estado para análisis de IA
    if 'ai_analysis' not in st.session_state:
        st.session_state.ai_analysis = {}
    
    # Generar análisis automáticamente si no existe
    if suc not in st.session_state.ai_analysis:
        with st.spinner("DigiBot está analizando la sucursal..."):
            sucursal_data = df_filtered_cluster.iloc[0].to_dict()
            st.session_state.ai_analysis[suc] = analyze_branch_with_gemini(sucursal_data)
    
    # Mostrar análisis
    analysis = st.session_state.ai_analysis[suc]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style='background: #fff5f5; padding: 20px; border-radius: 10px; border-left: 4px solid #c62828;'>
            <h3 style='color: #c62828; margin-top: 0;'> Posibles Causas</h3>
        """, unsafe_allow_html=True)
        
        for i, cause in enumerate(analysis.get('causes', []), 1):
            st.markdown(f"**{i}.** {cause}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Factor de riesgo principal
        st.markdown(f"""
        <div style='background: #ffebee; padding: 15px; border-radius: 8px; 
                    border: 2px solid #c62828; margin-top: 15px;'>
            <p style='margin: 0; font-weight: bold; color: #c62828; font-size: 12px;'>
                FACTOR DE RIESGO PRINCIPAL
            </p>
            <p style='margin: 5px 0 0 0; color: #b71c1c; font-weight: 600; font-size: 16px;'>
                {analysis.get('riskFactor', 'N/A')}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: #f1f8f4; padding: 20px; border-radius: 10px; border-left: 4px solid #2e7d32;'>
            <h3 style='color: #2e7d32; margin-top: 0;'> Sugerencias de Mejora</h3>
        """, unsafe_allow_html=True)
        
        for i, suggestion in enumerate(analysis.get('suggestions', []), 1):
            st.markdown(f"**{i}.** {suggestion}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================
    # KPIs PRINCIPALES
    # ========================================
    st.header("Indicadores Clave de Desempeño")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        icv_promedio = df_filtered_cluster['ICV_Actual'].mean()
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
        capital_dispersado = df_filtered_cluster['Capital_Dispersado_Actual'].sum()
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
        saldo_insoluto = df_filtered_cluster['Saldo_Insoluto_Total_Actual'].sum()
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
        fpd_promedio = df_filtered_cluster['FPD_Neto_Actual'].mean()
        fpd_global = df_clusters['FPD_Neto_Actual'].mean()
        delta_fpd = fpd_promedio - fpd_global
        delta_color_fpd = "#c62828" if delta_fpd > 0 else "#2e7d32"
        delta_text_fpd = f"+${delta_fpd:,.0f}" if delta_fpd > 0 else f"${delta_fpd:,.0f}"
        st.markdown(f"""
        <div class='metric-card'>
            <h4>FPD Neto Promedio</h4>
            <p>${fpd_promedio:,.0f}</p>
            <small style='color: {delta_color_fpd}; font-weight: 600;'>{delta_text_fpd} vs promedio</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # ========================================
    # ANÁLISIS TEMPORAL
    # ========================================
    st.header("Análisis Temporal de Indicadores")
    
    def calcular_datos_gráficas(nombre_columnas):
        datos = {}
        for col in nombre_columnas:
            formatted_col = col.replace(" ", "_").replace("-", "_")
            df_cols = df_completos[df_completos['Sucursal'] == suc].filter(like=formatted_col)
            
            # Pasar a formato largo
            df_long = df_cols.melt(
                var_name='Periodo',
                value_name=col
            )
            
            orden = df_cols.columns.tolist()

            # Ordenar los periodos según el orden original del df
            df_long['Periodo'] = pd.Categorical(df_long['Periodo'], categories=orden, ordered=True)
            df_long = df_long.sort_values('Periodo').reset_index(drop=True)
            df_long['t'] = range(len(df_long))
            
            # Calcular regresión lineal simple manualmente
            x = df_long['t']
            y = df_long[col]
            
            # Fórmula de regresión lineal simple
            n = len(x)
            sum_x = x.sum()
            sum_y = y.sum()
            sum_xy = (x * y).sum()
            sum_x2 = (x ** 2).sum()
            
            pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercepto = (sum_y - pendiente * sum_x) / n
            
            df_long['tendencia'] = intercepto + pendiente * df_long['t']
            datos[col] = (df_long, pendiente, orden)
            
        return datos

    columnas_historicas = ["ICV", "Capital Dispersado", "Saldo Insoluto Total", "Saldo Insoluto Vencido", 
                          "Saldo 30-89", "FPD Neto", "Castigos", "Quitas"]
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(columnas_historicas)
    
    datos_graficas = calcular_datos_gráficas(columnas_historicas)
    
    for idx, tab in enumerate([tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8]):
        with tab:
            col_name = columnas_historicas[idx]
            df_long, pendiente, orden = datos_graficas[col_name]
            
            # Crear la gráfica
            line_chart = (
                alt.Chart(df_long)
                .mark_line(point=True, strokeWidth=3)
                .encode(
                    x=alt.X('Periodo:N', sort=orden, title='Periodo'),
                    y=alt.Y(f'{col_name}:Q', title=f'{col_name}'),
                    tooltip=['Periodo:N', alt.Tooltip(f'{col_name}:Q', format=',.2f')]
                )
            )
            
            trend = (
                alt.Chart(df_long)
                .mark_line(strokeDash=[5,5], color='red', strokeWidth=2) 
                .encode(
                    x=alt.X('Periodo:N', sort=orden),
                    y=alt.Y('tendencia:Q')
                )
            )
            
            final_chart = line_chart + trend
            
            col1, col2 = st.columns([7, 3])
            with col1:
                st.write(f"#### Análisis de {col_name} a lo largo del tiempo")
            with col2:
                if pendiente > 0:
                    st.markdown(f"""
                    <div style='background: #ffebee; padding: 10px; border-radius: 6px; text-align: center;'>
                        <p style='margin: 0; color: #c62828; font-weight: bold;'>
                            📈 Tendencia al alza<br/>+{pendiente:,.2f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background: #e8f5e9; padding: 10px; border-radius: 6px; text-align: center;'>
                        <p style='margin: 0; color: #2e7d32; font-weight: bold;'>
                            📉 Tendencia a la baja<br/>{pendiente:,.2f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.altair_chart(final_chart, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================
    # WIDGET DE CHAT
    # ========================================
    # Preparar contexto completo para el chat con info del dataset
    chat_context = {
        'sucursal_actual': df_filtered_cluster.iloc[0].to_dict(),
        'dataset_completo': df_clusters.to_dict('records'),
        'total_sucursales': len(df_clusters),
        'sucursales_alto_riesgo': len(df_clusters[df_clusters['Nivel_Riesgo'] == 'Alto']),
        'promedio_fpd': df_clusters['FPD_Neto_Actual'].mean(),
        'promedio_icv': df_clusters['ICV_Actual'].mean()
    }
    chatWidget.render_chat_widget(chat_context)