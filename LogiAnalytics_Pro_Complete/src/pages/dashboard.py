from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from database import Database


def _db() -> Database:
    return Database()


_CSS = """
<style>
/* ── KPI cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #0f3460;
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    box-shadow: 0 4px 20px rgba(0,0,0,.25);
}
[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: .78rem !important;
    letter-spacing: .06em;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] svg { display: none; }

/* ── Alert cards ── */
.alert-crit {
    background: linear-gradient(90deg,#7f1d1d,#991b1b);
    border-left: 4px solid #ef4444;
    border-radius: 8px; padding: .7rem 1rem; margin-bottom: .4rem;
    color: #fecaca; font-size: .9rem;
}
.alert-warn {
    background: linear-gradient(90deg,#78350f,#92400e);
    border-left: 4px solid #f59e0b;
    border-radius: 8px; padding: .7rem 1rem; margin-bottom: .4rem;
    color: #fde68a; font-size: .9rem;
}
.alert-ok {
    background: linear-gradient(90deg,#052e16,#064e3b);
    border-left: 4px solid #10b981;
    border-radius: 8px; padding: .7rem 1rem; margin-bottom: .4rem;
    color: #a7f3d0; font-size: .9rem;
}

/* ── Section titles ── */
.section-title {
    font-size: 1.05rem; font-weight: 600;
    color: #cbd5e1; letter-spacing: .04em;
    margin: 1.4rem 0 .6rem;
    border-bottom: 1px solid #1e293b; padding-bottom: .4rem;
}
</style>
"""

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#cbd5e1",
    margin=dict(t=40, l=0, r=0, b=0),
    height=320,
)


