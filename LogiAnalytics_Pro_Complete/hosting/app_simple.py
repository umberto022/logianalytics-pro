import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import hashlib
import secrets
import re
import io
import json
import xml.etree.ElementTree as ET
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="LogiAnalytics Pro - Simple",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .menu-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 2rem auto;
        max-width: 600px;
        text-align: center;
    }
    .menu-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 1rem 2rem;
        border: none;
        border-radius: 10px;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        width: 100%;
    }
    .menu-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    .login-form {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 2rem auto;
        max-width: 400px;
    }
    .register-form {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 2rem auto;
        max-width: 500px;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin: 0.5rem;
        border-left: 5px solid #667eea;
    }
    .success-message {
        background: #2ed573;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    .error-message {
        background: #ff6b6b;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    .demo-credentials {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2ed573;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Clase de base de datos
class Database:
    def __init__(self, db_path="logi_analytics_simple.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                subscription_plan TEXT DEFAULT 'basic',
                company_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabla de sesiones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Crear usuario admin por defecto
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            password_hash, salt = self.hash_password('admin123')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, full_name, role, subscription_plan, company_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin@logianalytics.com', password_hash, salt, 'Administrador', 'admin', 'enterprise', 'LogiAnalytics Pro'))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt
    
    def verify_password(self, password, password_hash, salt):
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    
    def create_user(self, username, email, password, full_name, role='user', subscription_plan='basic', company_name=''):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash, salt = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, full_name, role, subscription_plan, company_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, full_name, role, subscription_plan, company_name))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def authenticate_user(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, salt, full_name, role, subscription_plan, company_name
            FROM users WHERE username = ? AND is_active = 1
        ''', (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and self.verify_password(password, user[3], user[4]):
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[5],
                'role': user[6],
                'subscription_plan': user[7],
                'company_name': user[8]
            }
        return None
    
    def create_session(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        cursor.execute('''
            INSERT INTO sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, session_token, expires_at))
        
        conn.commit()
        conn.close()
        return session_token

# Funciones de validación
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    return len(password) >= 6

def validate_username(username):
    return len(username) >= 3 and username.isalnum()

# Inicializar base de datos
@st.cache_resource
def init_database():
    return Database()

# Función principal
def main():
    # Inicializar base de datos
    db = init_database()
    
    # Inicializar variables de sesión
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'menu'
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🚚 LogiAnalytics Pro</h1>
        <p>Plataforma de Análisis Logístico Inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenido principal
    if st.session_state.user:
        show_main_app()
    else:
        if st.session_state.current_page == 'menu':
            show_main_menu()
        elif st.session_state.current_page == 'login':
            show_login_page(db)
        elif st.session_state.current_page == 'register':
            show_register_page(db)
        elif st.session_state.current_page == 'demo':
            show_demo_page()
        elif st.session_state.current_page == 'dashboard':
            show_demo_dashboard()
        elif st.session_state.current_page == 'optimization':
            show_demo_optimization()
        elif st.session_state.current_page == 'reports':
            show_demo_reports()
        elif st.session_state.current_page == 'settings':
            show_demo_settings()
        elif st.session_state.current_page == 'about':
            show_about_page()

