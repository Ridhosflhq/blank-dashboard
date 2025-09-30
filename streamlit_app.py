import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import requests
from datetime import date

st.set_page_config(page_title="Fire Hotspot Dashboard", layout="wide")

st.title("Fire Hotspot Dashboard")

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTbJg8ZlumI6gCGSj0ayEiKYeskiVmxtBR81PSjACW-hmAMJFycXtcen-TZ2bJCp23C9g69aMCdXor/pub?output=csv"
df = pd.read_csv(url)

df["Tanggal"] = pd.to_datetime(df["Tanggal"])
df = df[df["Ket"] == "Titik Api"]

selected_date = st.sidebar.date_input("Select Date", value=date.today())
filtered_df = df[df["Tanggal"].dt.date == selected_date]

st.sidebar.write(f"Total Hotspot: {len(filtered_df)}")

m = folium.Map(location=[-0.5, 110.5], zoom_start=7)

with open("aoi.json", "r") as f:
    boundary = json.load(f)
folium.GeoJson(boundary, name="Boundary").add_to(m)

for _, row in filtered_df.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=5,
        color="red",
        fill=True,
        fill_color="red",
        popup=(
            f"<b>Owner:</b> {row['Owner']}<br>"
            f"<b>Desa:</b> {row['Desa']}<br>"
            f"<b>Tanggal:</b> {row['Tanggal'].date()} {row['Jam']}<br>"
            f"<b>Penutup Lahan:</b> {row['Penutup Lahan']}<br>"
            f"<b>Blok:</b> {row['Blok']}"
        ),
    ).add_to(m)

folium.LayerControl().add_to(m)

# Render map in Streamlit
st_folium(m, width=1000, height=600)
