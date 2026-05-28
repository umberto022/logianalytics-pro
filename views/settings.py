import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

def show():
    st.title("⚙️ Configuración del Sistema")
    st.markdown("---")
    
    # Pestañas de configuración
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏢 Información de la Empresa", 
        "👥 Usuarios y Permisos", 
        "🔧 Configuración Técnica", 
        "💳 Planes y Facturación", 
        "🔒 Seguridad",
        "👤 Mi Perfil"
    ])
    
    with tab1:
        company_settings()
    
    with tab2:
        user_management()
    
    with tab3:
        technical_settings()
    
    with tab4:
        billing_settings()
    
    with tab5:
        security_settings()
    
    with tab6:
        profile_settings()

def company_settings():
    st.subheader("🏢 Información de la Empresa")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Información Básica")
        
        nombre_empresa = st.text_input("Nombre de la Empresa", value="Mi Empresa Logística")
        rfc = st.text_input("RFC", value="ABC123456789")
        direccion = st.text_area("Dirección", value="Av. Principal 123, Ciudad, Estado")
        telefono = st.text_input("Teléfono", value="+52 55 1234 5678")
        email = st.text_input("Email", value="contacto@miempresa.com")
        
        st.markdown("### Configuración Logística")
        
        zonas_cobertura = st.multiselect(
            "Zonas de Cobertura",
            ["Norte", "Sur", "Este", "Oeste", "Centro", "Noroeste", "Noreste", "Suroeste", "Sureste"],
            default=["Norte", "Sur", "Este", "Oeste", "Centro"]
        )
        
        tipos_envio = st.multiselect(
            "Tipos de Envío Ofrecidos",
            ["Express (24h)", "Estándar (2-3 días)", "Económico (5-7 días)", "Internacional"],
            default=["Express (24h)", "Estándar (2-3 días)", "Económico (5-7 días)"]
        )
        
        capacidad_diaria = st.number_input("Capacidad Diaria de Envíos", value=1000, min_value=1)
    
    with col2:
        st.markdown("### Configuración Regional")
        
        moneda = st.selectbox("Moneda Principal", ["MXN", "USD", "EUR", "CAD"])
        zona_horaria = st.selectbox("Zona Horaria", ["America/Mexico_City", "America/New_York", "Europe/London"])
        idioma = st.selectbox("Idioma", ["Español", "English", "Português"])
        
        st.markdown("### Configuración de Reportes")
        
        formato_fecha = st.selectbox("Formato de Fecha", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
        formato_hora = st.selectbox("Formato de Hora", ["24 horas", "12 horas (AM/PM)"])
        
        frecuencia_reporte = st.selectbox(
            "Frecuencia de Reportes Automáticos",
            ["Diario", "Semanal", "Mensual", "No enviar"]
        )
        
        if frecuencia_reporte != "No enviar":
            hora_reporte = st.time_input("Hora de Envío", value=datetime.now().time())
            emails_reporte = st.text_area(
                "Emails para Reportes (uno por línea)",
                value="admin@miempresa.com\ngerencia@miempresa.com"
            )
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Guardar Configuración", type="primary"):
            st.success("✅ Configuración guardada exitosamente")
    
    with col2:
        if st.button("🔄 Restaurar Valores"):
            st.info("ℹ️ Valores restaurados a la configuración anterior")
    
    with col3:
        if st.button("📤 Exportar Configuración"):
            st.info("ℹ️ Configuración exportada como archivo JSON")

def user_management():
    """Gestión de usuarios - redirige a la página dedicada"""
    st.info("👥 La gestión de usuarios se ha movido a una sección dedicada.")
    
    if st.button("🔗 Ir a Gestión de Usuarios"):
        st.session_state.current_page = "Gestión de Usuarios"
        st.rerun()

def technical_settings():
    st.subheader("🔧 Configuración Técnica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Configuración de Base de Datos")
        
        tipo_bd = st.selectbox("Tipo de Base de Datos", ["PostgreSQL", "MySQL", "SQL Server", "Oracle"])
        host_bd = st.text_input("Host", value="localhost")
        puerto_bd = st.number_input("Puerto", value=5432, min_value=1, max_value=65535)
        nombre_bd = st.text_input("Nombre de la Base de Datos", value="logi_analytics")
        
        if st.button("🔗 Probar Conexión"):
            st.success("✅ Conexión exitosa")
        
        st.markdown("### Configuración de API")
        
        api_key = st.text_input("API Key", value="sk-1234567890abcdef", type="password")
        rate_limit = st.number_input("Rate Limit (requests/min)", value=1000, min_value=1)
        timeout = st.number_input("Timeout (segundos)", value=30, min_value=1)
    
    with col2:
        st.markdown("### Configuración de Integraciones")
        
        # Integración con GPS
        gps_provider = st.selectbox("Proveedor de GPS", ["Google Maps", "Mapbox", "HERE", "TomTom"])
        gps_api_key = st.text_input("GPS API Key", value="gps-api-key-123", type="password")
        
        # Integración con ERP
        erp_sistema = st.selectbox("Sistema ERP", ["SAP", "Oracle", "Microsoft Dynamics", "Ninguno"])
        if erp_sistema != "Ninguno":
            erp_endpoint = st.text_input("ERP Endpoint", value="https://erp.miempresa.com/api")
            erp_usuario = st.text_input("ERP Usuario", value="erp_user")
            erp_password = st.text_input("ERP Contraseña", value="erp_pass", type="password")
        
        # Integración con WMS
        wms_habilitado = st.checkbox("Habilitar integración con WMS", value=True)
        if wms_habilitado:
            wms_endpoint = st.text_input("WMS Endpoint", value="https://wms.miempresa.com/api")
            wms_token = st.text_input("WMS Token", value="wms-token-123", type="password")
    
    # Configuración de notificaciones
    st.markdown("### Configuración de Notificaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Email")
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
        smtp_puerto = st.number_input("SMTP Puerto", value=587, min_value=1, max_value=65535)
        smtp_usuario = st.text_input("SMTP Usuario", value="notificaciones@miempresa.com")
        smtp_password = st.text_input("SMTP Contraseña", value="smtp_pass", type="password")
        
        if st.button("📧 Probar Email"):
            st.success("✅ Email de prueba enviado exitosamente")
    
    with col2:
        st.markdown("#### SMS")
        sms_provider = st.selectbox("Proveedor SMS", ["Twilio", "AWS SNS", "Ninguno"])
        if sms_provider != "Ninguno":
            sms_api_key = st.text_input("SMS API Key", value="sms-api-key-123", type="password")
            sms_phone = st.text_input("Número de Teléfono", value="+52 55 1234 5678")
    
    # Configuración de respaldos
    st.markdown("### Configuración de Respaldos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        frecuencia_respaldo = st.selectbox("Frecuencia de Respaldo", ["Diario", "Semanal", "Mensual"])
        hora_respaldo = st.time_input("Hora de Respaldo", value=datetime.now().time())
        retencion_dias = st.number_input("Retención (días)", value=30, min_value=1)
    
    with col2:
        destino_respaldo = st.selectbox("Destino de Respaldo", ["Local", "AWS S3", "Google Cloud", "Azure"])
        if destino_respaldo != "Local":
            backup_endpoint = st.text_input("Endpoint de Respaldo", value="https://backup.miempresa.com")
            backup_credentials = st.text_input("Credenciales", value="backup-cred-123", type="password")
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Guardar Configuración Técnica", type="primary"):
            st.success("✅ Configuración técnica guardada")
    
    with col2:
        if st.button("🔄 Reiniciar Servicios"):
            st.warning("⚠️ Servicios reiniciados")
    
    with col3:
        if st.button("📊 Ver Estado del Sistema"):
            show_system_status()

def billing_settings():
    st.subheader("💳 Planes y Facturación")
    
    # Información del plan actual
    st.markdown("### Plan Actual")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Plan", "Pro", "Activo")
    
    with col2:
        st.metric("Precio Mensual", "$299", "Desde 01/01/2024")
    
    with col3:
        st.metric("Próximo Pago", "01/02/2024", "En 15 días")
    
    # Detalles del plan
    st.markdown("### Características del Plan")
    
    caracteristicas = [
        "✅ Hasta 1,000 envíos por mes",
        "✅ Optimización de rutas avanzada",
        "✅ Reportes personalizados",
        "✅ Soporte por email",
        "✅ Integración con APIs",
        "❌ Consultoría personalizada",
        "❌ Soporte prioritario 24/7"
    ]
    
    for caracteristica in caracteristicas:
        st.write(caracteristica)
    
    # Uso actual
    st.markdown("### Uso Actual del Mes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        envios_usados = 750
        envios_limite = 1000
        porcentaje_envios = (envios_usados / envios_limite) * 100
        
        st.metric("Envíos", f"{envios_usados:,}/{envios_limite:,}", f"{porcentaje_envios:.1f}%")
        st.progress(porcentaje_envios / 100)
    
    with col2:
        almacenamiento_usado = 2.5
        almacenamiento_limite = 10
        porcentaje_almacenamiento = (almacenamiento_usado / almacenamiento_limite) * 100
        
        st.metric("Almacenamiento", f"{almacenamiento_usado:.1f}GB/{almacenamiento_limite}GB", f"{porcentaje_almacenamiento:.1f}%")
        st.progress(porcentaje_almacenamiento / 100)
    
    with col3:
        usuarios_activos = 8
        usuarios_limite = 10
        porcentaje_usuarios = (usuarios_activos / usuarios_limite) * 100
        
        st.metric("Usuarios", f"{usuarios_activos}/{usuarios_limite}", f"{porcentaje_usuarios:.1f}%")
        st.progress(porcentaje_usuarios / 100)
    
    # Cambio de plan
    st.markdown("### Cambiar Plan")
    
    planes = {
        "Básico": {
            "precio": 99,
            "envios": 100,
            "usuarios": 3,
            "almacenamiento": 1,
            "caracteristicas": ["Dashboard básico", "Reportes estándar", "Soporte por email"]
        },
        "Pro": {
            "precio": 299,
            "envios": 1000,
            "usuarios": 10,
            "almacenamiento": 10,
            "caracteristicas": ["Optimización avanzada", "Reportes personalizados", "Integración APIs", "Soporte prioritario"]
        },
        "Enterprise": {
            "precio": 999,
            "envios": -1,  # Ilimitado
            "usuarios": -1,  # Ilimitado
            "almacenamiento": 100,
            "caracteristicas": ["Todo incluido", "Consultoría personalizada", "Soporte 24/7", "Personalización completa"]
        }
    }
    
    col1, col2, col3 = st.columns(3)
    
    for i, (plan, detalles) in enumerate(planes.items()):
        with [col1, col2, col3][i]:
            st.markdown(f"#### {plan}")
            st.markdown(f"**${detalles['precio']}/mes**")
            
            if detalles['envios'] == -1:
                st.write("Envíos: Ilimitados")
            else:
                st.write(f"Envíos: {detalles['envios']:,}/mes")
            
            if detalles['usuarios'] == -1:
                st.write("Usuarios: Ilimitados")
            else:
                st.write(f"Usuarios: {detalles['usuarios']}")
            
            st.write(f"Almacenamiento: {detalles['almacenamiento']}GB")
            
            for caracteristica in detalles['caracteristicas']:
                st.write(f"• {caracteristica}")
            
            if plan == "Pro":
                st.success("Plan Actual")
            else:
                if st.button(f"Cambiar a {plan}", key=f"plan_{i}"):
                    st.info(f"ℹ️ Procesando cambio a plan {plan}...")
    
    # Historial de facturación
    st.markdown("### Historial de Facturación")
    
    facturas = generate_billing_history()
    df_facturas = pd.DataFrame(facturas)
    
    st.dataframe(df_facturas, use_container_width=True)
    
    # Información de pago
    st.markdown("### Información de Pago")
    
    col1, col2 = st.columns(2)
    
    with col1:
        metodo_pago = st.selectbox("Método de Pago", ["Tarjeta de Crédito", "Transferencia Bancaria", "PayPal"])
        
        if metodo_pago == "Tarjeta de Crédito":
            st.text_input("Número de Tarjeta", value="**** **** **** 1234", disabled=True)
            st.text_input("Fecha de Vencimiento", value="12/25", disabled=True)
            st.text_input("CVV", value="***", disabled=True)
    
    with col2:
        st.text_input("Email de Facturación", value="facturacion@miempresa.com")
        st.text_input("Razón Social", value="Mi Empresa Logística S.A. de C.V.")
        st.text_input("RFC", value="ABC123456789", disabled=True)

def security_settings():
    st.subheader("🔒 Configuración de Seguridad")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Autenticación")
        
        # Configuración de contraseñas
        longitud_minima = st.number_input("Longitud Mínima de Contraseña", value=8, min_value=6, max_value=20)
        complejidad = st.checkbox("Requerir complejidad (mayúsculas, números, símbolos)", value=True)
        expiracion = st.number_input("Días de expiración de contraseña", value=90, min_value=30)
        
        # Autenticación de dos factores
        st.markdown("#### Autenticación de Dos Factores")
        two_factor = st.checkbox("Habilitar 2FA", value=True)
        if two_factor:
            metodo_2fa = st.selectbox("Método 2FA", ["SMS", "Email", "App Authenticator"])
            if metodo_2fa == "SMS":
                st.text_input("Número de Teléfono", value="+52 55 1234 5678")
    
    with col2:
        st.markdown("### Sesiones")
        
        # Configuración de sesiones
        timeout_sesion = st.number_input("Timeout de Sesión (minutos)", value=60, min_value=15)
        sesiones_simultaneas = st.number_input("Sesiones Simultáneas Máximas", value=3, min_value=1)
        recordar_dispositivo = st.checkbox("Permitir 'Recordar dispositivo'", value=True)
        
        # Configuración de IP
        st.markdown("#### Restricciones de IP")
        whitelist_ip = st.checkbox("Habilitar Whitelist de IP", value=False)
        if whitelist_ip:
            ips_permitidas = st.text_area("IPs Permitidas (una por línea)", value="192.168.1.0/24\n10.0.0.0/8")
    
    # Auditoría y logs
    st.markdown("### Auditoría y Logs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Configuración de Logs")
        
        nivel_log = st.selectbox("Nivel de Log", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        retencion_logs = st.number_input("Retención de Logs (días)", value=90, min_value=7)
        logs_detallados = st.checkbox("Logs detallados de usuario", value=True)
    
    with col2:
        st.markdown("#### Eventos de Seguridad")
        
        eventos_seguridad = [
            "Inicio de sesión exitoso",
            "Intento de inicio de sesión fallido",
            "Cambio de contraseña",
            "Acceso a datos sensibles",
            "Exportación de datos",
            "Cambios de configuración"
        ]
        
        for evento in eventos_seguridad:
            st.checkbox(f"Registrar {evento}", value=True)
    
    # Políticas de seguridad
    st.markdown("### Políticas de Seguridad")
    
    politicas = [
        "Bloquear cuenta después de 5 intentos fallidos",
        "Notificar cambios de configuración por email",
        "Requerir confirmación para operaciones críticas",
        "Cifrar datos sensibles en reposo",
        "Usar HTTPS para todas las comunicaciones",
        "Validar entrada de datos del usuario"
    ]
    
    for politica in politicas:
        st.checkbox(politica, value=True)
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Guardar Configuración de Seguridad", type="primary"):
            st.success("✅ Configuración de seguridad guardada")
    
    with col2:
        if st.button("🔍 Generar Reporte de Seguridad"):
            st.info("ℹ️ Reporte de seguridad generado")
    
    with col3:
        if st.button("🚨 Forzar Cierre de Sesiones"):
            st.warning("⚠️ Todas las sesiones han sido cerradas")

def generate_users_data():
    """Genera datos de usuarios de ejemplo"""
    
    usuarios = [
        {
            "nombre": "Juan Pérez",
            "email": "juan.perez@miempresa.com",
            "rol": "Administrador",
            "departamento": "IT",
            "estado": "Activo",
            "ultimo_acceso": "2024-01-15 14:30:00",
            "permisos": "Completos"
        },
        {
            "nombre": "María García",
            "email": "maria.garcia@miempresa.com",
            "rol": "Gerente",
            "departamento": "Logística",
            "estado": "Activo",
            "ultimo_acceso": "2024-01-15 12:15:00",
            "permisos": "Gestión y Reportes"
        },
        {
            "nombre": "Carlos López",
            "email": "carlos.lopez@miempresa.com",
            "rol": "Operador",
            "departamento": "Operaciones",
            "estado": "Activo",
            "ultimo_acceso": "2024-01-15 16:45:00",
            "permisos": "Operaciones básicas"
        },
        {
            "nombre": "Ana Martínez",
            "email": "ana.martinez@miempresa.com",
            "rol": "Solo Lectura",
            "departamento": "Administración",
            "estado": "Inactivo",
            "ultimo_acceso": "2024-01-10 09:20:00",
            "permisos": "Solo lectura"
        }
    ]
    
    return usuarios

def generate_billing_history():
    """Genera historial de facturación"""
    
    facturas = []
    for i in range(12):  # Últimos 12 meses
        fecha = datetime.now().replace(day=1) - pd.DateOffset(months=i)
        facturas.append({
            "fecha": fecha.strftime("%Y-%m-%d"),
            "concepto": "Suscripción Mensual - Plan Pro",
            "monto": "$299.00",
            "estado": "Pagado",
            "metodo": "Tarjeta de Crédito",
            "referencia": f"INV-{fecha.strftime('%Y%m')}-001"
        })
    
    return facturas

def show_system_status():
    """Muestra el estado del sistema"""
    
    st.markdown("### Estado del Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("CPU", "45%", "Normal")
        st.metric("Memoria", "2.1GB / 8GB", "Normal")
    
    with col2:
        st.metric("Disco", "156GB / 500GB", "Normal")
        st.metric("Red", "125 Mbps", "Normal")
    
    with col3:
        st.metric("Base de Datos", "Activa", "✅")
        st.metric("API", "Activa", "✅")
    
    # Servicios
    st.markdown("### Servicios")
    
    servicios = [
        {"nombre": "Web Server", "estado": "Activo", "uptime": "99.9%"},
        {"nombre": "Database", "estado": "Activo", "uptime": "99.8%"},
        {"nombre": "API Gateway", "estado": "Activo", "uptime": "99.7%"},
        {"nombre": "Background Jobs", "estado": "Activo", "uptime": "99.5%"},
        {"nombre": "Email Service", "estado": "Activo", "uptime": "99.9%"}
    ]
    
    for servicio in servicios:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(servicio["nombre"])
        
        with col2:
            if servicio["estado"] == "Activo":
                st.success("✅ Activo")
            else:
                st.error("❌ Inactivo")
        
        with col3:
            st.write(servicio["uptime"])

def profile_settings():
    """Configuración del perfil del usuario actual"""
    st.subheader("👤 Mi Perfil")
    
    # Obtener datos del usuario actual
    user = st.session_state.user
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Información Personal")
            username = st.text_input("Usuario", value=user['username'], disabled=True)
            email = st.text_input("Email", value=user['email'])
            full_name = st.text_input("Nombre Completo", value=user['full_name'])
            phone = st.text_input("Teléfono", value=user['phone'] or "")
        
        with col2:
            st.markdown("### Información Empresarial")
            company_name = st.text_input("Empresa", value=user['company_name'] or "")
            role = st.text_input("Rol", value=user['role'].title(), disabled=True)
            subscription_plan = st.text_input("Plan", value=user['subscription_plan'].title(), disabled=True)
            is_active = st.checkbox("Usuario Activo", value=user['is_active'], disabled=True)
        
        st.markdown("### Cambiar Contraseña")
        current_password = st.text_input("Contraseña Actual", type="password", placeholder="Ingresa tu contraseña actual")
        new_password = st.text_input("Nueva Contraseña", type="password", placeholder="Mínimo 8 caracteres")
        confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password", placeholder="Repite la nueva contraseña")
        
        col1, col2 = st.columns(2)
        
        with col1:
            update_clicked = st.form_submit_button("💾 Actualizar Perfil", type="primary")
        
        with col2:
            password_clicked = st.form_submit_button("🔐 Cambiar Contraseña")
        
        if update_clicked:
            # Validar email
            if not email:
                st.error("El email es requerido")
            else:
                # Actualizar perfil
                if 'db' not in st.session_state:
                    st.session_state.db = Database()
                
                db = st.session_state.db
                success = db.update_user(
                    user['id'],
                    email=email,
                    full_name=full_name,
                    company_name=company_name,
                    phone=phone
                )
                
                if success:
                    # Actualizar datos en sesión
                    st.session_state.user['email'] = email
                    st.session_state.user['full_name'] = full_name
                    st.session_state.user['company_name'] = company_name
                    st.session_state.user['phone'] = phone
                    st.success("✅ Perfil actualizado exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Error al actualizar el perfil")
        
        if password_clicked:
            if not current_password or not new_password or not confirm_password:
                st.error("Todos los campos de contraseña son requeridos")
            elif new_password != confirm_password:
                st.error("Las contraseñas no coinciden")
            else:
                # Verificar contraseña actual
                if 'db' not in st.session_state:
                    st.session_state.db = Database()
                
                db = st.session_state.db
                
                # Obtener usuario con contraseña
                user_with_password = db.get_user_by_username(user['username'])
                if user_with_password and db.verify_password(current_password, user_with_password['password_hash']):
                    # Cambiar contraseña
                    success = db.update_user(user['id'], password=new_password)
                    if success:
                        st.success("✅ Contraseña cambiada exitosamente")
                    else:
                        st.error("❌ Error al cambiar la contraseña")
                else:
                    st.error("❌ La contraseña actual es incorrecta")
    
    # Información adicional
    st.markdown("---")
    st.markdown("### ℹ️ Información de la Cuenta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Miembro desde:** {user['created_at'][:10]}")
        st.write(f"**Último acceso:** {user['last_login'][:10] if user['last_login'] else 'Nunca'}")
    
    with col2:
        st.write(f"**ID de Usuario:** {user['id']}")
        st.write(f"**Estado:** {'🟢 Activo' if user['is_active'] else '🔴 Inactivo'}")
    
    # Acciones de cuenta
    st.markdown("### ⚠️ Acciones de Cuenta")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Exportar Mis Datos", type="secondary"):
            st.info("ℹ️ Función de exportación en desarrollo")
    
    with col2:
        if st.button("🗑️ Eliminar Mi Cuenta", type="secondary"):
            st.warning("⚠️ Esta acción no se puede deshacer. Contacta al administrador.")
