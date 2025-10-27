import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient

# --- Configuración InfluxDB ---
INFLUXDB_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUXDB_TOKEN = "JcKXoXE30JQvV9Ggb4-zv6sQc0Zh6B6Haz5eMRW0FrJEduG2KcFJN9-7RoYvVORcFgtrHR-Q_ly-52pD7IC6JQ=="
INFLUXDB_ORG = "0925ccf91ab36478"
INFLUXDB_BUCKET = "EXTREME_MANUFACTURING"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()

# --- Interfaz de Streamlit ---
st.set_page_config(page_title="Tablero Planta", page_icon="🏭", layout="wide")
st.title("🏭 Tablero de Digitalización de Planta Productiva")
st.write("Visualización de variables capturadas por sensores DHT22 y MPU6050 desde InfluxDB Cloud.")

# --- Selector de rango temporal ---
rango = st.selectbox(
    "Selecciona el rango de tiempo:",
    {
        "Últimas 24 horas": "-24h",
        "Últimos 3 días": "-3d",
        "Última semana": "-7d",
        "Últimos 15 días": "-15d"
    }
)

# --- Consultas Flux ---
query_dht22 = f"""
from(bucket: "{INFLUXDB_BUCKET}")
  |> range(start: {rango})
  |> filter(fn: (r) => r._measurement == "studio-dht22")
  |> filter(fn: (r) => r._field == "humedad" or r._field == "temperatura" or r._field == "sensacion_termica")
"""

query_mpu = f"""
from(bucket: "{INFLUXDB_BUCKET}")
  |> range(start: {rango})
  |> filter(fn: (r) => r._measurement == "mpu6050")
  |> filter(fn: (r) =>
      r._field == "accel_x" or r._field == "accel_y" or r._field == "accel_z" or
      r._field == "gyro_x" or r._field == "gyro_y" or r._field == "gyro_z" or
      r._field == "temperature")
"""

# --- Función para cargar datos de InfluxDB ---
def load_data(query):
    try:
        df = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
        if isinstance(df, list):
            df = pd.concat(df)
        if df.empty:
            return pd.DataFrame()

        columnas_validas = [c for c in ["_time", "_field", "_value"] if c in df.columns]
        df = df[columnas_validas]
        df = df.pivot(index="_time", columns="_field", values="_value")
        df.index = pd.to_datetime(df.index, errors="coerce")
        df = df.apply(pd.to_numeric, errors="coerce")
        df = df.dropna(how="all").sort_index()
        return df
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame()

# --- Cargar datos ---
df_dht22 = load_data(query_dht22)
df_mpu = load_data(query_mpu)

# --- Selección de sensor ---
sensor = st.radio("Selecciona el sensor a visualizar:", ["DHT22", "MPU6050"], horizontal=True)

# --- Mostrar gráficos ---
if sensor == "DHT22":
    st.subheader("🌡️ Sensor DHT22 - Temperatura, Humedad y Sensación Térmica")
    if not df_dht22.empty:
        st.line_chart(df_dht22.reset_index(), x="_time", y=list(df_dht22.columns))
        st.dataframe(df_dht22.describe().T)
    else:
        st.warning("⚠️ No hay datos disponibles del sensor DHT22 en el rango seleccionado.")
else:
    st.subheader("📈 Sensor MPU6050 - Acelerómetro y Giroscopio")
    if not df_mpu.empty:
        st.line_chart(df_mpu.reset_index(), x="_time", y=list(df_mpu.columns))
        st.dataframe(df_mpu.describe().T)
    else:
        st.warning("⚠️ No hay datos disponibles del sensor MPU6050 en el rango seleccionado.")

# --- Información adicional ---
st.markdown("---")
st.caption("Desarrollado para la práctica del curso *Digitalización de Plantas Productivas - EAFIT*")

