# ==========================================================
# TABLERO STREAMLIT - DIGITALIZACIÓN DE PLANTAS PRODUCTIVAS
# ==========================================================

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
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "studio-dht22")
  |> filter(fn: (r) => r._field == "humedad" or r._field == "temperatura" or r._field == "sensacion_termica")
"""

query_mpu = """
from(bucket: "EXTREME_MANUFACTURING")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "mpu6050")
  |> filter(fn: (r) =>
      r._field == "accel_x" or r._field == "accel_y" or r._field == "accel_z" or
      r._field == "gyro_x" or r._field == "gyro_y" or r._field == "gyro_z" or
      r._field == "temperature")
"""

# --- Cargar datos ---
df_dht22 = query_api.query_data_frame(org=INFLUXDB_ORG, query=query_dht22)
df_mpu = query_api.query_data_frame(org=INFLUXDB_ORG, query=query_mpu)

df_dht22 = df_dht22[["_time", "_field", "_value"]].pivot(index="_time", columns="_field", values="_value")
df_mpu = df_mpu[["_time", "_field", "_value"]].pivot(index="_time", columns="_field", values="_value")

# --- Interfaz ---
st.title("🌡️ Tablero de Digitalización de Planta")
st.subheader("Datos en tiempo real desde InfluxDB")

st.write("Este tablero muestra las variables medidas por los sensores DHT22 y MPU6050 durante las últimas 24 horas.")

# Selección de variable
sensor = st.selectbox("Selecciona el sensor a visualizar:", ["DHT22", "MPU6050"])

if sensor == "DHT22":
    st.line_chart(df_dht22[["temperatura", "humedad"]])
    st.write(df_dht22.describe())
else:
    st.line_chart(df_mpu[["accel_x", "accel_y", "accel_z"]])
    st.write(df_mpu.describe())

# --- Extensión ---
st.info("💡 Reto: Agrega una sección con un modelo predictivo simple (por ejemplo, una regresión lineal o suavizado exponencial).")
