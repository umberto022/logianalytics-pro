import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64
import random
import json


# =========================
# MAIN VIEW
# =========================
def show():
    st.title("📋 Reportes y Análisis")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Reportes Ejecutivos",
        "📈 Análisis Detallado",
        "🔔 Alertas",
        "📤 Exportar Datos"
    ])

    with tab1:
        executive_reports()

    with tab2:
        detailed_analysis()

    with tab3:
        alerts_system()

    with tab4:
        export_data()


# =========================
# EXECUTIVE REPORTS
# =========================
def executive_reports():
    st.subheader("📊 Reportes Ejecutivos")

    col1, col2, col3 = st.columns(3)

    with col1:
        periodo = st.selectbox(
            "Período",
            ["Última semana", "Último mes", "Último trimestre", "Último año"]
        )

    with col2:
        formato = st.selectbox(
            "Formato",
            ["Resumen", "Detallado", "Comparativo"]
        )

    with col3:
        generar = st.button("🔄 Generar Reporte", type="primary")

    if generar:
        st.session_state["reporte"] = generate_executive_report(periodo)

    if "reporte" in st.session_state:
        data = st.session_state["reporte"]

        st.markdown("### 📈 Resumen Ejecutivo")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Envíos", f"{data['total_envios']:,}")
        c2.metric("Ingresos", f"${data['ingresos']:,.2f}")
        c3.metric("Costos", f"${data['costo_total']:,.2f}")
        c4.metric("Margen", f"{data['margen']:.1f}%")

        fig = px.line(data["tendencia_envios"], x="fecha", y="envios")
        st.plotly_chart(fig, use_container_width=True)


# =========================
# DETAILED ANALYSIS
# =========================
def detailed_analysis():
    st.subheader("📈 Análisis Detallado")

    ruta = st.selectbox("Ruta", ["Todas", "Norte", "Sur", "Este", "Oeste"])
    tipo = st.selectbox("Tipo", ["Todos", "Express", "Económico"])

    fecha_inicio = st.date_input("Inicio", datetime.now() - timedelta(days=30))
    fecha_fin = st.date_input("Fin", datetime.now())

    data = generate_detailed_analysis()

    st.metric("Eficiencia", f"{data['eficiencia']:.1f}%")
    st.metric("Tiempo Promedio", f"{data['tiempo_promedio']:.1f} días")

    fig = px.bar(data["por_hora"], x="hora", y="rendimiento")
    st.plotly_chart(fig, use_container_width=True)


# =========================
# ALERTS
# =========================
def alerts_system():
    st.subheader("🔔 Sistema de Alertas")

    if st.button("🔍 Verificar Alertas"):
        alertas = check_alerts()

        if not alertas:
            st.success("No hay alertas activas")
        else:
            for a in alertas:
                if a["nivel"] == "critico":
                    st.error(a["mensaje"])
                elif a["nivel"] == "advertencia":
                    st.warning(a["mensaje"])
                else:
                    st.info(a["mensaje"])


# =========================
# EXPORT
# =========================
def export_data():
    st.subheader("📤 Exportar Datos")

    formato = st.selectbox("Formato", ["CSV", "JSON"])

    if st.button("Generar"):
        file = generate_export_file(formato)

        st.download_button(
            "Descargar",
            data=file["data"],
            file_name=file["filename"],
            mime=file["mime"]
        )


# =========================
# FUNCTIONS
# =========================
def generate_executive_report(periodo):
    dias = {"Última semana": 7, "Último mes": 30, "Último trimestre": 90}.get(periodo, 30)

    fechas = pd.date_range(end=datetime.now(), periods=dias)

    return {
        "total_envios": random.randint(5000, 15000),
        "ingresos": random.uniform(10000, 50000),
        "costo_total": random.uniform(5000, 30000),
        "margen": random.uniform(10, 40),
        "tendencia_envios": pd.DataFrame({
            "fecha": fechas,
            "envios": np.random.randint(100, 500, len(fechas))
        })
    }


def generate_detailed_analysis():
    return {
        "eficiencia": random.uniform(70, 95),
        "tiempo_promedio": random.uniform(1.5, 4.5),
        "por_hora": pd.DataFrame({
            "hora": list(range(6, 22)),
            "rendimiento": np.random.uniform(60, 95, 16)
        })
    }


def check_alerts():
    alertas = []

    if random.random() < 0.4:
        alertas.append({"nivel": "critico", "mensaje": "Tiempo de entrega elevado"})

    if random.random() < 0.4:
        alertas.append({"nivel": "advertencia", "mensaje": "Costo alto en ruta Norte"})

    return alertas


def generate_export_file(formato):
    if formato == "CSV":
        data = "id,costo,tiempo\n1,50,2\n2,60,3"
        return {
            "data": data,
            "filename": "export.csv",
            "mime": "text/csv"
        }

    data = json.dumps({"status": "ok"})
    return {
        "data": data,
        "filename": "export.json",
        "mime": "application/json"
    }