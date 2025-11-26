import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import ast
import re
from geminiPrueba import load_AI_info_sucursal
    
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
    col1, col2 = st.columns([5,1])
    with col1:
        st.subheader(f"Cluster: {cluster}")
    with col2: 
        st.subheader(f"Región: {region}")
    
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
        fpd_promedio = df_filtered_cluster['FPD_Actual'].mean()
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
    
    
    col5, col6 = st.columns([3,1])
    
    def calcular_datos_gráficas(nombre_columnas):
        datos = {}
        for col in nombre_columnas:
            formatted_col = col.replace(" ", "_").replace("-", "_")
            df_cols = df_completos[df_completos['Sucursal'] == suc].filter(like=formatted_col)
            # Eliminar columnas de FPD_NETO
            if col == "FPD":
                regex = rf'^{formatted_col}_(T.*|[Aa]ctual.*)$'
                df_cols = (df_completos[df_completos['Sucursal'] == suc].filter(regex=regex)) 
            
            df_cols = df_cols.copy()
            df_cols.columns = [c.rsplit("_", 1)[-1] for c in df_cols.columns]
        
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

    with col5:
        # Gráfico de lineas del ICV a lo largo del tiempo con tendencia
        columnas_historicas = ["ICV", "Capital Dispersado", "Saldo Insoluto Total", "Saldo Insoluto Vencido", "Saldo 30-89", "FPD", "Castigos", "Quitas"]
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(columnas_historicas)
        
        datos_graficas = calcular_datos_gráficas(columnas_historicas)
        for idx, tab in enumerate([tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8]):
            with tab:
                col_name = columnas_historicas[idx]
                df_long, pendiente, orden = datos_graficas[col_name]
                
                # Crear la gráfica
                line_chart = (
                    alt.Chart(df_long)
                    .mark_line()
                    .encode(
                        x=alt.X('Periodo:N', sort=orden, title='Periodo'),
                        y=alt.Y(f'{col_name}:Q', title=f'{col_name}')
                    )
                )
                
                points = (
                    alt.Chart(df_long)
                    .mark_circle(size=70)   # tamaño del punto
                    .encode(
                        x=alt.X('Periodo:N', sort=orden),
                        y=alt.Y(f'{col_name}:Q'),
                        tooltip=[
                            alt.Tooltip('Periodo:N', title='Periodo'),
                            alt.Tooltip(f'{col_name}:Q', title=col_name, format=',.2f'),
                        ]
                    )
                )
                
                trend = (
                    alt.Chart(df_long)
                    .mark_line(strokeDash=[5,5], color='red') 
                    .encode(
                        x=alt.X('Periodo:N', sort=orden),
                        y=alt.Y('tendencia:Q'),
                        tooltip=[
                            alt.Tooltip('Periodo:N', title='Periodo'),
                            alt.Tooltip('tendencia:Q', title='Tendencia', format=',.2f')
                        ]
                    )
                )
                
                final_chart = line_chart + points + trend
                
                col1, col2 = st.columns([8,3])
                # Mostrar título y tendencia
                with col1:
                    st.write (f"#### Análisis de {col_name} a lo largo del tiempo")
                with col2:
                    if pendiente > 0:
                        st.success(f"Tendencia al alza (+{pendiente:,.2f})")
                    else:
                        st.error(f"Tendencia a la baja ({pendiente:,.2f})")
                # Mostrar gráfica
                st.altair_chart(final_chart, use_container_width=True)
     
    with col6:
        st.markdown("### Posibles causas")
        st.warning(f"""
        - Procesos clave ejecutados con inconsistencias.
        - Falta de seguimiento en tareas críticas.
        - Errores recurrentes en la operación diaria.
        """)
        
    st.markdown("### Sugerencias de mejora")
    st.info(f"""
        - Reforzar seguimiento puntual de desempeño.
        - Implementar acciones correctivas inmediatas.
        - Revisar procesos críticos de operación.
        - Ajustar estrategia para reducir riesgos.
        - Monitorear indicadores críticos.
        """)
