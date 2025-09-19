import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# Page setup
st.set_page_config(page_title="🔥 Fire Hotspot Monitoring", layout="wide")
st.title("🔥 Fire Hotspot Monitoring Dashboard")

# Load Data from Google Sheets
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgZRjQlxUsTPmrXiDCtwky4_A0FJrGDj_r7JLgsqi8gvjOWxmDKpBSdJDWFF38VfRuxUxzWSjhk46C/pub?output=csv"
df = pd.read_csv(url)

# Convert date column
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# --- KPIs ---
today = pd.Timestamp.today().normalize()
this_month = today.month
this_year = today.year

today_count = df[df["date"].dt.date == today.date()].shape[0]
month_count = df[(df["date"].dt.month == this_month) & (df["date"].dt.year == this_year)].shape[0]

col1, col2 = st.columns(2)
col1.metric("🔥 Today's Fire Events", today_count)
col2.metric("🔥 This Month's Fire Events", month_count)

# --- Chart 1: Fire events per village ---
village_count = df["village"].value_counts().reset_index()
village_count.columns = ["Village", "Fire Events"]
fig_village = px.bar(village_count, x="Village", y="Fire Events", title="Fire Events per Village")
st.plotly_chart(fig_village, use_container_width=True)

# --- Chart 2: Fire events per block (monthly aggregate) ---
df["month"] = df["date"].dt.to_period("M").astype(str)
block_month = df.groupby(["Blok", "month"]).size().reset_index(name="count")
fig_block = px.bar(block_month, x="month", y="count", color="Blok", barmode="group",
                   title="Monthly Fire Events per Block")
st.plotly_chart(fig_block, use_container_width=True)

# --- Map ---
st.subheader("🗺️ Fire Hotspot Map")
m = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=10)
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=5,
        color="red",
        fill=True,
        popup=f"Date: {row['date']}<br>Owner: {row['owner']}<br>Village: {row['village']}<br>LC: {row['LC']}"
    ).add_to(m)

st_folium(m, width=800, height=500)

# --- Table ---
st.subheader("📋 Fire Hotspot Data Table")
st.dataframe(df[["latitude", "longitude", "date", "owner", "LC", "village"]])
