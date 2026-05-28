import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

def show():
    st.title("📊 Dashboard Principal")
    st.markdown("---")
    
    # Generar datos de ejemplo
    data = generate_dashboard_data()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Envíos Hoy",
            value=f"{data['envios_hoy']:,}",
            delta=f"{data['envios_delta']:+.1f}%"
        )
    
    with col2:
        st.metric(
            label="Costo Promedio",
            value=f"${data['costo_promedio']:.2f}",
            delta=f"{data['costo_delta']:+.1f}%"
        )
    
    with col3:
        st.metric(
            label="Tiempo Promedio",
            value=f"{data['tiempo_promedio']:.1f} días",
            delta=f"{data['tiempo_delta']:+.1f}%"
        )
    
    with col4:
        st.metric(
            label="Satisfacción",
            value=f"{data['satisfaccion']:.1f}%",
            delta=f"{data['satisfaccion_delta']:+.1f}%"
        )
    
    st.markdown("---")
    
    # Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Tendencias de Envíos")
        fig_envios = px.line(
            data['tendencias'], 
            x='fecha', 
            y='envios',
            title="Envíos por Día (Últimos 30 días)",
            color_discrete_sequence=['#667eea']
        )
        fig_envios.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Número de Envíos",
            height=400
        )
        st.plotly_chart(fig_envios, use_container_width=True)
    
    with col2:
        st.subheader("💰 Análisis de Costos")
        fig_costos = px.bar(
            data['costos_por_ruta'],
            x='ruta',
            y='costo_promedio',
            title="Costo Promedio por Ruta",
            color='costo_promedio',
            color_continuous_scale='Viridis'
        )
        fig_costos.update_layout(
            xaxis_title="Ruta",
            yaxis_title="Costo Promedio ($)",
            height=400
        )
        st.plotly_chart(fig_costos, use_container_width=True)
    
    # Análisis geográfico
    st.subheader("🗺️ Análisis Geográfico")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Mapa de calor de entregas
        fig_mapa = px.scatter_mapbox(
            data['entregas_geograficas'],
            lat="lat",
            lon="lon",
            size="cantidad",
            color="costo_promedio",
            hover_name="ciudad",
            hover_data=["envios", "costo_promedio"],
            color_continuous_scale="Viridis",
            size_max=50,
            zoom=3,
            title="Distribución de Entregas por Región"
        )
        fig_mapa.update_layout(
            mapbox_style="open-street-map",
            height=500
        )
        st.plotly_chart(fig_mapa, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Top Ciudades")
        for i, ciudad in enumerate(data['top_ciudades'], 1):
            st.write(f"{i}. **{ciudad['nombre']}**")
            st.write(f"   Envíos: {ciudad['envios']:,}")
            st.write(f"   Costo: ${ciudad['costo']:.2f}")
            st.write("---")
    
    # Análisis de eficiencia
    st.subheader("⚡ Análisis de Eficiencia")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Eficiencia por día de la semana
        fig_eficiencia = px.bar(
            data['eficiencia_semanal'],
            x='dia',
            y='eficiencia',
            title="Eficiencia por Día de la Semana",
            color='eficiencia',
            color_continuous_scale='RdYlGn'
        )
        fig_eficiencia.update_layout(
            xaxis_title="Día de la Semana",
            yaxis_title="Eficiencia (%)",
            height=400
        )
        st.plotly_chart(fig_eficiencia, use_container_width=True)
    
    with col2:
        # Distribución de tiempos de entrega
        fig_tiempos = px.histogram(
            data['tiempos_entrega'],
            x='tiempo_entrega',
            nbins=20,
            title="Distribución de Tiempos de Entrega",
            color_discrete_sequence=['#764ba2']
        )
        fig_tiempos.update_layout(
            xaxis_title="Tiempo de Entrega (días)",
            yaxis_title="Frecuencia",
            height=400
        )
        st.plotly_chart(fig_tiempos, use_container_width=True)
    
    # Alertas y notificaciones
    st.subheader("🔔 Alertas y Notificaciones")
    
    alertas = data['alertas']
    
    for alerta in alertas:
        if alerta['tipo'] == 'error':
            st.error(f"⚠️ {alerta['mensaje']}")
        elif alerta['tipo'] == 'warning':
            st.warning(f"⚠️ {alerta['mensaje']}")
        else:
            st.info(f"ℹ️ {alerta['mensaje']}")

def generate_dashboard_data():
    """Genera datos de ejemplo para el dashboard"""
    np.random.seed(42)
    
    # Métricas principales
    envios_hoy = random.randint(1200, 1500)
    envios_delta = random.uniform(-5, 15)
    costo_promedio = random.uniform(35, 55)
    costo_delta = random.uniform(-10, 5)
    tiempo_promedio = random.uniform(1.5, 3.5)
    tiempo_delta = random.uniform(-20, 10)
    satisfaccion = random.uniform(85, 98)
    satisfaccion_delta = random.uniform(-2, 5)
    
    # Tendencias de envíos (últimos 30 días)
    fechas = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    tendencias = pd.DataFrame({
        'fecha': fechas,
        'envios': np.random.randint(800, 1500, len(fechas))
    })
    
    # Costos por ruta
    rutas = ['Norte', 'Sur', 'Este', 'Oeste', 'Centro', 'Noroeste', 'Noreste', 'Suroeste', 'Sureste']
    costos_por_ruta = pd.DataFrame({
        'ruta': rutas,
        'costo_promedio': np.random.uniform(25, 65, len(rutas))
    })
    
    # Datos geográficos
    ciudades = [
        {'ciudad': 'Ciudad de México', 'lat': 19.4326, 'lon': -99.1332, 'envios': 450, 'costo_promedio': 42.50},
        {'ciudad': 'Guadalajara', 'lat': 20.6597, 'lon': -103.3496, 'envios': 320, 'costo_promedio': 38.75},
        {'ciudad': 'Monterrey', 'lat': 25.6866, 'lon': -100.3161, 'envios': 280, 'costo_promedio': 45.20},
        {'ciudad': 'Puebla', 'lat': 19.0414, 'lon': -98.2063, 'envios': 180, 'costo_promedio': 35.80},
        {'ciudad': 'Tijuana', 'lat': 32.5149, 'lon': -117.0382, 'envios': 150, 'costo_promedio': 52.30},
        {'ciudad': 'León', 'lat': 21.1256, 'lon': -101.6860, 'envios': 120, 'costo_promedio': 41.90},
        {'ciudad': 'Juárez', 'lat': 31.6904, 'lon': -106.4244, 'envios': 95, 'costo_promedio': 48.60},
        {'ciudad': 'Torreón', 'lat': 25.5431, 'lon': -103.4180, 'envios': 85, 'costo_promedio': 44.15}
    ]
    
    entregas_geograficas = pd.DataFrame(ciudades)
    entregas_geograficas['cantidad'] = entregas_geograficas['envios']
    
    # Top ciudades
    top_ciudades = sorted(ciudades, key=lambda x: x['envios'], reverse=True)[:5]
    
    # Eficiencia semanal
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    eficiencia_semanal = pd.DataFrame({
        'dia': dias,
        'eficiencia': np.random.uniform(75, 95, len(dias))
    })
    
    # Tiempos de entrega
    tiempos_entrega = pd.DataFrame({
        'tiempo_entrega': np.random.normal(2.5, 0.8, 1000)
    })
    
    # Alertas
    alertas = [
        {'tipo': 'warning', 'mensaje': 'Ruta Norte: Costo aumentó 15% esta semana'},
        {'tipo': 'info', 'mensaje': 'Nueva optimización disponible para ruta Sur'},
        {'tipo': 'error', 'mensaje': 'Retraso crítico en entrega #12345 - Cliente VIP'},
        {'tipo': 'info', 'mensaje': 'Meta mensual de envíos: 85% completada'}
    ]
    
    return {
        'envios_hoy': envios_hoy,
        'envios_delta': envios_delta,
        'costo_promedio': costo_promedio,
        'costo_delta': costo_delta,
        'tiempo_promedio': tiempo_promedio,
        'tiempo_delta': tiempo_delta,
        'satisfaccion': satisfaccion,
        'satisfaccion_delta': satisfaccion_delta,
        'tendencias': tendencias,
        'costos_por_ruta': costos_por_ruta,
        'entregas_geograficas': entregas_geograficas,
        'top_ciudades': top_ciudades,
        'eficiencia_semanal': eficiencia_semanal,
        'tiempos_entrega': tiempos_entrega,
        'alertas': alertas
    }
