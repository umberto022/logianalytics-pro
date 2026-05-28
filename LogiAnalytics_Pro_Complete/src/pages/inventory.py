from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from database import Database


def _db() -> Database:
    return Database()


_STATUS_COLOR = {"🔴 Crítico": "#ef4444", "🟡 Bajo": "#f59e0b", "🟢 Óptimo": "#10b981"}

_CSS = """
<style>
.stock-crit {
    background: linear-gradient(90deg,#7f1d1d,#991b1b);
    border-left: 4px solid #ef4444;
    border-radius: 8px; padding: .6rem 1rem; margin-bottom: .35rem;
    color: #fecaca; font-size: .88rem;
}
.stock-warn {
    background: linear-gradient(90deg,#78350f,#92400e);
    border-left: 4px solid #f59e0b;
    border-radius: 8px; padding: .6rem 1rem; margin-bottom: .35rem;
    color: #fde68a; font-size: .88rem;
}
</style>
"""


def _status(row: dict) -> str:
    c, mn, mx = int(row["current_stock"]), int(row["min_stock"]), int(row["max_stock"])
    if c <= mn:
        return "🔴 Crítico"
    if mx > mn and c <= mn + max(1, int((mx - mn) * 0.25)):
        return "🟡 Bajo"
    return "🟢 Óptimo"


def show() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.title("📦 Inventario")

    user = st.session_state.get("user")
    if not user:
        st.warning("Inicia sesión para continuar.")
        return

    uid = int(user["id"])
    company_id = user.get("company_id")
    db = _db()
    items = db.list_inventory(uid)

    tab_list, tab_add, tab_import = st.tabs([
        "📋 Mis productos",
        "➕ Agregar producto",
        "📤 Importar / Exportar",
    ])

    with tab_list:
        _product_list(db, uid, items)

    with tab_add:
        _add_form(db, uid, company_id)

    with tab_import:
        _import_export(db, uid, items)


# ─────────────────────────────── PRODUCT LIST ─────────────────────────────────

