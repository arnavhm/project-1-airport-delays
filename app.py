import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration (Wide layout, custom title)
st.set_page_config(
    page_title="US Aviation Delays | Arnav H. Mutt",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS to make KPIs look like a pro dashboard
st.markdown(
    """
    <style>
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #e0e4eb;
        padding: 5% 5% 5% 10%;
        border-radius: 10px;
        color: #0f1116;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. Header
st.title("✈️ US Domestic Flight Operations & Delays (2015)")
st.markdown(
    """
    **Portfolio Project by Arnav Hemanth Mutt** | [LinkedIn](https://www.linkedin.com/in/arnav-h-987390302/) • [GitHub](https://github.com/arnavhm)
    
    *This interactive dashboard analyzes a representative 10% sample (~570k flights) of the 2015 US DOT dataset to identify operational bottlenecks, airline performance, and temporal delay patterns.*
"""
)
st.markdown("---")


# 3. Data Loading Logic
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/flights_sample.csv")
    # Map Day of Week numbers to names for better charts
    day_map = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    if "DAY_OF_WEEK" in df.columns:
        df["DAY_NAME"] = df["DAY_OF_WEEK"].map(day_map)
    return df


with st.spinner("Initializing aviation database..."):
    try:
        df = load_data()
    except FileNotFoundError:
        st.error(
            "Data file not found! Please ensure 'flights_sample.csv' is in 'data/processed/'."
        )
        st.stop()

# 4. Sidebar - Professional Filtering
with st.sidebar:
    st.header("🎛️ Flight Parameters")

    all_airlines = sorted(df["AIRLINE"].dropna().unique())
    all_airports = sorted(df["ORIGIN_AIRPORT"].dropna().unique())
    min_month, max_month = int(df["MONTH"].min()), int(df["MONTH"].max())

    selected_airlines = st.multiselect(
        "Select Airlines", all_airlines, placeholder="All Airlines"
    )
    selected_origin = st.multiselect(
        "Origin Airports", all_airports, placeholder="All Airports"
    )
    selected_months = st.slider(
        "Operating Months",
        min_value=min_month,
        max_value=max_month,
        value=(min_month, max_month),
    )

    st.markdown("---")
    st.markdown("### 💾 Export Data")
    st.caption("Download the current filtered dataset for local analysis.")

# Apply filters
filtered_df = df.copy()
if selected_airlines:
    filtered_df = filtered_df[filtered_df["AIRLINE"].isin(selected_airlines)]
if selected_origin:
    filtered_df = filtered_df[filtered_df["ORIGIN_AIRPORT"].isin(selected_origin)]
filtered_df = filtered_df[
    (filtered_df["MONTH"] >= selected_months[0])
    & (filtered_df["MONTH"] <= selected_months[1])
]

# Provide download button in sidebar (needs filtered data)
with st.sidebar:
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="filtered_flight_data.csv",
        mime="text/csv",
    )

# 5. Top-Level KPIs
total_flights = len(filtered_df)
delayed_flights = (
    (filtered_df["ARRIVAL_DELAY"] > 15).sum()
    if "ARRIVAL_DELAY" in filtered_df.columns
    else 0
)
delay_rate = (delayed_flights / total_flights * 100) if total_flights > 0 else 0
avg_delay = filtered_df["ARRIVAL_DELAY"].mean() if total_flights > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Flights (Est. Full Volume)", f"{(total_flights * 10):,}")
col2.metric("Sample Volume Processed", f"{total_flights:,}")
col3.metric("System Delay Rate (>15m)", f"{delay_rate:.1f}%")
col4.metric("Mean Arrival Delay", f"{avg_delay:.1f} min")

st.markdown("<br>", unsafe_allow_html=True)

# 6. Tabbed Interface for Advanced Analysis
tab1, tab2, tab3 = st.tabs(
    ["📊 Executive Overview", "🛫 Airline Deep-Dive", "⏱️ Temporal & Congestion Trends"]
)

# --- TAB 1: OVERVIEW ---
with tab1:
    st.markdown("#### System-Wide Operations")
    colA, colB = st.columns([1, 1.5])

    with colA:
        if total_flights > 0 and "DELAY_CATEGORY" in filtered_df.columns:
            dist_data = filtered_df["DELAY_CATEGORY"].value_counts().reset_index()
            dist_data.columns = ["Category", "Count"]
            color_map = {
                "On Time": "#2ca02c",
                "Minor (<15 min)": "#ffb74d",
                "Moderate (15-60 min)": "#f57c00",
                "Severe (>60 min)": "#d32f2f",
            }

            fig_pie = px.pie(
                dist_data,
                values="Count",
                names="Category",
                color="Category",
                color_discrete_map=color_map,
                hole=0.5,
                title="Delay Severity Breakdown",
            )
            fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

    with colB:
        if total_flights > 0:
            airport_stats = (
                filtered_df.groupby("ORIGIN_AIRPORT")
                .agg(
                    Total=("ARRIVAL_DELAY", "count"),
                    Delayed=("ARRIVAL_DELAY", lambda x: (x > 15).sum()),
                )
                .reset_index()
            )
            airport_stats = airport_stats[
                airport_stats["Total"] >= 50
            ]  # Filter low-volume
            airport_stats["Delay Rate (%)"] = (
                airport_stats["Delayed"] / airport_stats["Total"]
            ) * 100
            worst_airports = airport_stats.sort_values(
                "Delay Rate (%)", ascending=False
            ).head(12)

            fig_bar = px.bar(
                worst_airports,
                x="ORIGIN_AIRPORT",
                y="Delay Rate (%)",
                color="Delay Rate (%)",
                color_continuous_scale="Reds",
                title="Critical Origin Airports (Highest Delay %)",
            )
            fig_bar.update_layout(
                xaxis_title="Airport Code",
                yaxis_title="Delay Rate (%)",
                margin=dict(t=40, b=0, l=0, r=0),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 2: AIRLINE DEEP-DIVE ---
with tab2:
    st.markdown("#### Carrier Performance Metrics")
    colC, colD = st.columns(2)

    with colC:
        if total_flights > 0:
            airline_stats = (
                filtered_df.groupby("AIRLINE")
                .agg(
                    Total=("ARRIVAL_DELAY", "count"),
                    Delayed=("ARRIVAL_DELAY", lambda x: (x > 15).sum()),
                )
                .reset_index()
            )
            airline_stats["Delay Rate (%)"] = (
                airline_stats["Delayed"] / airline_stats["Total"]
            ) * 100
            airline_stats = airline_stats.sort_values("Delay Rate (%)", ascending=False)

            fig_airlines = px.bar(
                airline_stats,
                y="AIRLINE",
                x="Delay Rate (%)",
                orientation="h",
                color="Delay Rate (%)",
                color_continuous_scale="Blues",
                title="Carrier Delay Rate Rankings",
            )
            fig_airlines.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(t=40, b=0, l=0, r=0),
            )
            st.plotly_chart(fig_airlines, use_container_width=True)

    with colD:
        if total_flights > 0:
            # Box plot to show delay distribution (excluding extreme outliers for clean view)
            box_df = filtered_df[
                (filtered_df["ARRIVAL_DELAY"] > 15)
                & (filtered_df["ARRIVAL_DELAY"] < 180)
            ]
            fig_box = px.box(
                box_df,
                x="AIRLINE",
                y="ARRIVAL_DELAY",
                color="AIRLINE",
                title="Distribution of Delay Durations by Carrier (15m - 3h)",
            )
            fig_box.update_layout(
                showlegend=False,
                xaxis_title="Carrier",
                yaxis_title="Delay Duration (mins)",
                margin=dict(t=40, b=0, l=0, r=0),
            )
            st.plotly_chart(fig_box, use_container_width=True)

# --- TAB 3: TEMPORAL TRENDS ---
with tab3:
    st.markdown("#### Congestion & Temporal Heatmaps")
    colE, colF = st.columns(2)

    with colE:
        if total_flights > 0 and "TIME_OF_DAY" in filtered_df.columns:
            time_stats = (
                filtered_df.groupby("TIME_OF_DAY")
                .agg(
                    Total=("ARRIVAL_DELAY", "count"),
                    Delayed=("ARRIVAL_DELAY", lambda x: (x > 15).sum()),
                )
                .reset_index()
            )
            time_stats["Delay Rate (%)"] = (
                time_stats["Delayed"] / time_stats["Total"]
            ) * 100
            time_order = [
                "Morning (5am-12pm)",
                "Afternoon (12pm-5pm)",
                "Evening (5pm-9pm)",
                "Night (9pm-5am)",
            ]

            fig_time = px.area(
                time_stats,
                x="TIME_OF_DAY",
                y="Delay Rate (%)",
                markers=True,
                category_orders={"TIME_OF_DAY": time_order},
                title="Delay Volatility by Time of Day",
            )
            fig_time.update_traces(
                line_color="royalblue", fillcolor="rgba(65, 105, 225, 0.2)"
            )
            fig_time.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_time, use_container_width=True)

    with colF:
        if total_flights > 0 and "DAY_NAME" in filtered_df.columns:
            day_stats = (
                filtered_df.groupby("DAY_NAME")
                .agg(
                    Total=("ARRIVAL_DELAY", "count"),
                    Delayed=("ARRIVAL_DELAY", lambda x: (x > 15).sum()),
                )
                .reset_index()
            )
            day_stats["Delay Rate (%)"] = (
                day_stats["Delayed"] / day_stats["Total"]
            ) * 100
            day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

            fig_day = px.bar(
                day_stats,
                x="DAY_NAME",
                y="Delay Rate (%)",
                category_orders={"DAY_NAME": day_order},
                color="Delay Rate (%)",
                color_continuous_scale="Purples",
                title="Delay Impact by Day of Week",
            )
            fig_day.update_layout(margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig_day, use_container_width=True)