def show_main_menu():
    st.markdown("""
    <div class="menu-container">
        <h2>🎯 Bienvenido a LogiAnalytics Pro</h2>
        <p>Selecciona una opción para continuar</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Menú desplegable principal
    st.markdown("### 🎛️ Menú Principal")
    
    # Crear menú desplegable con selectbox
    menu_options = {
        "🔐 Iniciar Sesión": "login",
        "📝 Crear Cuenta": "register", 
        "🎮 Ver Demo": "demo",
        "📊 Ver Dashboard": "dashboard",
        "🚛 Optimización": "optimization",
        "📋 Reportes": "reports",
        "⚙️ Configuración": "settings",
        "ℹ️ Acerca de": "about"
    }
    
    selected_option = st.selectbox(
        "Selecciona una opción:",
        options=list(menu_options.keys()),
        index=0,
        help="Elige la opción que deseas utilizar"
    )
    
    # Botón para ejecutar la opción seleccionada
    if st.button("🚀 Continuar", use_container_width=True):
        st.session_state.current_page = menu_options[selected_option]
        st.rerun()
    
    st.markdown("---")
    
    # Botones rápidos adicionales
    st.markdown("### ⚡ Acceso Rápido")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔐 Login", key="quick_login", use_container_width=True):
            st.session_state.current_page = 'login'
            st.rerun()
    
    with col2:
        if st.button("📝 Registro", key="quick_register", use_container_width=True):
            st.session_state.current_page = 'register'
            st.rerun()
    
    with col3:
        if st.button("🎮 Demo", key="quick_demo", use_container_width=True):
            st.session_state.current_page = 'demo'
            st.rerun()
    
    # Credenciales de demo
    st.markdown("""
    <div class="demo-credentials">
        <h4>🎯 Credenciales de Demo</h4>
        <p><strong>Usuario:</strong> admin</p>
        <p><strong>Contraseña:</strong> admin123</p>
        <p><em>O crea una cuenta nueva para una experiencia personalizada</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Características principales
    st.markdown("### 🚀 Características Principales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📊 Dashboard Inteligente**
        - KPIs en tiempo real
        - Métricas de rendimiento
        - Análisis predictivo
        - Gráficos interactivos
        """)
    
    with col2:
        st.markdown("""
        **🚛 Optimización Avanzada**
        - Algoritmos de rutas
        - Reducción de costos
        - Gestión de inventario
        - Predicción de demanda
        """)
    
    with col3:
        st.markdown("""
        **📋 Reportes Automáticos**
        - Generación automática
        - Múltiples formatos
        - Insights accionables
        - Exportación fácil
        """)

def show_login_page(db):
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-form">
            <h2 style="text-align: center; color: #667eea; margin-bottom: 2rem;">🔐 Iniciar Sesión</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)
            with col2:
                back = st.form_submit_button("🔙 Menú Principal", use_container_width=True)
            
            if submit:
                if username and password:
                    user = db.authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.session_token = db.create_session(user['id'])
                        st.success("✅ ¡Login exitoso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
                else:
                    st.error("❌ Por favor completa todos los campos")
            
            if back:
                st.session_state.current_page = 'menu'
                st.rerun()
        
        # Credenciales de demo
        st.markdown("""
        <div class="demo-credentials">
            <h4>🎯 Credenciales de Demo</h4>
            <p><strong>Usuario:</strong> admin</p>
            <p><strong>Contraseña:</strong> admin123</p>
        </div>
        """, unsafe_allow_html=True)

def show_register_page(db):
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="register-form">
            <h2 style="text-align: center; color: #667eea; margin-bottom: 2rem;">📝 Crear Nueva Cuenta</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("👤 Usuario", placeholder="Mínimo 3 caracteres")
                email = st.text_input("📧 Email", placeholder="tu@email.com")
                password = st.text_input("🔑 Contraseña", type="password", placeholder="Mínimo 6 caracteres")
            
            with col2:
                full_name = st.text_input("👨‍💼 Nombre Completo", placeholder="Tu nombre completo")
                company_name = st.text_input("🏢 Empresa", placeholder="Nombre de tu empresa")
                confirm_password = st.text_input("🔑 Confirmar Contraseña", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("🚀 Crear Cuenta", use_container_width=True)
            with col2:
                back = st.form_submit_button("🔙 Menú Principal", use_container_width=True)
            
            if submit:
                # Validaciones
                if not validate_username(username):
                    st.error("❌ El usuario debe tener al menos 3 caracteres y ser alfanumérico")
                elif not validate_email(email):
                    st.error("❌ Email inválido")
                elif not validate_password(password):
                    st.error("❌ La contraseña debe tener al menos 6 caracteres")
                elif password != confirm_password:
                    st.error("❌ Las contraseñas no coinciden")
                elif not full_name:
                    st.error("❌ El nombre completo es requerido")
                else:
                    success = db.create_user(username, email, password, full_name, 'user', 'basic', company_name)
                    if success:
                        st.success("✅ ¡Cuenta creada exitosamente!")
                        st.info("🎉 Ahora puedes iniciar sesión con tus credenciales")
                        st.session_state.current_page = 'login'
                        st.rerun()
                    else:
                        st.error("❌ El usuario o email ya existe")
            
            if back:
                st.session_state.current_page = 'menu'
                st.rerun()

def show_main_app():
    # Sidebar con información del usuario
    with st.sidebar:
        st.markdown(f"""
        <div style="background: #667eea; color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h3>👤 {st.session_state.user['full_name']}</h3>
            <p>📊 Plan: {st.session_state.user['subscription_plan'].title()}</p>
            <p>🏢 {st.session_state.user['company_name']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.user = None
            st.session_state.session_token = None
            st.session_state.current_page = 'menu'
            st.rerun()
    
    # Navegación principal con pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🚛 Optimización", "📋 Reportes", "⚙️ Configuración"])
    
    if tab1:
        show_dashboard()
    elif tab2:
        show_optimization()
    elif tab3:
        show_reports()
    elif tab4:
        show_settings()

def show_dashboard():
    st.markdown("## 📊 Dashboard Principal")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📦 Envíos Hoy</h3>
            <h2 style="color: #667eea;">1,247</h2>
            <p style="color: #2ed573;">+12% vs ayer</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>💰 Costo Promedio</h3>
            <h2 style="color: #667eea;">$45.20</h2>
            <p style="color: #2ed573;">-8% vs ayer</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>⏱️ Tiempo Promedio</h3>
            <h2 style="color: #667eea;">2.3 días</h2>
            <p style="color: #2ed573;">-15% vs ayer</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>😊 Satisfacción</h3>
            <h2 style="color: #667eea;">94.2%</h2>
            <p style="color: #2ed573;">+3% vs ayer</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de tendencias
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        shipments = np.random.poisson(50, len(dates))
        
        fig = px.line(x=dates, y=shipments, 
                     title='📈 Tendencias de Envíos',
                     color_discrete_sequence=['#667eea'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de costos por ruta
        routes = ['Norte', 'Sur', 'Este', 'Oeste', 'Centro']
        costs = [42.5, 38.2, 45.8, 41.3, 39.7]
        
        fig = px.bar(x=routes, y=costs, 
                    title='💰 Costos por Ruta',
                    color=costs,
                    color_continuous_scale='Blues')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def show_optimization():
    st.markdown("## 🚛 Optimización de Rutas")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Optimización", "💰 Costos", "📦 Inventario", "🎯 Predicción"])
    
    with tab1:
        st.markdown("### 📍 Configuración de Optimización")
        
        col1, col2 = st.columns(2)
        
        with col1:
            num_vehicles = st.number_input("Número de Vehículos", min_value=1, max_value=10, value=3)
            max_capacity = st.number_input("Capacidad Máxima (kg)", min_value=100, max_value=5000, value=2000)
        
        with col2:
            max_time = st.number_input("Tiempo Máximo (horas)", min_value=1, max_value=24, value=12)
            optimization_criteria = st.selectbox("Criterio de Optimización", 
                                               ["Minimizar Distancia", "Minimizar Tiempo", "Minimizar Costo"])
        
        if st.button("🚀 Optimizar Rutas", type="primary"):
            st.success("✅ Rutas optimizadas exitosamente!")
            
            # Mostrar resultados
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Distancia Total", "450.2 km")
            with col2:
                st.metric("Tiempo Total", "8.5 horas")
            with col3:
                st.metric("Costo Total", "$1,250.50")
            
            st.info("💡 Ahorro estimado: 25% distancia, 20% tiempo, 30% costo")

def show_reports():
    st.markdown("## 📋 Reportes y Análisis")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Ejecutivos", "📈 Detallado", "🔔 Alertas", "📤 Exportar"])
    
    with tab1:
        st.markdown("### 📊 Reportes Ejecutivos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            period = st.selectbox("Período", ["Último mes", "Últimos 3 meses", "Último año"])
            report_type = st.selectbox("Tipo de Reporte", ["Resumen", "Detallado", "Comparativo"])
        
        with col2:
            format_type = st.selectbox("Formato", ["PDF", "Excel", "CSV"])
            if st.button("🔄 Generar Reporte"):
                st.success("✅ Reporte generado exitosamente!")
        
        # Resumen ejecutivo
        st.markdown("### 📈 Resumen Ejecutivo")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Envíos", "15,420", "+18.5%")
        with col2:
            st.metric("Ingresos", "$695,250", "+22.3%")
        with col3:
            st.metric("Costo Total", "$485,675", "+15.2%")
        with col4:
            st.metric("Margen", "30.1%", "+5.2%")

def show_settings():
    st.markdown("## ⚙️ Configuración del Sistema")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 Empresa", "👥 Usuarios", "🔧 Técnica", "💳 Facturación"])
    
    with tab1:
        st.markdown("### 🏢 Información de la Empresa")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Nombre de la Empresa", value=st.session_state.user['company_name'])
            rfc = st.text_input("RFC", value="ABC123456789")
            address = st.text_area("Dirección", value="Av. Principal 123, Ciudad, Estado")
        
        with col2:
            phone = st.text_input("Teléfono", value="+52 55 1234 5678")
            email = st.text_input("Email", value=st.session_state.user['email'])
            website = st.text_input("Sitio Web", value="www.miempresa.com")
        
        if st.button("💾 Guardar Configuración"):
            st.success("✅ Configuración guardada exitosamente!")

def show_demo_page():
    st.markdown("## 🎮 Demo de LogiAnalytics Pro")
    
    st.info("🎯 Esta es una demostración de las funcionalidades principales de LogiAnalytics Pro")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 Características Principales
        
        **📊 Dashboard Inteligente**
        - KPIs en tiempo real
        - Métricas de rendimiento
        - Análisis predictivo
        - Gráficos interactivos
        
        **🚛 Optimización Avanzada**
        - Algoritmos de rutas
        - Reducción de costos
        - Gestión de inventario
        - Predicción de demanda
        """)
    
    with col2:
        st.markdown("""
        ### 💰 Planes de Suscripción
        
        **🥉 Básico - $29/mes**
        - Hasta 100 envíos/mes
        - Reportes básicos
        - Soporte por email
        
        **🥈 Pro - $99/mes**
        - Hasta 1,000 envíos/mes
        - Optimización avanzada
        - Soporte prioritario
        
        **🥇 Enterprise - $299/mes**
        - Envíos ilimitados
        - Personalización completa
        - Soporte 24/7
        """)
    
    if st.button("🔙 Volver al Menú Principal"):
        st.session_state.current_page = 'menu'
        st.rerun()

def show_demo_dashboard():
    st.markdown("## 📊 Demo - Dashboard Principal")
    
    st.warning("⚠️ Esta es una vista previa del dashboard. Inicia sesión para acceder a la funcionalidad completa.")
    
    # Métricas de demo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Envíos Hoy", "1,247", "+12%")
    with col2:
        st.metric("💰 Costo Promedio", "$45.20", "-8%")
    with col3:
        st.metric("⏱️ Tiempo Promedio", "2.3 días", "-15%")
    with col4:
        st.metric("😊 Satisfacción", "94.2%", "+3%")
    
    # Gráfico de demo
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    shipments = np.random.poisson(50, len(dates))
    
    fig = px.line(x=dates, y=shipments, 
                 title='📈 Tendencias de Envíos - Demo',
                 color_discrete_sequence=['#667eea'])
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    if st.button("🔙 Volver al Menú Principal"):
        st.session_state.current_page = 'menu'
        st.rerun()

def show_demo_optimization():
    st.markdown("## 🚛 Demo - Optimización de Rutas")
    
    # Pestañas para diferentes secciones
    tab1, tab2, tab3 = st.tabs(["📍 Configuración", "📊 Análisis de Costos", "📦 Gestión de Inventario"])
    
    with tab1:
        st.warning("⚠️ Esta es una vista previa de la optimización. Inicia sesión para acceder a la funcionalidad completa.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📍 Configuración de Optimización")
            num_vehicles = st.number_input("Número de Vehículos", min_value=1, max_value=10, value=3, disabled=True)
            max_capacity = st.number_input("Capacidad Máxima (kg)", min_value=100, max_value=5000, value=2000, disabled=True)
        
        with col2:
            st.markdown("### ⚙️ Parámetros")
            max_time = st.number_input("Tiempo Máximo (horas)", min_value=1, max_value=24, value=12, disabled=True)
            optimization_criteria = st.selectbox("Criterio de Optimización", 
                                               ["Minimizar Distancia", "Minimizar Tiempo", "Minimizar Costo"], disabled=True)
    
    with tab2:
        st.markdown("### 📊 Análisis de Costos")
        st.info("💡 Funcionalidad de importación de datos disponible en modo demo")
        show_cost_analysis_menu()
    
    with tab3:
        st.markdown("### 📦 Gestión de Inventario")
        st.info("💡 Funcionalidad de importación de datos disponible en modo demo")
        show_inventory_management_menu()
    
    if st.button("🔙 Volver al Menú Principal"):
        st.session_state.current_page = 'menu'
        st.rerun()

def show_demo_reports():
    st.markdown("## 📋 Demo - Reportes y Análisis")
    
    st.warning("⚠️ Esta es una vista previa de los reportes. Inicia sesión para acceder a la funcionalidad completa.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Tipos de Reportes")
        st.markdown("""
        - **Reportes Ejecutivos**: Resúmenes de alto nivel
        - **Análisis Detallado**: Métricas específicas
        - **Alertas del Sistema**: Notificaciones importantes
        - **Exportación de Datos**: Múltiples formatos
        """)
    
    with col2:
        st.markdown("### 📈 Métricas Disponibles")
        st.markdown("""
        - **Envíos**: Cantidad y tendencias
        - **Costos**: Análisis por ruta
        - **Tiempo**: Eficiencia de entrega
        - **Satisfacción**: Feedback de clientes
        """)
    
    st.info("💡 Inicia sesión para generar reportes personalizados")
    
    if st.button("🔙 Volver al Menú Principal"):
        st.session_state.current_page = 'menu'
        st.rerun()

def show_demo_settings():
    st.markdown("## ⚙️ Demo - Configuración del Sistema")
    
    st.warning("⚠️ Esta es una vista previa de la configuración. Inicia sesión para acceder a la funcionalidad completa.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 Empresa", "👥 Usuarios", "🔧 Técnica", "💳 Facturación"])
    
    with tab1:
        st.markdown("### 🏢 Información de la Empresa")
        st.text_input("Nombre de la Empresa", value="Mi Empresa Logística", disabled=True)
        st.text_input("RFC", value="ABC123456789", disabled=True)
        st.text_area("Dirección", value="Av. Principal 123, Ciudad, Estado", disabled=True)
    
    with tab2:
        st.markdown("### 👥 Gestión de Usuarios")
        st.info("Funcionalidad disponible para administradores")
    
    with tab3:
        st.markdown("### 🔧 Configuración Técnica")
        st.text_input("Host de Base de Datos", value="localhost", disabled=True)
        st.number_input("Puerto", value=5432, disabled=True)
    
    with tab4:
        st.markdown("### 💳 Facturación")
        st.info("Información de facturación disponible para usuarios registrados")
    
    if st.button("🔙 Volver al Menú Principal"):
        st.session_state.current_page = 'menu'
        st.rerun()

def show_cost_analysis_menu():
    st.markdown("### 💰 Análisis de Costos Logísticos")
    
    # Opciones de importación
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📁 Importar Datos de Costos")
        
        # Selector de tipo de archivo
        file_type = st.selectbox(
            "Tipo de archivo:",
            ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)", "XML (.xml)"],
            key="cost_file_type"
        )
        
        # Uploader de archivo
        uploaded_file = st.file_uploader(
            "Selecciona tu archivo de costos:",
            type=['xlsx', 'csv', 'json', 'xml'],
            key="cost_file_uploader",
            help="Formatos soportados: Excel, CSV, JSON, XML"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ Archivo cargado: {uploaded_file.name}")
            
            # Mostrar preview del archivo
            if st.button("👁️ Ver Vista Previa", key="cost_preview"):
                show_file_preview(uploaded_file, "costos")
    
    with col2:
        st.markdown("#### ⚙️ Configuración de Importación")
        
        # Opciones de configuración
        st.markdown("**📋 Opciones de mapeo:**")
        cost_columns = st.multiselect(
            "Columnas de costos:",
            ["Costo de Combustible", "Costo de Mano de Obra", "Costo de Mantenimiento", 
             "Costo de Peaje", "Costo de Seguro", "Otros Costos"],
            default=["Costo de Combustible", "Costo de Mano de Obra"],
            key="cost_columns"
        )
        
        date_column = st.selectbox(
            "Columna de fecha:",
            ["Fecha", "Date", "Timestamp", "Período"],
            key="cost_date_column"
        )
        
        # Botón de procesamiento
        if st.button("🔄 Procesar Datos", key="process_cost_data"):
            if uploaded_file is not None:
                st.success("✅ Datos procesados exitosamente!")
                st.info("📊 Los datos se han cargado y están listos para análisis")
            else:
                st.warning("⚠️ Por favor, selecciona un archivo primero")
    
    # Sección de datos de ejemplo
    st.markdown("---")
    st.markdown("#### 📊 Datos de Ejemplo - Costos")
    
    # Crear datos de ejemplo
    if 'cost_data' not in st.session_state:
        st.session_state.cost_data = pd.DataFrame({
            'Fecha': pd.date_range('2024-01-01', periods=30, freq='D'),
            'Costo_Combustible': np.random.normal(500, 50, 30),
            'Costo_Mano_Obra': np.random.normal(800, 100, 30),
            'Costo_Mantenimiento': np.random.normal(200, 30, 30),
            'Costo_Peaje': np.random.normal(150, 20, 30),
            'Costo_Seguro': np.random.normal(100, 10, 30)
        })
    
    # Mostrar tabla de datos
    st.dataframe(st.session_state.cost_data.head(10))
    
    # Métricas de análisis
    st.markdown("#### 📈 Métricas de Costos")
    col1, col2, col3 = st.columns(3)
    
    total_cost = st.session_state.cost_data['Costo_Combustible'].sum() + \
                 st.session_state.cost_data['Costo_Mano_Obra'].sum() + \
                 st.session_state.cost_data['Costo_Mantenimiento'].sum()
    
    with col1:
        st.metric("💰 Costo Total", f"${total_cost:,.0f}", "+5.2%")
    with col2:
        st.metric("⛽ Combustible", f"${st.session_state.cost_data['Costo_Combustible'].sum():,.0f}", "+8.1%")
    with col3:
        st.metric("🔧 Mantenimiento", f"${st.session_state.cost_data['Costo_Mantenimiento'].sum():,.0f}", "-2.3%")
    
    # Gráfico de costos
    cost_summary = {
        'Categoría': ['Combustible', 'Mano de Obra', 'Mantenimiento', 'Peaje', 'Seguro'],
        'Costo': [
            st.session_state.cost_data['Costo_Combustible'].sum(),
            st.session_state.cost_data['Costo_Mano_Obra'].sum(),
            st.session_state.cost_data['Costo_Mantenimiento'].sum(),
            st.session_state.cost_data['Costo_Peaje'].sum(),
            st.session_state.cost_data['Costo_Seguro'].sum()
        ]
    }
    
    fig = px.pie(values=cost_summary['Costo'], names=cost_summary['Categoría'], 
                 title="📊 Distribución de Costos")
    st.plotly_chart(fig, use_container_width=True)

def show_inventory_management_menu():
    st.markdown("### 📦 Gestión de Inventario")
    
    # Opciones de importación
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📁 Importar Datos de Inventario")
        
        # Selector de tipo de archivo
        file_type = st.selectbox(
            "Tipo de archivo:",
            ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)", "XML (.xml)"],
            key="inventory_file_type"
        )
        
        # Uploader de archivo
        uploaded_file = st.file_uploader(
            "Selecciona tu archivo de inventario:",
            type=['xlsx', 'csv', 'json', 'xml'],
            key="inventory_file_uploader",
            help="Formatos soportados: Excel, CSV, JSON, XML"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ Archivo cargado: {uploaded_file.name}")
            
            # Mostrar preview del archivo
            if st.button("👁️ Ver Vista Previa", key="inventory_preview"):
                show_file_preview(uploaded_file, "inventario")
    
    with col2:
        st.markdown("#### ⚙️ Configuración de Importación")
        
        # Opciones de configuración
        st.markdown("**📋 Opciones de mapeo:**")
        inventory_columns = st.multiselect(
            "Columnas de inventario:",
            ["SKU", "Producto", "Cantidad", "Precio Unitario", "Ubicación", 
             "Fecha de Entrada", "Fecha de Vencimiento", "Proveedor"],
            default=["SKU", "Producto", "Cantidad", "Precio Unitario"],
            key="inventory_columns"
        )
        
        warehouse_location = st.selectbox(
            "Ubicación del almacén:",
            ["Almacén Central", "Almacén Norte", "Almacén Sur", "Almacén Este", "Almacén Oeste"],
            key="warehouse_location"
        )
        
        # Botón de procesamiento
        if st.button("🔄 Procesar Datos", key="process_inventory_data"):
            if uploaded_file is not None:
                st.success("✅ Datos procesados exitosamente!")
                st.info("📊 Los datos se han cargado y están listos para análisis")
            else:
                st.warning("⚠️ Por favor, selecciona un archivo primero")
    
    # Sección de datos de ejemplo
    st.markdown("---")
    st.markdown("#### 📊 Datos de Ejemplo - Inventario")
    
    # Crear datos de ejemplo
    if 'inventory_data' not in st.session_state:
        st.session_state.inventory_data = pd.DataFrame({
            'SKU': [f'SKU_{i:04d}' for i in range(1, 51)],
            'Producto': [f'Producto_{i}' for i in range(1, 51)],
            'Cantidad': np.random.randint(10, 500, 50),
            'Precio_Unitario': np.random.normal(50, 15, 50),
            'Ubicacion': [f'Estante_{i%10+1}' for i in range(50)],
            'Categoria': [f'Categoría_{i%8+1}' for i in range(50)]
        })
    
    # Mostrar tabla de datos
    st.dataframe(st.session_state.inventory_data.head(10))
    
    # Métricas de análisis
    st.markdown("#### 📈 Métricas de Inventario")
    col1, col2, col3, col4 = st.columns(4)
    
    total_products = len(st.session_state.inventory_data)
    total_value = (st.session_state.inventory_data['Cantidad'] * st.session_state.inventory_data['Precio_Unitario']).sum()
    low_stock = len(st.session_state.inventory_data[st.session_state.inventory_data['Cantidad'] < 50])
    
    with col1:
        st.metric("📦 Total Productos", f"{total_products:,}", "+12%")
    with col2:
        st.metric("💰 Valor Total", f"${total_value:,.0f}", "+8.5%")
    with col3:
        st.metric("⚠️ Stock Bajo", f"{low_stock}", "-15%")
    with col4:
        st.metric("📈 Rotación", "4.2x", "+0.3x")
    
    # Gráfico de inventario por categoría
    category_counts = st.session_state.inventory_data['Categoria'].value_counts()
    
    fig = px.bar(x=category_counts.index, y=category_counts.values,
                 title="📊 Inventario por Categoría",
                 color=category_counts.values,
                 color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de distribución de precios
    fig2 = px.histogram(st.session_state.inventory_data, x='Precio_Unitario',
                       title="📊 Distribución de Precios Unitarios",
                       nbins=20)
    st.plotly_chart(fig2, use_container_width=True)

def show_file_preview(uploaded_file, file_type):
    """Muestra una vista previa del archivo cargado"""
    st.markdown(f"#### 👁️ Vista Previa - {file_type.title()}")
    
    try:
        if uploaded_file.name.endswith('.xlsx'):
            try:
                df = pd.read_excel(uploaded_file)
            except Exception as e:
                st.warning("⚠️ Para leer archivos Excel, instala: pip install openpyxl")
                st.info("💡 Por ahora, puedes usar archivos CSV que funcionan sin dependencias adicionales")
                return
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.json'):
            df = pd.read_json(uploaded_file)
        else:
            st.warning("⚠️ Formato de archivo no soportado para vista previa")
            return
        
        st.dataframe(df.head(10))
        st.info(f"📊 Archivo contiene {len(df)} filas y {len(df.columns)} columnas")
        
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        st.info("💡 Asegúrate de que el archivo tenga el formato correcto")

def show_about_page():
    st.markdown("## ℹ️ Acerca de LogiAnalytics Pro")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚚 LogiAnalytics Pro
        
        **Versión:** 1.0.0  
        **Desarrollado por:** LogiAnalytics Team  
        **Fecha:** 2024  
        **Licencia:** MIT  
        
        ### 🎯 Misión
        
        Revolucionar la gestión logística mediante análisis de datos inteligentes y optimización automatizada de rutas.
        
        ### 🌟 Características
        
        - Dashboard en tiempo real
        - Optimización de rutas
        - Reportes automáticos
        - Análisis predictivo
        - Gestión de inventario
        - Monitoreo de KPIs
        """)
    
    with col2:
        st.markdown("""
        ### 📞 Contacto
        
        **Email:** soporte@logianalytics.com  
        **Teléfono:** +1 (555) 123-4567  
        **Sitio Web:** www.logianalytics.com  
        
        ### 🛠️ Tecnologías
        
        - **Frontend:** Streamlit
        - **Backend:** Python
        - **Base de Datos:** SQLite
        - **Visualización:** Plotly
        - **Análisis:** Pandas, NumPy
        
        ### 📊 Estadísticas
        
        - **Usuarios Activos:** 1,250+
        - **Envíos Optimizados:** 50,000+
        - **Ahorro Promedio:** 25%
        - **Uptime:** 99.9%
        """)
    
    st.markdown("---")
    
    st.markdown("### 🎉 ¡Gracias por usar LogiAnalytics Pro!")
    
    if st.button("🔙 Volver al Menú Principal"):
        st.session_state.current_page = 'menu'
        st.rerun()

if __name__ == "__main__":
    main()
