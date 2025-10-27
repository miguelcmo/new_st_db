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

# --- Consultas Flux ---
query_dht22 = """
from(bucket: "EXTREME_MANUFACTURING")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "studio-dht22")
  |> filter(fn: (r) => r._field == "humedad" or r._field == "temperatura" or r._field == "sensacion_termica")
"""

query_mpu = """
from(bucket: "EXTREME_MANUFACTURING")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "mpu6050")
  |> filter(fn: (r) =>
      r._field == "accel_x" or r._field == "accel_y" or r._field == "accel_z" or
      r._field == "gyro_x" or r._field == "gyro_y" or r._field == "gyro_z" or
      r._field == "temperature")
"""

# --- Función auxiliar para cargar y limpiar datos ---
def load_data(query):
    df = query_api.query_data_frame(org=INFLUXDB_ORG, query=query)
    if isinstance(df, list):
        df = pd.concat(df)
    if df.empty:
        return pd.DataFrame()
    df = df[["_time", "_field", "_value"]].pivot(index="_time", columns="_field", values="_value")
    df.index = pd.to_datetime(df.index)
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.sort_index()
    return df

# --- Cargar datos ---
df_dht22 = load_data(query_dht22)
df_mpu = load_data(query_mpu)

# --- Interfaz ---
st.title("🌡️ Tablero de Digitalización de Planta")
st.subheader("Datos desde InfluxDB")

sensor = st.selectbox("Selecciona el sensor:", ["DHT22", "MPU6050"])

if sensor == "DHT22":
    if not df_dht22.empty:
        st.line_chart(df_dht22)
        st.dataframe(df_dht22.describe())
    else:
        st.warning("No hay datos disponibles del sensor DHT22 en el rango seleccionado.")
else:
    if not df_mpu.empty:
        st.line_chart(df_mpu)
        st.dataframe(df_mpu.describe())
    else:
        st.warning("No hay datos disponibles del sensor MPU6050 en el rango seleccionado.")
