import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import plotly.express as px

url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTbJg8ZlumI6gCGSj0ayEiKYeskiVmxtBR81PSjACW-hmAMJFycXtcen-TZ2bJCp23C9g69aMCdXor/pub?output=csv"
df = pd.read_csv(url)

df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
df = df[df["Ket"] == "Titik Api"]

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
else:
    start_date, end_date = min_date, max_date

col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Tanggal Awal", value=start_date, min_value=min_date, max_value=max_date)
end_date = col2.date_input("Tanggal Akhir", value=end_date, min_value=min_date, max_value=max_date)

mask = (df["Tanggal"].dt.date >= start_date) & (df["Tanggal"].dt.date <= end_date)
filtered_df = df[mask]

st.sidebar.write(f"Total Hotspot: **{len(filtered_df)}**")

basemap_options = {
    "OpenStreetMap": "OpenStreetMap",
    "CartoDB Positron": "CartoDB positron",
    "CartoDB Dark": "CartoDB dark_matter",
    "Esri World Imagery": "Esri.WorldImagery",
    "Stamen Terrain": "Stamen Terrain",
}
selected_basemap = st.sidebar.selectbox("Pilih Basemap", list(basemap_options.keys()))

left_col, right_col = st.columns([3, 1])

st.markdown(
    """
    <script>
    function sendHeight(){
        const height = window.innerHeight;
        document.querySelector('body').dataset.height = height;
    }
    window.addEventListener('load', sendHeight);
    window.addEventListener('resize', sendHeight);
    </script>
    """, unsafe_allow_html=True
)

map_height = 700

with left_col:
    try:
        with open("aoi.json", "r") as f:
            boundary = json.load(f)

        bounds_coords = []
        for feature in boundary["features"]:
            coords = feature["geometry"]["coordinates"]
            if feature["geometry"]["type"] == "Polygon":
                bounds_coords.extend(coords[0])
            elif feature["geometry"]["type"] == "MultiPolygon":
                for poly in coords:
                    bounds_coords.extend(poly[0])

        lats = [c[1] for c in bounds_coords]
        lons = [c[0] for c in bounds_coords]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)


        center_lat, center_lon = 0.8028, 110.2967

        m = folium.Map(location=[center_lat, center_lon], tiles=basemap_options[selected_basemap])

        m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=(50, 50))

        folium.GeoJson(
            boundary,
            name="Boundary",
            style_function=lambda x: {
                "color": "blue",
                "weight": 2,
                "fillOpacity": 0,
            }
        ).add_to(m)

    except Exception:

        m = folium.Map(location=[0.8028, 110.2967],
                       zoom_start=13,
                       tiles=basemap_options[selected_basemap])

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

    st_folium(m, width="100%", height=map_height)

with right_col:
    st.subheader("Statistik")

    if not filtered_df.empty:

        desa_count = filtered_df["Desa"].value_counts().reset_index()
        desa_count.columns = ["Desa", "Jumlah"]
        fig_desa = px.bar(
            desa_count,
            x="Jumlah", y="Desa",
            orientation="h",
            title="Hotspot per Desa",
            height=300
        )
        st.plotly_chart(fig_desa, use_container_width=True)

        df_monthly = (
            filtered_df.groupby([
                filtered_df["Tanggal"].dt.to_period("M"),
                "Blok"
            ])
            .size()
            .reset_index(name="Jumlah")
            .sort_values("Tanggal")
        )
        df_monthly["Label"] = df_monthly["Tanggal"].dt.strftime("%m/%y")

        fig_blok = px.bar(
            df_monthly,
            x="Label", y="Jumlah", color="Blok",
            title="Hotspot per Blok per Bulan",
            height=400
        )
        st.plotly_chart(fig_blok, use_container_width=True)
    else:
        st.info("Tidak ada data pada rentang tanggal ini.")