def show() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    user = st.session_state.get("user")
    if not user:
        st.warning("Inicia sesión para continuar.")
        return

    uid = int(user["id"])
    db = _db()

    company_name = user.get("company_name") or "tu empresa"
    hour = datetime.now().hour
    greeting = "Buenos días" if hour < 12 else ("Buenas tardes" if hour < 19 else "Buenas noches")
    st.markdown(
        f"## {greeting}, **{user.get('full_name') or user['username']}** 👋",
    )
    st.caption(f"Dashboard de {company_name} · {datetime.now().strftime('%A %d de %B, %Y')}")

    # ── Pull data ──────────────────────────────────────────────────────────────
    inv_items   = db.list_inventory(uid)
    summary_30  = db.get_sales_summary(uid, days=30)
    summary_7   = db.get_sales_summary(uid, days=7)
    sales_30    = db.get_sales(uid, days=30)
    routes      = db.get_profitability_by_route(uid, days=30)
    products    = db.get_profitability_by_product(uid, days=30)

    has_inventory = bool(inv_items)
    has_sales     = summary_30["num_sales"] > 0

    # ── Empty state ────────────────────────────────────────────────────────────
    if not has_inventory and not has_sales:
        _empty_state(company_name)
        return

    # ── KPIs ───────────────────────────────────────────────────────────────────
    st.markdown('<p class="section-title">RESUMEN DEL NEGOCIO · ÚLTIMOS 30 DÍAS</p>',
                unsafe_allow_html=True)

    inv_value   = sum(i["current_stock"] * i["unit_cost"] for i in inv_items)
    n_crit      = sum(1 for i in inv_items if i["current_stock"] <= i["min_stock"])
    margin_30   = (summary_30["profit"] / summary_30["revenue"] * 100
                   if summary_30["revenue"] > 0 else 0)
    rev_delta   = _week_delta(summary_7["revenue"], summary_30["revenue"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ingresos (30d)",    f"${summary_30['revenue']:,.0f}",  f"{rev_delta:+.1f}% vs sem")
    c2.metric("Ganancia (30d)",    f"${summary_30['profit']:,.0f}",   f"{margin_30:.1f}% margen")
    c3.metric("Ventas registradas",f"{summary_30['num_sales']:,}",    f"{summary_7['num_sales']} esta semana")
    c4.metric("Valor inventario",  f"${inv_value:,.0f}",             f"{len(inv_items)} SKUs")
    c5.metric("Alertas stock",     str(n_crit),
              "crítico" if n_crit > 0 else "todo ok",
              delta_color="inverse" if n_crit > 0 else "normal")

    # ── Charts row 1 ──────────────────────────────────────────────────────────
    if has_sales:
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown('<p class="section-title">TENDENCIA DE INGRESOS Y GANANCIA</p>',
                        unsafe_allow_html=True)
            df_s = pd.DataFrame(sales_30)
            df_s["sale_date"] = pd.to_datetime(df_s["sale_date"])
            daily = (
                df_s.groupby(df_s["sale_date"].dt.date)
                .agg(Ingresos=("total_revenue","sum"), Ganancia=("profit","sum"))
                .reset_index()
                .rename(columns={"sale_date":"Fecha"})
            )
            # fill missing days
            idx = pd.date_range(
                datetime.now() - timedelta(days=29), datetime.now(), freq="D"
            )
            daily = (
                daily.set_index("Fecha")
                .reindex(idx.date, fill_value=0)
                .reset_index()
                .rename(columns={"index":"Fecha"})
            )
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=daily["Fecha"], y=daily["Ingresos"],
                name="Ingresos", mode="lines",
                line=dict(color="#667eea", width=2.5),
                fill="tozeroy", fillcolor="rgba(102,126,234,0.08)",
            ))
            fig_trend.add_trace(go.Scatter(
                x=daily["Fecha"], y=daily["Ganancia"],
                name="Ganancia", mode="lines",
                line=dict(color="#48bb78", width=2),
                fill="tozeroy", fillcolor="rgba(72,187,120,0.06)",
            ))
            fig_trend.update_layout(**_PLOTLY_LAYOUT, showlegend=True,
                                    legend=dict(orientation="h", y=1.1))
            fig_trend.update_xaxes(showgrid=False)
            fig_trend.update_yaxes(showgrid=True, gridcolor="#1e293b")
            st.plotly_chart(fig_trend, use_container_width=True)

        with col_right:
            st.markdown('<p class="section-title">GANANCIA POR RUTA</p>',
                        unsafe_allow_html=True)
            if routes:
                df_r = pd.DataFrame(routes).nlargest(7, "profit")
                fig_r = px.bar(
                    df_r,
                    x="profit", y="route", orientation="h",
                    color="margin_pct", color_continuous_scale="teal",
                    labels={"profit":"Ganancia ($)","route":"","margin_pct":"Margen %"},
                    text=df_r["profit"].apply(lambda v: f"${v:,.0f}"),
                )
                fig_r.update_traces(textposition="outside")
                fig_r.update_layout(**_PLOTLY_LAYOUT, coloraxis_showscale=False)
                fig_r.update_xaxes(showgrid=False)
                fig_r.update_yaxes(showgrid=False)
                st.plotly_chart(fig_r, use_container_width=True)
            else:
                st.info("Registra ventas con ruta para ver este gráfico.")

        # ── Charts row 2 ──────────────────────────────────────────────────────
        col2_left, col2_right = st.columns([2, 3])

        with col2_left:
            st.markdown('<p class="section-title">TOP 5 PRODUCTOS</p>',
                        unsafe_allow_html=True)
            if products:
                df_p = pd.DataFrame(products).head(5)
                fig_p = px.bar(
                    df_p,
                    x="profit", y="product_name", orientation="h",
                    color="margin_pct", color_continuous_scale="Purples",
                    labels={"profit":"Ganancia ($)","product_name":"","margin_pct":"Margen %"},
                )
                fig_p.update_layout(**_PLOTLY_LAYOUT, coloraxis_showscale=False)
                fig_p.update_xaxes(showgrid=False)
                fig_p.update_yaxes(showgrid=False)
                st.plotly_chart(fig_p, use_container_width=True)

        with col2_right:
            st.markdown('<p class="section-title">DISTRIBUCIÓN DE VENTAS POR CATEGORÍA</p>',
                        unsafe_allow_html=True)
            if not df_s.empty and "category" in df_s.columns:
                cat = (
                    df_s.groupby("category")
                    .agg(revenue=("total_revenue","sum"), units=("quantity","sum"))
                    .reset_index()
                )
                fig_cat = px.treemap(
                    cat,
                    path=["category"],
                    values="revenue",
                    color="units",
                    color_continuous_scale="Blues",
                    labels={"revenue":"Ingresos ($)","units":"Unidades","category":"Categoría"},
                )
                fig_cat.update_layout(**_PLOTLY_LAYOUT, height=300)
                st.plotly_chart(fig_cat, use_container_width=True)

    # ── Inventory health + Alerts ──────────────────────────────────────────────
    col_inv, col_alerts = st.columns([2, 1])

    with col_inv:
        if has_inventory:
            st.markdown('<p class="section-title">ESTADO DEL INVENTARIO</p>',
                        unsafe_allow_html=True)
            df_inv = pd.DataFrame(inv_items)
            df_inv["valor"] = df_inv["current_stock"] * df_inv["unit_cost"]
            df_inv["estado"] = df_inv.apply(
                lambda r: "Crítico" if r["current_stock"] <= r["min_stock"]
                else ("Bajo" if r["current_stock"] <= r["min_stock"] * 1.5 else "Óptimo"),
                axis=1,
            )
            color_map = {"Crítico":"#ef4444","Bajo":"#f59e0b","Óptimo":"#10b981"}
            fig_inv = px.bar(
                df_inv.nlargest(12, "valor"),
                x="sku", y="current_stock",
                color="estado",
                color_discrete_map=color_map,
                labels={"current_stock":"Unidades","sku":"SKU","estado":"Estado"},
                text="current_stock",
            )
            fig_inv.update_traces(textposition="outside")
            fig_inv.update_layout(**_PLOTLY_LAYOUT, height=300,
                                  showlegend=True,
                                  legend=dict(orientation="h", y=1.1))
            fig_inv.update_xaxes(showgrid=False, tickangle=-35)
            fig_inv.update_yaxes(showgrid=True, gridcolor="#1e293b")
            st.plotly_chart(fig_inv, use_container_width=True)

    with col_alerts:
        st.markdown('<p class="section-title">ALERTAS ACTIVAS</p>',
                    unsafe_allow_html=True)
        alerts = _build_alerts(inv_items, summary_30)
        if not alerts:
            st.markdown('<div class="alert-ok">✅ Todo en orden. Sin alertas activas.</div>',
                        unsafe_allow_html=True)
        else:
            for a in alerts[:8]:
                cls = "alert-crit" if a["level"] == "crit" else "alert-warn"
                st.markdown(f'<div class="{cls}">{a["msg"]}</div>',
                            unsafe_allow_html=True)

    # ── Recent sales mini-table ────────────────────────────────────────────────
    if has_sales:
        st.markdown('<p class="section-title">ÚLTIMAS VENTAS</p>',
                    unsafe_allow_html=True)
        recent = pd.DataFrame(sales_30[:10])
        recent["sale_date"] = pd.to_datetime(recent["sale_date"]).dt.strftime("%d/%m %H:%M")
        cols = ["sale_date","product_name","quantity","unit_price","route","total_revenue","profit"]
        cols = [c for c in cols if c in recent.columns]
        st.dataframe(
            recent[cols].rename(columns={
                "sale_date":"Fecha","product_name":"Producto","quantity":"Cant.",
                "unit_price":"Precio u.","route":"Ruta",
                "total_revenue":"Ingreso ($)","profit":"Ganancia ($)",
            }),
            use_container_width=True,
            hide_index=True,
            height=320,
        )


