import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Fire Hotspot Dashboard", layout="wide")

st.title("Fire Hotspot Dashboard")

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTbJg8ZlumI6gCGSj0ayEiKYeskiVmxtBR81PSjACW-hmAMJFycXtcen-TZ2bJCp23C9g69aMCdXor/pub?output=csv"
df = pd.read_csv(url)

df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
df = df[df["Ket"] == "Titik Api"]

st.sidebar.header("Filter Options")

min_date, max_date = df["Tanggal"].min().date(), df["Tanggal"].max().date()
date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df["Tanggal"].dt.date >= start_date) & (df["Tanggal"].dt.date <= end_date)
    filtered_df = df[mask]
else:
    filtered_df = df[df["Tanggal"].dt.date == date_range]

st.sidebar.write(f"Total Hotspot: {len(filtered_df)}")

basemap_options = {
    "OpenStreetMap": "OpenStreetMap",
    "CartoDB Positron": "CartoDB positron",
    "CartoDB Dark": "CartoDB dark_matter",
    "Esri World Imagery": "Esri.WorldImagery",
    "Stamen Terrain": "Stamen Terrain",
}
selected_basemap = st.sidebar.selectbox("Pilih Basemap", list(basemap_options.keys()))

m = folium.Map(location=[-0.5, 110.5], zoom_start=7, tiles=basemap_options[selected_basemap])

with open("CMI.json", "r") as f:
    boundary = json.load(f)

folium.GeoJson(
    boundary,
    name="Boundary",
    style_function=lambda x: {
        "color": "blue",
        "weight": 2,
        "fillOpacity": 0,
    }
).add_to(m)

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

st_folium(m, width=None, height=800)
