import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from database import Database


def _db() -> Database:
    return Database()


def show() -> None:
    st.title("💰 Registro de Ventas")
    st.markdown(
        "Registra tus ventas aquí. "
        "El inventario se **actualiza automáticamente** cada vez que guardas una venta."
    )

    user = st.session_state.get("user")
    if not user:
        st.warning("Inicia sesión para continuar.")
        return

    uid = int(user["id"])
    company_id = user.get("company_id")
    db = _db()

    tab_reg, tab_hist = st.tabs(["✏️ Registrar venta", "📋 Historial"])

    with tab_reg:
        _register_sale(db, uid, company_id)

    with tab_hist:
        _sales_history(db, uid)


def _register_sale(db: Database, uid: int, company_id) -> None:
    items = db.list_inventory(uid)
    if not items:
        st.info(
            "No tienes productos en inventario. "
            "Ve a **📦 Inventario** para cargar tus artículos primero."
        )
        return

    options = {
        f"{i['name']}"
        f"{' · ' + i['color'] if i.get('color') else ''}"
        f"  [{i['category']}]  — stock: {i['current_stock']}": i
        for i in items
    }

    with st.form("sale_form", clear_on_submit=True):
        st.subheader("Nueva venta")
        c1, c2 = st.columns(2)
        with c1:
            label    = st.selectbox("Producto *", list(options.keys()))
            selected = options[label]
            quantity = st.number_input("Cantidad *", min_value=1, value=1, step=1)
            unit_price = st.number_input(
                "Precio unitario de venta ($) *",
                min_value=0.01,
                value=float(selected["sale_price"]) if selected["sale_price"] > 0 else 1.0,
                step=0.01,
                format="%.2f",
            )
        with c2:
            route     = st.text_input("Ruta", placeholder="ej. Norte, Sur, Zona Centro")
            zone      = st.text_input("Zona / Ciudad", placeholder="ej. Caracas, Medellín")
            client    = st.text_input("Cliente", placeholder="Nombre o código")
            sale_date = st.date_input("Fecha de venta", value=date.today())

        total  = quantity * unit_price
        costo  = quantity * (selected["unit_cost"] or 0)
        margen = total - costo
        pct    = (margen / total * 100) if total > 0 else 0
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total venta",  f"${total:,.2f}")
        m2.metric("Costo total",  f"${costo:,.2f}")
        m3.metric("Ganancia",     f"${margen:,.2f}")
        m4.metric("Margen",       f"{pct:.1f}%")

        submit = st.form_submit_button(
            "✅ Registrar venta", type="primary", use_container_width=True
        )

    if submit:
        if quantity > selected["current_stock"]:
            st.error(f"Stock insuficiente. Disponible: **{selected['current_stock']}** unidades.")
        else:
            ok, msg = db.register_sale(
                user_id=uid,
                inventory_id=int(selected["id"]),
                quantity=int(quantity),
                unit_price=float(unit_price),
                route=route.strip(),
                zone=zone.strip(),
                client=client.strip(),
                sale_date=sale_date.isoformat(),
                company_id=company_id,
            )
            if ok:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")

    with st.expander("Ver stock actual del inventario"):
        df_inv = pd.DataFrame(items)[
            ["sku", "name", "category", "current_stock", "min_stock", "sale_price", "unit_cost"]
        ].copy()
        df_inv.columns = ["SKU", "Producto", "Categoría", "Stock", "Mínimo", "Precio venta", "Costo"]

        def _row_style(row):
            if row["Stock"] <= row["Mínimo"]:
                return ["background-color: #fee2e2"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df_inv.style.apply(_row_style, axis=1),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Filas en rojo = stock en o por debajo del mínimo.")


def _sales_history(db: Database, uid: int) -> None:
    col1, _ = st.columns([1, 3])
    with col1:
        days = st.selectbox(
            "Período",
            [7, 15, 30, 60, 90, 180],
            index=2,
            format_func=lambda x: f"Últimos {x} días",
        )

    sales = db.get_sales(uid, days=days)
    if not sales:
        st.info("No hay ventas registradas en este período.")
        return

    df = pd.DataFrame(sales)
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventas",          f"{len(df):,}")
    c2.metric("Ingresos totales", f"${df['total_revenue'].sum():,.2f}")
    c3.metric("Costo total",      f"${df['total_cost'].sum():,.2f}")
    c4.metric("Ganancia total",   f"${df['profit'].sum():,.2f}")

    daily = (
        df.groupby(df["sale_date"].dt.date)
        .agg(revenue=("total_revenue", "sum"), profit=("profit", "sum"))
        .reset_index()
    )
    daily.columns = ["fecha", "Ingresos", "Ganancia"]
    fig = px.line(
        daily, x="fecha", y=["Ingresos", "Ganancia"],
        title="Ingresos y ganancia por día",
        labels={"value": "$", "variable": "Métrica"},
        color_discrete_map={"Ingresos": "#667eea", "Ganancia": "#48bb78"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detalle de ventas")
    show_cols = ["sale_date", "sku", "product_name", "quantity",
                 "unit_price", "route", "zone", "client", "total_revenue", "profit"]
    show_cols = [c for c in show_cols if c in df.columns]
    renamed = {
        "sale_date": "Fecha", "sku": "SKU", "product_name": "Producto",
        "quantity": "Cant.", "unit_price": "Precio u.", "route": "Ruta",
        "zone": "Zona", "client": "Cliente",
        "total_revenue": "Ingreso ($)", "profit": "Ganancia ($)",
    }
    st.dataframe(df[show_cols].rename(columns=renamed), use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV", data=csv,
                       file_name=f"ventas_{days}d.csv", mime="text/csv")
