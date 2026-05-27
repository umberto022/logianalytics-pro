import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.optimize import minimize
import random
from datetime import datetime, timedelta

def show():
    st.title("🚛 Optimización de Rutas y Costos")
    st.markdown("---")
    
    # Pestañas para diferentes tipos de optimización
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Optimización de Rutas", "💰 Análisis de Costos", "📦 Gestión de Inventario", "🎯 Predicción de Demanda"])
    
    with tab1:
        route_optimization()
    
    with tab2:
        cost_analysis()
    
    with tab3:
        inventory_management()
    
    with tab4:
        demand_prediction()

def route_optimization():
    st.subheader("📍 Optimización de Rutas")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Configuración")
        
        # Parámetros de optimización
        num_vehiculos = st.slider("Número de Vehículos", 1, 10, 3)
        capacidad_max = st.slider("Capacidad Máxima (kg)", 1000, 5000, 2000)
        tiempo_max = st.slider("Tiempo Máximo (horas)", 8, 16, 12)
        
        # Criterios de optimización
        criterio = st.selectbox(
            "Criterio de Optimización",
            ["Minimizar Distancia", "Minimizar Tiempo", "Minimizar Costo", "Balanceado"]
        )
        
        if st.button("🚀 Optimizar Rutas", type="primary"):
            with st.spinner("Calculando rutas óptimas..."):
                rutas_optimizadas = calculate_optimal_routes(num_vehiculos, capacidad_max, tiempo_max, criterio)
                st.session_state['rutas_optimizadas'] = rutas_optimizadas
    
    with col2:
        st.markdown("### Resultados de Optimización")
        
        if 'rutas_optimizadas' in st.session_state:
            rutas = st.session_state['rutas_optimizadas']
            
            # Métricas de optimización
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Distancia Total", f"{rutas['distancia_total']:.1f} km")
            with col2:
                st.metric("Tiempo Total", f"{rutas['tiempo_total']:.1f} h")
            with col3:
                st.metric("Costo Total", f"${rutas['costo_total']:.2f}")
            
            # Mapa de rutas
            fig = create_route_map(rutas['rutas'])
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de rutas detallada
            st.markdown("### Detalles por Ruta")
            df_rutas = pd.DataFrame(rutas['rutas'])
            st.dataframe(df_rutas, use_container_width=True)
            
            # Ahorros estimados
            st.markdown("### 💡 Ahorros Estimados")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Reducción de Distancia", f"{rutas['ahorro_distancia']:.1f}%")
                st.metric("Reducción de Tiempo", f"{rutas['ahorro_tiempo']:.1f}%")
            
            with col2:
                st.metric("Reducción de Costo", f"{rutas['ahorro_costo']:.1f}%")
                st.metric("Ahorro Mensual", f"${rutas['ahorro_mensual']:,.2f}")
        else:
            st.info("Configure los parámetros y haga clic en 'Optimizar Rutas' para ver los resultados")

def cost_analysis():
    st.subheader("💰 Análisis de Costos")
    
    # Generar datos de costos
    costos_data = generate_cost_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Costos por Categoría")
        fig_costos = px.pie(
            costos_data['por_categoria'],
            values='costo',
            names='categoria',
            title="Distribución de Costos"
        )
        st.plotly_chart(fig_costos, use_container_width=True)
    
    with col2:
        st.markdown("### Tendencias de Costos")
        fig_tendencia = px.line(
            costos_data['tendencias'],
            x='mes',
            y='costo_total',
            title="Evolución de Costos (Últimos 12 meses)",
            markers=True
        )
        st.plotly_chart(fig_tendencia, use_container_width=True)
    
    # Análisis de costos por ruta
    st.markdown("### Análisis Detallado por Ruta")
    
    fig_costos_ruta = px.bar(
        costos_data['por_ruta'],
        x='ruta',
        y='costo_promedio',
        color='costo_promedio',
        title="Costo Promedio por Ruta",
        color_continuous_scale='Reds'
    )
    st.plotly_chart(fig_costos_ruta, use_container_width=True)
    
    # Recomendaciones de optimización
    st.markdown("### 🎯 Recomendaciones de Optimización")
    
    recomendaciones = [
        "Consolidar envíos en la ruta Norte para reducir costos fijos",
        "Implementar entregas nocturnas en zona Centro para evitar tráfico",
        "Negociar tarifas preferenciales con proveedores de combustible",
        "Optimizar rutas urbanas usando algoritmos de machine learning"
    ]
    
    for i, rec in enumerate(recomendaciones, 1):
        st.write(f"{i}. {rec}")

