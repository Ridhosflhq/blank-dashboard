import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import json

# -------------------
# Load Data
# -------------------
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgZRjQlxUsTPmrXiDCtwky4_A0FJrGDj_r7JLgsqi8gvjOWxmDKpBSdJDWFF38VfRuxUxzWSjhk46C/pub?output=csv"
df = pd.read_csv(csv_url)
df['date'] = pd.to_datetime(df['date'])

# Load AOI (GeoJSON)
with open("aoi.json", "r") as f:
    aoi = json.load(f)

# -------------------
# Data Preparation
# -------------------
today = pd.Timestamp.today().normalize()
this_month, this_year = today.month, today.year

today_count = df[df['date'].dt.date == today.date()].shape[0]
month_count = df[(df['date'].dt.month == this_month) & (df['date'].dt.year == this_year)].shape[0]

# Fires per Village
village_count = df['village'].value_counts().reset_index()
village_count.columns = ['Village', 'Fire Events']

# Fires per Block per Month
df['year_month'] = df['date'].dt.to_period('M').astype(str)
block_month = df.groupby(['year_month', 'Blok']).size().reset_index(name='Fire Events')

# -------------------
# Layout Config
# -------------------
st.set_page_config(layout="wide")
st.title("🔥 Fire Hotspot Monitoring Dashboard")

# -------------------
# Top KPI Metrics
# -------------------
col1, col2 = st.columns(2)
col1.metric("🔥 Fires Today", today_count)
col2.metric("🔥 Fires This Month", month_count)

# -------------------
# Main Layout (Left, Center, Right)
# -------------------
left, center, right = st.columns([1, 2, 1.3])

# --- Left Column: Charts
with left:
    st.subheader("🔥 Fires per Village")
    fig_village = px.bar(village_count, x="Village", y="Fire Events", color="Village",
                         template="plotly_white")
    fig_village.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    st.plotly_chart(fig_village, use_container_width=True)

    st.subheader("🔥 Fires per Block per Month")
    fig_block = px.bar(block_month, x="year_month", y="Fire Events", color="Blok", barmode="group",
                       template="plotly_white")
    fig_block.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    st.plotly_chart(fig_block, use_container_width=True)

# --- Center Column: Map
with center:
    st.subheader("🗺️ Fire Hotspot Map")

    midpoint = (df["latitude"].mean(), df["longitude"].mean())

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=midpoint[0],
            longitude=midpoint[1],
            zoom=11,
            pitch=0,
        ),
        layers=[
            # AOI Boundary
            pdk.Layer(
                "GeoJsonLayer",
                aoi,
                stroked=True,
                filled=False,
                get_line_color=[0, 0, 255],
                line_width_min_pixels=3,
            ),
            # Fire Points
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[longitude, latitude]",
                get_color="[255, 0, 0, 160]",
                get_radius=300,
            ),
        ],
    ))

# --- Right Column: Fire Rating + Table
with right:
    st.subheader("🔥 Fire Danger Rating")
    st.info("Block 1: LOW")   # Placeholder, can calculate later
    st.info("Block 2: LOW")

    st.subheader("📋 Fire Events Table")
    st.dataframe(df[['date','owner','LC','village','latitude','longitude']], height=300)
