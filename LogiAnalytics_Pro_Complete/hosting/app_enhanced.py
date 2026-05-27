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
from streamlit_option_menu import option_menu
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="LogiAnalytics Pro - Enhanced",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado mejorado
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
    .info-message {
        background: #3742fa;
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
</style>
""", unsafe_allow_html=True)

# Clase de base de datos
class Database:
    def __init__(self, db_path="logi_analytics_enhanced.db"):
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

def show_main_menu():
    st.markdown("""
    <div class="menu-container">
        <h2>🎯 Bienvenido a LogiAnalytics Pro</h2>
        <p>Selecciona una opción para continuar</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Botón de Login
        if st.button("🔐 Iniciar Sesión", key="login_btn", use_container_width=True):
            st.session_state.current_page = 'login'
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón de Registro
        if st.button("📝 Crear Cuenta", key="register_btn", use_container_width=True):
            st.session_state.current_page = 'register'
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón de Demo
        if st.button("🎮 Ver Demo", key="demo_btn", use_container_width=True):
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
    
    # Navegación principal
    selected = option_menu(
        menu_title=None,
        options=["📊 Dashboard", "🚛 Optimización", "📋 Reportes", "⚙️ Configuración"],
        icons=["speedometer2", "truck", "file-earmark-text", "gear"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "#667eea", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#eee"
            },
            "nav-link-selected": {"background-color": "#667eea"},
        }
    )
    
    if selected == "📊 Dashboard":
        show_dashboard()
    elif selected == "🚛 Optimización":
        show_optimization()
    elif selected == "📋 Reportes":
        show_reports()
    elif selected == "⚙️ Configuración":
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

if __name__ == "__main__":
    main()
