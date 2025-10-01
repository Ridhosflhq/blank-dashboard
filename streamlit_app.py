import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import plotly.express as px


# ===== Load Data =====
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTbJg8ZlumI6gCGSj0ayEiKYeskiVmxtBR81PSjACW-hmAMJFycXtcen-TZ2bJCp23C9g69aMCdXor/pub?output=csv"
df = pd.read_csv(url)
df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
df = df[df["Ket"] == "Titik Api"]

# ===== Sidebar Filter =====
st.sidebar.header("Filter Options")

min_date, max_date = df["Tanggal"].min().date(), df["Tanggal"].max().date()

quick_filter = st.sidebar.selectbox(
    "Quick Date Range",
    ["Semua", "1 Minggu Terakhir", "1 Bulan Terakhir", "6 Bulan Terakhir"]
)

if quick_filter == "Semua":
    start_date, end_date = min_date, max_date
elif quick_filter == "1 Minggu Terakhir":
    start_date, end_date = max_date - pd.Timedelta(days=7), max_date
elif quick_filter == "1 Bulan Terakhir":
    start_date, end_date = max_date - pd.DateOffset(months=1), max_date
elif quick_filter == "6 Bulan Terakhir":
    start_date, end_date = max_date - pd.DateOffset(months=6), max_date

col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Tanggal Awal", value=start_date, min_value=min_date, max_value=max_date)
end_date = col2.date_input("Tanggal Akhir", value=end_date, min_value=min_date, max_value=max_date)

filtered_df = df[(df["Tanggal"].dt.date >= start_date) & (df["Tanggal"].dt.date <= end_date)]
st.sidebar.write(f"Total Hotspot: **{len(filtered_df)}**")

# ===== Basemap =====
basemap_options = {
    "OpenStreetMap": "OpenStreetMap",
    "CartoDB Positron": "CartoDB positron",
    "CartoDB Dark": "CartoDB dark_matter",
    "Esri World Imagery": "Esri.WorldImagery",
    "Stamen Terrain": "Stamen Terrain",
}
selected_basemap = st.sidebar.selectbox("Pilih Basemap", list(basemap_options.keys()))

# ===== Layout =====
left_col, right_col = st.columns([3, 1])

with left_col:
    # ===== Map =====
    center = [0.8240212468388239, 110.3212231153715]
    m = folium.Map(location=center, zoom_start=12, tiles=basemap_options[selected_basemap])

    # ===== AOI Layer =====
    try:
        with open("aoi.json") as f:
            boundary = json.load(f)
        folium.GeoJson(
            boundary,
            name="Boundary",
            style_function=lambda x: {"color": "blue", "weight": 2, "fillOpacity": 0}
        ).add_to(m)
    except Exception:
        st.warning("AOI JSON tidak ditemukan atau gagal dibaca.")

    # ===== Hotspot Layer =====
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
            )
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width="100%", height=700)  # tinggi map tetap, responsif

with right_col:
    st.subheader("Statistik")

    if not filtered_df.empty:
        # Hotspot per Desa
        desa_count = filtered_df["Desa"].value_counts().reset_index()
        desa_count.columns = ["Desa", "Jumlah"]
        fig_desa = px.bar(desa_count, x="Jumlah", y="Desa", orientation="h",
                          title="Hotspot per Desa", height=300)
        st.plotly_chart(fig_desa, use_container_width=True)

        # Hotspot per Blok per Bulan
        df_monthly = (filtered_df.groupby([filtered_df["Tanggal"].dt.to_period("M"), "Blok"])
                      .size().reset_index(name="Jumlah").sort_values("Tanggal"))
        df_monthly["Label"] = df_monthly["Tanggal"].dt.strftime("%m/%y")
        fig_blok = px.bar(df_monthly, x="Label", y="Jumlah", color="Blok",
                          title="Hotspot per Blok per Bulan", height=400)
        st.plotly_chart(fig_blok, use_container_width=True)
    else:
        st.info("Tidak ada data pada rentang tanggal ini.")
