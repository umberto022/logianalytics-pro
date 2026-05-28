import os
import sys

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

st.set_page_config(
    page_title="LogiAnalytics Pro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database import Database


def _db() -> Database:
    return Database()


# ──────────────────────────────────────────────────────────────
# AUTH SCREENS
# ──────────────────────────────────────────────────────────────

def show_login():
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.title("🚚 LogiAnalytics Pro")
        st.markdown("Plataforma de analítica logística para tu empresa")
        st.markdown("---")

        tab_login, tab_register = st.tabs(["Iniciar sesión", "Crear cuenta"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Usuario o email")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button(
                    "Ingresar", type="primary", use_container_width=True
                )
            if submit:
                if not username or not password:
                    st.error("Completa todos los campos")
                else:
                    db = _db()
                    user = db.authenticate_user(username, password)
                    if user:
                        token = db.create_session(user["id"])
                        st.session_state.user = user
                        st.session_state.session_token = token
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")

        with tab_register:
            with st.form("register_form"):
                c1, c2 = st.columns(2)
                with c1:
                    r_user  = st.text_input("Nombre de usuario *")
                    r_email = st.text_input("Email *")
                    r_name  = st.text_input("Nombre completo *")
                with c2:
                    r_phone = st.text_input("Teléfono")
                    r_pass  = st.text_input("Contraseña *", type="password")
                    r_conf  = st.text_input("Confirmar contraseña *", type="password")
                submit_reg = st.form_submit_button(
                    "Crear cuenta", type="primary", use_container_width=True
                )
            if submit_reg:
                if not all([r_user, r_email, r_name, r_pass, r_conf]):
                    st.error("Completa todos los campos obligatorios (*)")
                elif r_pass != r_conf:
                    st.error("Las contraseñas no coinciden")
                elif len(r_pass) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres")
                else:
                    db = _db()
                    ok, msg = db.register_user(r_user, r_email, r_name, r_pass, r_phone)
                    if ok:
                        user = db.authenticate_user(r_user, r_pass)
                        token = db.create_session(user["id"])
                        st.session_state.user = user
                        st.session_state.session_token = token
                        st.session_state.logged_in = True
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# ──────────────────────────────────────────────────────────────
# COMPANY SETUP SCREEN
# ──────────────────────────────────────────────────────────────

def show_company_setup():
    user = st.session_state.user
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.title("🏢 Registra tu empresa")
        st.markdown(
            f"Bienvenido/a **{user.get('full_name') or user['username']}**. "
            "Antes de continuar, registra los datos de tu empresa."
        )
        st.markdown("---")

        with st.form("company_form"):
            c1, c2 = st.columns(2)
            with c1:
                c_name     = st.text_input("Nombre de la empresa *")
                c_rif      = st.text_input("RIF / NIT / RFC")
                c_industry = st.selectbox("Industria", [
                    "Logística / Transporte", "Comercio / Retail", "Manufactura",
                    "Distribución", "Alimentos y Bebidas", "Tecnología", "Otro",
                ])
                c_country  = st.selectbox("País", [
                    "Venezuela", "Colombia", "México", "Argentina", "Chile",
                    "Perú", "Ecuador", "Uruguay", "Otro",
                ])
            with c2:
                c_address = st.text_area("Dirección", height=90)
                c_phone   = st.text_input("Teléfono")
                c_email   = st.text_input("Email empresarial")

            col_a, col_b = st.columns(2)
            with col_a:
                submit = st.form_submit_button(
                    "Registrar empresa y continuar", type="primary", use_container_width=True
                )
            with col_b:
                skip = st.form_submit_button("Omitir por ahora", use_container_width=True)

        if submit:
            if not c_name:
                st.error("El nombre de la empresa es obligatorio")
            else:
                db = _db()
                ok, company_id = db.register_company(
                    owner_id=user["id"], name=c_name, rif=c_rif,
                    address=c_address, phone=c_phone, email=c_email,
                    industry=c_industry, country=c_country,
                )
                if ok:
                    fresh = db.get_user_by_id(user["id"])
                    st.session_state.user = fresh
                    st.success(f"Empresa '{c_name}' registrada exitosamente")
                    st.rerun()
                else:
                    st.error("Error al registrar la empresa")
        if skip:
            st.session_state.skip_company = True
            st.rerun()


# ──────────────────────────────────────────────────────────────
# MAIN APP
# ──────────────────────────────────────────────────────────────

def show_app():
    from pages import dashboard, inventory, settings
    from pages import sales, profitability

    user = st.session_state.user
    db = _db()

    with st.sidebar:
        st.markdown(f"### 👤 {user.get('full_name') or user['username']}")
        if user.get("company_name"):
            st.markdown(f"🏢 **{user['company_name']}**")
        elif user.get("company_id"):
            company = db.get_company(user["company_id"])
            if company:
                st.markdown(f"🏢 **{company['name']}**")
        st.markdown("---")

        page = st.radio(
            "Navegación",
            [
                "📊 Dashboard",
                "💰 Ventas",
                "📈 Rentabilidad",
                "📦 Inventario",
                "⚙️ Configuración",
            ],
        )

        st.markdown("---")
        if st.button("Cerrar sesión", use_container_width=True):
            token = st.session_state.get("session_token")
            if token:
                db.delete_session(token)
            st.session_state.clear()
            st.rerun()

    if page == "📊 Dashboard":
        dashboard.show()
    elif page == "💰 Ventas":
        sales.show()
    elif page == "📈 Rentabilidad":
        profitability.show()
    elif page == "📦 Inventario":
        inventory.show()
    elif page == "⚙️ Configuración":
        settings.show()


# ──────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────

def main():
    if not st.session_state.get("logged_in"):
        show_login()
        return

    db = _db()
    fresh = db.get_user_by_id(st.session_state.user["id"])
    if fresh:
        st.session_state.user = fresh

    user = st.session_state.user
    if not user.get("company_id") and not st.session_state.get("skip_company"):
        show_company_setup()
        return

    show_app()


if __name__ == "__main__":
    main()
