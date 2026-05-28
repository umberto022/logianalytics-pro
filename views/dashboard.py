from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import Database

_CSS = """
<style>
.kpi-card {
    background: linear-gradient(135deg,#667eea,#764ba2);
    border-radius:12px; padding:1rem 1.2rem; color:#fff;
    margin-bottom:.5rem;
}
.kpi-card .kpi-label { font-size:.8rem; opacity:.85; margin-bottom:.2rem; }
.kpi-card .kpi-value { font-size:1.8rem; font-weight:700; line-height:1.1; }
.kpi-card .kpi-delta { font-size:.78rem; opacity:.8; margin-top:.25rem; }
.alert-crit {
    background:linear-gradient(90deg,#7f1d1d,#991b1b);
    border-left:4px solid #ef4444; border-radius:8px;
    padding:.55rem 1rem; margin-bottom:.3rem;
    color:#fecaca; font-size:.85rem;
}
.alert-warn {
    background:linear-gradient(90deg,#78350f,#92400e);
    border-left:4px solid #f59e0b; border-radius:8px;
    padding:.55rem 1rem; margin-bottom:.3rem;
    color:#fde68a; font-size:.85rem;
}
.alert-ok {
    background:linear-gradient(90deg,#064e3b,#065f46);
    border-left:4px solid #10b981; border-radius:8px;
    padding:.55rem 1rem; margin-bottom:.3rem;
    color:#a7f3d0; font-size:.85rem;
}
</style>
"""


def _db() -> Database:
    return Database()


