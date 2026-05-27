"""
Centro de control de inventario: datos operativos, ABC, EOQ, punto de pedido,
stock de seguridad, alertas y visualizaciones para decisiones logísticas.
"""
from __future__ import annotations

import io
import math
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from database import Database


def _db() -> Database:
    return Database()


def _effective_daily(row: pd.Series, fallback: float) -> float:
    v = row.get("daily_demand")
    if v is not None and not (isinstance(v, float) and math.isnan(v)) and float(v) > 0:
        return float(v)
    return max(fallback, 0.01)


def _safety_stock(daily: float, lead: int, z: float) -> int:
    """Stock de seguridad (aprox.): z * demanda_diaria * sqrt(lead)."""
    lead = max(1, int(lead))
    return max(0, int(round(z * daily * math.sqrt(lead))))


def _reorder_point(min_stock: int, daily: float, lead: int, z: float) -> int:
    """Punto de pedido: max(mínimo político, demanda en ciclo + stock de seguridad)."""
    lead = max(1, int(lead))
    ss = _safety_stock(daily, lead, z)
    cycle = daily * lead
    return max(int(min_stock), int(round(cycle + ss)))


def _eoq(annual_demand: float, order_cost: float, unit_cost: float, holding_rate: float) -> int:
    """Cantidad económica de pedido (EOQ). H = costo de mantener una unidad al año."""
    if annual_demand <= 0 or order_cost <= 0 or unit_cost <= 0 or holding_rate <= 0:
        return 0
    h = unit_cost * holding_rate
    q = math.sqrt((2.0 * annual_demand * order_cost) / h)
    return max(0, int(round(q)))


def _abc_class(valor_linea: float, total: float, cum_pct: float) -> str:
    if total <= 0:
        return "C"
    if cum_pct <= 0.80:
        return "A"
    if cum_pct <= 0.95:
        return "B"
    return "C"


def _estado(row: pd.Series, rop: int) -> str:
    c, mn, mx = int(row["current_stock"]), int(row["min_stock"]), int(row["max_stock"])
    if c <= mn:
        return "Crítico"
    if c <= rop:
        return "Bajo (≤ punto pedido)"
    if mx > mn and c >= mx:
        return "Sobrestock"
    if c <= mn + max(1, int((mx - mn) * 0.15)):
        return "Preventivo"
    return "Óptimo"


def _health_score(df: pd.DataFrame) -> tuple[float, str]:
    """Puntuación 0–100 y texto (más alto = mejor situación de stock)."""
    if df.empty:
        return 0.0, "Sin datos."
    n = len(df)
    crit = (df["_estado"] == "Crítico").sum()
    low = df["_estado"].str.contains("Bajo", na=False).sum()
    over = (df["_estado"] == "Sobrestock").sum()
    pen = (crit * 25 + low * 12 + over * 5) / max(n, 1)
    score = max(0.0, min(100.0, 100.0 - pen))
    if score >= 80:
        txt = "Salud del inventario: **buena**. Prioriza refinamiento y costos de pedido."
    elif score >= 55:
        txt = "Salud del inventario: **moderada**. Revisa SKUs en rojo y punto de pedido."
    else:
        txt = "Salud del inventario: **requiere acción**. Hay varios SKUs críticos o bajo punto de pedido."
    return round(score, 1), txt


