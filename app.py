import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient

# ==========================================================
# TABLERO STREAMLIT - DIGITALIZACIÓN DE PLANTAS PRODUCTIVAS
# ==========================================================

# --- Configuración InfluxDB ---
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUXDB_TOKEN = "JcKXoXE30JQvV9Ggb4-zv6sQc0Zh6B6Haz5eMRW0FrJEduG2KcFJN9-7RoYvVORcFgtrHR-Q_ly-52pD7IC6JQ=="
INFLUXDB_ORG = "0925ccf91ab36478"
INFLUXDB_BUCKET = "EXTREME_MANUFACTURING"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()

# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def build_query(measurement: str, fields: list, start_time: str, stop_time: str):
    """Construye dinámicamente la consulta Flux."""
    fields_filter = " or ".join([f'r._field == "{f}"' for f in fields])
    return f"""
from(bucket: "{INFLUXDB_BUCKET}")
  |> range(start: {start_time}, stop: {stop_time})
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> filter(fn: (r) => {fields_filter})
"""

def load_data(query: str):
    """Ejecuta la consulta y prepara el DataFrame."""
    df = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
    if isinstance(df, list):
        df = pd.concat(df)
    if df.empty:
        return pd.DataFrame()
    df = df[["_time", "_field", "_value"]].pivot(index="_time", columns="_field", values="_value")
    df.index = pd.to_datetime(df.index)
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.sort_index()
    return df

# ==========================================================
# INTERFAZ STREAMLIT
# ==========================================================

st.set_page_config(page_title="Tablero de Digitalización", page_icon="🌡️", layout="wide")

st.title("🌡️ Tablero de Digitalización de Planta Productiva")
st.markdown("Visualización de datos en tiempo real desde **InfluxDB Cloud**. \
Seleccione el rango de fechas y el sensor que desea analizar.")

# --- Selector de fechas ---
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("📅 Fecha inicial", datetime.now() - timedelta(days=7))
with col2:
    end_date = st.date_input("📅 Fecha final", datetime.now())

if start_date > end_date:
    st.error("⚠️ La fecha inicial no puede ser posterior a la fecha final.")
    st.stop()

# Convertir fechas a formato Flux
start_flux = f"time(v: {int(datetime.combine(start_date, datetime.min.time()).timestamp())}s)"
end_flux = f"time(v: {int(datetime.combine(end_date, datetime.max.time()).timestamp())}s)"

# --- Selector de sensor ---
sensor = st.selectbox("Seleccione el sensor a visualizar:", ["DHT22", "MPU6050"])

# ==========================================================
# CONSULTA Y VISUALIZACIÓN DE DATOS
# ==========================================================

with st.spinner("🔄 Consultando datos desde InfluxDB..."):
    if sensor == "DHT22":
        fields = ["temperatura", "humedad", "sensacion_termica"]
        query = build_query("studio-dht22", fields, start_flux, end_flux)
        df = load_data(query)
    else:
        fields = ["accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z", "temperature"]
        query = build_query("mpu6050", fields, start_flux, end_flux)
        df = load_data(query)

if df.empty:
    st.warning("⚠️ No se encontraron datos para el rango de fechas seleccionado.")
else:
    st.success(f"✅ Datos cargados correctamente ({len(df)} registros).")

    # Mostrar estadísticas y gráficos
    st.subheader("📊 Visualización de datos")
    st.line_chart(df, height=400)

    with st.expander("📈 Estadísticas descriptivas"):
        st.dataframe(df.describe().round(2))

# ==========================================================
# PIE DE PÁGINA
# ==========================================================
st.markdown("---")
st.caption("Curso: *Digitalización de Plantas Productivas* – Universidad EAFIT (2025)")
st.caption("Instructor: Miguel Ángel Carrillo – Basado en datos reales de InfluxDB Cloud")
