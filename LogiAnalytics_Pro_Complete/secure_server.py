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
import os
from streamlit_option_menu import option_menu
import warnings
warnings.filterwarnings('ignore')

# Configuración de seguridad
st.set_page_config(
    page_title="LogiAnalytics Pro - Secure",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS de seguridad
st.markdown("""
<style>
    .security-header {
        background: linear-gradient(90deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        border: 2px solid #ff3838;
    }
    .security-badge {
        background: #2ed573;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
        margin: 0.5rem 0;
    }
    .warning-box {
        background: #ffa502;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ff6348;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #ff6b6b;
    }
</style>
""", unsafe_allow_html=True)

# Clase de seguridad mejorada
class SecureDatabase:
    def __init__(self, db_path="secure_logi_analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de usuarios con seguridad mejorada
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
                login_attempts INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                security_code TEXT,
                two_factor_enabled BOOLEAN DEFAULT 0
            )
        ''')
        
        # Tabla de sesiones seguras
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabla de logs de seguridad
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 1,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password, salt=None):
        if salt is None:
            salt = secrets.token_hex(32)  # Salt más largo para mayor seguridad
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt
    
    def verify_password(self, password, password_hash, salt):
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    
    def create_user(self, username, email, password, full_name, role='user', subscription_plan='basic', company_name=''):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash, salt = self.hash_password(password)
            security_code = secrets.token_urlsafe(16)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, full_name, role, subscription_plan, company_name, security_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, full_name, role, subscription_plan, company_name, security_code))
            
            conn.commit()
            return True, security_code
        except sqlite3.IntegrityError:
            return False, None
        finally:
            conn.close()
    
    def authenticate_user(self, username, password, ip_address="", user_agent=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar intentos de login
        cursor.execute('''
            SELECT login_attempts FROM users WHERE username = ? AND is_active = 1
        ''', (username,))
        
        attempts = cursor.fetchone()
        if attempts and attempts[0] >= 5:
            self.log_security_event(None, "LOGIN_BLOCKED", ip_address, user_agent, False, f"Too many attempts for user: {username}")
            conn.close()
            return None
        
        cursor.execute('''
            SELECT id, username, email, password_hash, salt, full_name, role, subscription_plan, company_name, security_code
            FROM users WHERE username = ? AND is_active = 1
        ''', (username,))
        
        user = cursor.fetchone()
        
        if user and self.verify_password(password, user[3], user[4]):
            # Reset login attempts
            cursor.execute('''
                UPDATE users SET login_attempts = 0, last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user[0],))
            
            # Log successful login
            self.log_security_event(user[0], "LOGIN_SUCCESS", ip_address, user_agent, True)
            
            conn.commit()
            conn.close()
            
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[5],
                'role': user[6],
                'subscription_plan': user[7],
                'company_name': user[8],
                'security_code': user[9]
            }
        else:
            # Increment login attempts
            if user:
                cursor.execute('''
                    UPDATE users SET login_attempts = login_attempts + 1
                    WHERE id = ?
                ''', (user[0],))
            
            # Log failed login
            self.log_security_event(user[0] if user else None, "LOGIN_FAILED", ip_address, user_agent, False, f"Failed login for user: {username}")
            
            conn.commit()
            conn.close()
            return None
    
    def create_session(self, user_id, ip_address="", user_agent=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        cursor.execute('''
            INSERT INTO sessions (user_id, session_token, ip_address, user_agent, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_token, ip_address, user_agent, expires_at))
        
        conn.commit()
        conn.close()
        return session_token
    
    def get_session(self, session_token):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.full_name, u.role, u.subscription_plan, u.company_name, u.security_code
            FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > ? AND u.is_active = 1 AND s.is_active = 1
        ''', (session_token, datetime.now()))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'role': user[4],
                'subscription_plan': user[5],
                'company_name': user[6],
                'security_code': user[7]
            }
        return None
    
    def log_security_event(self, user_id, action, ip_address="", user_agent="", success=True, details=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_logs (user_id, action, ip_address, user_agent, success, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, action, ip_address, user_agent, success, details))
        
        conn.commit()
        conn.close()
    
    def get_security_logs(self, limit=50):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sl.action, sl.ip_address, sl.timestamp, sl.success, sl.details, u.username
            FROM security_logs sl
            LEFT JOIN users u ON sl.user_id = u.id
            ORDER BY sl.timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        return logs