def inventory_management():
    st.subheader("📦 Gestión de Inventario")
    
    # Parámetros de inventario
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Configuración de Inventario")
        
        stock_actual = st.number_input("Stock Actual", value=1000, min_value=0)
        demanda_promedio = st.number_input("Demanda Promedio (unidades/día)", value=50, min_value=1)
        tiempo_entrega = st.number_input("Tiempo de Entrega (días)", value=7, min_value=1)
        costo_almacenamiento = st.number_input("Costo de Almacenamiento (% anual)", value=20, min_value=0)
        costo_pedido = st.number_input("Costo por Pedido", value=100, min_value=0)
    
    with col2:
        st.markdown("### Análisis de Inventario")
        
        # Calcular punto de reorden
        punto_reorden = demanda_promedio * tiempo_entrega
        stock_seguridad = demanda_promedio * 2  # 2 días de stock de seguridad
        
        # Calcular cantidad económica de pedido (EOQ)
        eoq = np.sqrt((2 * demanda_promedio * 365 * costo_pedido) / (costo_almacenamiento / 100))
        
        st.metric("Punto de Reorden", f"{punto_reorden:.0f} unidades")
        st.metric("Stock de Seguridad", f"{stock_seguridad:.0f} unidades")
        st.metric("Cantidad Óptima de Pedido", f"{eoq:.0f} unidades")
        
        # Estado del inventario
        if stock_actual < punto_reorden:
            st.error("⚠️ Stock bajo - Se requiere reabastecimiento urgente")
        elif stock_actual < punto_reorden + stock_seguridad:
            st.warning("⚠️ Stock bajo - Considerar reabastecimiento")
        else:
            st.success("✅ Stock adecuado")
    
    # Simulación de inventario
    st.markdown("### Simulación de Inventario (Próximos 30 días)")
    
    if st.button("Simular Inventario"):
        simulacion = simulate_inventory(stock_actual, demanda_promedio, tiempo_entrega, eoq)
        
        fig = px.line(
            simulacion,
            x='dia',
            y='stock',
            title="Proyección de Stock",
            markers=True
        )
        fig.add_hline(y=punto_reorden, line_dash="dash", line_color="red", 
                     annotation_text="Punto de Reorden")
        fig.add_hline(y=stock_seguridad, line_dash="dash", line_color="orange", 
                     annotation_text="Stock de Seguridad")
        
        st.plotly_chart(fig, use_container_width=True)

