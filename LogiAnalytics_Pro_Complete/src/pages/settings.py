import streamlit as st
from database import Database


def _db() -> Database:
    return Database()


def show() -> None:
    st.title("⚙️ Configuración")

    user = st.session_state.get("user")
    if not user:
        st.warning("Inicia sesión para continuar.")
        return

    tab_profile, tab_company = st.tabs(["👤 Mi Perfil", "🏢 Mi Empresa"])

    with tab_profile:
        _profile(user)

    with tab_company:
        _company(user)


# ─────────────────────────────── PROFILE ──────────────────────────────────────

def _profile(user: dict) -> None:
    st.subheader("👤 Mi Perfil")
    db = _db()
    uid = int(user["id"])

    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Usuario", value=user["username"], disabled=True)
            email     = st.text_input("Email *", value=user.get("email") or "")
            full_name = st.text_input("Nombre completo", value=user.get("full_name") or "")
        with c2:
            phone = st.text_input("Teléfono", value=user.get("phone") or "")
            st.text_input("Rol", value=(user.get("role") or "user").title(), disabled=True)
            st.text_input("Plan", value=(user.get("subscription_plan") or "free").title(), disabled=True)

        st.markdown("#### Cambiar contraseña")
        c3, c4, c5 = st.columns(3)
        with c3:
            cur_pass  = st.text_input("Contraseña actual", type="password")
        with c4:
            new_pass  = st.text_input("Nueva contraseña", type="password")
        with c5:
            conf_pass = st.text_input("Confirmar nueva", type="password")

        col_a, col_b = st.columns(2)
        with col_a:
            save_profile = st.form_submit_button("💾 Guardar perfil", type="primary",
                                                  use_container_width=True)
        with col_b:
            change_pass  = st.form_submit_button("🔐 Cambiar contraseña",
                                                  use_container_width=True)

    if save_profile:
        if not email:
            st.error("El email es obligatorio.")
        else:
            db.update_user(uid, email=email, full_name=full_name, phone=phone)
            st.session_state.user["email"]     = email
            st.session_state.user["full_name"] = full_name
            st.session_state.user["phone"]     = phone
            st.success("✅ Perfil actualizado.")

    if change_pass:
        if not cur_pass or not new_pass or not conf_pass:
            st.error("Completa todos los campos de contraseña.")
        elif new_pass != conf_pass:
            st.error("Las contraseñas nuevas no coinciden.")
        elif len(new_pass) < 6:
            st.error("La contraseña debe tener al menos 6 caracteres.")
        else:
            row = db.get_user_by_username(user["username"])
            if row and db.verify_password(cur_pass, row["password_hash"]):
                db.update_user(uid, password=new_pass)
                st.success("✅ Contraseña cambiada exitosamente.")
            else:
                st.error("❌ La contraseña actual es incorrecta.")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Miembro desde:** {(user.get('created_at') or '')[:10]}")
    with c2:
        ll = (user.get("last_login") or "")[:16].replace("T", " ")
        st.write(f"**Último acceso:** {ll or 'Primera sesión'}")


# ─────────────────────────────── COMPANY ──────────────────────────────────────

def _company(user: dict) -> None:
    st.subheader("🏢 Datos de la Empresa")
    db = _db()
    uid = int(user["id"])
    company = db.get_company(user["company_id"]) if user.get("company_id") else None

    if not company:
        st.info("Aún no has registrado una empresa.")
        with st.form("new_company_form"):
            c1, c2 = st.columns(2)
            with c1:
                name     = st.text_input("Nombre de la empresa *")
                rif      = st.text_input("RIF / NIT / RFC")
                industry = st.selectbox("Industria", [
                    "Logística / Transporte", "Comercio / Retail", "Manufactura",
                    "Distribución", "Alimentos y Bebidas", "Tecnología", "Otro",
                ])
            with c2:
                country  = st.selectbox("País", [
                    "Venezuela", "Colombia", "México", "Argentina", "Chile",
                    "Perú", "Ecuador", "Uruguay", "Otro",
                ])
                phone    = st.text_input("Teléfono")
                email    = st.text_input("Email empresarial")
            address = st.text_area("Dirección")
            submit = st.form_submit_button("Registrar empresa", type="primary",
                                           use_container_width=True)
        if submit:
            if not name:
                st.error("El nombre es obligatorio.")
            else:
                ok, cid = db.register_company(uid, name, rif=rif, address=address,
                                               phone=phone, email=email,
                                               industry=industry, country=country)
                if ok:
                    fresh = db.get_user_by_id(uid)
                    st.session_state.user = fresh
                    st.success(f"✅ Empresa '{name}' registrada.")
                    st.rerun()
                else:
                    st.error("Error al registrar la empresa.")
        return

    with st.form("edit_company_form"):
        c1, c2 = st.columns(2)
        with c1:
            name     = st.text_input("Nombre de la empresa *", value=company["name"])
            rif      = st.text_input("RIF / NIT / RFC", value=company.get("rif") or "")
            industry = st.selectbox("Industria", [
                "Logística / Transporte", "Comercio / Retail", "Manufactura",
                "Distribución", "Alimentos y Bebidas", "Tecnología", "Otro",
            ], index=_industry_index(company.get("industry") or ""))
        with c2:
            country  = st.selectbox("País", [
                "Venezuela", "Colombia", "México", "Argentina", "Chile",
                "Perú", "Ecuador", "Uruguay", "Otro",
            ], index=_country_index(company.get("country") or ""))
            phone    = st.text_input("Teléfono", value=company.get("phone") or "")
            email    = st.text_input("Email empresarial", value=company.get("email") or "")
        address = st.text_area("Dirección", value=company.get("address") or "")
        save = st.form_submit_button("💾 Guardar cambios", type="primary",
                                     use_container_width=True)

    if save:
        if not name:
            st.error("El nombre es obligatorio.")
        else:
            db.update_company(company["id"], name=name, rif=rif, address=address,
                              phone=phone, email=email, industry=industry, country=country)
            st.session_state.user["company_name"] = name
            st.success("✅ Datos de la empresa actualizados.")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Registrada el:** {(company.get('created_at') or '')[:10]}")
    with c2:
        st.write(f"**ID empresa:** {company['id']}")


def _industry_index(v: str) -> int:
    opts = ["Logística / Transporte","Comercio / Retail","Manufactura",
            "Distribución","Alimentos y Bebidas","Tecnología","Otro"]
    return opts.index(v) if v in opts else 6

def _country_index(v: str) -> int:
    opts = ["Venezuela","Colombia","México","Argentina","Chile","Perú","Ecuador","Uruguay","Otro"]
    return opts.index(v) if v in opts else 8
