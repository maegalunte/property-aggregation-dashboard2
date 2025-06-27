import streamlit as st
import pandas as pd
import pydeck as pdk

# Page config
st.set_page_config(page_title="Book of Business Dashboard", layout="wide")
st.title("📘 Book of Business Dashboard")

# Load data
file_path = "Book_with_Coordinates.xlsx"
df = pd.read_excel(file_path)
df.columns = df.columns.str.strip().str.lower()

# Sidebar filters
st.sidebar.header("🔍 Filters")
city_list = sorted(df["cust city"].dropna().unique())
zip_list = sorted(df["cust zip"].dropna().unique())
carrier_list = sorted(df["writing company"].dropna().unique())

selected_cities = st.sidebar.multiselect("Select Cities", city_list, default=city_list)
selected_zips = st.sidebar.multiselect("Select ZIP Codes", zip_list, default=zip_list)
selected_carriers = st.sidebar.multiselect("Select Carriers", carrier_list, default=carrier_list)

# Apply filters
filtered_df = df[
    df["cust city"].isin(selected_cities) &
    df["cust zip"].isin(selected_zips) &
    df["writing company"].isin(selected_carriers)
]

# Tabs
summary_tab, map_tab, export_tab = st.tabs(["📊 Dashboard", "🗺️ Coverage A Map", "📤 Export"])

with summary_tab:
    st.subheader("📊 Overview")
    st.metric("Filtered Policies", len(filtered_df))
    st.dataframe(filtered_df.head(10), use_container_width=True)

    if not filtered_df.empty and "dwelling limit" in filtered_df.columns:
        st.subheader("🏘️ Coverage A by ZIP Code")
        zip_summary = (
            filtered_df.groupby("cust zip")["dwelling limit"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        st.bar_chart(zip_summary.set_index("cust zip"))
    else:
        st.warning("Could not find 'Dwelling Limit' column in the dataset.")

with map_tab:
    st.subheader("🗺️ Coverage A Map")

    if {"latitude", "longitude", "dwelling limit"}.issubset(filtered_df.columns):
        map_df = filtered_df.copy()
        map_df["latitude"] = pd.to_numeric(map_df["latitude"], errors="coerce")
        map_df["longitude"] = pd.to_numeric(map_df["longitude"], errors="coerce")
        map_df["dwelling limit"] = pd.to_numeric(map_df["dwelling limit"], errors="coerce")
        map_df = map_df.dropna(subset=["latitude", "longitude", "dwelling limit"])

        if not map_df.empty:
            # Normalize CovA for color scaling
            max_cov = map_df["dwelling limit"].max()
            map_df["color_scale"] = map_df["dwelling limit"] / max_cov * 255

            # Build layer with tooltip
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position='[longitude, latitude]',
                get_radius=300,
                get_fill_color='[255, 255 - color_scale, 100]',
                pickable=True
            )

            view_state = pdk.ViewState(
                latitude=map_df["latitude"].mean(),
                longitude=map_df["longitude"].mean(),
                zoom=9,
                pitch=30
            )

            tooltip = {
                "html": "<b>{customer name}</b><br/>Carrier: {writing company}<br/>CovA: ${dwelling limit}",
                "style": {"backgroundColor": "white", "color": "black"}
            }

            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))
        else:
            st.info("No valid data to render the map.")
    else:
        st.warning("Required columns (latitude, longitude, dwelling limit) not found.")

with export_tab:
    st.subheader("📤 Download Filtered Data")
    st.download_button(
        label="Download CSV",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_book_of_business.csv",
        mime="text/csv"
    )
