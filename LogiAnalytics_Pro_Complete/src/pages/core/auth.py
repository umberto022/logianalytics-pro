import streamlit as st
from database import Database

db = Database()

# =========================
# LOGIN
# =========================
def login(username, password):
    user = db.authenticate_user(username, password)

    if user:
        session_token = db.create_session(user["id"])

        st.session_state["user"] = user
        st.session_state["session_token"] = session_token
        st.session_state["logged_in"] = True

        return True

    return False


# =========================
# LOGOUT
# =========================
def logout():
    token = st.session_state.get("session_token")

    if token:
        db.delete_session(token)

    st.session_state.clear()


# =========================
# CHECK LOGIN
# =========================
def require_login():
    if not st.session_state.get("logged_in"):
        st.warning("🔒 Debes iniciar sesión")
        st.stop()