def demand_prediction():
    st.subheader("🎯 Predicción de Demanda")
    
    # Parámetros de predicción
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Configuración de Predicción")
        
        horizonte = st.selectbox("Horizonte de Predicción", ["1 semana", "1 mes", "3 meses", "6 meses"])
        confianza = st.slider("Nivel de Confianza (%)", 80, 99, 95)
        
        # Factores estacionales
        estacionalidad = st.checkbox("Incluir Estacionalidad", value=True)
        tendencia = st.checkbox("Incluir Tendencia", value=True)
    
    with col2:
        st.markdown("### Predicción Actual")
        
        # Generar predicción
        prediccion = generate_demand_prediction(horizonte, confianza, estacionalidad, tendencia)
        
        st.metric("Demanda Esperada", f"{prediccion['demanda_esperada']:.0f} unidades")
        st.metric("Intervalo de Confianza", f"±{prediccion['intervalo']:.0f} unidades")
        st.metric("Probabilidad de Stockout", f"{prediccion['prob_stockout']:.1f}%")
    
    # Gráfico de predicción
    st.markdown("### Proyección de Demanda")
    
    fig = go.Figure()
    
    # Datos históricos
    fig.add_trace(go.Scatter(
        x=prediccion['fechas_historicas'],
        y=prediccion['demanda_historica'],
        mode='lines',
        name='Demanda Histórica',
        line=dict(color='blue')
    ))
    
    # Predicción
    fig.add_trace(go.Scatter(
        x=prediccion['fechas_prediccion'],
        y=prediccion['demanda_prediccion'],
        mode='lines',
        name='Predicción',
        line=dict(color='red', dash='dash')
    ))
    
    # Intervalo de confianza
    fig.add_trace(go.Scatter(
        x=prediccion['fechas_prediccion'],
        y=prediccion['limite_superior'],
        mode='lines',
        line=dict(width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=prediccion['fechas_prediccion'],
        y=prediccion['limite_inferior'],
        mode='lines',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(255,0,0,0.2)',
        name=f'Intervalo de Confianza {confianza}%'
    ))
    
    fig.update_layout(
        title="Predicción de Demanda",
        xaxis_title="Fecha",
        yaxis_title="Demanda (unidades)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recomendaciones basadas en la predicción
    st.markdown("### 📋 Recomendaciones")
    
    if prediccion['prob_stockout'] > 20:
        st.warning("⚠️ Alta probabilidad de stockout - Aumentar inventario de seguridad")
    
    if prediccion['demanda_esperada'] > prediccion['demanda_historica'].mean() * 1.2:
        st.info("📈 Demanda creciente - Considerar expansión de capacidad")
    
    if prediccion['demanda_esperada'] < prediccion['demanda_historica'].mean() * 0.8:
        st.info("📉 Demanda decreciente - Revisar estrategia de marketing")

def calculate_optimal_routes(num_vehiculos, capacidad_max, tiempo_max, criterio):
    """Calcula rutas óptimas usando algoritmos de optimización"""
    
    # Generar datos de ejemplo de puntos de entrega
    puntos = generate_delivery_points(20)
    
    # Simular optimización (en un caso real usaríamos algoritmos como TSP o VRP)
    rutas = []
    total_distance = 0
    total_time = 0
    total_cost = 0
    
    for i in range(num_vehiculos):
        # Simular asignación de puntos a cada vehículo
        puntos_vehiculo = puntos[i*4:(i+1)*4] if i < num_vehiculos-1 else puntos[i*4:]
        
        if puntos_vehiculo:
            distancia = random.uniform(50, 200)
            tiempo = random.uniform(4, 12)
            costo = distancia * random.uniform(0.5, 1.5)
            
            rutas.append({
                'vehiculo': f'Vehículo {i+1}',
                'puntos': len(puntos_vehiculo),
                'distancia': distancia,
                'tiempo': tiempo,
                'costo': costo,
                'capacidad_utilizada': random.uniform(60, 95)
            })
            
            total_distance += distancia
            total_time += tiempo
            total_cost += costo
    
    # Calcular ahorros (simulados)
    ahorro_distancia = random.uniform(15, 30)
    ahorro_tiempo = random.uniform(10, 25)
    ahorro_costo = random.uniform(20, 35)
    ahorro_mensual = total_cost * ahorro_costo / 100 * 30
    
    return {
        'rutas': rutas,
        'distancia_total': total_distance,
        'tiempo_total': total_time,
        'costo_total': total_cost,
        'ahorro_distancia': ahorro_distancia,
        'ahorro_tiempo': ahorro_tiempo,
        'ahorro_costo': ahorro_costo,
        'ahorro_mensual': ahorro_mensual
    }

def create_route_map(rutas):
    """Crea un mapa con las rutas optimizadas"""
    
    # Coordenadas de ejemplo (Ciudad de México y alrededores)
    centro_lat, centro_lon = 19.4326, -99.1332
    
    fig = go.Figure()
    
    # Agregar puntos de entrega
    for i, ruta in enumerate(rutas):
        # Generar puntos aleatorios alrededor del centro
        lat = centro_lat + random.uniform(-0.5, 0.5)
        lon = centro_lon + random.uniform(-0.5, 0.5)
        
        fig.add_trace(go.Scatter(
            x=[lon],
            y=[lat],
            mode='markers',
            marker=dict(size=10, color=f'hsl({i*40}, 70%, 50%)'),
            name=f"{ruta['vehiculo']} ({ruta['puntos']} puntos)",
            text=f"Distancia: {ruta['distancia']:.1f} km<br>Tiempo: {ruta['tiempo']:.1f} h<br>Costo: ${ruta['costo']:.2f}",
            hovertemplate="%{text}<extra></extra>"
        ))
    
    fig.update_layout(
        title="Rutas Optimizadas",
        xaxis_title="Longitud",
        yaxis_title="Latitud",
        height=500,
        showlegend=True
    )
    
    return fig

def generate_cost_data():
    """Genera datos de costos para análisis"""
    
    # Costos por categoría
    categorias = ['Combustible', 'Mantenimiento', 'Salarios', 'Peajes', 'Seguros', 'Otros']
    costos_categoria = [random.uniform(10000, 50000) for _ in categorias]
    
    por_categoria = pd.DataFrame({
        'categoria': categorias,
        'costo': costos_categoria
    })
    
    # Tendencias mensuales
    meses = pd.date_range(start='2023-01-01', end='2023-12-31', freq='ME')
    tendencias = pd.DataFrame({
        'mes': meses,
        'costo_total': np.random.uniform(80000, 120000, len(meses))
    })
    
    # Costos por ruta
    rutas = ['Norte', 'Sur', 'Este', 'Oeste', 'Centro']
    por_ruta = pd.DataFrame({
        'ruta': rutas,
        'costo_promedio': np.random.uniform(200, 800, len(rutas))
    })
    
    return {
        'por_categoria': por_categoria,
        'tendencias': tendencias,
        'por_ruta': por_ruta
    }

def generate_delivery_points(num_points):
    """Genera puntos de entrega aleatorios"""
    return [{'id': i, 'lat': 19.4326 + random.uniform(-0.5, 0.5), 
             'lon': -99.1332 + random.uniform(-0.5, 0.5)} for i in range(num_points)]

def simulate_inventory(stock_actual, demanda_promedio, tiempo_entrega, eoq):
    """Simula el comportamiento del inventario"""
    
    dias = 30
    stock = [stock_actual]
    pedidos = []
    
    for dia in range(1, dias + 1):
        # Demanda del día
        demanda_dia = np.random.poisson(demanda_promedio)
        
        # Verificar si llega un pedido
        if dia in pedidos:
            stock_actual += eoq
        
        # Reducir stock por demanda
        stock_actual = max(0, stock_actual - demanda_dia)
        
        # Verificar si hacer un nuevo pedido
        if stock_actual < demanda_promedio * tiempo_entrega and dia not in pedidos:
            pedidos.append(dia + tiempo_entrega)
        
        stock.append(stock_actual)
    
    return pd.DataFrame({
        'dia': range(dias + 1),
        'stock': stock
    })

def generate_demand_prediction(horizonte, confianza, estacionalidad, tendencia):
    """Genera predicción de demanda"""
    
    # Datos históricos (últimos 6 meses)
    fechas_historicas = pd.date_range(start='2023-07-01', end='2023-12-31', freq='D')
    demanda_historica = np.random.poisson(50, len(fechas_historicas))
    
    # Predicción (próximo mes)
    fechas_prediccion = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    demanda_prediccion = np.random.poisson(55, len(fechas_prediccion))  # Ligeramente mayor
    
    # Calcular intervalos de confianza
    z_score = {80: 1.28, 90: 1.64, 95: 1.96, 99: 2.58}[confianza]
    std_dev = np.std(demanda_historica)
    intervalo = z_score * std_dev
    
    limite_superior = demanda_prediccion + intervalo
    limite_inferior = np.maximum(0, demanda_prediccion - intervalo)
    
    # Calcular probabilidad de stockout
    prob_stockout = max(0, (1 - confianza/100) * 100)
    
    return {
        'fechas_historicas': fechas_historicas,
        'demanda_historica': demanda_historica,
        'fechas_prediccion': fechas_prediccion,
        'demanda_prediccion': demanda_prediccion,
        'limite_superior': limite_superior,
        'limite_inferior': limite_inferior,
        'demanda_esperada': np.mean(demanda_prediccion),
        'intervalo': intervalo,
        'prob_stockout': prob_stockout
    }
