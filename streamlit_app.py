import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import altair as alt

st.set_page_config(page_title="Fire Hotspot Dashboard", layout="wide")

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTbJg8ZlumI6gCGSj0ayEiKYeskiVmxtBR81PSjACW-hmAMJFycXtcen-TZ2bJCp23C9g69aMCdXor/pub?output=csv"
df = pd.read_csv(url)

df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
df = df[df["Ket"] == "Titik Api"]

st.sidebar.header("Filter Options")

min_date, max_date = df["Tanggal"].min().date(), df["Tanggal"].max().date()

start_date = st.sidebar.date_input("Tanggal Awal", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("Tanggal Akhir", max_date, min_value=min_date, max_value=max_date)

quick_range = st.sidebar.selectbox(
    "Pilih Rentang Cepat",
    ["-- Tidak Ada --", "7 Hari Terakhir", "30 Hari Terakhir", "6 Bulan Terakhir"]
)

if quick_range == "7 Hari Terakhir":
    start_date = max_date - pd.Timedelta(days=7)
elif quick_range == "30 Hari Terakhir":
    start_date = max_date - pd.Timedelta(days=30)
elif quick_range == "6 Bulan Terakhir":
    start_date = max_date - pd.Timedelta(days=180)

mask = (df["Tanggal"].dt.date >= start_date) & (df["Tanggal"].dt.date <= end_date)
filtered_df = df[mask]

st.sidebar.write(f"Total Hotspot: {len(filtered_df)}")

col1, col2 = st.columns([2, 1], gap="small")

with col1:
    with open("aoi.json", "r") as f:
        boundary = json.load(f)

    coords = []
    def extract_coords(geom):
        if geom["type"] == "Polygon":
            coords.extend(geom["coordinates"][0])
        elif geom["type"] == "MultiPolygon":
            for poly in geom["coordinates"]:
                coords.extend(poly[0])

    for feat in boundary["features"]:
        extract_coords(feat["geometry"])

    if coords:
        lats, lons = zip(*coords)
        center_lat, center_lon = sum(lats) / len(lats), sum(lons) / len(lons)
    else:
        center_lat, center_lon = -0.5, 110.5

    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles="CartoDB.Positron")

    folium.GeoJson(
        boundary,
        name="Boundary",
        style_function=lambda x: {"color": "blue", "weight": 2, "fillOpacity": 0}
    ).add_to(m)

    for _, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=1,
            popup=(
                f"<b>Owner:</b> {row['Owner']}<br>"
                f"<b>Desa:</b> {row['Desa']}<br>"
                f"<b>Tanggal:</b> {row['Tanggal'].date()} {row['Jam']}<br>"
                f"<b>Penutup Lahan:</b> {row['Penutup Lahan']}<br>"
                f"<b>Blok:</b> {row['Blok']}"
            ),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=800, height=600)

with col2:
    st.subheader("Statistik Hotspot")

    desa_count = filtered_df.groupby("Desa").size().reset_index(name="Jumlah Hotspot")
    if not desa_count.empty:
        chart_desa = alt.Chart(desa_count).mark_bar().encode(
            x="Jumlah Hotspot:Q",
            y=alt.Y("Desa:N", sort="-x")
        ).properties(title="Hotspot per Desa", height=250)
        st.altair_chart(chart_desa, use_container_width=True)

    if not filtered_df.empty:
        blok_bulan = (
            filtered_df
            .assign(Bulan=filtered_df["Tanggal"].dt.to_period("M").astype(str))
            .groupby(["Blok", "Bulan"])
            .size()
            .reset_index(name="Jumlah Hotspot")
        )

        chart_blok = alt.Chart(blok_bulan).mark_bar().encode(
            x="Bulan:N",
            y="Jumlah Hotspot:Q",
            color="Blok:N",
            tooltip=["Blok", "Bulan", "Jumlah Hotspot"]
        ).properties(title="Hotspot per Blok per Bulan", height=300)
        st.altair_chart(chart_blok, use_container_width=True)
