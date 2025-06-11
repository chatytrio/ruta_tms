import streamlit as st
import openrouteservice
import requests
import math
from datetime import datetime, timedelta

# API KEY de OpenRouteService
api_key = "5b3ce3597851110001cf6248e38c54a14f3b4a1b85d665c9694e9874"
client = openrouteservice.Client(key=api_key)

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

st.title("🚛 Planificador de Ruta para Camiones")
st.markdown("Calcula el tiempo total estimado (con descansos) y la hora de llegada según el Reglamento UE.")

origen = st.text_input("📍 Origen", value="Valencia, España")
destino = st.text_input("📍 Destino", value="Madrid, España")
hora_salida_str = st.time_input("🕒 Hora de salida", value=datetime.strptime("08:00", "%H:%M")).strftime("%H:%M")

if st.button("Calcular Ruta"):
    coord_origen, label_origen = geocode(origen)
    coord_destino, label_destino = geocode(destino)

    if not coord_origen or not coord_destino:
        st.error("No se pudo geolocalizar una de las direcciones.")
    else:
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

        st.success("✅ Ruta calculada correctamente")
        st.markdown(f"**Origen:** {label_origen}")
        st.markdown(f"**Destino:** {label_destino}")
        st.markdown(f"**Distancia estimada:** {distancia_km:.2f} km")
        st.markdown(f"**Tiempo de conducción:** {duracion_horas:.2f} h")
        st.markdown(f"**Descansos obligatorios:** {descansos} x 45 min")
        st.markdown(f"**Tiempo total (con descansos):** {tiempo_total_h:.2f} h")
        st.markdown(f"**Hora estimada de llegada:** {hora_llegada.strftime('%H:%M')}")

        if tiempo_total_h > 13:
            st.warning("⚠️ Este viaje excede el límite de jornada diaria (13h). Requiere planificación con descanso diario.")
        else:
            st.success("🟢 El viaje puede completarse en una sola jornada de trabajo.")
