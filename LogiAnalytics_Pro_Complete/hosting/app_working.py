import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="LogiAnalytics Pro", page_icon="🚚", layout="wide")

st.title("🚚 LogiAnalytics Pro")
st.markdown("### Plataforma de Análisis Logístico")

# Menú
st.sidebar.title("Menú")
page = st.sidebar.selectbox("Selecciona:", ["🏠 Home", "🚛 Optimización", "📊 Dashboard"])

if page == "🏠 Home":
    st.header("🎯 Bienvenido")
    st.info("Selecciona una opción del menú lateral")
    
    col1, col2, col3 = st.columns(3)
    col1.button("🔐 Login")
    col2.button("📝 Registro")
    col3.button("🎮 Demo")

elif page == "🚛 Optimización":
    st.header("🚛 Optimización de Rutas")
    
    tab1, tab2 = st.tabs(["💰 Análisis de Costos", "📦 Gestión de Inventario"])
    
    with tab1:
        st.subheader("📊 Análisis de Costos")
        st.markdown("#### 📁 Importar Datos de Costos")
        
        file_type = st.selectbox("Tipo de archivo:", ["CSV (.csv)", "JSON (.json)"])
        uploaded_file = st.file_uploader("Selecciona tu archivo:", type=['csv', 'json'])
        
        if uploaded_file is not None:
            st.success(f"✅ Archivo cargado: {uploaded_file.name}")
            
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.json'):
                    df = pd.read_json(uploaded_file)
                
                st.dataframe(df.head(10))
                st.info(f"📊 Archivo contiene {len(df)} filas y {len(df.columns)} columnas")
                
                if st.button("🔄 Procesar Datos"):
                    st.success("✅ Datos procesados exitosamente!")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        st.subheader("📈 Métricas de Costos")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Costo Total", "$45,230", "+5.2%")
        col2.metric("⛽ Combustible", "$18,500", "+8.1%")
        col3.metric("🔧 Mantenimiento", "$12,750", "-2.3%")
        
        # Gráfico
        cost_data = pd.DataFrame({
            'Categoría': ['Combustible', 'Mano de Obra', 'Mantenimiento'],
            'Costo': [18500, 15200, 12750]
        })
        fig = px.pie(cost_data, values='Costo', names='Categoría', title="Distribución de Costos")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("📦 Gestión de Inventario")
        st.markdown("#### 📁 Importar Datos de Inventario")
        
        file_type = st.selectbox("Tipo de archivo:", ["CSV (.csv)", "JSON (.json)"], key="inv_type")
        uploaded_file = st.file_uploader("Selecciona tu archivo:", type=['csv', 'json'], key="inv_file")
        
        if uploaded_file is not None:
            st.success(f"✅ Archivo cargado: {uploaded_file.name}")
            
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith('.json'):
                    df = pd.read_json(uploaded_file)
                
                st.dataframe(df.head(10))
                st.info(f"📊 Archivo contiene {len(df)} filas y {len(df.columns)} columnas")
                
                if st.button("🔄 Procesar Datos", key="process_inv"):
                    st.success("✅ Datos procesados exitosamente!")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        st.subheader("📈 Métricas de Inventario")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Total Productos", "1,247", "+12%")
        col2.metric("💰 Valor Total", "$2.3M", "+8.5%")
        col3.metric("⚠️ Stock Bajo", "23", "-15%")
        col4.metric("📈 Rotación", "4.2x", "+0.3x")
        
        # Datos de ejemplo
        inv_data = pd.DataFrame({
            'Categoría': ['Electrónicos', 'Ropa', 'Hogar', 'Deportes'],
            'Cantidad': [450, 320, 280, 150]
        })
        fig = px.bar(inv_data, x='Categoría', y='Cantidad', title="Inventario por Categoría")
        st.plotly_chart(fig, use_container_width=True)

elif page == "📊 Dashboard":
    st.header("📊 Dashboard Principal")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Envíos Hoy", "1,247", "+12%")
    col2.metric("💰 Costo Promedio", "$45.20", "-8%")
    col3.metric("⏱️ Tiempo Promedio", "2.3 días", "-15%")
    col4.metric("😊 Satisfacción", "94.2%", "+3%")
    
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    fig = px.line(x=dates, y=np.random.poisson(50, 30), title="Tendencias de Envíos")
    st.plotly_chart(fig, use_container_width=True)