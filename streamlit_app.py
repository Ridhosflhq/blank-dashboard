import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

# ====== Layout ======
st.set_page_config(layout="wide")
st.title("🔥 Fire Dashboard")

# ====== Data ======
df = pd.read_csv("fire_data.csv", parse_dates=["date"])  # pastikan ada kolom "date"

# ====== Date Filter ======
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", df["date"].min().date())
with col2:
    end_date = st.date_input("End Date", df["date"].max().date())

mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
df_filtered = df.loc[mask]

# ====== Chart: Fires per Village ======
st.subheader("Fires per Village")
fig1 = px.bar(
    df_filtered.groupby("village")["fire_event"].count().reset_index(),
    x="village",
    y="fire_event",
    color="village",
    title="Fires per Village",
)

# Styling chart
fig1.update_layout(
    plot_bgcolor="#44444E",
    paper_bgcolor="#ffffff",
    font=dict(color="white"),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5
    )
)
st.plotly_chart(fig1, use_container_width=True)

# ====== Map ======
st.subheader("Fire Map")

m = folium.Map(location=[-0.5, 113], zoom_start=6)

# Basemaps
folium.TileLayer("OpenStreetMap").add_to(m)
folium.TileLayer("Stamen Terrain").add_to(m)
folium.TileLayer("CartoDB positron").add_to(m)
folium.LayerControl().add_to(m)

# Tambahkan AOI (jika ada file aoi.json)
import json
with open("aoi.json") as f:
    aoi = json.load(f)
folium.GeoJson(aoi, name="AOI").add_to(m)

# Tampilkan map di Streamlit
st_folium(m, width=1000, height=500)

# ====== Tabel ======
st.subheader("Filtered Data Table")
st.dataframe(df_filtered)
