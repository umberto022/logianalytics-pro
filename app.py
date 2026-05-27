import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pages import dashboard, optimization, reports, settings
from database import Database
import re

# Configuración de la página
st.set_page_config(
    page_title="LogiAnalytics Pro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar base de datos
@st.cache_resource
def init_database():
    return Database()

# Funciones de validación
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe tener al menos una mayúscula"
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe tener al menos una minúscula"
    if not re.search(r'\d', password):
        return False, "La contraseña debe tener al menos un número"
    return True, "Contraseña válida"

def validate_username(username):
    if len(username) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "El nombre de usuario solo puede contener letras, números y guiones bajos"
    return True, "Nombre de usuario válido"

def main():
    # Header principal
    st.markdown('<h1 class="main-header">🚚 LogiAnalytics Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Plataforma de Análisis Logístico Inteligente</p>', unsafe_allow_html=True)
    
    # Inicializar base de datos
    db = init_database()
    
    # Inicializar estado de sesión
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    # Sidebar para autenticación
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/667eea/ffffff?text=LogiAnalytics", width=200)
        
        if st.session_state.user is None:
            # Mostrar formulario de login o registro
            if st.session_state.show_register:
                show_register_form(db)
            else:
                show_login_form(db)
        else:
            # Usuario autenticado
            st.success(f'Bienvenido {st.session_state.user["full_name"]}')
            
            # Navegación principal
            st.markdown("---")
            st.markdown("### 📊 Navegación")
            
            page = st.selectbox(
                "Selecciona una sección:",
                ["Dashboard", "Optimización", "Reportes", "Configuración", "Gestión de Usuarios"]
            )
            
            # Información del usuario
            st.markdown("---")
            st.markdown("### 👤 Usuario")
            st.write(f"**Nombre:** {st.session_state.user['full_name']}")
            st.write(f"**Usuario:** {st.session_state.user['username']}")
            st.write(f"**Rol:** {st.session_state.user['role'].title()}")
            st.write(f"**Plan:** {st.session_state.user['subscription_plan'].title()}")
            
            if st.button('🚪 Cerrar Sesión', type="secondary"):
                # Cerrar sesión
                if st.session_state.session_token:
                    db.logout_session(st.session_state.session_token)
                st.session_state.user = None
                st.session_state.session_token = None
                st.rerun()
    
    # Contenido principal basado en la página seleccionada
    if st.session_state.user is not None:
        if page == "Dashboard":
            dashboard.show()
        elif page == "Optimización":
            optimization.show()
        elif page == "Reportes":
            reports.show()
        elif page == "Configuración":
            settings.show()
        elif page == "Gestión de Usuarios":
            from pages import user_management
            user_management.show()
    else:
        # Página de bienvenida para usuarios no autenticados
        show_welcome_page()

def show_login_form(db):
    """Muestra el formulario de login"""
    st.markdown("### 🔐 Iniciar Sesión")
    
    with st.form("login_form"):
        username = st.text_input("Usuario", placeholder="Ingresa tu nombre de usuario")
        password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        col1, col2 = st.columns(2)
        
        with col1:
            login_clicked = st.form_submit_button("🚀 Iniciar Sesión", type="primary")
        
        with col2:
            register_clicked = st.form_submit_button("📝 Registrarse")
        
        if login_clicked:
            if username and password:
                user = db.authenticate_user(username, password)
                if user:
                    # Crear sesión
                    session_token = db.create_session(user['id'])
                    st.session_state.user = user
                    st.session_state.session_token = session_token
                    st.success("¡Inicio de sesión exitoso!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
            else:
                st.warning("Por favor completa todos los campos")
        
        if register_clicked:
            st.session_state.show_register = True
            st.rerun()

def show_register_form(db):
    """Muestra el formulario de registro"""
    st.markdown("### 📝 Registro de Usuario")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Usuario", placeholder="Nombre de usuario")
            email = st.text_input("Email", placeholder="tu@email.com")
            full_name = st.text_input("Nombre Completo", placeholder="Tu nombre completo")
        
        with col2:
            company_name = st.text_input("Empresa", placeholder="Nombre de tu empresa")
            phone = st.text_input("Teléfono", placeholder="+52 55 1234 5678")
            subscription_plan = st.selectbox("Plan", ["basic", "pro", "enterprise"])
        
        password = st.text_input("Contraseña", type="password", placeholder="Mínimo 8 caracteres")
        confirm_password = st.text_input("Confirmar Contraseña", type="password", placeholder="Repite tu contraseña")
        
        # Términos y condiciones
        terms_accepted = st.checkbox("Acepto los términos y condiciones", value=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            register_clicked = st.form_submit_button("✅ Registrarse", type="primary")
        
        with col2:
            back_clicked = st.form_submit_button("⬅️ Volver al Login")
        
        if register_clicked:
            # Validaciones
            errors = []
            
            # Validar username
            if not username:
                errors.append("El nombre de usuario es requerido")
            else:
                valid, msg = validate_username(username)
                if not valid:
                    errors.append(msg)
                elif db.get_user_by_username(username):
                    errors.append("El nombre de usuario ya existe")
            
            # Validar email
            if not email:
                errors.append("El email es requerido")
            elif not validate_email(email):
                errors.append("El email no es válido")
            elif db.get_user_by_email(email):
                errors.append("El email ya está registrado")
            
            # Validar contraseña
            if not password:
                errors.append("La contraseña es requerida")
            else:
                valid, msg = validate_password(password)
                if not valid:
                    errors.append(msg)
            
            # Validar confirmación de contraseña
            if password != confirm_password:
                errors.append("Las contraseñas no coinciden")
            
            # Validar términos
            if not terms_accepted:
                errors.append("Debes aceptar los términos y condiciones")
            
            # Validar nombre completo
            if not full_name:
                errors.append("El nombre completo es requerido")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Crear usuario
                success = db.create_user(
                    username=username,
                    email=email,
                    full_name=full_name,
                    password=password,
                    company_name=company_name,
                    phone=phone,
                    subscription_plan=subscription_plan
                )
                
                if success:
                    st.success("¡Usuario registrado exitosamente! Ya puedes iniciar sesión.")
                    st.session_state.show_register = False
                    st.rerun()
                else:
                    st.error("Error al crear el usuario. Intenta de nuevo.")
        
        if back_clicked:
            st.session_state.show_register = False
            st.rerun()

def show_welcome_page():
    st.markdown("""
    ## 🎯 Bienvenido a LogiAnalytics Pro
    
    **La plataforma más avanzada para análisis logístico empresarial**
    
    ### ✨ Características Principales
    
    - **📊 Dashboard Inteligente**: Visualiza KPIs clave en tiempo real
    - **🚛 Optimización de Rutas**: Algoritmos avanzados para reducir costos
    - **📈 Análisis Predictivo**: Predice demanda y optimiza inventario
    - **🔔 Alertas Automáticas**: Notificaciones inteligentes
    - **📋 Reportes Personalizados**: Genera reportes automáticos
    
    ### 💼 Beneficios Empresariales
    
    - ⬇️ **Reducción de costos** hasta 25%
    - ⚡ **Mejora de eficiencia** en 40%
    - 📊 **Toma de decisiones** basada en datos
    - 🎯 **Optimización continua** de procesos
    
    ### 🚀 Planes de Suscripción
    
    | Plan | Precio | Características |
    |------|--------|----------------|
    | **Básico** | $99/mes | Dashboard básico, 100 envíos/mes |
    | **Pro** | $299/mes | Optimización avanzada, 1000 envíos/mes |
    | **Enterprise** | $999/mes | Personalización completa, envíos ilimitados |
    
    ---
    
    **Inicia sesión o regístrate para acceder a la plataforma completa**
    """)
    
    # Demo de datos
    st.markdown("### 📊 Vista Previa de Datos")
    
    # Generar datos de ejemplo
    demo_data = generate_demo_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Envíos Hoy", "1,247", "12%")
        st.metric("Costo Promedio", "$45.20", "-8%")
    
    with col2:
        st.metric("Tiempo Promedio", "2.3 días", "-15%")
        st.metric("Satisfacción", "94.2%", "3%")
    
    # Gráfico de ejemplo
    fig = px.line(demo_data, x='fecha', y='envios', title='Envíos por Día')
    st.plotly_chart(fig, use_container_width=True)
    
    # Información adicional
    st.markdown("### 🔐 Credenciales de Demo")
    st.info("""
    **Para probar la plataforma, puedes usar:**
    - **Usuario:** admin
    - **Contraseña:** admin123
    
    O regístrate con tu propia cuenta para una experiencia personalizada.
    """)

def generate_demo_data():
    """Genera datos de demostración"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    np.random.seed(42)
    
    data = {
        'fecha': dates,
        'envios': np.random.randint(800, 1500, len(dates)),
        'costo': np.random.uniform(35, 55, len(dates)),
        'tiempo': np.random.uniform(1.5, 3.5, len(dates))
    }
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    main()
