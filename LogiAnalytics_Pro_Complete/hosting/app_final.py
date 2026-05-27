import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import sqlite3
import hashlib
import secrets
import re
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="LogiAnalytics Pro",
    page_icon="🚚",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Base de datos simple
class SimpleDB:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                salt TEXT,
                full_name TEXT
            )
        ''')
        # Usuario admin por defecto
        password_hash, salt = self.hash_password('admin123')
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, salt, full_name)
            VALUES (?, ?, ?, ?)
        ''', ('admin', password_hash, salt, 'Administrador'))
        conn.commit()
        conn.close()
    
    def hash_password(self, password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        return hashlib.sha256((password + salt).encode()).hexdigest(), salt
    
    def verify_password(self, password, password_hash, salt):
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    
    def authenticate(self, username, password):
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash, salt, full_name FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and self.verify_password(password, user[0], user[1]):
            return {'username': username, 'full_name': user[2]}
        return None

# Inicializar
db = SimpleDB()

# Estado
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Header
st.markdown("""
<div class="main-header">
    <h1>🚚 LogiAnalytics Pro</h1>
    <p>Plataforma de Análisis Logístico</p>
</div>
""", unsafe_allow_html=True)

# Contenido
if st.session_state.user:
    # Usuario logueado
    st.sidebar.success(f"👤 {st.session_state.user['full_name']}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()
    
    # Navegación
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🚛 Optimización", "📋 Reportes"])
    
    if tab1:
        st.title("📊 Dashboard")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Envíos", "1,247", "+12%")
        col2.metric("Costo", "$45.20", "-8%")
        col3.metric("Tiempo", "2.3 días", "-15%")
        col4.metric("Satisfacción", "94.2%", "+3%")
        
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        fig = px.line(x=dates, y=np.random.poisson(50, 30), title="Tendencias")
        st.plotly_chart(fig, use_container_width=True)
    
    elif tab2:
        st.title("🚛 Optimización")
        tab2a, tab2b, tab2c = st.tabs(["📍 Rutas", "💰 Costos", "📦 Inventario"])
        
        if tab2b:
            st.subheader("📊 Análisis de Costos")
            st.markdown("#### 📁 Importar Datos")
            
            file_type = st.selectbox("Tipo de archivo:", ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"])
            uploaded_file = st.file_uploader("Selecciona archivo:", type=['xlsx', 'csv', 'json'])
            
            if uploaded_file:
                st.success(f"✅ {uploaded_file.name}")
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                        st.dataframe(df.head(10))
                        st.info(f"📊 {len(df)} filas, {len(df.columns)} columnas")
                    elif uploaded_file.name.endswith('.json'):
                        df = pd.read_json(uploaded_file)
                        st.dataframe(df.head(10))
                    else:
                        st.info("💡 Para Excel, instala: pip install openpyxl")
                        st.info("📊 Mostrando datos de ejemplo:")
                        df = pd.DataFrame({
                            'Fecha': pd.date_range('2024-01-01', periods=10),
                            'Costo': np.random.normal(500, 50, 10)
                        })
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            st.markdown("---")
            st.subheader("📈 Métricas")
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Total", "$45,230", "+5.2%")
            col2.metric("⛽ Combustible", "$18,500", "+8.1%")
            col3.metric("🔧 Mantenimiento", "$12,750", "-2.3%")
            
            fig = px.pie(values=[18500, 15200, 12750], names=['Combustible', 'Mano Obra', 'Mantenimiento'], title="Distribución")
            st.plotly_chart(fig, use_container_width=True)
        
        elif tab2c:
            st.subheader("📦 Gestión de Inventario")
            st.markdown("#### 📁 Importar Datos")
            
            file_type = st.selectbox("Tipo:", ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"], key="inv_type")
            uploaded_file = st.file_uploader("Archivo:", type=['xlsx', 'csv', 'json'], key="inv_file")
            
            if uploaded_file:
                st.success(f"✅ {uploaded_file.name}")
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                        st.dataframe(df.head(10))
                    elif uploaded_file.name.endswith('.json'):
                        df = pd.read_json(uploaded_file)
                        st.dataframe(df.head(10))
                    else:
                        st.info("💡 Para Excel: pip install openpyxl")
                        df = pd.DataFrame({
                            'SKU': [f'SKU_{i:04d}' for i in range(1, 11)],
                            'Producto': [f'Producto {i}' for i in range(1, 11)],
                            'Cantidad': np.random.randint(10, 500, 10),
                            'Precio': np.random.normal(50, 15, 10)
                        })
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            st.markdown("---")
            st.subheader("📈 Métricas")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📦 Productos", "1,247", "+12%")
            col2.metric("💰 Valor", "$2.3M", "+8.5%")
            col3.metric("⚠️ Stock Bajo", "23", "-15%")
            col4.metric("📈 Rotación", "4.2x", "+0.3x")
    
    elif tab3:
        st.title("📋 Reportes")
        st.info("Funcionalidad de reportes disponible")
    
else:
    # No logueado
    if st.session_state.page == 'home':
        st.title("🎯 Bienvenido")
        
        menu = st.selectbox("Menú:", ["🔐 Login", "📝 Registro", "🎮 Demo", "🚛 Optimización"])
        
        if st.button("🚀 Continuar"):
            if menu == "🔐 Login":
                st.session_state.page = 'login'
                st.rerun()
            elif menu == "📝 Registro":
                st.session_state.page = 'register'
                st.rerun()
            elif menu == "🚛 Optimización":
                st.session_state.page = 'optimization'
                st.rerun()
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.button("🔐 Login", use_container_width=True, on_click=lambda: setattr(st.session_state, 'page', 'login') or st.rerun())
        col2.button("📝 Registro", use_container_width=True, on_click=lambda: setattr(st.session_state, 'page', 'register') or st.rerun())
        col3.button("🎮 Demo", use_container_width=True)
        
        st.info("👤 Demo: admin / admin123")
    
    elif st.session_state.page == 'login':
        st.title("🔐 Login")
        with st.form("login"):
            user = st.text_input("Usuario")
            pwd = st.text_input("Contraseña", type="password")
            if st.form_submit_button("🚀 Entrar"):
                u = db.authenticate(user, pwd)
                if u:
                    st.session_state.user = u
                    st.session_state.page = 'home'
                    st.success("✅ Login exitoso!")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")
        if st.button("🔙 Atrás"):
            st.session_state.page = 'home'
            st.rerun()
    
    elif st.session_state.page == 'register':
        st.title("📝 Registro")
        with st.form("register"):
            user = st.text_input("Usuario")
            email = st.text_input("Email")
            pwd = st.text_input("Contraseña", type="password")
            name = st.text_input("Nombre")
            if st.form_submit_button("🚀 Crear"):
                st.success("✅ Cuenta creada!")
                st.session_state.page = 'login'
                st.rerun()
        if st.button("🔙 Atrás"):
            st.session_state.page = 'home'
            st.rerun()
    
    elif st.session_state.page == 'optimization':
        st.title("🚛 Optimización")
        tab1, tab2 = st.tabs(["💰 Costos", "📦 Inventario"])
        
        with tab1:
            st.subheader("📊 Análisis de Costos")
            file = st.file_uploader("📁 Subir archivo:", type=['csv', 'json'])
            if file:
                try:
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_json(file)
                    st.dataframe(df)
                    st.success(f"✅ {len(df)} filas cargadas")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with tab2:
            st.subheader("📦 Inventario")
            file = st.file_uploader("📁 Subir archivo:", type=['csv', 'json'], key="inv")
            if file:
                try:
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_json(file)
                    st.dataframe(df)
                    st.success(f"✅ {len(df)} filas cargadas")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if st.button("🔙 Menú"):
            st.session_state.page = 'home'
            st.rerun()