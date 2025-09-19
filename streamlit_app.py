import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgZRjQlxUsTPmrXiDCtwky4_A0FJrGDj_r7JLgsqi8gvjOWxmDKpBSdJDWFF38VfRuxUxzWSjhk46C/pub?output=csv"
df = pd.read_csv(url)

# Convert date
df['date'] = pd.to_datetime(df['date'])

# --- KPIs ---
today = pd.Timestamp.today().normalize()
this_month = today.month
this_year = today.year

today_count = df[df['date'].dt.date == today.date()].shape[0]
month_count = df[(df['date'].dt.month == this_month) & (df['date'].dt.year == this_year)].shape[0]

# --- Aggregations ---
village_count = df['village'].value_counts().reset_index()
village_count.columns = ['Village', 'Fire Events']

df['year_month'] = df['date'].dt.to_period('M').astype(str)
block_month = df.groupby(['year_month', 'Blok']).size().reset_index(name='Fire Events')

# --- Layout ---
st.set_page_config(layout="wide")
st.title("🔥 Fire Hotspot Monitoring Dashboard")

# KPIs on top
col1, col2 = st.columns(2)
col1.metric("Today's Fires", today_count)
col2.metric("This Month's Fires", month_count)

# Middle: Bar charts
col3, col4 = st.columns(2)
with col3:
    fig_village = px.bar(village_count, x="Village", y="Fire Events", title="Fires per Village")
    st.plotly_chart(fig_village, use_container_width=True)
with col4:
    fig_block = px.bar(block_month, x="year_month", y="Fire Events", color="Blok", barmode="group",
                       title="Fires per Block per Month")
    st.plotly_chart(fig_block, use_container_width=True)

# Bottom: Data table
st.subheader("📋 Fire Event Records")
st.dataframe(df[['latitude','longitude','date','owner','LC','village']])