# ── helpers ───────────────────────────────────────────────────────────────────

def _empty_state(company: str) -> None:
    st.markdown("---")
    st.markdown(
        f"""
        ### 🚀 Bienvenido a LogiAnalytics Pro

        Aún no hay datos para **{company}**. Sigue estos pasos para empezar:

        | Paso | Acción | Módulo |
        |------|--------|--------|
        | 1️⃣ | Carga tu inventario de productos | **📦 Inventario** |
        | 2️⃣ | Registra tus primeras ventas con ruta y zona | **💰 Ventas** |
        | 3️⃣ | Analiza qué productos y rutas son más rentables | **📈 Rentabilidad** |

        Una vez que registres ventas, este dashboard mostrará métricas reales de tu negocio.
        """
    )


def _build_alerts(items: list, summary: dict) -> list:
    alerts = []
    for i in items:
        if i["current_stock"] <= i["min_stock"]:
            alerts.append({
                "level": "crit",
                "msg": f"⚠️ <b>{i['sku']}</b>: stock crítico "
                       f"({i['current_stock']} u. / mín {i['min_stock']})",
            })
        elif i["current_stock"] <= i["min_stock"] * 1.5:
            alerts.append({
                "level": "warn",
                "msg": f"📉 <b>{i['sku']}</b>: stock bajo "
                       f"({i['current_stock']} u.)",
            })
    if summary["revenue"] > 0 and summary["profit"] / summary["revenue"] < 0.10:
        alerts.append({
            "level": "warn",
            "msg": "📊 Margen global bajo el 10% este mes. Revisa precios.",
        })
    return alerts


def _week_delta(week_val: float, month_val: float) -> float:
    expected_week = month_val / 4.3
    if expected_week == 0:
        return 0.0
    return (week_val - expected_week) / expected_week * 100
