import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import Database


def _db() -> Database:
    return Database()


def show() -> None:
    st.title("📈 Rentabilidad")
    st.markdown(
        "Analiza qué **rutas**, **productos** y **zonas** generan más ganancia."
    )

    user = st.session_state.get("user")
    if not user:
        st.warning("Inicia sesión para continuar.")
        return

    uid = int(user["id"])
    db = _db()

    col1, _ = st.columns([1, 3])
    with col1:
        days = st.selectbox(
            "Período de análisis",
            [7, 15, 30, 60, 90, 180],
            index=2,
            format_func=lambda x: f"Últimos {x} días",
        )

    summary = db.get_sales_summary(uid, days=days)

    if summary["num_sales"] == 0:
        st.info(
            "No hay ventas en este período. "
            "Ve a **💰 Ventas** para registrar transacciones."
        )
        return

    # Global KPIs
    margin = (
        summary["profit"] / summary["revenue"] * 100
        if summary["revenue"] > 0
        else 0
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ventas",           f"{summary['num_sales']:,}")
    c2.metric("Unidades vendidas", f"{summary['total_units']:,}")
    c3.metric("Ingresos totales",  f"${summary['revenue']:,.2f}")
    c4.metric("Costo total",       f"${summary['cost']:,.2f}")
    c5.metric("Ganancia / Margen", f"${summary['profit']:,.2f}", f"{margin:.1f}%")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🗺️ Por ruta", "📦 Por producto", "🔄 Movimientos"])

    with tab1:
        _by_route(db, uid, days)

    with tab2:
        _by_product(db, uid, days)

    with tab3:
        _movements(db, uid)


# ─────────────────────────────── BY ROUTE ─────────────────────────────────────

def _by_route(db: Database, uid: int, days: int) -> None:
    rows = db.get_profitability_by_route(uid, days)
    if not rows:
        st.info("Sin datos de rutas para este período.")
        return

    df = pd.DataFrame(rows).fillna(0)

    best = df.nlargest(1, "profit").iloc[0]
    st.success(
        f"Mejor ruta: **{best['route']}** — "
        f"Ganancia **${best['profit']:,.2f}** | Margen **{best['margin_pct']:.1f}%**"
    )

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            df.sort_values("profit", ascending=False),
            x="route",
            y=["revenue", "cost", "profit"],
            barmode="group",
            title="Ingresos, costo y ganancia por ruta",
            labels={"value": "$", "variable": "Métrica", "route": "Ruta"},
            color_discrete_map={
                "revenue": "#667eea",
                "cost": "#f56565",
                "profit": "#48bb78",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig2 = px.bar(
            df.sort_values("margin_pct"),
            x="margin_pct",
            y="route",
            orientation="h",
            title="Margen de ganancia por ruta (%)",
            labels={"margin_pct": "Margen (%)", "route": "Ruta"},
            color="margin_pct",
            color_continuous_scale="RdYlGn",
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Units chart
    fig3 = px.pie(
        df,
        names="route",
        values="total_units",
        title="Distribución de unidades vendidas por ruta",
        hole=0.4,
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Tabla de rutas")
    df_show = df[["route","num_sales","total_units","revenue","cost","profit","margin_pct"]].copy()
    df_show.columns = ["Ruta","Ventas","Unidades","Ingresos ($)","Costo ($)","Ganancia ($)","Margen (%)"]
    st.dataframe(df_show, use_container_width=True, hide_index=True)


# ─────────────────────────────── BY PRODUCT ───────────────────────────────────

def _by_product(db: Database, uid: int, days: int) -> None:
    rows = db.get_profitability_by_product(uid, days)
    if not rows:
        st.info("Sin datos de productos para este período.")
        return

    df = pd.DataFrame(rows).fillna(0)

    c1, c2 = st.columns(2)
    with c1:
        best = df.nlargest(1, "profit").iloc[0]
        st.success(
            f"Mejor producto: **{best['product_name']}** — "
            f"Ganancia **${best['profit']:,.2f}** | Margen **{best['margin_pct']:.1f}%**"
        )
    with c2:
        if len(df) > 1:
            worst = df.nsmallest(1, "margin_pct").iloc[0]
            if worst["margin_pct"] < 10:
                st.warning(
                    f"Menor margen: **{worst['product_name']}** — {worst['margin_pct']:.1f}%"
                )

    # Treemap: revenue by category → product, color = margin
    if not df.empty:
        fig_tree = px.treemap(
            df,
            path=["category", "product_name"],
            values="revenue",
            color="margin_pct",
            color_continuous_scale="RdYlGn",
            title="Mapa de ingresos por categoría y producto (color = margen %)",
            labels={"margin_pct": "Margen (%)", "revenue": "Ingreso ($)"},
        )
        fig_tree.update_traces(
            textinfo="label+value",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Ingreso: $%{value:,.2f}<br>"
                "Margen: %{color:.1f}%<extra></extra>"
            ),
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        top10 = df.nlargest(10, "profit")
        fig_bar = px.bar(
            top10,
            x="product_name",
            y="profit",
            color="margin_pct",
            color_continuous_scale="RdYlGn",
            title="Top 10 productos por ganancia ($)",
            labels={
                "product_name": "Producto",
                "profit": "Ganancia ($)",
                "margin_pct": "Margen (%)",
            },
        )
        fig_bar.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        fig_sc = px.scatter(
            df,
            x="total_units",
            y="profit",
            size="revenue",
            color="margin_pct",
            hover_name="product_name",
            color_continuous_scale="RdYlGn",
            title="Unidades vendidas vs Ganancia (tamaño = ingreso)",
            labels={
                "total_units": "Unidades vendidas",
                "profit": "Ganancia ($)",
                "margin_pct": "Margen (%)",
            },
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    st.subheader("Tabla de productos")
    df_show = df[[
        "sku","product_name","category","num_sales",
        "total_units","revenue","cost","profit","margin_pct"
    ]].copy()
    df_show.columns = [
        "SKU","Producto","Categoría","Ventas",
        "Unidades","Ingresos ($)","Costo ($)","Ganancia ($)","Margen (%)"
    ]
    st.dataframe(df_show, use_container_width=True, hide_index=True)


# ─────────────────────────────── MOVEMENTS ────────────────────────────────────

def _movements(db: Database, uid: int) -> None:
    st.subheader("Movimientos de inventario")
    st.caption(
        "Cada venta registrada actualiza el inventario automáticamente mediante un trigger. "
        "Aquí puedes auditar todos los movimientos."
    )

    col1, _ = st.columns([1, 3])
    with col1:
        days = st.selectbox(
            "Período",
            [7, 15, 30, 60, 90],
            index=2,
            format_func=lambda x: f"Últimos {x} días",
            key="mov_days",
        )

    movements = db.get_inventory_movements(uid, days=days)
    if not movements:
        st.info("Sin movimientos en este período.")
        return

    df = pd.DataFrame(movements)
    type_map = {"sale": "🔴 Venta", "purchase": "🟢 Compra", "adjustment": "🟡 Ajuste"}
    df["Tipo"] = df["movement_type"].map(type_map).fillna(df["movement_type"])
    df["Cantidad"] = df["quantity"].apply(lambda x: f"+{x}" if x > 0 else str(x))

    show = df[["created_at","Tipo","sku","name","Cantidad","reference","note"]].copy()
    show.columns = ["Fecha","Tipo","SKU","Producto","Cantidad","Referencia","Nota"]
    st.dataframe(show, use_container_width=True, hide_index=True)

    # Movement chart
    df["date"] = pd.to_datetime(df["created_at"]).dt.date
    df["qty_signed"] = df["quantity"]
    by_day = (
        df.groupby(["date","movement_type"])["qty_signed"]
        .sum()
        .reset_index()
    )
    if not by_day.empty:
        by_day["movement_type"] = by_day["movement_type"].map(
            {"sale":"Ventas","purchase":"Compras","adjustment":"Ajustes"}
        ).fillna(by_day["movement_type"])
        fig = px.bar(
            by_day,
            x="date",
            y="qty_signed",
            color="movement_type",
            title="Movimientos de stock por día",
            labels={"qty_signed":"Unidades","date":"Fecha","movement_type":"Tipo"},
            color_discrete_map={
                "Ventas": "#f56565",
                "Compras": "#48bb78",
                "Ajustes": "#ecc94b",
            },
        )
        st.plotly_chart(fig, use_container_width=True)
