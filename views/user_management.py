import streamlit as st
import pandas as pd
from database import Database
from datetime import datetime

def show():
    st.title("👥 Gestión de Usuarios")
    st.markdown("---")
    
    # Inicializar base de datos
    if 'db' not in st.session_state:
        st.session_state.db = Database()
    
    db = st.session_state.db
    
    # Verificar permisos de administrador
    if st.session_state.user['role'] != 'admin':
        st.error("❌ No tienes permisos para acceder a esta sección")
        return
    
    # Pestañas de gestión
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Lista de Usuarios", "➕ Agregar Usuario", "✏️ Editar Usuario", "📊 Estadísticas"])
    
    with tab1:
        show_users_list(db)
    
    with tab2:
        show_add_user_form(db)
    
    with tab3:
        show_edit_user_form(db)
    
    with tab4:
        show_user_statistics(db)

def show_users_list(db):
    """Muestra la lista de usuarios"""
    st.subheader("📋 Lista de Usuarios")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        role_filter = st.selectbox("Filtrar por Rol", ["Todos", "admin", "user"])
    
    with col2:
        status_filter = st.selectbox("Filtrar por Estado", ["Todos", "Activo", "Inactivo"])
    
    with col3:
        plan_filter = st.selectbox("Filtrar por Plan", ["Todos", "basic", "pro", "enterprise"])
    
    # Obtener usuarios
    users = db.get_all_users()
    
    # Aplicar filtros
    if role_filter != "Todos":
        users = [u for u in users if u['role'] == role_filter]
    
    if status_filter != "Todos":
        is_active = status_filter == "Activo"
        users = [u for u in users if u['is_active'] == is_active]
    
    if plan_filter != "Todos":
        users = [u for u in users if u['subscription_plan'] == plan_filter]
    
    if users:
        # Convertir a DataFrame para mejor visualización
        df = pd.DataFrame(users)
        
        # Formatear fechas
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Mostrar tabla
        st.dataframe(
            df[['username', 'full_name', 'email', 'role', 'subscription_plan', 'is_active', 'created_at', 'last_login']],
            use_container_width=True
        )
        
        # Estadísticas rápidas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Usuarios", len(users))
        
        with col2:
            active_users = len([u for u in users if u['is_active']])
            st.metric("Usuarios Activos", active_users)
        
        with col3:
            admin_users = len([u for u in users if u['role'] == 'admin'])
            st.metric("Administradores", admin_users)
        
        with col4:
            pro_users = len([u for u in users if u['subscription_plan'] in ['pro', 'enterprise']])
            st.metric("Usuarios Pro+", pro_users)
    
    else:
        st.info("No hay usuarios que coincidan con los filtros seleccionados")

def show_add_user_form(db):
    """Muestra el formulario para agregar usuario"""
    st.subheader("➕ Agregar Nuevo Usuario")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Usuario", placeholder="Nombre de usuario único")
            email = st.text_input("Email", placeholder="correo@empresa.com")
            full_name = st.text_input("Nombre Completo", placeholder="Nombre completo del usuario")
            company_name = st.text_input("Empresa", placeholder="Nombre de la empresa")
        
        with col2:
            phone = st.text_input("Teléfono", placeholder="+52 55 1234 5678")
            role = st.selectbox("Rol", ["user", "admin"])
            subscription_plan = st.selectbox("Plan de Suscripción", ["basic", "pro", "enterprise"])
            is_active = st.checkbox("Usuario Activo", value=True)
        
        password = st.text_input("Contraseña Temporal", type="password", placeholder="Contraseña temporal")
        confirm_password = st.text_input("Confirmar Contraseña", type="password", placeholder="Repite la contraseña")
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit_clicked = st.form_submit_button("✅ Crear Usuario", type="primary")
        
        with col2:
            clear_clicked = st.form_submit_button("🔄 Limpiar Formulario")
        
        if submit_clicked:
            # Validaciones
            errors = []
            
            if not username:
                errors.append("El nombre de usuario es requerido")
            elif db.get_user_by_username(username):
                errors.append("El nombre de usuario ya existe")
            
            if not email:
                errors.append("El email es requerido")
            elif db.get_user_by_email(email):
                errors.append("El email ya está registrado")
            
            if not password:
                errors.append("La contraseña es requerida")
            elif password != confirm_password:
                errors.append("Las contraseñas no coinciden")
            
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
                    role=role,
                    company_name=company_name,
                    phone=phone,
                    subscription_plan=subscription_plan
                )
                
                if success:
                    st.success("✅ Usuario creado exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Error al crear el usuario")

