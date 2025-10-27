import streamlit as st
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# -------------------------------
# Configuración inicial de la app
# -------------------------------
st.set_page_config(page_title="Monitoreo IoT | SCADA Digital", layout="wide")
st.title("📈 Monitoreo IoT de Planta Productiva")

# -------------------------------
# Parámetros de conexión
# -------------------------------
url = "https://us-east-1-1.aws.cloud2.influxdata.com"
token = "JcKXoXE30JQvV9Ggb4-zv6sQc0Zh6B6Haz5eMRW0FrJEduG2KcFJN9-7RoYvVORcFgtrHR-Q_ly-52pD7IC6JQ=="
org = "0925ccf91ab36478"
bucket = "EXTREME_MANUFACTURING"

# -------------------------------
# Función para obtener datos de InfluxDB
# -------------------------------
@st.cache_data(ttl=300)
def obtener_datos(rango_horas):
    try:
        with InfluxDBClient(url=url, token=token, org=org) as client:
            query_api = client.query_api()
            query = f'''
            from(bucket: "{bucket}")
              |> range(start: -{rango_horas}h)
              |> filter(fn: (r) => r._measurement == "sensores")
              |> filter(fn: (r) => r._field == "temperatura" or r._field == "humedad")
              |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
              |> yield(name: "mean")
            '''
            df = query_api.query_data_frame(org=org, query=query)

            if df.empty:
                return pd.DataFrame()

            # Limpiar y organizar datos
            df = df[["_time", "_field", "_value"]]
            df = df.rename(columns={"_time": "Tiempo", "_value": "Valor", "_field": "Variable"})
            return df

    except InfluxDBError as e:
        st.error(f"Error en la consulta a InfluxDB: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocurrió un error inesperado: {e}")
        return pd.DataFrame()

# -------------------------------
# Filtros de la interfaz
# -------------------------------
st.sidebar.header("⚙️ Configuración de visualización")

rango_opciones = {
    "Última hora": 1,
    "Últimas 6 horas": 6,
    "Últimas 12 horas": 12,
    "Últimas 24 horas": 24,
    "Últimos 3 días": 72,
}
rango_seleccion = st.sidebar.selectbox("Selecciona rango de tiempo:", list(rango_opciones.keys()))

st.info(f"🔄 Cargando datos de los últimos {rango_opciones[rango_seleccion]} horas...")

# -------------------------------
# Cargar los datos
# -------------------------------
df = obtener_datos(rango_opciones[rango_seleccion])

# -------------------------------
# Mostrar resultados
# -------------------------------
if df.empty:
    st.warning("⚠️ No se encontraron datos para el rango seleccionado.")
else:
    st.success(f"✅ Datos cargados correctamente ({len(df)} registros).")

    col1, col2 = st.columns(2)
    with col1:
        temp_df = df[df["Variable"] == "temperatura"]
        if not temp_df.empty:
            fig_temp = px.line(temp_df, x="Tiempo", y="Valor", title="Temperatura (°C)", markers=True)
            st.plotly_chart(fig_temp, use_container_width=True)
        else:
            st.info("No hay datos de temperatura disponibles.")

    with col2:
        hum_df = df[df["Variable"] == "humedad"]
        if not hum_df.empty:
            fig_hum = px.line(hum_df, x="Tiempo", y="Valor", title="Humedad (%)", markers=True)
            st.plotly_chart(fig_hum, use_container_width=True)
        else:
            st.info("No hay datos de humedad disponibles.")

# -------------------------------
# Debug opcional
# -------------------------------
with st.expander("🧠 Datos crudos (debug)"):
    st.dataframe(df)