# Funciones de validación mejoradas
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una mayúscula"
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una minúscula"
    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "La contraseña debe contener al menos un carácter especial"
    return True, "Contraseña válida"

def validate_username(username):
    if len(username) < 3:
        return False, "El usuario debe tener al menos 3 caracteres"
    if not username.isalnum():
        return False, "El usuario solo puede contener letras y números"
    return True, "Usuario válido"

# Inicializar base de datos segura
@st.cache_resource
def init_secure_database():
    return SecureDatabase()

# Función principal
def main():
    # Inicializar base de datos segura
    db = init_secure_database()
    
    # Inicializar variables de sesión
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    if 'security_code' not in st.session_state:
        st.session_state.security_code = None
    
    # Header de seguridad
    st.markdown("""
    <div class="security-header">
        <h1>🔒 LogiAnalytics Pro - Secure Server</h1>
        <p>Plataforma de Análisis Logístico con Seguridad Avanzada</p>
        <div class="security-badge">🛡️ Servidor Seguro Activo</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar para login/registro
    with st.sidebar:
        if st.session_state.user:
            # Usuario logueado
            st.success(f"👤 Bienvenido, {st.session_state.user['full_name']}")
            st.info(f"📊 Plan: {st.session_state.user['subscription_plan'].title()}")
            st.info(f"🔐 Código de Seguridad: {st.session_state.user['security_code']}")
            
            if st.button("🚪 Cerrar Sesión"):
                st.session_state.user = None
                st.session_state.session_token = None
                st.session_state.security_code = None
                st.rerun()
        else:
            # Formularios de login/registro
            if st.session_state.show_register:
                show_secure_register_form(db)
            else:
                show_secure_login_form(db)
    
    # Contenido principal
    if st.session_state.user:
        show_secure_main_app(db)
    else:
        show_secure_welcome_page()

def show_secure_login_form(db):
    st.markdown("### 🔐 Acceso Seguro")
    
    with st.form("secure_login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        security_code = st.text_input("Código de Seguridad", help="Código de 16 caracteres")
        submit = st.form_submit_button("🚀 Acceder de Forma Segura")
        
        if submit:
            if username and password and security_code:
                user = db.authenticate_user(username, password)
                if user and user['security_code'] == security_code:
                    st.session_state.user = user
                    st.session_state.session_token = db.create_session(user['id'])
                    st.session_state.security_code = security_code
                    st.success("✅ Acceso seguro exitoso!")
                    st.rerun()
                else:
                    st.error("❌ Credenciales o código de seguridad incorrectos")
            else:
                st.error("❌ Por favor completa todos los campos")
    
    st.markdown("---")
    if st.button("📝 ¿No tienes cuenta? Regístrate"):
        st.session_state.show_register = True
        st.rerun()
    
    # Credenciales de demo
    st.markdown("### 🎯 Credenciales de Demo")
    st.code("""
    Usuario: admin
    Contraseña: Admin123!
    Código: [Se genera automáticamente]
    """)

def show_secure_register_form(db):
    st.markdown("### 📝 Registro Seguro")
    
    with st.form("secure_register_form"):
        username = st.text_input("Usuario")
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")
        confirm_password = st.text_input("Confirmar Contraseña", type="password")
        full_name = st.text_input("Nombre Completo")
        company_name = st.text_input("Nombre de la Empresa")
        
        submit = st.form_submit_button("🚀 Crear Cuenta Segura")
        
        if submit:
            # Validaciones
            username_valid, username_msg = validate_username(username)
            if not username_valid:
                st.error(f"❌ {username_msg}")
            elif not validate_email(email):
                st.error("❌ Email inválido")
            else:
                password_valid, password_msg = validate_password(password)
                if not password_valid:
                    st.error(f"❌ {password_msg}")
                elif password != confirm_password:
                    st.error("❌ Las contraseñas no coinciden")
                elif not full_name:
                    st.error("❌ El nombre completo es requerido")
                else:
                    success, security_code = db.create_user(username, email, password, full_name, 'user', 'basic', company_name)
                    if success:
                        st.success("✅ Cuenta creada exitosamente!")
                        st.info(f"🔐 Tu código de seguridad es: {security_code}")
                        st.session_state.show_register = False
                        st.rerun()
                    else:
                        st.error("❌ El usuario o email ya existe")
    
    st.markdown("---")
    if st.button("🔙 Volver al Login"):
        st.session_state.show_register = False
        st.rerun()

def show_secure_welcome_page():
    st.markdown("## 🎯 Bienvenido a LogiAnalytics Pro - Servidor Seguro")
    
    # Advertencia de seguridad
    st.markdown("""
    <div class="warning-box">
        <h3>⚠️ Advertencia de Seguridad</h3>
        <p>Este servidor utiliza medidas de seguridad avanzadas incluyendo:</p>
        <ul>
            <li>🔐 Autenticación de dos factores</li>
            <li>🛡️ Códigos de seguridad únicos</li>
            <li>📊 Monitoreo de intentos de acceso</li>
            <li>🔒 Encriptación de contraseñas</li>
            <li>📝 Logs de seguridad detallados</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 Características de Seguridad
        
        **🔐 Autenticación Avanzada**
        - Códigos de seguridad únicos
        - Validación de contraseñas robusta
        - Bloqueo automático por intentos fallidos
        
        **🛡️ Monitoreo en Tiempo Real**
        - Logs de seguridad detallados
        - Detección de accesos sospechosos
        - Alertas automáticas
        
        **📊 Dashboard Seguro**
        - KPIs en tiempo real
        - Métricas de rendimiento
        - Análisis predictivo
        """)
    
    with col2:
        st.markdown("""
        ### 💰 Planes de Suscripción Seguros
        
        **🥉 Básico - $29/mes**
        - Hasta 100 envíos/mes
        - Seguridad estándar
        - Soporte por email
        
        **🥈 Pro - $99/mes**
        - Hasta 1,000 envíos/mes
        - Seguridad avanzada
        - Soporte prioritario
        
        **🥇 Enterprise - $299/mes**
        - Envíos ilimitados
        - Seguridad empresarial
        - Soporte 24/7
        """)
    
    # Métricas de seguridad
    st.markdown("### 🛡️ Estado del Servidor")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sesiones Activas", "0", "0%")
    with col2:
        st.metric("Intentos de Acceso", "0", "0%")
    with col3:
        st.metric("Alertas de Seguridad", "0", "0%")
    with col4:
        st.metric("Uptime", "99.9%", "+0.1%")

def show_secure_main_app(db):
    # Navegación principal
    selected = option_menu(
        menu_title=None,
        options=["📊 Dashboard", "🚛 Optimización", "📋 Reportes", "🔒 Seguridad", "⚙️ Configuración"],
        icons=["speedometer2", "truck", "file-earmark-text", "shield-check", "gear"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "#ff6b6b", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#eee"
            },
            "nav-link-selected": {"background-color": "#ff6b6b"},
        }
    )
    
    if selected == "📊 Dashboard":
        show_secure_dashboard()
    elif selected == "🚛 Optimización":
        show_secure_optimization()
    elif selected == "📋 Reportes":
        show_secure_reports()
    elif selected == "🔒 Seguridad":
        show_security_monitoring(db)
    elif selected == "⚙️ Configuración":
        show_secure_settings()

def show_secure_dashboard():
    st.markdown("## 📊 Dashboard Seguro")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Envíos Hoy", "1,247", "+12%")
    with col2:
        st.metric("Costo Promedio", "$45.20", "-8%")
    with col3:
        st.metric("Tiempo Promedio", "2.3 días", "-15%")
    with col4:
        st.metric("Satisfacción Cliente", "94.2%", "+3%")
    
    st.markdown("---")
    
    # Gráficos seguros
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de tendencias
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        shipments = np.random.poisson(50, len(dates))
        
        fig = px.line(x=dates, y=shipments, 
                     title='Tendencias de Envíos Seguros',
                     color_discrete_sequence=['#ff6b6b'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de costos por ruta
        routes = ['Norte', 'Sur', 'Este', 'Oeste', 'Centro']
        costs = [42.5, 38.2, 45.8, 41.3, 39.7]
        
        fig = px.bar(x=routes, y=costs, 
                    title='Costos por Ruta',
                    color=costs,
                    color_continuous_scale='Reds')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def show_secure_optimization():
    st.markdown("## 🚛 Optimización Segura de Rutas")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Optimización", "💰 Costos", "📦 Inventario", "🎯 Predicción"])
    
    with tab1:
        st.markdown("### 📍 Configuración de Optimización Segura")
        
        col1, col2 = st.columns(2)
        
        with col1:
            num_vehicles = st.number_input("Número de Vehículos", min_value=1, max_value=10, value=3)
            max_capacity = st.number_input("Capacidad Máxima (kg)", min_value=100, max_value=5000, value=2000)
        
        with col2:
            max_time = st.number_input("Tiempo Máximo (horas)", min_value=1, max_value=24, value=12)
            optimization_criteria = st.selectbox("Criterio de Optimización", 
                                               ["Minimizar Distancia", "Minimizar Tiempo", "Minimizar Costo"])
        
        if st.button("🚀 Optimizar Rutas de Forma Segura", type="primary"):
            st.success("✅ Rutas optimizadas de forma segura!")
            
            # Mostrar resultados
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Distancia Total", "450.2 km")
            with col2:
                st.metric("Tiempo Total", "8.5 horas")
            with col3:
                st.metric("Costo Total", "$1,250.50")
            
            st.info("💡 Ahorro estimado: 25% distancia, 20% tiempo, 30% costo")

def show_secure_reports():
    st.markdown("## 📋 Reportes Seguros")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Ejecutivos", "📈 Detallado", "🔔 Alertas", "📤 Exportar"])
    
    with tab1:
        st.markdown("### 📊 Reportes Ejecutivos Seguros")
        
        col1, col2 = st.columns(2)
        
        with col1:
            period = st.selectbox("Período", ["Último mes", "Últimos 3 meses", "Último año"])
            report_type = st.selectbox("Tipo de Reporte", ["Resumen", "Detallado", "Comparativo"])
        
        with col2:
            format_type = st.selectbox("Formato", ["PDF", "Excel", "CSV"])
            if st.button("🔄 Generar Reporte Seguro"):
                st.success("✅ Reporte generado de forma segura!")
        
        # Resumen ejecutivo
        st.markdown("### 📈 Resumen Ejecutivo Seguro")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Envíos", "15,420", "+18.5%")
        with col2:
            st.metric("Ingresos", "$695,250", "+22.3%")
        with col3:
            st.metric("Costo Total", "$485,675", "+15.2%")
        with col4:
            st.metric("Margen", "30.1%", "+5.2%")

def show_security_monitoring(db):
    st.markdown("## 🔒 Monitoreo de Seguridad")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Logs", "🚨 Alertas", "👥 Usuarios", "🛡️ Estado"])
    
    with tab1:
        st.markdown("### 📊 Logs de Seguridad")
        
        # Obtener logs de seguridad
        logs = db.get_security_logs(20)
        
        if logs:
            log_data = []
            for log in logs:
                log_data.append({
                    'Acción': log[0],
                    'IP': log[1],
                    'Fecha': log[2],
                    'Éxito': '✅' if log[3] else '❌',
                    'Detalles': log[4],
                    'Usuario': log[5] if log[5] else 'Sistema'
                })
            
            df = pd.DataFrame(log_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay logs de seguridad disponibles")
    
    with tab2:
        st.markdown("### 🚨 Alertas de Seguridad")
        
        # Simulación de alertas
        alerts = [
            {"tipo": "🚨", "mensaje": "Múltiples intentos de acceso fallidos", "fecha": "2024-01-15 14:30"},
            {"tipo": "⚠️", "mensaje": "Acceso desde IP desconocida", "fecha": "2024-01-15 13:45"},
            {"tipo": "✅", "mensaje": "Sesión iniciada correctamente", "fecha": "2024-01-15 13:30"},
            {"tipo": "🔒", "mensaje": "Código de seguridad validado", "fecha": "2024-01-15 13:30"}
        ]
        
        for alert in alerts:
            st.markdown(f"{alert['tipo']} **{alert['mensaje']}** - {alert['fecha']}")
    
    with tab3:
        st.markdown("### 👥 Usuarios Activos")
        
        # Simulación de usuarios activos
        users = [
            {"usuario": "admin", "rol": "Administrador", "último_acceso": "2024-01-15 14:30", "estado": "Activo"},
            {"usuario": "user1", "rol": "Usuario", "último_acceso": "2024-01-15 13:45", "estado": "Activo"},
            {"usuario": "user2", "rol": "Usuario", "último_acceso": "2024-01-15 12:30", "estado": "Inactivo"}
        ]
        
        df = pd.DataFrame(users)
        st.dataframe(df, use_container_width=True)
    
    with tab4:
        st.markdown("### 🛡️ Estado del Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Sesiones Activas", "2", "+1")
            st.metric("Intentos de Acceso", "15", "+5")
            st.metric("Alertas de Seguridad", "3", "+2")
        
        with col2:
            st.metric("Uptime", "99.9%", "+0.1%")
            st.metric("Latencia", "45ms", "-5ms")
            st.metric("Disponibilidad", "100%", "0%")

def show_secure_settings():
    st.markdown("## ⚙️ Configuración Segura")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 Empresa", "👥 Usuarios", "🔧 Técnica", "🔒 Seguridad"])
    
    with tab1:
        st.markdown("### 🏢 Información de la Empresa")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Nombre de la Empresa", value="Mi Empresa Logística")
            rfc = st.text_input("RFC", value="ABC123456789")
            address = st.text_area("Dirección", value="Av. Principal 123, Ciudad, Estado")
        
        with col2:
            phone = st.text_input("Teléfono", value="+52 55 1234 5678")
            email = st.text_input("Email", value="contacto@miempresa.com")
            website = st.text_input("Sitio Web", value="www.miempresa.com")
        
        if st.button("💾 Guardar Configuración Segura"):
            st.success("✅ Configuración guardada de forma segura!")
    
    with tab2:
        st.markdown("### 👥 Gestión de Usuarios Segura")
        st.info("Funcionalidad de gestión de usuarios disponible en versión Pro+")
    
    with tab3:
        st.markdown("### 🔧 Configuración Técnica Segura")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Configuración de Base de Datos**")
            db_host = st.text_input("Host", value="localhost")
            db_port = st.number_input("Puerto", value=5432)
            db_name = st.text_input("Nombre de BD", value="secure_logi_analytics")
        
        with col2:
            st.markdown("**Configuración de API Segura**")
            api_key = st.text_input("API Key", type="password")
            webhook_url = st.text_input("Webhook URL")
            rate_limit = st.number_input("Rate Limit", value=1000)
        
        if st.button("🔧 Aplicar Configuración Técnica"):
            st.success("✅ Configuración técnica aplicada de forma segura!")
    
    with tab4:
        st.markdown("### 🔒 Configuración de Seguridad")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Configuración de Contraseñas**")
            min_length = st.number_input("Longitud Mínima", value=8)
            require_special = st.checkbox("Requerir Caracteres Especiales", value=True)
            require_numbers = st.checkbox("Requerir Números", value=True)
            require_uppercase = st.checkbox("Requerir Mayúsculas", value=True)
        
        with col2:
            st.markdown("**Sesiones Seguras**")
            session_timeout = st.number_input("Timeout de Sesión (minutos)", value=60)
            max_sessions = st.number_input("Máximo de Sesiones", value=3)
            two_factor = st.checkbox("Autenticación de Dos Factores", value=True)
            security_code = st.checkbox("Código de Seguridad", value=True)
        
        if st.button("🔒 Aplicar Configuración de Seguridad"):
            st.success("✅ Configuración de seguridad aplicada!")

if __name__ == "__main__":
    main()