def show_edit_user_form(db):
    """Muestra el formulario para editar usuario"""
    st.subheader("✏️ Editar Usuario")
    
    # Seleccionar usuario
    users = db.get_all_users()
    user_options = {f"{u['username']} ({u['full_name']})": u for u in users}
    
    selected_user = st.selectbox("Seleccionar Usuario", list(user_options.keys()))
    
    if selected_user:
        user = user_options[selected_user]
        
        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Usuario", value=user['username'], disabled=True)
                email = st.text_input("Email", value=user['email'])
                full_name = st.text_input("Nombre Completo", value=user['full_name'])
                company_name = st.text_input("Empresa", value=user['company_name'] or "")
            
            with col2:
                phone = st.text_input("Teléfono", value=user['phone'] or "")
                role = st.selectbox("Rol", ["user", "admin"], index=0 if user['role'] == 'user' else 1)
                subscription_plan = st.selectbox("Plan", ["basic", "pro", "enterprise"], 
                                               index=["basic", "pro", "enterprise"].index(user['subscription_plan']))
                is_active = st.checkbox("Usuario Activo", value=user['is_active'])
            
            new_password = st.text_input("Nueva Contraseña (opcional)", type="password", placeholder="Dejar vacío para mantener la actual")
            
            col1, col2 = st.columns(2)
            
            with col1:
                update_clicked = st.form_submit_button("💾 Actualizar Usuario", type="primary")
            
            with col2:
                delete_clicked = st.form_submit_button("🗑️ Eliminar Usuario", type="secondary")
            
            if update_clicked:
                # Preparar datos para actualizar
                update_data = {
                    'email': email,
                    'full_name': full_name,
                    'company_name': company_name,
                    'phone': phone,
                    'role': role,
                    'subscription_plan': subscription_plan,
                    'is_active': is_active
                }
                
                if new_password:
                    update_data['password'] = new_password
                
                # Actualizar usuario
                success = db.update_user(user['id'], **update_data)
                
                if success:
                    st.success("✅ Usuario actualizado exitosamente")
                    st.rerun()
                else:
                    st.error("❌ Error al actualizar el usuario")
            
            if delete_clicked:
                # Confirmar eliminación
                if st.checkbox("Confirmar eliminación", value=False):
                    success = db.delete_user(user['id'])
                    if success:
                        st.success("✅ Usuario eliminado exitosamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar el usuario")

def show_user_statistics(db):
    """Muestra estadísticas de usuarios"""
    st.subheader("📊 Estadísticas de Usuarios")
    
    users = db.get_all_users()
    
    if not users:
        st.info("No hay usuarios registrados")
        return
    
    # Estadísticas generales
    col1, col2, col3, col4 = st.columns(4)
    
    total_users = len(users)
    active_users = len([u for u in users if u['is_active']])
    admin_users = len([u for u in users if u['role'] == 'admin'])
    pro_users = len([u for u in users if u['subscription_plan'] in ['pro', 'enterprise']])
    
    with col1:
        st.metric("Total Usuarios", total_users)
    
    with col2:
        st.metric("Usuarios Activos", active_users, f"{active_users/total_users*100:.1f}%")
    
    with col3:
        st.metric("Administradores", admin_users)
    
    with col4:
        st.metric("Usuarios Pro+", pro_users, f"{pro_users/total_users*100:.1f}%")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución por rol
        role_counts = pd.Series([u['role'] for u in users]).value_counts()
        
        fig_role = px.pie(
            values=role_counts.values,
            names=role_counts.index,
            title="Distribución por Rol"
        )
        st.plotly_chart(fig_role, use_container_width=True)
    
    with col2:
        # Distribución por plan
        plan_counts = pd.Series([u['subscription_plan'] for u in users]).value_counts()
        
        fig_plan = px.bar(
            x=plan_counts.index,
            y=plan_counts.values,
            title="Distribución por Plan de Suscripción",
            color=plan_counts.values,
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_plan, use_container_width=True)
    
    # Usuarios recientes
    st.markdown("### 👥 Usuarios Recientes")
    
    recent_users = sorted(users, key=lambda x: x['created_at'], reverse=True)[:5]
    
    for user in recent_users:
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        
        with col1:
            st.write(f"**{user['full_name']}**")
            st.write(f"@{user['username']}")
        
        with col2:
            st.write(f"📧 {user['email']}")
            st.write(f"🏢 {user['company_name'] or 'Sin empresa'}")
        
        with col3:
            status_color = "🟢" if user['is_active'] else "🔴"
            st.write(f"{status_color} {user['role'].title()}")
        
        with col4:
            st.write(f"📅 {user['created_at'][:10]}")
    
    # Actividad por mes
    st.markdown("### 📈 Registros por Mes")
    
    # Convertir fechas y agrupar por mes
    df_users = pd.DataFrame(users)
    df_users['created_at'] = pd.to_datetime(df_users['created_at'])
    df_users['month'] = df_users['created_at'].dt.to_period('M')
    
    monthly_counts = df_users.groupby('month').size().reset_index(name='count')
    monthly_counts['month_str'] = monthly_counts['month'].astype(str)
    
    fig_monthly = px.line(
        monthly_counts,
        x='month_str',
        y='count',
        title="Usuarios Registrados por Mes",
        markers=True
    )
    fig_monthly.update_xaxis(tickangle=45)
    st.plotly_chart(fig_monthly, use_container_width=True)
