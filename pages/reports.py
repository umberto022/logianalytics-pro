import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64

def show():
    st.title("📋 Reportes y Análisis")
    st.markdown("---")
    
    # Pestañas para diferentes tipos de reportes
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Reportes Ejecutivos", "📈 Análisis Detallado", "🔔 Alertas", "📤 Exportar Datos"])
    
    with tab1:
        executive_reports()
    
    with tab2:
        detailed_analysis()
    
    with tab3:
        alerts_system()
    
    with tab4:
        export_data()

def executive_reports():
    st.subheader("📊 Reportes Ejecutivos")
    
    # Selector de período
    col1, col2, col3 = st.columns(3)
    
    with col1:
        periodo = st.selectbox("Período", ["Última semana", "Último mes", "Último trimestre", "Último año"])
    
    with col2:
        formato = st.selectbox("Formato", ["Resumen", "Detallado", "Comparativo"])
    
    with col3:
        if st.button("🔄 Generar Reporte", type="primary"):
            st.session_state['reporte_generado'] = True
    
    if st.session_state.get('reporte_generado', False):
        # Generar datos del reporte
        reporte_data = generate_executive_report(periodo, formato)
        
        # Métricas principales
        st.markdown("### 📈 Resumen Ejecutivo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Envíos",
                f"{reporte_data['total_envios']:,}",
                f"{reporte_data['envios_delta']:+.1f}%"
            )
        
        with col2:
            st.metric(
                "Ingresos",
                f"${reporte_data['ingresos']:,.2f}",
                f"{reporte_data['ingresos_delta']:+.1f}%"
            )
        
        with col3:
            st.metric(
                "Costo Total",
                f"${reporte_data['costo_total']:,.2f}",
                f"{reporte_data['costo_delta']:+.1f}%"
            )
        
        with col4:
            st.metric(
                "Margen de Ganancia",
                f"{reporte_data['margen']:.1f}%",
                f"{reporte_data['margen_delta']:+.1f}%"
            )
        
        # Gráficos principales
        col1, col2 = st.columns(2)
        
        with col1:
            # Tendencia de envíos
            fig_envios = px.line(
                reporte_data['tendencia_envios'],
                x='fecha',
                y='envios',
                title="Tendencia de Envíos",
                color_discrete_sequence=['#667eea']
            )
            fig_envios.update_layout(height=400)
            st.plotly_chart(fig_envios, use_container_width=True)
        
        with col2:
            # Análisis de rentabilidad
            fig_rentabilidad = px.bar(
                reporte_data['rentabilidad_rutas'],
                x='ruta',
                y='margen',
                title="Rentabilidad por Ruta",
                color='margen',
                color_continuous_scale='RdYlGn'
            )
            fig_rentabilidad.update_layout(height=400)
            st.plotly_chart(fig_rentabilidad, use_container_width=True)
        
        # Análisis de satisfacción del cliente
        st.markdown("### 😊 Satisfacción del Cliente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución de calificaciones
            fig_calificaciones = px.pie(
                reporte_data['calificaciones'],
                values='cantidad',
                names='calificacion',
                title="Distribución de Calificaciones",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_calificaciones, use_container_width=True)
        
        with col2:
            # Tendencias de satisfacción
            fig_satisfaccion = px.line(
                reporte_data['tendencia_satisfaccion'],
                x='semana',
                y='satisfaccion',
                title="Evolución de Satisfacción",
                markers=True
            )
            fig_satisfaccion.update_layout(height=400)
            st.plotly_chart(fig_satisfaccion, use_container_width=True)
        
        # Recomendaciones estratégicas
        st.markdown("### 🎯 Recomendaciones Estratégicas")
        
        for i, recomendacion in enumerate(reporte_data['recomendaciones'], 1):
            st.write(f"**{i}. {recomendacion['titulo']}**")
            st.write(f"   {recomendacion['descripcion']}")
            st.write(f"   *Impacto estimado: {recomendacion['impacto']}*")
            st.write("---")

def detailed_analysis():
    st.subheader("📈 Análisis Detallado")
    
    # Filtros de análisis
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ruta_filtro = st.selectbox("Filtrar por Ruta", ["Todas", "Norte", "Sur", "Este", "Oeste", "Centro"])
    
    with col2:
        tipo_envio = st.selectbox("Tipo de Envío", ["Todos", "Express", "Estándar", "Económico"])
    
    with col3:
        fecha_inicio = st.date_input("Fecha Inicio", value=datetime.now() - timedelta(days=30))
        fecha_fin = st.date_input("Fecha Fin", value=datetime.now())
    
    # Análisis de rendimiento
    st.markdown("### 🚀 Análisis de Rendimiento")
    
    # Generar datos de análisis
    analisis_data = generate_detailed_analysis(ruta_filtro, tipo_envio, fecha_inicio, fecha_fin)
    
    # Métricas de rendimiento
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Eficiencia Promedio", f"{analisis_data['eficiencia']:.1f}%")
    
    with col2:
        st.metric("Tiempo Promedio", f"{analisis_data['tiempo_promedio']:.1f} días")
    
    with col3:
        st.metric("Costo por Envío", f"${analisis_data['costo_promedio']:.2f}")
    
    with col4:
        st.metric("Tasa de Éxito", f"{analisis_data['tasa_exito']:.1f}%")
    
    # Análisis temporal
    st.markdown("### ⏰ Análisis Temporal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Rendimiento por hora del día
        fig_hora = px.bar(
            analisis_data['por_hora'],
            x='hora',
            y='rendimiento',
            title="Rendimiento por Hora del Día",
            color='rendimiento',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_hora, use_container_width=True)
    
    with col2:
        # Rendimiento por día de la semana
        fig_dia = px.bar(
            analisis_data['por_dia'],
            x='dia',
            y='rendimiento',
            title="Rendimiento por Día de la Semana",
            color='rendimiento',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_dia, use_container_width=True)
    
    # Análisis de costos detallado
    st.markdown("### 💰 Análisis de Costos Detallado")
    
    fig_costos = px.sunburst(
        analisis_data['costos_detallados'],
        path=['categoria', 'subcategoria'],
        values='costo',
        title="Desglose de Costos"
    )
    st.plotly_chart(fig_costos, use_container_width=True)
    
    # Análisis de problemas
    st.markdown("### ⚠️ Análisis de Problemas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Problemas más frecuentes
        fig_problemas = px.bar(
            analisis_data['problemas'],
            x='problema',
            y='frecuencia',
            title="Problemas Más Frecuentes",
            color='frecuencia',
            color_continuous_scale='Reds'
        )
        fig_problemas.update_xaxis(tickangle=45)
        st.plotly_chart(fig_problemas, use_container_width=True)
    
    with col2:
        # Tendencias de problemas
        fig_tendencia_problemas = px.line(
            analisis_data['tendencia_problemas'],
            x='fecha',
            y='problemas',
            title="Tendencia de Problemas",
            color_discrete_sequence=['#ff6b6b']
        )
        st.plotly_chart(fig_tendencia_problemas, use_container_width=True)

def alerts_system():
    st.subheader("🔔 Sistema de Alertas")
    
    # Configuración de alertas
    st.markdown("### ⚙️ Configuración de Alertas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Alertas de Rendimiento")
        
        alerta_tiempo = st.checkbox("Tiempo de entrega excedido", value=True)
        if alerta_tiempo:
            umbral_tiempo = st.slider("Umbral de tiempo (días)", 1, 10, 3)
        
        alerta_costo = st.checkbox("Costo por envío elevado", value=True)
        if alerta_costo:
            umbral_costo = st.slider("Umbral de costo ($)", 20, 100, 50)
        
        alerta_eficiencia = st.checkbox("Eficiencia baja", value=True)
        if alerta_eficiencia:
            umbral_eficiencia = st.slider("Umbral de eficiencia (%)", 50, 90, 75)
    
    with col2:
        st.markdown("#### Alertas de Inventario")
        
        alerta_stock = st.checkbox("Stock bajo", value=True)
        if alerta_stock:
            umbral_stock = st.slider("Umbral de stock (unidades)", 10, 100, 50)
        
        alerta_demanda = st.checkbox("Demanda inusual", value=True)
        if alerta_demanda:
            umbral_demanda = st.slider("Umbral de desviación (%)", 10, 50, 25)
        
        alerta_reabastecimiento = st.checkbox("Reabastecimiento requerido", value=True)
    
    # Alertas activas
    st.markdown("### 🚨 Alertas Activas")
    
    if st.button("🔍 Verificar Alertas"):
        alertas = check_alerts(alerta_tiempo, alerta_costo, alerta_eficiencia, 
                             alerta_stock, alerta_demanda, alerta_reabastecimiento)
        
        if alertas:
            for alerta in alertas:
                if alerta['nivel'] == 'critico':
                    st.error(f"🔴 **CRÍTICO**: {alerta['mensaje']}")
                elif alerta['nivel'] == 'advertencia':
                    st.warning(f"🟡 **ADVERTENCIA**: {alerta['mensaje']}")
                else:
                    st.info(f"🔵 **INFO**: {alerta['mensaje']}")
                
                st.write(f"   *Detectado: {alerta['timestamp']}*")
                st.write("---")
        else:
            st.success("✅ No hay alertas activas")
    
    # Historial de alertas
    st.markdown("### 📜 Historial de Alertas")
    
    historial = generate_alert_history()
    
    # Filtros para el historial
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nivel_filtro = st.selectbox("Nivel", ["Todos", "Crítico", "Advertencia", "Info"])
    
    with col2:
        tipo_filtro = st.selectbox("Tipo", ["Todos", "Rendimiento", "Inventario", "Sistema"])
    
    with col3:
        dias_historial = st.slider("Últimos días", 1, 30, 7)
    
    # Tabla de historial
    df_historial = pd.DataFrame(historial)
    if not df_historial.empty:
        # Aplicar filtros
        if nivel_filtro != "Todos":
            df_historial = df_historial[df_historial['nivel'] == nivel_filtro.lower()]
        
        if tipo_filtro != "Todos":
            df_historial = df_historial[df_historial['tipo'] == tipo_filtro.lower()]
        
        st.dataframe(df_historial, use_container_width=True)
    else:
        st.info("No hay alertas en el historial seleccionado")

def export_data():
    st.subheader("📤 Exportar Datos")
    
    # Opciones de exportación
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Seleccionar Datos")
        
        tipo_datos = st.multiselect(
            "Tipo de datos a exportar",
            ["Envíos", "Rutas", "Costos", "Inventario", "Clientes", "Rendimiento"],
            default=["Envíos", "Rutas", "Costos"]
        )
        
        formato_export = st.selectbox(
            "Formato de exportación",
            ["CSV", "Excel", "JSON", "PDF"]
        )
        
        fecha_inicio = st.date_input("Fecha inicio", value=datetime.now() - timedelta(days=30))
        fecha_fin = st.date_input("Fecha fin", value=datetime.now())
    
    with col2:
        st.markdown("### ⚙️ Configuración")
        
        incluir_graficos = st.checkbox("Incluir gráficos", value=True)
        incluir_metricas = st.checkbox("Incluir métricas", value=True)
        incluir_recomendaciones = st.checkbox("Incluir recomendaciones", value=True)
        
        comprimir = st.checkbox("Comprimir archivo", value=False)
    
    # Generar y descargar datos
    if st.button("📥 Generar Archivo de Exportación", type="primary"):
        with st.spinner("Generando archivo de exportación..."):
            archivo = generate_export_file(
                tipo_datos, formato_export, fecha_inicio, fecha_fin,
                incluir_graficos, incluir_metricas, incluir_recomendaciones, comprimir
            )
            
            if archivo:
                st.success("✅ Archivo generado exitosamente")
                
                # Botón de descarga
                st.download_button(
                    label="⬇️ Descargar Archivo",
                    data=archivo['data'],
                    file_name=archivo['filename'],
                    mime=archivo['mime_type']
                )
                
                # Mostrar resumen
                st.markdown("### 📋 Resumen de Exportación")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Registros", f"{archivo['registros']:,}")
                
                with col2:
                    st.metric("Tamaño", f"{archivo['tamaño']:.1f} MB")
                
                with col3:
                    st.metric("Tiempo de generación", f"{archivo['tiempo']:.1f} seg")

def generate_executive_report(periodo, formato):
    """Genera reporte ejecutivo"""
    
    # Simular datos basados en el período
    if periodo == "Última semana":
        dias = 7
    elif periodo == "Último mes":
        dias = 30
    elif periodo == "Último trimestre":
        dias = 90
    else:
        dias = 365
    
    # Métricas principales
    total_envios = random.randint(5000, 15000)
    envios_delta = random.uniform(-10, 20)
    ingresos = total_envios * random.uniform(25, 45)
    ingresos_delta = random.uniform(-5, 15)
    costo_total = ingresos * random.uniform(0.6, 0.8)
    costo_delta = random.uniform(-10, 10)
    margen = ((ingresos - costo_total) / ingresos) * 100
    margen_delta = random.uniform(-2, 5)
    
    # Tendencia de envíos
    fechas = pd.date_range(start=datetime.now() - timedelta(days=dias), end=datetime.now(), freq='D')
    tendencia_envios = pd.DataFrame({
        'fecha': fechas,
        'envios': np.random.randint(100, 500, len(fechas))
    })
    
    # Rentabilidad por ruta
    rutas = ['Norte', 'Sur', 'Este', 'Oeste', 'Centro']
    rentabilidad_rutas = pd.DataFrame({
        'ruta': rutas,
        'margen': np.random.uniform(15, 35, len(rutas))
    })
    
    # Calificaciones de satisfacción
    calificaciones = pd.DataFrame({
        'calificacion': ['5 estrellas', '4 estrellas', '3 estrellas', '2 estrellas', '1 estrella'],
        'cantidad': [45, 30, 15, 7, 3]
    })
    
    # Tendencia de satisfacción
    semanas = pd.date_range(start=datetime.now() - timedelta(days=dias), end=datetime.now(), freq='W')
    tendencia_satisfaccion = pd.DataFrame({
        'semana': semanas,
        'satisfaccion': np.random.uniform(85, 95, len(semanas))
    })
    
    # Recomendaciones
    recomendaciones = [
        {
            'titulo': 'Optimizar Ruta Norte',
            'descripcion': 'La ruta norte muestra el menor margen de ganancia. Considerar renegociar tarifas o cambiar proveedores.',
            'impacto': 'Alto'
        },
        {
            'titulo': 'Implementar Entregas Nocturnas',
            'descripcion': 'Las entregas nocturnas podrían reducir costos de combustible y mejorar eficiencia.',
            'impacto': 'Medio'
        },
        {
            'titulo': 'Expandir Capacidad en Zona Centro',
            'descripcion': 'La zona centro muestra alta demanda. Considerar aumentar capacidad de almacenamiento.',
            'impacto': 'Alto'
        }
    ]
    
    return {
        'total_envios': total_envios,
        'envios_delta': envios_delta,
        'ingresos': ingresos,
        'ingresos_delta': ingresos_delta,
        'costo_total': costo_total,
        'costo_delta': costo_delta,
        'margen': margen,
        'margen_delta': margen_delta,
        'tendencia_envios': tendencia_envios,
        'rentabilidad_rutas': rentabilidad_rutas,
        'calificaciones': calificaciones,
        'tendencia_satisfaccion': tendencia_satisfaccion,
        'recomendaciones': recomendaciones
    }

def generate_detailed_analysis(ruta_filtro, tipo_envio, fecha_inicio, fecha_fin):
    """Genera análisis detallado"""
    
    # Métricas de rendimiento
    eficiencia = random.uniform(70, 95)
    tiempo_promedio = random.uniform(1.5, 4.0)
    costo_promedio = random.uniform(25, 60)
    tasa_exito = random.uniform(85, 98)
    
    # Rendimiento por hora
    horas = list(range(6, 22))
    por_hora = pd.DataFrame({
        'hora': horas,
        'rendimiento': np.random.uniform(60, 95, len(horas))
    })
    
    # Rendimiento por día
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    por_dia = pd.DataFrame({
        'dia': dias,
        'rendimiento': np.random.uniform(70, 90, len(dias))
    })
    
    # Costos detallados
    costos_detallados = pd.DataFrame({
        'categoria': ['Transporte', 'Transporte', 'Personal', 'Personal', 'Operaciones', 'Operaciones'],
        'subcategoria': ['Combustible', 'Mantenimiento', 'Conductores', 'Administrativo', 'Almacén', 'Seguros'],
        'costo': [15000, 8000, 25000, 12000, 5000, 3000]
    })
    
    # Problemas más frecuentes
    problemas = pd.DataFrame({
        'problema': ['Retraso en entrega', 'Daño en paquete', 'Dirección incorrecta', 'Cliente no disponible', 'Problema de ruta'],
        'frecuencia': [25, 15, 12, 8, 5]
    })
    
    # Tendencia de problemas
    fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')
    tendencia_problemas = pd.DataFrame({
        'fecha': fechas,
        'problemas': np.random.randint(0, 20, len(fechas))
    })
    
    return {
        'eficiencia': eficiencia,
        'tiempo_promedio': tiempo_promedio,
        'costo_promedio': costo_promedio,
        'tasa_exito': tasa_exito,
        'por_hora': por_hora,
        'por_dia': por_dia,
        'costos_detallados': costos_detallados,
        'problemas': problemas,
        'tendencia_problemas': tendencia_problemas
    }

def check_alerts(*args):
    """Verifica alertas activas"""
    
    alertas = []
    
    # Simular algunas alertas
    if random.random() < 0.3:  # 30% de probabilidad de alerta
        alertas.append({
            'nivel': 'critico',
            'mensaje': 'Tiempo de entrega promedio excede el umbral establecido',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    if random.random() < 0.4:  # 40% de probabilidad de alerta
        alertas.append({
            'nivel': 'advertencia',
            'mensaje': 'Costo por envío en ruta Norte supera el promedio',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    if random.random() < 0.2:  # 20% de probabilidad de alerta
        alertas.append({
            'nivel': 'info',
            'mensaje': 'Nueva optimización de ruta disponible',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return alertas

def generate_alert_history():
    """Genera historial de alertas"""
    
    alertas = []
    for i in range(50):  # 50 alertas de ejemplo
        niveles = ['critico', 'advertencia', 'info']
        tipos = ['rendimiento', 'inventario', 'sistema']
        
        alertas.append({
            'timestamp': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S'),
            'nivel': random.choice(niveles),
            'tipo': random.choice(tipos),
            'mensaje': f'Alerta de ejemplo {i+1}',
            'resuelta': random.choice([True, False])
        })
    
    return alertas

def generate_export_file(tipo_datos, formato, fecha_inicio, fecha_fin, incluir_graficos, incluir_metricas, incluir_recomendaciones, comprimir):
    """Genera archivo de exportación"""
    
    # Simular generación de datos
    registros = random.randint(1000, 10000)
    tamaño = random.uniform(1.5, 15.0)
    tiempo = random.uniform(2.0, 8.0)
    
    # Generar datos de ejemplo
    if formato == "CSV":
        data = "fecha,envio,costo,tiempo\n"
        for i in range(100):
            data += f"2024-01-{i%30+1:02d},ENV{i:04d},{random.uniform(20,80):.2f},{random.uniform(1,5):.1f}\n"
        
        mime_type = "text/csv"
        filename = "logi_analytics_export.csv"
    
    elif formato == "Excel":
        # Simular archivo Excel
        data = b"Excel file content simulation"
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "logi_analytics_export.xlsx"
    
    elif formato == "JSON":
        data = json.dumps({
            "envios": [{"id": i, "costo": random.uniform(20, 80), "tiempo": random.uniform(1, 5)} 
                      for i in range(100)],
            "metricas": {"total_envios": 100, "costo_promedio": 45.5},
            "timestamp": datetime.now().isoformat()
        })
        mime_type = "application/json"
        filename = "logi_analytics_export.json"
    
    else:  # PDF
        data = b"PDF file content simulation"
        mime_type = "application/pdf"
        filename = "logi_analytics_export.pdf"
    
    return {
        'data': data,
        'filename': filename,
        'mime_type': mime_type,
        'registros': registros,
        'tamaño': tamaño,
        'tiempo': tiempo
    }
