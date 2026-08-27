"""Dashboard interactivo de ventas retail - Streamlit + Docker.

Actividad 1: Introduccion a Docker y Uso de Contenedores.
Ejecutar local:  streamlit run app.py
Ejecutar Docker: docker run -p 8501:8501 dashboard-ventas
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

RUTA_DATOS = Path(__file__).parent / "data" / "ventas_retail.csv"
PALETA = ["#2E86AB", "#F6511D", "#7FB800", "#FFB400", "#A23B72", "#00A6A6"]

st.set_page_config(
    page_title="Dashboard de Ventas Retail",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; padding-bottom: 2rem;}
      [data-testid="stMetric"] {
        background: rgba(128,128,128,.08);
        border: 1px solid rgba(128,128,128,.20);
        border-radius: .6rem; padding: .8rem 1rem;
      }
      [data-testid="stMetricLabel"] p {font-size:.82rem; opacity:.85;}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Carga de datos
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner="Cargando dataset...")
def cargar_datos(ruta: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta, parse_dates=["fecha"])
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.to_period("M").dt.to_timestamp()
    df["nombre_mes"] = df["fecha"].dt.month
    df["dia_semana"] = df["fecha"].dt.dayofweek
    df["semana"] = df["fecha"].dt.isocalendar().week.astype(int)
    return df


@st.cache_data
def a_csv(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


if not RUTA_DATOS.exists():
    st.error(f"No se encontro el dataset en {RUTA_DATOS}. Ejecuta: python data/generar_dataset.py")
    st.stop()

datos = cargar_datos(RUTA_DATOS)

# --------------------------------------------------------------------------- #
# Sidebar: filtros interactivos
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.title("🎛️ Filtros")

    fmin, fmax = datos["fecha"].min().date(), datos["fecha"].max().date()
    rango = st.date_input("Rango de fechas", value=(fmin, fmax), min_value=fmin, max_value=fmax)
    if isinstance(rango, tuple) and len(rango) == 2:
        desde, hasta = rango
    else:
        desde, hasta = fmin, fmax

    categorias = st.multiselect(
        "Categoria", sorted(datos["categoria"].unique()), default=sorted(datos["categoria"].unique())
    )
    regiones = st.multiselect(
        "Region", sorted(datos["region"].unique()), default=sorted(datos["region"].unique())
    )
    canales = st.multiselect(
        "Canal de venta", sorted(datos["canal"].unique()), default=sorted(datos["canal"].unique())
    )
    segmentos = st.multiselect(
        "Segmento de cliente", sorted(datos["segmento_cliente"].unique()),
        default=sorted(datos["segmento_cliente"].unique()),
    )

    st.divider()
    ticket_min, ticket_max = float(datos["ingreso"].min()), float(datos["ingreso"].max())
    ticket = st.slider(
        "Ticket (S/)", ticket_min, ticket_max, (ticket_min, ticket_max), step=10.0, format="S/ %.0f"
    )
    incluir_devueltos = st.toggle("Incluir ventas devueltas", value=True)
    granularidad = st.radio(
        "Granularidad temporal", ["Diaria", "Semanal", "Mensual"], index=2, horizontal=True
    )

    st.divider()
    st.caption("Dataset sintetico de 12.000 transacciones (2023-2025) generado con data/generar_dataset.py")

mascara = (
    datos["fecha"].between(pd.Timestamp(desde), pd.Timestamp(hasta))
    & datos["categoria"].isin(categorias)
    & datos["region"].isin(regiones)
    & datos["canal"].isin(canales)
    & datos["segmento_cliente"].isin(segmentos)
    & datos["ingreso"].between(*ticket)
)
if not incluir_devueltos:
    mascara &= ~datos["devuelto"]

df = datos.loc[mascara].copy()

st.title("📊 Dashboard de Ventas Retail")
st.caption(
    f"Periodo {desde:%d/%m/%Y} - {hasta:%d/%m/%Y}  ·  {len(df):,} de {len(datos):,} transacciones"
)

if df.empty:
    st.warning("Ningun registro cumple los filtros seleccionados. Ajusta los criterios en la barra lateral.")
    st.stop()


# --------------------------------------------------------------------------- #
# KPIs con comparativo contra el periodo anterior de igual duracion
# --------------------------------------------------------------------------- #
dias_periodo = (pd.Timestamp(hasta) - pd.Timestamp(desde)).days + 1
prev_hasta = pd.Timestamp(desde) - pd.Timedelta(days=1)
prev_desde = prev_hasta - pd.Timedelta(days=dias_periodo - 1)
mascara_prev = (
    datos["fecha"].between(prev_desde, prev_hasta)
    & datos["categoria"].isin(categorias)
    & datos["region"].isin(regiones)
    & datos["canal"].isin(canales)
    & datos["segmento_cliente"].isin(segmentos)
)
df_prev = datos.loc[mascara_prev]


def delta(actual: float, previo: float) -> str | None:
    """Variacion porcentual contra el periodo previo; None si no hay base."""
    if not previo or pd.isna(previo):
        return None
    return f"{(actual - previo) / previo * 100:+.1f}% vs periodo previo"


ingresos = df["ingreso"].sum()
utilidad = df["utilidad"].sum()
ticket_prom = df["ingreso"].mean()
unidades = int(df["cantidad"].sum())
tasa_dev = df["devuelto"].mean() * 100

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Ingresos", f"S/ {ingresos:,.0f}", delta(ingresos, df_prev["ingreso"].sum()))
k2.metric("Utilidad", f"S/ {utilidad:,.0f}", delta(utilidad, df_prev["utilidad"].sum()))
k3.metric("Margen", f"{utilidad / ingresos * 100:.1f}%")
k4.metric("Ticket promedio", f"S/ {ticket_prom:,.0f}", delta(ticket_prom, df_prev["ingreso"].mean()))
k5.metric("Unidades vendidas", f"{unidades:,}", f"{tasa_dev:.1f}% devuelto", delta_color="inverse")

st.divider()

tab_evo, tab_prod, tab_geo, tab_clientes, tab_datos = st.tabs(
    ["📈 Evolucion", "🏷️ Productos", "🗺️ Territorio", "👥 Clientes", "🔎 Datos"]
)

FREQ = {"Diaria": "D", "Semanal": "W-MON", "Mensual": "MS"}[granularidad]

# --------------------------------------------------------------------------- #
# Tab 1: evolucion temporal + proyeccion
# --------------------------------------------------------------------------- #
with tab_evo:
    serie = (
        df.set_index("fecha")
        .resample(FREQ)
        .agg(ingreso=("ingreso", "sum"), utilidad=("utilidad", "sum"), ventas=("id_venta", "count"))
        .reset_index()
    )
    ventana = {"Diaria": 30, "Semanal": 8, "Mensual": 3}[granularidad]
    serie["media_movil"] = serie["ingreso"].rolling(ventana, min_periods=1).mean()

    col_a, col_b = st.columns([3, 1])
    with col_b:
        proyectar = st.toggle(
            "Proyeccion lineal", value=True,
            help="Regresion de minimos cuadrados sobre la serie filtrada.",
        )
        horizonte = st.number_input("Periodos a proyectar", 1, 12, 3, disabled=not proyectar)
        mostrar_utilidad = st.checkbox("Superponer utilidad", value=True)

    fig = go.Figure()
    fig.add_bar(x=serie["fecha"], y=serie["ingreso"], name="Ingresos", marker_color=PALETA[0], opacity=.75)
    fig.add_scatter(
        x=serie["fecha"], y=serie["media_movil"], name=f"Media movil ({ventana})",
        line=dict(color=PALETA[1], width=3),
    )
    if mostrar_utilidad:
        fig.add_scatter(
            x=serie["fecha"], y=serie["utilidad"], name="Utilidad",
            line=dict(color=PALETA[2], width=2, dash="dot"),
        )

    if proyectar and len(serie) >= 3:
        x = np.arange(len(serie))
        pendiente, intercepto = np.polyfit(x, serie["ingreso"], 1)
        futuro_x = np.arange(len(serie), len(serie) + int(horizonte))
        paso = serie["fecha"].diff().median()
        futuro_fechas = [serie["fecha"].iloc[-1] + paso * (i + 1) for i in range(int(horizonte))]
        fig.add_scatter(
            x=[serie["fecha"].iloc[-1]] + futuro_fechas,
            y=np.concatenate([[serie["ingreso"].iloc[-1]], pendiente * futuro_x + intercepto]),
            name="Proyeccion", line=dict(color=PALETA[4], width=3, dash="dash"),
        )
        tendencia = "creciente" if pendiente > 0 else "decreciente"
        st.info(f"Tendencia **{tendencia}**: S/ {pendiente:,.0f} por periodo ({granularidad.lower()}).")

    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(t=30, b=0, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        yaxis_title="Soles (S/)", xaxis_title=None,
    )
    col_a.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    calor = (
        df.groupby(["dia_semana", "nombre_mes"], as_index=False)["ingreso"].sum()
        .pivot(index="dia_semana", columns="nombre_mes", values="ingreso")
    )
    dias = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    calor.index = [dias[i] for i in calor.index]
    fig_calor = px.imshow(
        calor, aspect="auto", color_continuous_scale="Blues",
        labels=dict(x="Mes", y="Dia", color="Ingresos"),
        title="Estacionalidad: dia de semana vs mes",
    )
    fig_calor.update_layout(height=330, margin=dict(t=50, b=0, l=0, r=0))
    c1.plotly_chart(fig_calor, use_container_width=True)

    mix = df.groupby([pd.Grouper(key="fecha", freq=FREQ), "canal"], as_index=False)["ingreso"].sum()
    fig_mix = px.area(
        mix, x="fecha", y="ingreso", color="canal", color_discrete_sequence=PALETA,
        title="Mix de ingresos por canal", groupnorm="percent",
    )
    fig_mix.update_layout(
        height=330, margin=dict(t=50, b=0, l=0, r=0), yaxis_title="% de ingresos", xaxis_title=None
    )
    c2.plotly_chart(fig_mix, use_container_width=True)

# --------------------------------------------------------------------------- #
# Tab 2: productos
# --------------------------------------------------------------------------- #
with tab_prod:
    top_n = st.slider("Top N productos", 5, 20, 10)
    prod = (
        df.groupby(["categoria", "producto"], as_index=False)
        .agg(ingreso=("ingreso", "sum"), utilidad=("utilidad", "sum"), unidades=("cantidad", "sum"))
        .sort_values("ingreso", ascending=False)
    )

    c1, c2 = st.columns([1.2, 1])
    fig_top = px.bar(
        prod.head(top_n).sort_values("ingreso"), x="ingreso", y="producto", color="categoria",
        orientation="h", color_discrete_sequence=PALETA,
        title=f"Top {top_n} productos por ingresos", text_auto=".2s",
    )
    fig_top.update_layout(
        height=460, margin=dict(t=50, b=0, l=0, r=0), yaxis_title=None, xaxis_title="Soles (S/)"
    )
    c1.plotly_chart(fig_top, use_container_width=True)

    fig_sun = px.sunburst(
        prod, path=["categoria", "producto"], values="ingreso",
        color="categoria", color_discrete_sequence=PALETA,
        title="Composicion por categoria y producto",
    )
    fig_sun.update_layout(height=460, margin=dict(t=50, b=0, l=0, r=0))
    c2.plotly_chart(fig_sun, use_container_width=True)

    # Pareto 80/20
    pareto = prod.sort_values("ingreso", ascending=False).copy()
    pareto["acumulado"] = pareto["ingreso"].cumsum() / pareto["ingreso"].sum() * 100
    fig_par = go.Figure()
    fig_par.add_bar(x=pareto["producto"], y=pareto["ingreso"], name="Ingresos", marker_color=PALETA[0])
    fig_par.add_scatter(
        x=pareto["producto"], y=pareto["acumulado"], name="% acumulado", yaxis="y2",
        line=dict(color=PALETA[1], width=3),
    )
    fig_par.add_hline(y=80, line_dash="dash", line_color="gray", yref="y2")
    fig_par.update_layout(
        title="Analisis de Pareto (regla 80/20)", height=440,
        yaxis=dict(title="Soles (S/)"),
        yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0, 105]),
        margin=dict(t=50, b=0, l=0, r=0),
        legend=dict(orientation="h", y=1.02, yanchor="bottom"),
    )
    st.plotly_chart(fig_par, use_container_width=True)
    criticos = int((pareto["acumulado"] <= 80).sum()) + 1
    st.success(f"**{criticos}** de **{len(pareto)}** productos concentran el 80% de los ingresos.")

# --------------------------------------------------------------------------- #
# Tab 3: territorio
# --------------------------------------------------------------------------- #
with tab_geo:
    geo = (
        df.groupby(["region", "ciudad"], as_index=False)
        .agg(
            ingreso=("ingreso", "sum"), utilidad=("utilidad", "sum"),
            ventas=("id_venta", "count"), satisfaccion=("satisfaccion", "mean"),
            envio=("dias_envio", "mean"),
        )
    )
    geo["margen_pct"] = geo["utilidad"] / geo["ingreso"] * 100

    c1, c2 = st.columns(2)
    fig_tree = px.treemap(
        geo, path=["region", "ciudad"], values="ingreso", color="margen_pct",
        color_continuous_scale="RdYlGn",
        title="Ingresos por region y ciudad (color = margen %)",
    )
    fig_tree.update_layout(height=430, margin=dict(t=50, b=0, l=0, r=0))
    c1.plotly_chart(fig_tree, use_container_width=True)

    fig_disp = px.scatter(
        geo, x="ventas", y="ingreso", size="ingreso", color="region",
        hover_name="ciudad", color_discrete_sequence=PALETA, size_max=55,
        title="Volumen de transacciones vs ingresos por ciudad",
        labels={"ventas": "N. de transacciones", "ingreso": "Ingresos (S/)"},
    )
    fig_disp.update_layout(height=430, margin=dict(t=50, b=0, l=0, r=0))
    c2.plotly_chart(fig_disp, use_container_width=True)

    st.subheader("Tabla comparativa por ciudad")
    st.dataframe(
        geo.sort_values("ingreso", ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            "ingreso": st.column_config.ProgressColumn(
                "Ingresos", format="S/ %.0f", max_value=float(geo["ingreso"].max())
            ),
            "utilidad": st.column_config.NumberColumn("Utilidad", format="S/ %.0f"),
            "margen_pct": st.column_config.NumberColumn("Margen", format="%.1f%%"),
            "satisfaccion": st.column_config.NumberColumn("Satisfaccion", format="%.2f"),
            "envio": st.column_config.NumberColumn("Dias envio", format="%.1f"),
            "ventas": st.column_config.NumberColumn("Transacciones", format="%d"),
        },
    )

# --------------------------------------------------------------------------- #
# Tab 4: clientes
# --------------------------------------------------------------------------- #
with tab_clientes:
    c1, c2, c3 = st.columns(3)

    seg = df.groupby("segmento_cliente", as_index=False)["ingreso"].sum()
    fig_seg = px.pie(
        seg, names="segmento_cliente", values="ingreso", hole=.55,
        color_discrete_sequence=PALETA, title="Ingresos por segmento",
    )
    fig_seg.update_layout(height=350, margin=dict(t=50, b=0, l=0, r=0))
    c1.plotly_chart(fig_seg, use_container_width=True)

    pago = df.groupby("metodo_pago", as_index=False).agg(ingreso=("ingreso", "sum"))
    fig_pago = px.bar(
        pago.sort_values("ingreso"), x="ingreso", y="metodo_pago", orientation="h",
        color_discrete_sequence=[PALETA[5]], title="Ingresos por metodo de pago", text_auto=".2s",
    )
    fig_pago.update_layout(height=350, margin=dict(t=50, b=0, l=0, r=0), yaxis_title=None, xaxis_title=None)
    c2.plotly_chart(fig_pago, use_container_width=True)

    sat = df.groupby(["canal", "satisfaccion"], as_index=False)["id_venta"].count()
    fig_sat = px.bar(
        sat, x="satisfaccion", y="id_venta", color="canal", barmode="group",
        color_discrete_sequence=PALETA, title="Satisfaccion por canal",
        labels={"id_venta": "Transacciones", "satisfaccion": "Puntaje"},
    )
    fig_sat.update_layout(height=350, margin=dict(t=50, b=0, l=0, r=0))
    c3.plotly_chart(fig_sat, use_container_width=True)

    st.subheader("Efecto del descuento sobre la utilidad")
    muestra = df.sample(min(3000, len(df)), random_state=7)
    fig_desc = px.scatter(
        muestra, x="descuento", y="utilidad", color="categoria",
        color_discrete_sequence=PALETA, opacity=.55,
        labels={"descuento": "Descuento aplicado", "utilidad": "Utilidad (S/)"},
    )
    fig_desc.update_layout(height=430, margin=dict(t=20, b=0, l=0, r=0))
    st.plotly_chart(fig_desc, use_container_width=True)

    corr = df[
        ["precio_unitario", "cantidad", "descuento", "ingreso", "utilidad", "satisfaccion", "dias_envio"]
    ].corr()
    fig_corr = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        title="Matriz de correlacion entre variables numericas",
    )
    fig_corr.update_layout(height=470, margin=dict(t=50, b=0, l=0, r=0))
    st.plotly_chart(fig_corr, use_container_width=True)

# --------------------------------------------------------------------------- #
# Tab 5: datos crudos
# --------------------------------------------------------------------------- #
with tab_datos:
    busqueda = st.text_input(
        "Buscar producto, ciudad o id de venta", placeholder="Ej. Laptop, Cusco, V101234"
    )
    vista = df.drop(columns=["anio", "mes", "nombre_mes", "dia_semana", "semana"])
    if busqueda:
        patron = busqueda.strip()
        vista = vista[
            vista["producto"].str.contains(patron, case=False, na=False, regex=False)
            | vista["ciudad"].str.contains(patron, case=False, na=False, regex=False)
            | vista["id_venta"].str.contains(patron, case=False, na=False, regex=False)
        ]

    st.caption(f"{len(vista):,} registros")
    st.dataframe(vista, use_container_width=True, hide_index=True, height=420)

    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇️ Descargar seleccion (CSV)", a_csv(vista), file_name="ventas_filtradas.csv",
        mime="text/csv", use_container_width=True,
    )
    resumen = (
        df.groupby(["categoria", "canal"], as_index=False)
        .agg(ingreso=("ingreso", "sum"), utilidad=("utilidad", "sum"), ventas=("id_venta", "count"))
    )
    c2.download_button(
        "⬇️ Descargar resumen agregado (CSV)", a_csv(resumen),
        file_name="resumen_categoria_canal.csv", mime="text/csv", use_container_width=True,
    )

    with st.expander("Estadisticas descriptivas"):
        st.dataframe(df.describe().T, use_container_width=True)

st.divider()
st.caption("Actividad 1 - Streamlit + Docker + Killercoda")