def _build_analytics(
    df: pd.DataFrame,
    demand_fallback: float,
    order_cost: float,
    holding_rate: float,
    z_safety: float,
) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["_daily"] = out.apply(lambda r: _effective_daily(r, demand_fallback), axis=1)
    out["_lead"] = out["lead_time_days"].fillna(7).astype(int).clip(lower=1)
    out["cobertura_dias"] = (out["current_stock"] / out["_daily"]).replace([np.inf, -np.inf], np.nan).round(1)
    out["stock_seguridad"] = out.apply(
        lambda r: _safety_stock(float(r["_daily"]), int(r["_lead"]), z_safety), axis=1
    )
    out["punto_pedido"] = out.apply(
        lambda r: _reorder_point(int(r["min_stock"]), float(r["_daily"]), int(r["_lead"]), z_safety),
        axis=1,
    )
    out["demanda_anual"] = (out["_daily"] * 365.0).round(1)
    out["eoq"] = out.apply(
        lambda r: _eoq(float(r["demanda_anual"]), order_cost, float(r["unit_cost"]), holding_rate),
        axis=1,
    )
    out["valor_linea"] = out["current_stock"] * out["unit_cost"]
    out["gap_pedido"] = (out["punto_pedido"] - out["current_stock"]).clip(lower=0).astype(int)
    out["sugerencia_pedido"] = out.apply(
        lambda r: max(
            int(r["gap_pedido"]),
            max(0, int(r["eoq"]) - int(r["current_stock"])) if int(r["current_stock"]) < int(r["punto_pedido"]) else 0,
        ),
        axis=1,
    )
    out["_estado"] = out.apply(lambda r: _estado(r, int(r["punto_pedido"])), axis=1)
    total_val = out["valor_linea"].sum()
    out = out.sort_values("valor_linea", ascending=False).reset_index(drop=True)
    cum = out["valor_linea"].cumsum()
    cum_pct = cum / total_val if total_val > 0 else cum * 0
    out["clase_ABC"] = [ _abc_class(v, total_val, cp) for v, cp in zip(out["valor_linea"], cum_pct) ]
    out["pct_acum_valor"] = (cum_pct * 100).round(1)
    return out


