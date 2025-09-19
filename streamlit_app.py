import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import json

# -------------------
# Config
# -------------------
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    /* Background kembali default */
    body {
        background-color: #ffffff;
        color: black;
    }
    .block-container {
        padding: 1rem 2rem;
        background-color: #ffffff;
    }
    /* Styling container chart/table */
    .stPlotlyChart, .stMetric, .stDataFrame {
        background-color: #44444E;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #666666;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------
# Load Data
# -------------------
csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgZRjQlxUsTPmrXiDCtwky4_A0FJrGDj_r7JLgsqi8gvjOWxmDKpBSdJDWFF38VfRuxUxzWSjhk46C/pub?output=csv"
df = pd.read_csv(csv_url)
df['date'] = pd.to_datetime(df['date'])

with open("aoi.json", "r") as f:
    aoi = json.load(f)

# -------------------
# Filter Date
# -------------------
st.sidebar.header("📅 Date Filter")
min_date, max_date = df['date'].min(), df['date'].max()

start_date = st.sidebar.date_input("Start Date", min_date)
end_date = st.sidebar.date_input("End Date", max_date)

mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
df = df.loc[mask]

today = pd.Timestamp.today().normalize()
this_month, this_year = today.month, today.year

today_count = df[df['date'].dt.date == today.date()].shape[0]
month_count = df[(df['date'].dt.month == this_month) & (df['date'].dt.year == this_year)].shape[0]

village_count = df['village'].value_counts().reset_index()
village_count.columns = ['Village', 'Fire Events']

df['year_month'] = df['date'].dt.to_period('M').astype(str)
block_month = df.groupby(['year_month', 'Blok']).size().reset_index(name='Fire Events')

st.title("🔥 Fire Hotspot Monitoring Dashboard")

col1, col2 = st.columns(2)
with col1:
    st.metric("🔥 Fires Today", today_count)
with col2:
    st.metric("🔥 Fires This Month", month_count)

left, center, right = st.columns([1, 2, 1.3])

with left:
    st.subheader("🔥 Fires per Village")
    fig_village = px.bar(
        village_count, x="Village", y="Fire Events", color="Village",
        template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_village.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="#44444E",
        paper_bgcolor="#44444E",
        font=dict(color="white"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="white",
            borderwidth=1
        )
    )
    st.plotly_chart(fig_village, use_container_width=True)

    st.subheader("🔥 Fires per Block per Month")
    fig_block = px.bar(
        block_month, x="year_month", y="Fire Events", color="Blok", barmode="group",
        template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig_block.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="#44444E",
        paper_bgcolor="#44444E",
        font=dict(color="white"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="white",
            borderwidth=1
        )
    )
    st.plotly_chart(fig_block, use_container_width=True)

with center:
    st.subheader("🗺️ Fire Hotspot Map")
    midpoint = (df["latitude"].mean(), df["longitude"].mean())
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v11",  # 🔹 ganti basemap lebih terang
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
                get_color="[255, 100, 100, 200]",
                get_radius=300,
            ),
        ],
    ))

with right:
    st.subheader("🔥 Fire Danger Rating")
    st.info("Block 1: LOW")
    st.info("Block 2: LOW")

st.subheader("📋 Fire Events Table")
st.dataframe(df[['date','owner','LC','village','latitude','longitude']], height=350)
