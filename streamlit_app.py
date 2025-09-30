import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
from datetime import timedelta
import altair as alt

st.set_page_config(page_title="Fire Hotspot Dashboard", layout="wide")

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTbJg8ZlumI6gCGSj0ayEiKYeskiVmxtBR81PSjACW-hmAMJFycXtcen-TZ2bJCp23C9g69aMCdXor/pub?output=csv"
df = pd.read_csv(url)

df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
df = df[df["Ket"] == "Titik Api"]

st.sidebar.header("Filter Options")

min_date, max_date = df["Tanggal"].min().date(), df["Tanggal"].max().date()

preset = st.sidebar.selectbox(
    "Pilih Rentang Waktu Cepat",
    ["Custom", "7 Hari Terakhir", "1 Bulan Terakhir", "6 Bulan Terakhir", "1 Tahun Terakhir", "Semua Data"]
)

if preset == "7 Hari Terakhir":
    start_date, end_date = max_date - timedelta(days=7), max_date
elif preset == "1 Bulan Terakhir":
    start_date, end_date = max_date - timedelta(days=30), max_date
elif preset == "6 Bulan Terakhir":
    start_date, end_date = max_date - timedelta(days=182), max_date
elif preset == "1 Tahun Terakhir":
    start_date, end_date = max_date - timedelta(days=365), max_date
elif preset == "Semua Data":
    start_date, end_date = min_date, max_date
else:
    start_date = st.sidebar.date_input("Tanggal Awal", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("Tanggal Akhir", value=max_date, min_value=min_date, max_value=max_date)

mask = (df["Tanggal"].dt.date >= start_date) & (df["Tanggal"].dt.date <= end_date)
filtered_df = df[mask]

desa_options = ["Semua"] + sorted(filtered_df["Desa"].dropna().unique().tolist())
selected_desa = st.sidebar.selectbox("Pilih Desa", desa_options)
if selected_desa != "Semua":
    filtered_df = filtered_df[filtered_df["Desa"] == selected_desa]

blok_options = ["Semua"] + sorted(filtered_df["Blok"].dropna().unique().tolist())
selected_blok = st.sidebar.selectbox("Pilih Blok", blok_options)
if selected_blok != "Semua":
    filtered_df = filtered_df[filtered_df["Blok"] == selected_blok]

st.sidebar.write(f"Total Hotspot: {len(filtered_df)}")

basemap_options = {
    "OpenStreetMap": "OpenStreetMap",
    "CartoDB Positron": "CartoDB.Positron",
    "CartoDB Dark": "CartoDB.DarkMatter",
    "Esri World Imagery": "Esri.WorldImagery",
    "Stamen Terrain": "Stamen.Terrain",
}
selected_basemap = st.sidebar.selectbox("Pilih Basemap", list(basemap_options.keys()))

col1, col2 = st.columns([3, 1])

with col1:

    m = folium.Map(location=[0, 110], zoom_start=5, tiles=basemap_options[selected_basemap])


    with open("aoi.json", "r") as f:
        boundary = json.load(f)

    geojson_obj = folium.GeoJson(
        boundary,
        name="Boundary",
        style_function=lambda x: {
            "color": "blue",
            "weight": 2,
            "fillOpacity": 0,
        }
    ).add_to(m)

    m.fit_bounds(geojson_obj.get_bounds())

    for _, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=1,
            popup=(f"<b>Owner:</b> {row['Owner']}<br>"
                   f"<b>Desa:</b> {row['Desa']}<br>"
                   f"<b>Tanggal:</b> {row['Tanggal'].date()} {row['Jam']}<br>"
                   f"<b>Penutup Lahan:</b> {row['Penutup Lahan']}<br>"
                   f"<b>Blok:</b> {row['Blok']}")
        ).add_to(m)

    folium.LayerControl().add_to(m)

    st_folium(m, width=None, height=800)

with col2:
    if not filtered_df.empty:
        desa_counts = filtered_df.groupby("Desa").size().reset_index(name="Jumlah")
        chart_desa = alt.Chart(desa_counts).mark_bar().encode(
            x="Jumlah:Q",
            y=alt.Y("Desa:N", sort="-x"),
            tooltip=["Desa", "Jumlah"]
        ).properties(title="Hotspot per Desa", height=250)
        st.altair_chart(chart_desa, use_container_width=True)

        filtered_df["Bulan"] = filtered_df["Tanggal"].dt.to_period("M").dt.to_timestamp()
        filtered_df["BulanLabel"] = filtered_df["Bulan"].dt.strftime("%B %Y")

        blok_month = filtered_df.groupby(["Blok", "BulanLabel"]).size().reset_index(name="Jumlah")

        chart_blok = alt.Chart(blok_month).mark_bar().encode(
            x=alt.X("BulanLabel:N", sort=list(filtered_df["BulanLabel"].unique())),
            y="Jumlah:Q",
            color="Blok:N",
            tooltip=["Blok", "BulanLabel", "Jumlah"]
        ).properties(title="Hotspot per Blok per Bulan", height=250)
        st.altair_chart(chart_blok, use_container_width=True)
    else:
        st.info("Tidak ada data untuk filter yang dipilih.")