def _product_list(db: Database, uid: int, items: list) -> None:
    if not items:
        st.info("Aún no tienes productos. Ve a **➕ Agregar producto** para empezar.")
        return

    df = pd.DataFrame(items)
    df["estado"] = df.apply(_status, axis=1)

    # KPIs
    n_crit = (df["estado"] == "🔴 Crítico").sum()
    n_low  = (df["estado"] == "🟡 Bajo").sum()
    total_u = int(df["current_stock"].sum())
    total_v = (df["current_stock"] * df["unit_cost"]).sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Productos", len(df))
    c2.metric("Unidades en stock", f"{total_u:,}")
    c3.metric("Valor del inventario", f"${total_v:,.2f}")
    c4.metric("Alertas de stock", f"{n_crit} críticos  {n_low} bajos",
              delta_color="inverse" if n_crit + n_low > 0 else "normal")

    # Alerts
    alerts = df[df["estado"] != "🟢 Óptimo"].sort_values("estado")
    if not alerts.empty:
        with st.expander(f"⚠️ {len(alerts)} producto(s) con stock bajo", expanded=n_crit > 0):
            for _, r in alerts.iterrows():
                cls = "stock-crit" if r["estado"] == "🔴 Crítico" else "stock-warn"
                st.markdown(
                    f'<div class="{cls}">'
                    f'<b>{r["name"]}</b>'
                    f'{" · " + r["color"] if r.get("color") else ""}'
                    f' — stock: <b>{int(r["current_stock"])}</b> '
                    f'/ mín: {int(r["min_stock"])} / máx: {int(r["max_stock"])}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # Filter bar
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        tipos = ["Todos"] + sorted(df["category"].dropna().unique().tolist())
        tipo_f = st.selectbox("Tipo", tipos, key="inv_tipo")
    with col_f2:
        colores = ["Todos"] + sorted(df["color"].dropna().replace("", pd.NA).dropna().unique().tolist())
        color_f = st.selectbox("Color", colores, key="inv_color")
    with col_f3:
        estado_f = st.selectbox("Estado", ["Todos","🔴 Crítico","🟡 Bajo","🟢 Óptimo"], key="inv_est")

    dff = df.copy()
    if tipo_f   != "Todos": dff = dff[dff["category"] == tipo_f]
    if color_f  != "Todos": dff = dff[dff["color"]    == color_f]
    if estado_f != "Todos": dff = dff[dff["estado"]   == estado_f]

    # Table
    show_cols = ["name","category","color","current_stock","min_stock","max_stock",
                 "unit_cost","sale_price","estado","supplier","updated_at"]
    show_cols = [c for c in show_cols if c in dff.columns]
    renamed = {
        "name":"Producto","category":"Tipo","color":"Color",
        "current_stock":"Stock","min_stock":"Mín","max_stock":"Máx",
        "unit_cost":"Costo ($)","sale_price":"Precio venta ($)",
        "estado":"Estado","supplier":"Proveedor","updated_at":"Actualizado",
    }
    st.dataframe(
        dff[show_cols].rename(columns=renamed),
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "Stock": st.column_config.ProgressColumn(
                "Stock", min_value=0,
                max_value=int(dff["max_stock"].max()) if not dff.empty else 100,
                format="%d",
            ),
        },
    )

    # Inline edit / delete
    st.markdown("---")
    st.subheader("Editar o eliminar producto")
    labels = {f"{r['name']}  ({r['category']} · {r['color'] or 'sin color'})  — stock {r['current_stock']}": r
              for r in items}
    pick = st.selectbox("Selecciona un producto", list(labels.keys()), key="inv_pick")
    rec  = labels[pick]

    with st.form("edit_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            e_name  = st.text_input("Producto *", value=rec["name"])
            e_tipo  = st.text_input("Tipo", value=rec["category"])
            e_color = st.text_input("Color", value=rec.get("color") or "")
        with c2:
            e_stock = st.number_input("Stock actual", value=int(rec["current_stock"]), min_value=0)
            e_min   = st.number_input("Stock mínimo", value=int(rec["min_stock"]),     min_value=0)
            e_max   = st.number_input("Stock máximo", value=int(rec["max_stock"]),     min_value=0)
        with c3:
            e_cost  = st.number_input("Costo unitario ($)",  value=float(rec["unit_cost"]),  min_value=0.0, step=0.01, format="%.2f")
            e_price = st.number_input("Precio de venta ($)", value=float(rec["sale_price"]), min_value=0.0, step=0.01, format="%.2f")
            e_sup   = st.text_input("Proveedor", value=rec.get("supplier") or "")

        ca, cb = st.columns(2)
        with ca:
            save   = st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
        with cb:
            delete = st.form_submit_button("🗑️ Eliminar", type="secondary", use_container_width=True)

    if save:
        if not e_name:
            st.error("El nombre del producto es obligatorio.")
        else:
            ok, msg = db.update_inventory_item(
                int(rec["id"]), uid, rec["sku"], e_name, e_tipo,
                int(e_stock), int(e_min), int(e_max), float(e_cost),
                supplier=e_sup, sale_price=float(e_price), color=e_color,
            )
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    if delete:
        ok, msg = db.delete_inventory_item(int(rec["id"]), uid)
        (st.success if ok else st.error)(msg)
        if ok:
            st.rerun()

    # Stock bar chart
    if not dff.empty:
        st.markdown("---")
        fig = px.bar(
            dff.sort_values("current_stock", ascending=False),
            x="name", y="current_stock",
            color="estado",
            color_discrete_map={k: v for k, v in _STATUS_COLOR.items()},
            text="current_stock",
            labels={"name": "Producto", "current_stock": "Unidades", "estado": "Estado"},
            title="Stock por producto",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1", height=340,
            margin=dict(t=40, l=0, r=0, b=0),
            xaxis_tickangle=-35,
        )
        fig.update_yaxes(showgrid=True, gridcolor="#1e293b")
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────── ADD FORM ─────────────────────────────────────

def _add_form(db: Database, uid: int, company_id) -> None:
    st.subheader("Registrar nuevo producto")

    with st.form("add_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name  = st.text_input("Producto *", placeholder="ej. Camiseta manga corta")
            tipo  = st.text_input("Tipo *",     placeholder="ej. Ropa, Electrónico, Repuesto")
            color = st.text_input("Color",      placeholder="ej. Rojo, Azul, Negro")
        with c2:
            stock = st.number_input("Stock inicial", min_value=0, value=0, step=1)
            s_min = st.number_input("Stock mínimo",  min_value=0, value=5,  step=1,
                                    help="Alerta cuando el stock llegue a este número")
            s_max = st.number_input("Stock máximo",  min_value=0, value=100, step=1,
                                    help="Capacidad máxima de almacenamiento")
        with c3:
            cost  = st.number_input("Costo unitario ($)",  min_value=0.0, value=0.0, step=0.01, format="%.2f")
            price = st.number_input("Precio de venta ($)", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            sup   = st.text_input("Proveedor", placeholder="Nombre del proveedor")

        # Auto-generate SKU preview
        if name and tipo:
            sku_preview = f"{tipo[:3].upper()}-{name[:4].upper()}-{datetime.now().strftime('%m%d')}"
        else:
            sku_preview = "—"
        st.caption(f"SKU asignado automáticamente: **{sku_preview}**")

        submit = st.form_submit_button("➕ Agregar al inventario", type="primary",
                                       use_container_width=True)

    if submit:
        if not name or not tipo:
            st.error("Producto y Tipo son obligatorios.")
        else:
            sku = f"{tipo[:3].upper()}-{name[:4].upper()}-{datetime.now().strftime('%m%d%H%M%S')}"
            ok, msg = db.add_inventory_item(
                uid, sku, name, tipo, int(stock), int(s_min), int(s_max),
                float(cost), supplier=sup, sale_price=float(price),
                color=color, company_id=company_id,
            )
            if ok:
                st.success(f"✅ **{name}** agregado al inventario.")
                st.rerun()
            else:
                st.error(msg)


# ─────────────────────────────── IMPORT / EXPORT ──────────────────────────────

def _import_export(db: Database, uid: int, items: list) -> None:
    col_exp, col_imp = st.columns(2)

    with col_exp:
        st.subheader("📥 Exportar")
        if items:
            df_exp = pd.DataFrame(items)[[
                "sku","name","category","color","current_stock",
                "min_stock","max_stock","unit_cost","sale_price","supplier",
            ]].rename(columns={
                "sku":"sku","name":"producto","category":"tipo","color":"color",
                "current_stock":"stock","min_stock":"stock_minimo",
                "max_stock":"stock_maximo","unit_cost":"costo",
                "sale_price":"precio_venta","supplier":"proveedor",
            })
            csv = df_exp.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Descargar inventario (CSV)",
                data=csv,
                file_name=f"inventario_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("Aún no hay productos para exportar.")

    with col_imp:
        st.subheader("📤 Importar CSV")
        st.caption(
            "Columnas **obligatorias**: `producto`, `tipo`, `stock`, `stock_minimo`, `stock_maximo`  \n"
            "Columnas opcionales: `color`, `costo`, `precio_venta`, `proveedor`"
        )
        template = "producto,tipo,color,stock,stock_minimo,stock_maximo,costo,precio_venta,proveedor\n"
        template += "Camiseta Roja,Ropa,Rojo,50,10,200,5.00,12.00,Proveedor A\n"
        template += "Zapato Deportivo,Calzado,Negro,30,5,100,20.00,55.00,Proveedor B\n"
        st.download_button(
            "⬇️ Descargar plantilla",
            data=template.encode("utf-8"),
            file_name="plantilla_inventario.csv",
            mime="text/csv",
            use_container_width=True,
        )

        up = st.file_uploader("Sube tu archivo CSV", type=["csv"])
        if up is not None:
            try:
                raw = pd.read_csv(io.BytesIO(up.read()))
                raw.columns = [c.strip().lower() for c in raw.columns]
                req = {"producto", "tipo", "stock", "stock_minimo", "stock_maximo"}
                miss = req - set(raw.columns)
                if miss:
                    st.error(f"Faltan columnas: {sorted(miss)}")
                else:
                    st.write(f"Vista previa — {len(raw)} filas:")
                    st.dataframe(raw.head(5), use_container_width=True, hide_index=True)
                    if st.button("✅ Importar al inventario", type="primary",
                                 use_container_width=True):
                        ok_c, bad = 0, []
                        for _, r in raw.iterrows():
                            name_v  = str(r["producto"])
                            tipo_v  = str(r["tipo"])
                            color_v = str(r.get("color") or "")
                            stk     = int(r["stock"])
                            mn      = int(r["stock_minimo"])
                            mx      = int(r["stock_maximo"])
                            cost_v  = float(r["costo"])        if "costo"        in raw.columns and pd.notna(r.get("costo"))        else 0.0
                            price_v = float(r["precio_venta"]) if "precio_venta" in raw.columns and pd.notna(r.get("precio_venta")) else 0.0
                            sup_v   = str(r["proveedor"])      if "proveedor"    in raw.columns and pd.notna(r.get("proveedor"))     else ""
                            sku_v   = f"{tipo_v[:3].upper()}-{name_v[:4].upper()}-{datetime.now().strftime('%m%d%H%M%S')}{ok_c}"
                            o, m = db.add_inventory_item(
                                uid, sku_v, name_v, tipo_v, stk, mn, mx,
                                cost_v, supplier=sup_v, sale_price=price_v,
                                color=color_v, company_id=None,
                            )
                            if o: ok_c += 1
                            else: bad.append(f"{name_v}: {m}")
                        st.success(f"✅ {ok_c} producto(s) importados.")
                        if bad:
                            st.warning("Algunos no se importaron: " + " | ".join(bad[:5]))
                        st.rerun()
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")
