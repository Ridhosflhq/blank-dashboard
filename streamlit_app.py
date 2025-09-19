import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import json

csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgZRjQlxUsTPmrXiDCtwky4_A0FJrGDj_r7JLgsqi8gvjOWxmDKpBSdJDWFF38VfRuxUxzWSjhk46C/pub?output=csv"
df = pd.read_csv(csv_url)
df['date'] = pd.to_datetime(df['date'])

with open("aoi.json", "r") as f:
    aoi = json.load(f)

st.set_page_config(layout="wide")
st.title("🔥 Fire Hotspot Monitoring Dashboard")

min_date = df['date'].min().date()
max_date = df['date'].max().date()

date_range = st.date_input(
    "📅 Select Date Range:",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

today = pd.Timestamp.today().normalize()
this_month, this_year = today.month, today.year

today_count = df[df['date'].dt.date == today.date()].shape[0]
month_count = df[(df['date'].dt.month == this_month) & (df['date'].dt.year == this_year)].shape[0]

village_count = df['village'].value_counts().reset_index()
village_count.columns = ['Village', 'Fire Events']

df['year_month'] = df['date'].dt.to_period('M').astype(str)
block_month = df.groupby(['year_month', 'Blok']).size().reset_index(name='Fire Events')


col1, col2 = st.columns(2)
col1.metric("🔥 Fires Today", today_count)
col2.metric("🔥 Fires This Month", month_count)

left, center, right = st.columns([1, 2, 1.3])

with left:
    st.subheader("🔥 Fires per Village")
    fig_village = px.bar(village_count, x="Village", y="Fire Events", color="Village",
                         color_discrete_sequence=px.colors.sequential.OrRd,
                         template="plotly_dark")
    fig_village.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="#111111",
        paper_bgcolor="#111111"
    )
    st.plotly_chart(fig_village, use_container_width=True)

    st.subheader("🔥 Fires per Block per Month")
    fig_block = px.bar(block_month, x="year_month", y="Fire Events", color="Blok", barmode="group",
                       color_discrete_sequence=px.colors.qualitative.Set2,
                       template="plotly_dark")
    fig_block.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="#111111",
        paper_bgcolor="#111111"
    )
    st.plotly_chart(fig_block, use_container_width=True)

with center:
    st.subheader("🗺️ Fire Hotspot Map")

    midpoint = (df["latitude"].mean(), df["longitude"].mean())

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=pdk.ViewState(
            latitude=midpoint[0],
            longitude=midpoint[1],
            zoom=11,
            pitch=0,
        ),
        layers=[

            pdk.Layer(
                "GeoJsonLayer",
                aoi,
                stroked=True,
                filled=False,
                get_line_color=[0, 150, 255],
                line_width_min_pixels=3,
            ),

            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[longitude, latitude]",
                get_color="[255, 80, 0, 180]",
                get_radius=300,
            ),
        ],
    ))

with right:
    st.subheader("🔥 Fire Danger Rating")
    st.info("Block 1: LOW")
    st.info("Block 2: LOW")

st.subheader("📋 Fire Events Table")
st.dataframe(df[['date','owner','LC','village','latitude','longitude']], height=400)
