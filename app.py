import streamlit as st
import openrouteservice
import requests
import math
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium

# API Key
api_key = "5b3ce3597851110001cf6248e38c54a14f3b4a1b85d665c9694e9874"
client = openrouteservice.Client(key=api_key)

# Geocodificación
def geocode(direccion):
    url = "https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": api_key,
        "text": direccion,
        "boundary.country": "ES",
        "size": 1
    }
    r = requests.get(url, params=params)
    data = r.json()
    if data["features"]:
        coord = data["features"][0]["geometry"]["coordinates"]
        label = data["features"][0]["properties"]["label"]
        return coord, label
    else:
        return None, None

# Configuración inicial
st.set_page_config(page_title="Virosque TMS", page_icon="🚛", layout="wide")
st.markdown("## 🚛 Virosque | Planificador de Ruta para Camiones")
st.markdown("Calcula distancias, tiempos de conducción y descansos obligatorios, con visualización en mapa.")

# Entradas del usuario
col1, col2, col3 = st.columns(3)
with col1:
    origen = st.text_input("📍 Origen", value="Valencia, España")
with col2:
    destino = st.text_input("🏁 Destino", value="Madrid, España")
with col3:
    hora_salida_str = st.time_input("🕒 Hora de salida", value=datetime.strptime("08:00", "%H:%M")).strftime("%H:%M")

# Botón y control de estado
if st.button("🔍 Calcular Ruta"):
    st.session_state["calcular"] = True

if st.session_state.get("calcular"):
    coord_origen, label_origen = geocode(origen)
    coord_destino, label_destino = geocode(destino)

    if not coord_origen or not coord_destino:
        st.error("❌ No se pudo geolocalizar una de las direcciones.")
        st.stop()

    try:
        ruta = client.directions(
            coordinates=[coord_origen, coord_destino],
            profile='driving-hgv',
            format='geojson'
        )
    except openrouteservice.exceptions.ApiError as e:
        st.error(f"❌ Error al calcular la ruta: {e}")
        st.stop()

    segmento = ruta['features'][0]['properties']['segments'][0]
    distancia_km = segmento['distance'] / 1000
    duracion_horas = segmento['duration'] / 3600
    descansos = math.floor(duracion_horas / 4.5)
    tiempo_total_h = duracion_horas + descansos * 0.75
    hora_salida = datetime.strptime(hora_salida_str, "%H:%M")
    hora_llegada = hora_salida + timedelta(hours=tiempo_total_h)

    # Métricas principales alineadas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🛣 Distancia", f"{distancia_km:.2f} km")
    col2.metric("🕓 Conducción", f"{duracion_horas:.2f} h")
    col3.metric("⏱ Total (con descansos)", f"{tiempo_total_h:.2f} h")
    col4.metric("📅 Llegada estimada", hora_llegada.strftime("%H:%M"))

    # Validación de jornada
    if tiempo_total_h > 13:
        st.warning("⚠️ Este viaje excede el límite de jornada diaria (13h). Requiere descanso adicional.")
    else:
        st.success("🟢 El viaje puede completarse en una sola jornada de trabajo.")

    # Mapa de ruta
    linea = ruta["features"][0]["geometry"]["coordinates"]
    linea_latlon = [[p[1], p[0]] for p in linea]
    m = folium.Map(location=linea_latlon[0], zoom_start=6)
    folium.Marker(location=[coord_origen[1], coord_origen[0]], tooltip="📍 Origen").add_to(m)
    folium.Marker(location=[coord_destino[1], coord_destino[0]], tooltip="🏁 Destino").add_to(m)
    folium.PolyLine(linea_latlon, color="blue", weight=5).add_to(m)

    st.markdown("### 🗺️ Ruta estimada en mapa:")
    st_folium(m, width=1200, height=500)

