import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
    
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
    st.subheader(f"Cluster: {cluster}")
    
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
    
    
    col5, col6 = st.columns([3,1])
    
    with col5:
        # Gráfico de lineas del ICV a lo largo del tiempo con tendencia
        
        df_icv  = df_completos[df_completos['Sucursal'] == suc].filter(like='ICV')
        # Pasar a formato largo
        df_long = df_icv.melt(
            var_name='Periodo',
            value_name='ICV'
        )
        
        orden = df_icv.columns.tolist()

        # Ordenar los periodos según el orden original del df
        df_long['Periodo'] = pd.Categorical(df_long['Periodo'], categories=orden, ordered=True)
        df_long = df_long.sort_values('Periodo').reset_index(drop=True)
        df_long['t'] = range(len(df_long))
        
        # Calcular regresión lineal simple manualmente
        x = df_long['t']
        y = df_long['ICV']
        
        # Fórmula de regresión lineal simple
        n = len(x)
        sum_x = x.sum()
        sum_y = y.sum()
        sum_xy = (x * y).sum()
        sum_x2 = (x ** 2).sum()
        
        pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercepto = (sum_y - pendiente * sum_x) / n
        
        df_long['tendencia'] = intercepto + pendiente * df_long['t']
        
        # Crear la gráfica
        line_chart = (
            alt.Chart(df_long.reset_index())
            .mark_line(color='#1f77b4')
            .encode(
                x=alt.X('Periodo:N', title='Periodo', sort=orden),
                y=alt.Y('ICV:Q', title='ICV (%)'),
            )
        )
        
        trend = (
            alt.Chart(df_long)
            .mark_line(strokeDash=[5,5], color='red') 
            .encode(
                x=alt.X('Periodo:N', sort=orden),
                y=alt.Y('tendencia:Q')
            )
        )
        
        final_chart = line_chart + trend
        
        col7, col8 = st.columns([3,1])
        with col7: 
            st.subheader("Análisis ICV")
        with col8:
            if pendiente > 0:
                st.write(f"Aumento {pendiente:.2f}")
            else:
                st.write(f"Disminución {pendiente:.2f}")
                    
        st.altair_chart(final_chart, use_container_width=True)
    with col6:
        st.markdown("### Posibles causas")
        st.warning("""
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
        - Monitorear indicadores críticos
    """)