def show() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.title("📊 Dashboard")

    user = st.session_state.get("user")
    if not user:
        st.warning("Inicia sesión para continuar.")
        return

    uid = int(user["id"])
    db  = _db()

    col_period, _ = st.columns([1, 3])
    with col_period:
        days = st.selectbox(
            "Período",
            [7, 15, 30, 60, 90],
            index=2,
            format_func=lambda x: f"Últimos {x} días",
        )

    summary  = db.get_sales_summary(uid, days=days)
    items    = db.list_inventory(uid)
    routes   = db.get_profitability_by_route(uid, days=days)
    products = db.get_profitability_by_product(uid, days=days)

    if summary["num_sales"] == 0 and not items:
        _empty_state()
        return

    # ── KPIs ──────────────────────────────────────────────────────────
    margin_pct = (
        summary["profit"] / summary["revenue"] * 100
        if summary["revenue"] > 0 else 0
    )
    inv_value  = sum(int(i["current_stock"]) * float(i["unit_cost"]) for i in items)
    n_crit     = sum(1 for i in items if int(i["current_stock"]) <= int(i["min_stock"]))
    n_low      = sum(
        1 for i in items
        if int(i["current_stock"]) > int(i["min_stock"])
        and int(i["max_stock"]) > int(i["min_stock"])
        and int(i["current_stock"]) <= int(i["min_stock"]) + max(1, int((int(i["max_stock"]) - int(i["min_stock"])) * 0.25))
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ingresos",         f"${summary['revenue']:,.2f}")
    c2.metric("Ganancia",         f"${summary['profit']:,.2f}",  f"{margin_pct:.1f}%")
    c3.metric("Ventas",           f"{summary['num_sales']:,}")
    c4.metric("Valor inventario", f"${inv_value:,.2f}")
    c5.metric("Alertas stock",    f"{n_crit} crít  {n_low} bajos",
              delta_color="inverse" if n_crit + n_low > 0 else "normal")

    st.markdown("---")

    # ── Stock alerts ──────────────────────────────────────────────────
    alerts = _build_alerts(items)
    if alerts:
        with st.expander(f"⚠️ {len(alerts)} alerta(s) de inventario", expanded=n_crit > 0):
            for cls, text in alerts:
                st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)

    # ── Trend chart ───────────────────────────────────────────────────
    sales_rows = db.get_sales(uid, days=days)
    if sales_rows:
        df_sales = pd.DataFrame(sales_rows)
        df_sales["sale_date"] = pd.to_datetime(df_sales["sale_date"])
        daily = (
            df_sales.groupby(df_sales["sale_date"].dt.date)
            .agg(Ingresos=("total_revenue", "sum"), Ganancia=("profit", "sum"))
            .reset_index()
            .rename(columns={"sale_date": "Fecha"})
        )
        fig_trend = px.line(
            daily, x="Fecha", y=["Ingresos", "Ganancia"],
            title=f"Ingresos y ganancia — últimos {days} días",
            labels={"value": "$", "variable": "Métrica"},
            color_discrete_map={"Ingresos": "#667eea", "Ganancia": "#48bb78"},
        )
        fig_trend.update_layout(legend_title_text="")
        st.plotly_chart(fig_trend, use_container_width=True)

    # ── Route + Products row ───────────────────────────────────────────
    col_r, col_p = st.columns(2)

    with col_r:
        if routes:
            df_r = pd.DataFrame(routes).fillna(0).sort_values("profit", ascending=False)
            fig_r = px.bar(
                df_r, x="route", y="profit",
                color="margin_pct", color_continuous_scale="RdYlGn",
                title="Ganancia por ruta ($)",
                labels={"route": "Ruta", "profit": "Ganancia ($)", "margin_pct": "Margen (%)"},
                text_auto=".2s",
            )
            fig_r.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.info("Sin datos de rutas para este período.")

    with col_p:
        if products:
            df_p = pd.DataFrame(products).fillna(0).nlargest(5, "profit")
            fig_p = px.bar(
                df_p, x="product_name", y="profit",
                color="margin_pct", color_continuous_scale="RdYlGn",
                title="Top 5 productos por ganancia ($)",
                labels={"product_name": "Producto", "profit": "Ganancia ($)", "margin_pct": "Margen (%)"},
                text_auto=".2s",
            )
            fig_p.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.info("Sin datos de productos para este período.")

    # ── Category treemap + Inventory health ──────────────────────────
    if products:
        col_t, col_h = st.columns(2)
        df_all = pd.DataFrame(products).fillna(0)

        with col_t:
            fig_tree = px.treemap(
                df_all, path=["category", "product_name"], values="revenue",
                color="margin_pct", color_continuous_scale="RdYlGn",
                title="Ingresos por categoría (color = margen %)",
                labels={"margin_pct": "Margen (%)", "revenue": "Ingreso ($)"},
            )
            st.plotly_chart(fig_tree, use_container_width=True)

        with col_h:
            if items:
                df_inv = pd.DataFrame(items)
                def _status(r):
                    c, mn, mx = int(r["current_stock"]), int(r["min_stock"]), int(r["max_stock"])
                    if c <= mn: return "🔴 Crítico"
                    if mx > mn and c <= mn + max(1, int((mx - mn) * 0.25)): return "🟡 Bajo"
                    return "🟢 Óptimo"
                df_inv["estado"] = df_inv.apply(_status, axis=1)
                counts = df_inv["estado"].value_counts().reset_index()
                counts.columns = ["estado", "cantidad"]
                fig_h = px.bar(
                    counts, x="estado", y="cantidad",
                    color="estado",
                    color_discrete_map={"🔴 Crítico": "#ef4444", "🟡 Bajo": "#f59e0b", "🟢 Óptimo": "#10b981"},
                    title="Estado del inventario",
                    labels={"estado": "Estado", "cantidad": "Productos"},
                    text_auto=True,
                )
                fig_h.update_layout(showlegend=False)
                st.plotly_chart(fig_h, use_container_width=True)

    # ── Recent sales table ─────────────────────────────────────────────
    if sales_rows:
        st.markdown("---")
        st.subheader("Ventas recientes")
        df_recent = pd.DataFrame(sales_rows[:10])
        show_cols = [c for c in ["sale_date", "product_name", "quantity", "unit_price",
                                  "route", "zone", "client", "total_revenue", "profit"]
                     if c in df_recent.columns]
        renamed = {
            "sale_date": "Fecha", "product_name": "Producto", "quantity": "Cant.",
            "unit_price": "Precio u.", "route": "Ruta", "zone": "Zona",
            "client": "Cliente", "total_revenue": "Ingreso ($)", "profit": "Ganancia ($)",
        }
        st.dataframe(
            df_recent[show_cols].rename(columns=renamed),
            use_container_width=True, hide_index=True,
        )


def _build_alerts(items: list) -> list[tuple[str, str]]:
    alerts = []
    for i in items:
        c, mn, mx = int(i["current_stock"]), int(i["min_stock"]), int(i["max_stock"])
        name = i["name"]
        if c <= mn:
            alerts.append(("alert-crit", f"<b>🔴 Crítico</b> · {name} — stock {c} ≤ mín {mn}"))
        elif mx > mn and c <= mn + max(1, int((mx - mn) * 0.25)):
            alerts.append(("alert-warn", f"<b>🟡 Bajo</b> · {name} — stock {c} (mín {mn})"))
    return alerts


def _empty_state() -> None:
    st.info(
        "¡Bienvenido/a! Aún no tienes datos. Sigue estos pasos:\n\n"
        "1. **📦 Inventario** → agrega tus productos\n"
        "2. **💰 Ventas** → registra tus ventas\n"
        "3. Vuelve aquí para ver tu dashboard con datos reales."
    )
