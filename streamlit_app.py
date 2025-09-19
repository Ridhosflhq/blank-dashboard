import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk

# Load data
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgZRjQlxUsTPmrXiDCtwky4_A0FJrGDj_r7JLgsqi8gvjOWxmDKpBSdJDWFF38VfRuxUxzWSjhk46C/pub?output=csv"
df = pd.read_csv(url)
df['date'] = pd.to_datetime(df['date'])

# --- Aggregations ---
today = pd.Timestamp.today().normalize()
this_month, this_year = today.month, today.year
today_count = df[df['date'].dt.date == today.date()].shape[0]
month_count = df[(df['date'].dt.month == this_month) & (df['date'].dt.year == this_year)].shape[0]

village_count = df['village'].value_counts().reset_index()
village_count.columns = ['Village', 'Fire Events']

df['year_month'] = df['date'].dt.to_period('M').astype(str)
block_month = df.groupby(['year_month', 'Blok']).size().reset_index(name='Fire Events')

# --- Layout settings ---
st.set_page_config(layout="wide")
st.title("🔥 Fire Hotspot Monitoring Dashboard")

# --- Top KPIs ---
col1, col2 = st.columns(2)
col1.metric("🔥 Fires Today", today_count)
col2.metric("🔥 Fires This Month", month_count)

# --- Main content (Left, Center, Right) ---
left, center, right = st.columns([1,2,1.2])

# Left column: charts
with left:
    st.subheader("🔥 Fires per Village")
    fig_village = px.bar(village_count, x="Village", y="Fire Events", color="Village")
    st.plotly_chart(fig_village, use_container_width=True)

    st.subheader("🔥 Fires per Block per Month")
    fig_block = px.bar(block_month, x="year_month", y="Fire Events", color="Blok", barmode="group")
    st.plotly_chart(fig_block, use_container_width=True)

# Center: map
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
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[longitude, latitude]",
                get_color="[255, 0, 0, 160]",
                get_radius=300,
            ),
        ],
    ))

# Right column: rating + table
with right:
    st.subheader("🔥 Fire Danger Rating")
    st.info("Block 1: LOW")   # later: calculate dynamically
    st.info("Block 2: LOW")   # later: calculate dynamically
    
    st.subheader("📋 Fire Events Table")
    st.dataframe(df[['date','owner','LC','village','latitude','longitude']], height=300)