def show() -> None:
    st.markdown(
        """
        <style>
        div.metric-card { background: linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);
          padding:1rem 1.25rem; border-radius:12px; border:1px solid #0f3460;
          box-shadow: 0 4px 14px rgba(0,0,0,.12); }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Centro de control de inventario")
    st.markdown(
        "Gestiona SKUs con **demanda por artículo**, **tiempo de entrega** y **proveedor**. "
        "El motor calcula **punto de pedido**, **stock de seguridad**, **EOQ**, **clase ABC** y **alertas**."
    )

    user = st.session_state.user
    if not user:
        st.warning("Inicia sesión para usar el módulo de inventario.")
        return

    uid = int(user["id"])
    db = _db()
    rows = db.list_inventory(uid)

    with st.expander("Parámetros de análisis logístico (aplican a EOQ, seguridad y cobertura)", expanded=not rows):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            demand_fallback = st.number_input(
                "Demanda diaria por defecto (SKU sin dato propio)",
                min_value=0.1,
                max_value=999.0,
                value=5.0,
                step=0.5,
                help="Si un artículo no tiene 'Demanda diaria' propia, se usa este valor para cobertura y ROP.",
            )
        with c2:
            order_cost = st.number_input(
                "Costo fijo por pedido ($)",
                min_value=1.0,
                max_value=50000.0,
                value=75.0,
                step=5.0,
                help="S en la fórmula EOQ = √(2DS/H).",
            )
        with c3:
            holding_rate = st.slider(
                "Tasa anual de mantenimiento (% del costo unitario)",
                min_value=5,
                max_value=60,
                value=25,
                help="H = costo unitario × este % anual.",
            )
            holding_rate_f = holding_rate / 100.0
        with c4:
            z_safety = st.slider(
                "Factor Z (servicio / stock de seguridad)",
                min_value=1.0,
                max_value=2.33,
                value=1.65,
                step=0.05,
                help="Mayor Z = más stock de seguridad ante la misma demanda y lead time.",
            )

    df_raw = pd.DataFrame(rows) if rows else pd.DataFrame()
    df = _build_analytics(df_raw, demand_fallback, order_cost, holding_rate_f, z_safety) if not df_raw.empty else df_raw

    tab_res, tab_ges, tab_adv = st.tabs(
        ["Resumen ejecutivo", "Gestión de artículos", "ABC · EOQ · Mapas y CSV"]
    )

    with tab_res:
        if df.empty:
            st.info(
                "Aún no hay artículos. Ve a **Gestión de artículos** para dar de alta SKUs "
                "o importa un CSV en la última pestaña."
            )
            return

        score, health_txt = _health_score(df)
        u_total = int(df["current_stock"].sum())
        valor = float(df["valor_linea"].sum())
        n_crit = int((df["_estado"] == "Crítico").sum())
        n_bajo = int(df["_estado"].str.contains("Bajo", na=False).sum())
        n_over = int((df["_estado"] == "Sobrestock").sum())
        cap_a = df[df["clase_ABC"] == "A"]["valor_linea"].sum()
        pct_a = (cap_a / valor * 100) if valor > 0 else 0

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Referencias activas", len(df))
        m2.metric("Unidades en stock", f"{u_total:,}")
        m3.metric("Valor inventario", f"${valor:,.0f}")
        m4.metric("Ítems clase A (valor)", f"{pct_a:.0f}% del capital")
        m5.metric("Críticos / bajo P. pedido", f"{n_crit} / {n_bajo}")
        m6.metric("Índice de salud", f"{score}/100")

        st.markdown(health_txt)
        if n_over:
            st.caption(f"Sobrestock detectado en **{n_over}** SKU(s): revisa política de máximos o promociones.")

        c1, c2 = st.columns((1.1, 1))
        with c1:
            fig_treemap = px.treemap(
                df,
                path=["category", "sku"],
                values="valor_linea",
                color="clase_ABC",
                color_discrete_map={"A": "#e94560", "B": "#0f3460", "C": "#533483"},
                title="Mapa de valor por categoría y SKU (tamaño = valor en inventario)",
            )
            fig_treemap.update_layout(height=520, margin=dict(t=40, l=0, r=0, b=0))
            st.plotly_chart(fig_treemap, use_container_width=True)

        with c2:
            top = df.nlargest(12, "valor_linea")
            fig_bar = px.bar(
                top,
                x="sku",
                y="valor_linea",
                color="clase_ABC",
                title="Top 12 SKUs por valor en inventario ($)",
                labels={"valor_linea": "Valor ($)", "sku": "SKU"},
                color_discrete_map={"A": "#e94560", "B": "#0f3460", "C": "#533483"},
            )
            fig_bar.update_layout(height=520, showlegend=True)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Prioridades sugeridas (acción)")
        urg = df[(df["_estado"] == "Crítico") | (df["_estado"].str.contains("Bajo", na=False))].copy()
        urg = urg.sort_values("valor_linea", ascending=False)
        if urg.empty:
            st.success("No hay SKUs por debajo del punto de pedido ni en mínimo crítico con la configuración actual.")
        else:
            for _, r in urg.head(15).iterrows():
                st.markdown(
                    f"- **{r['sku']}** — {r['name']}: stock **{int(r['current_stock'])}**, "
                    f"punto de pedido **{int(r['punto_pedido'])}**, sugerido **{int(r['sugerencia_pedido'])}** u., "
                    f"EOQ ref. **{int(r['eoq'])}**, cobertura **{r['cobertura_dias']}** d."
                )

    with tab_ges:
        st.subheader("Alta de artículo")
        with st.form("form_alta", clear_on_submit=True):
            r1, r2, r3 = st.columns(3)
            with r1:
                sku = st.text_input("SKU *", placeholder="ej. SKU-2024-001")
                name = st.text_input("Nombre descriptivo *", placeholder="Producto / presentación")
                supplier = st.text_input("Proveedor", placeholder="Nombre proveedor")
            with r2:
                category = st.text_input("Categoría", value="General")
                current = st.number_input("Stock físico actual", min_value=0, value=0, step=1)
                min_s = st.number_input("Stock mínimo (política)", min_value=0, value=10, step=1)
            with r3:
                max_s = st.number_input("Stock máximo / capacidad", min_value=0, value=200, step=1)
                unit = st.number_input("Costo unitario ($)", min_value=0.0, value=0.0, step=0.01)
                sale_price_add = st.number_input("Precio de venta ($)", min_value=0.0, value=0.0, step=0.01)
                daily = st.number_input(
                    "Demanda diaria esperada (opcional)",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    help="0 = usar demanda por defecto del panel superior solo para cálculos.",
                )
                lead = st.number_input("Lead time (días)", min_value=1, value=7, step=1)
            if st.form_submit_button("Registrar en base de datos", type="primary"):
                dd: Optional[float] = float(daily) if daily and daily > 0 else None
                ok, msg = db.add_inventory_item(
                    uid, sku, name, category, int(current), int(min_s), int(max_s), float(unit),
                    daily_demand=dd, lead_time_days=int(lead), supplier=supplier,
                    sale_price=float(sale_price_add),
                )
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

        st.divider()
        st.subheader("Edición rápida y eliminación")
        items = db.list_inventory(uid)
        if not items:
            st.info("No hay registros.")
        else:
            labels = {f"{r['sku']} — {r['name']} (id {r['id']})": r["id"] for r in items}
            pick = st.selectbox("Artículo a modificar", list(labels.keys()))
            rid = labels[pick]
            rec = next(r for r in items if r["id"] == rid)
            with st.form("form_edit"):
                a, b, c = st.columns(3)
                with a:
                    esku = st.text_input("SKU", value=rec["sku"], key="e_sku")
                    ename = st.text_input("Nombre", value=rec["name"], key="e_nm")
                    esup = st.text_input("Proveedor", value=rec.get("supplier") or "", key="e_sup")
                with b:
                    ecat = st.text_input("Categoría", value=rec["category"], key="e_cat")
                    est = st.number_input("Stock actual", value=int(rec["current_stock"]), min_value=0, key="e_st")
                    emn = st.number_input("Stock mínimo", value=int(rec["min_stock"]), min_value=0, key="e_mn")
                with c:
                    emx = st.number_input("Stock máximo", value=int(rec["max_stock"]), min_value=0, key="e_mx")
                    eun = st.number_input("Costo unitario", value=float(rec["unit_cost"]), min_value=0.0, key="e_un")
                    esp = st.number_input("Precio de venta ($)", value=float(rec.get("sale_price") or 0.0), min_value=0.0, key="e_sp")
                    edd = float(rec["daily_demand"]) if rec.get("daily_demand") not in (None, "") else 0.0
                    edaily = st.number_input("Demanda diaria (0=defecto global)", value=edd, min_value=0.0, step=0.1, key="e_dd")
                    elead = st.number_input("Lead time (días)", value=int(rec.get("lead_time_days") or 7), min_value=1, key="e_ld")
                colu, cold = st.columns(2)
                with colu:
                    save = st.form_submit_button("Guardar cambios", type="primary")
                with cold:
                    delete = st.form_submit_button("Eliminar artículo", type="secondary")
                if save:
                    dd2 = float(edaily) if edaily > 0 else None
                    ok, msg = db.update_inventory_item(
                        int(rid), uid, esku, ename, ecat, int(est), int(emn), int(emx), float(eun),
                        daily_demand=dd2, lead_time_days=int(elead), supplier=esup,
                        sale_price=float(esp),
                    )
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
                if delete:
                    ok, msg = db.delete_inventory_item(int(rid), uid)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

        st.divider()
        st.subheader("Vista tabla (edición masiva)")
        if not items:
            st.caption("Sin filas.")
        else:
            dfe = pd.DataFrame(items)
            cols = [
                "id", "sku", "name", "category", "supplier", "current_stock",
                "min_stock", "max_stock", "unit_cost", "sale_price", "daily_demand", "lead_time_days",
            ]
            dfe = dfe[[c for c in cols if c in dfe.columns]]
            edited = st.data_editor(
                dfe,
                use_container_width=True,
                num_rows="fixed",
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True, format="%d"),
                    "sku": st.column_config.TextColumn("SKU", required=True),
                    "name": st.column_config.TextColumn("Nombre", required=True),
                    "category": st.column_config.TextColumn("Categoría"),
                    "supplier": st.column_config.TextColumn("Proveedor"),
                    "current_stock": st.column_config.NumberColumn("Stock", min_value=0, step=1),
                    "min_stock": st.column_config.NumberColumn("Mín.", min_value=0, step=1),
                    "max_stock": st.column_config.NumberColumn("Máx.", min_value=0, step=1),
                    "unit_cost": st.column_config.NumberColumn("Costo u.", min_value=0.0, format="$%.2f"),
                    "sale_price": st.column_config.NumberColumn("Precio venta", min_value=0.0, format="$%.2f"),
                    "daily_demand": st.column_config.NumberColumn("Demanda/día", min_value=0.0, format="%.2f"),
                    "lead_time_days": st.column_config.NumberColumn("Lead (d)", min_value=1, step=1),
                },
                key="inv_bulk_editor",
            )
            if st.button("Persistir cambios de la tabla", type="primary"):
                err = []
                for _, r in edited.iterrows():
                    ddv = float(r["daily_demand"]) if pd.notna(r.get("daily_demand")) and float(r["daily_demand"]) > 0 else None
                    o, m = db.update_inventory_item(
                        int(r["id"]), uid, str(r["sku"]), str(r["name"]), str(r["category"]),
                        int(r["current_stock"]), int(r["min_stock"]), int(r["max_stock"]), float(r["unit_cost"]),
                        daily_demand=ddv,
                        lead_time_days=int(r["lead_time_days"]) if pd.notna(r.get("lead_time_days")) else 7,
                        supplier=str(r.get("supplier") or ""),
                        sale_price=float(r["sale_price"]) if pd.notna(r.get("sale_price")) else 0.0,
                    )
                    if not o:
                        err.append(m)
                if err:
                    for e in err[:12]:
                        st.error(e)
                else:
                    st.success("Tabla guardada correctamente.")
                    st.rerun()

    with tab_adv:
        if df.empty:
            st.info("Sin datos para análisis ABC/EOQ.")
            return

        f1, f2 = st.columns(2)
        with f1:
            cat_f = st.multiselect("Filtrar categoría", sorted(df["category"].unique().tolist()))
        with f2:
            abc_f = st.multiselect("Filtrar clase ABC", ["A", "B", "C"])

        dff = df.copy()
        if cat_f:
            dff = dff[dff["category"].isin(cat_f)]
        if abc_f:
            dff = dff[dff["clase_ABC"].isin(abc_f)]

        st.subheader("Clasificación ABC (por valor de inventario)")
        abc_sum = dff.groupby("clase_ABC", as_index=False).agg(
            skus=("sku", "count"),
            valor=("valor_linea", "sum"),
            unidades=("current_stock", "sum"),
        )
        abc_sum["% valor"] = (abc_sum["valor"] / abc_sum["valor"].sum() * 100).round(1)
        st.dataframe(abc_sum, use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            fig_abc = px.sunburst(
                dff,
                path=["clase_ABC", "category"],
                values="valor_linea",
                title="Distribución del valor: ABC → categoría",
            )
            st.plotly_chart(fig_abc, use_container_width=True)
        with c2:
            fig_sc = px.scatter(
                dff,
                x="current_stock",
                y="punto_pedido",
                size="valor_linea",
                color="_estado",
                hover_data=["sku", "name", "cobertura_dias", "eoq"],
                title="Stock actual vs punto de pedido (tamaño = valor)",
                labels={"current_stock": "Stock actual", "punto_pedido": "Punto de pedido"},
            )
            mx = max(float(dff["current_stock"].max()), 1.0)
            fig_sc.add_shape(
                type="line",
                line=dict(dash="dash", color="gray"),
                x0=0,
                y0=0,
                x1=mx * 1.05,
                y1=mx * 1.05,
            )
            st.plotly_chart(fig_sc, use_container_width=True)

        st.subheader("Tabla logística detallada")
        logistic_detail = dff[
            [
                "sku", "name", "category", "supplier", "current_stock", "min_stock", "max_stock",
                "unit_cost", "_daily", "_lead", "stock_seguridad", "punto_pedido", "eoq",
                "cobertura_dias", "sugerencia_pedido", "valor_linea", "clase_ABC", "_estado",
            ]
        ].rename(
            columns={
                "_daily": "Demanda/día (efectiva)",
                "_lead": "Lead (d)",
                "sugerencia_pedido": "Sugerido pedir (u.)",
                "valor_linea": "Valor ($)",
                "_estado": "Estado",
            }
        )
        st.dataframe(logistic_detail, use_container_width=True, hide_index=True, height=420)

        st.subheader("Cobertura vs valor (priorizar gestión)")
        fig_bub = px.scatter(
            dff,
            x="cobertura_dias",
            y="valor_linea",
            size="current_stock",
            color="clase_ABC",
            hover_name="sku",
            labels={"cobertura_dias": "Días de cobertura", "valor_linea": "Valor en inventario ($)"},
            title="SKUs con poca cobertura y alto valor arriba-izquierda son prioridad",
        )
        st.plotly_chart(fig_bub, use_container_width=True)

        st.subheader("Importar / exportar")
        e1, e2 = st.columns(2)
        with e1:
            csv_out = df_raw.to_csv(index=False).encode("utf-8") if not df_raw.empty else b""
            st.download_button(
                "Descargar inventario (CSV)",
                data=csv_out,
                file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                disabled=df_raw.empty,
            )
        with e2:
            up = st.file_uploader("CSV (columnas base + opcionales)", type=["csv"])
            st.caption(
                "Obligatorias: sku,name,category,current_stock,min_stock,max_stock,unit_cost. "
                "Opcionales: sale_price,daily_demand,lead_time_days,supplier"
            )
            if up is not None:
                raw = pd.read_csv(io.BytesIO(up.read()))
                raw.columns = [c.strip() for c in raw.columns]
                req = {"sku", "name", "category", "current_stock", "min_stock", "max_stock", "unit_cost"}
                miss = req - set(raw.columns)
                if miss:
                    st.error(f"Faltan columnas: {sorted(miss)}")
                elif st.button("Importar al inventario"):
                    okc, bad = 0, []
                    for _, r in raw.iterrows():
                        dd_imp = None
                        if "daily_demand" in raw.columns and pd.notna(r.get("daily_demand")):
                            try:
                                if float(r["daily_demand"]) > 0:
                                    dd_imp = float(r["daily_demand"])
                            except (TypeError, ValueError):
                                pass
                        ld = int(r["lead_time_days"]) if "lead_time_days" in raw.columns and pd.notna(r.get("lead_time_days")) else 7
                        sup = str(r["supplier"]) if "supplier" in raw.columns and pd.notna(r.get("supplier")) else ""
                        sp_imp = 0.0
                        if "sale_price" in raw.columns and pd.notna(r.get("sale_price")):
                            try:
                                sp_imp = float(r["sale_price"])
                            except (TypeError, ValueError):
                                pass
                        o, m = db.add_inventory_item(
                            uid,
                            str(r["sku"]),
                            str(r["name"]),
                            str(r["category"]),
                            int(r["current_stock"]),
                            int(r["min_stock"]),
                            int(r["max_stock"]),
                            float(r["unit_cost"]),
                            daily_demand=dd_imp,
                            lead_time_days=ld,
                            supplier=sup,
                            sale_price=sp_imp,
                        )
                        if o:
                            okc += 1
                        else:
                            bad.append(f"{r.get('sku')}: {m}")
                    st.success(f"Filas importadas: {okc}")
                    if bad:
                        st.warning("Algunas filas no se importaron:")
                        for b in bad[:25]:
                            st.text(b)
                    st.rerun()
