import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np
import sys
import joblib

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.data.pipeline import load_and_preprocess_data

# 1. Page Configuration (Wide layout, custom title)
st.set_page_config(
    page_title="US Aviation Operations Dashboard | Arnav H. Mutt",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Premium Styling & Google Font Injections (CSS Glassmorphism & Hover Micro-Animations)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Typography Reset */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Metric Cards - Premium Glassmorphism Design */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(226, 232, 240, 0.8);
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        color: #0f172a;
        transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 20px -8px rgba(0, 0, 0, 0.12), 0 4px 12px -2px rgba(0, 0, 0, 0.06);
        border-color: rgba(99, 102, 241, 0.4);
    }
    
    /* Custom Info Boxes styling */
    .explain-card {
        background-color: #f8fafc;
        border-left: 5px solid #6366f1;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    /* Styled headings */
    .premium-h4 {
        color: #1e293b;
        font-weight: 600;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. Auxiliary Metadata Data Loaders
@st.cache_data
def load_airlines():
    path = "data/raw/airlines.csv"
    if not os.path.exists(path):
        return {}
    df_air = pd.read_csv(path)
    df_air["IATA_CODE"] = df_air["IATA_CODE"].astype(str).str.strip()
    return dict(zip(df_air["IATA_CODE"], df_air["AIRLINE"]))

@st.cache_data
def load_airports():
    path = "data/raw/airports.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    df_port = pd.read_csv(path)
    df_port["IATA_CODE"] = df_port["IATA_CODE"].astype(str).str.strip()
    return df_port

# Helper conversion functions for dynamic column generation
def categorize_delay(delay):
    if pd.isna(delay):
        return "Unknown"
    if delay <= 0:
        return "On Time"
    elif delay <= 15:
        return "Minor (<15 min)"
    elif delay <= 60:
        return "Moderate (15-60 min)"
    else:
        return "Severe (>60 min)"

def categorize_time_of_day(scheduled_dep):
    if pd.isna(scheduled_dep) or not (0 <= scheduled_dep < 2400):
        return "Unknown"
    hour = int(scheduled_dep) // 100
    if 5 <= hour < 12:
        return "Morning (5am-12pm)"
    elif 12 <= hour < 17:
        return "Afternoon (12pm-5pm)"
    elif 17 <= hour < 21:
        return "Evening (5pm-9pm)"
    else:
        return "Night (9pm-5am)"

# 3. Main Data Ingestion (Shared Pipeline for Zero Training-Serving Skew)
@st.cache_data
def load_data():
    df, config = load_and_preprocess_data()
    # Add UI-specific derived columns
    if "ARRIVAL_DELAY" in df.columns:
        df["DELAY_CATEGORY"] = df["ARRIVAL_DELAY"].apply(categorize_delay)
    return df, config

@st.cache_resource
def load_model():
    path = "artifacts/model_pipeline.joblib"
    if os.path.exists(path):
        return joblib.load(path)
    return None

with st.spinner("Initializing ML inference pipeline and loading data..."):
    try:
        df, config = load_data()
        ml_model = load_model()
    except FileNotFoundError:
        st.error("Data file not found! Please ensure 'flights_sample.csv' is in 'data/processed/'.")
        st.stop()

# 4. Sidebar - Control Telemetry
with st.sidebar:
    st.header("🎛️ Flight Parameters")

    all_airlines = sorted(df["AIRLINE_NAME"].dropna().unique())
    all_airports = sorted(df["ORIGIN_AIRPORT"].dropna().unique())
    min_month, max_month = int(df["MONTH"].min()), int(df["MONTH"].max())

    selected_airlines = st.multiselect("Select Airlines", all_airlines, placeholder="All Airlines")
    selected_origin = st.multiselect("Origin Airports", all_airports, placeholder="All Airports")
    selected_months = st.slider("Operating Months", min_value=min_month, max_value=max_month, value=(min_month, max_month))

# Filter Application
filtered_df = df.copy()
if selected_airlines:
    filtered_df = filtered_df[filtered_df["AIRLINE_NAME"].isin(selected_airlines)]
if selected_origin:
    filtered_df = filtered_df[filtered_df["ORIGIN_AIRPORT"].isin(selected_origin)]
filtered_df = filtered_df[(filtered_df["MONTH"] >= selected_months[0]) & (filtered_df["MONTH"] <= selected_months[1])]

# ----------------- WHAT-IF SCENARIO SIMULATOR -----------------
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🎛️ Operational Improvement Simulator")
    st.sidebar.caption("Simulate decisions to improve operations and see estimated savings.")
    sim_nk_pct = st.slider("Spirit Airlines (NK) Turnaround Relief", 0, 100, 0, help="Reduce delay minutes of Spirit Airlines flights by this %.")
    sim_ord_pct = st.slider("Chicago O'Hare (ORD) Traffic Relief", 0, 100, 0, help="Reduce delay minutes of ORD flights by this %.")
    sim_evening_pct = st.slider("Evening Shift Scheduling Buffer", 0, 100, 0, help="Reduce cascading evening delays (5pm-9pm) by this %.")

# Apply simulation parameters in real-time
sim_df = filtered_df.copy()
passenger_hours_saved = 0.0

if "ARRIVAL_DELAY" in sim_df.columns:
    sim_df["ORIGINAL_ARRIVAL_DELAY"] = sim_df["ARRIVAL_DELAY"]
    
    # Spirit Airlines NK adjustment
    nk_mask = (sim_df["AIRLINE"] == "NK") | (sim_df["AIRLINE_NAME"] == "Spirit Air Lines")
    if sim_nk_pct > 0:
        pos_delay_mask = nk_mask & (sim_df["ARRIVAL_DELAY"] > 0)
        sim_df.loc[pos_delay_mask, "ARRIVAL_DELAY"] = sim_df.loc[pos_delay_mask, "ARRIVAL_DELAY"] * (1 - sim_nk_pct / 100)
        
    # ORD adjustment
    ord_mask = (sim_df["ORIGIN_AIRPORT"] == "ORD") | (sim_df["DESTINATION_AIRPORT"] == "ORD")
    if sim_ord_pct > 0:
        pos_delay_mask = ord_mask & (sim_df["ARRIVAL_DELAY"] > 0)
        sim_df.loc[pos_delay_mask, "ARRIVAL_DELAY"] = sim_df.loc[pos_delay_mask, "ARRIVAL_DELAY"] * (1 - sim_ord_pct / 100)
        
    # Evening buffer adjustment
    evening_mask = sim_df["TIME_OF_DAY"] == "Evening (5pm-9pm)"
    if sim_evening_pct > 0:
        pos_delay_mask = evening_mask & (sim_df["ARRIVAL_DELAY"] > 0)
        sim_df.loc[pos_delay_mask, "ARRIVAL_DELAY"] = sim_df.loc[pos_delay_mask, "ARRIVAL_DELAY"] * (1 - sim_evening_pct / 100)
        
    # Recalculate derived columns
    sim_df["IS_DELAYED"] = (sim_df["ARRIVAL_DELAY"] > 15).astype(int)
    sim_df["DELAY_CATEGORY"] = sim_df["ARRIVAL_DELAY"].apply(categorize_delay)
    
    # Calculate savings
    delay_saved_mins = (sim_df["ORIGINAL_ARRIVAL_DELAY"] - sim_df["ARRIVAL_DELAY"]).sum()
    # 10x sample factor, assume average 120 passengers per flight
    passenger_hours_saved = (delay_saved_mins * 10 * 120) / 60

# Override filtered_df with simulated df so all charts automatically render simulated future
original_filtered_df = filtered_df.copy()
filtered_df = sim_df

# ----------------- ROUTE EXPLORER SIDEBAR -----------------
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🛣️ Route Explorer")
    st.sidebar.caption("Highlight a specific flight route path on the map.")
    
    # Get all origins
    origins = sorted(df["ORIGIN_AIRPORT"].dropna().unique())
    selected_route_origin = st.selectbox("Route Origin", origins, index=origins.index("ORD") if "ORD" in origins else 0)
    
    # Get all destinations from this origin
    destinations = sorted(df[df["ORIGIN_AIRPORT"] == selected_route_origin]["DESTINATION_AIRPORT"].dropna().unique())
    selected_route_dest = st.selectbox("Route Destination", destinations)

# Defer CSV processing to resolve interaction lag
@st.cache_data
def convert_df_to_csv(dataframe_to_export):
    return dataframe_to_export.to_csv(index=False).encode("utf-8")

with st.sidebar:
    st.markdown("---")
    st.markdown("### 💾 Export Data")
    st.caption("Download the current filtered dataset for local analysis.")
    csv_bytes = convert_df_to_csv(filtered_df)
    st.download_button(
        label="Download CSV",
        data=csv_bytes,
        file_name="filtered_flight_data.csv",
        mime="text/csv",
    )

# 5. Header Visual Branding
col_logo, col_title = st.columns([0.08, 0.92])
with col_title:
    st.markdown("### Portfolio Project by Arnav Hemanth Mutt | Aviation Operations Analytics")
    st.markdown("[LinkedIn](https://www.linkedin.com/in/arnav-h-987390302/) • [GitHub](https://github.com/arnavhm)")

# 6. Top-Level KPIs (Premium Layout with metric container styling)
total_flights = len(filtered_df)
delayed_flights = (filtered_df["ARRIVAL_DELAY"] > 15).sum() if "ARRIVAL_DELAY" in filtered_df.columns else 0
delay_rate = (delayed_flights / total_flights * 100) if total_flights > 0 else 0
avg_delay = filtered_df["ARRIVAL_DELAY"].mean() if total_flights > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Flights (Est. Full Volume)", f"{(total_flights * 10):,}")
col2.metric("Sample Volume Processed", f"{total_flights:,}")
col3.metric("System Delay Rate (>15m)", f"{delay_rate:.1f}%")
col4.metric("Mean Arrival Delay", f"{avg_delay:.1f} min")

# Render active simulation banner
if sim_nk_pct > 0 or sim_ord_pct > 0 or sim_evening_pct > 0:
    st.success(
        f"💡 **Prescriptive Simulation Mode Active:** Recalculating airport network operations under hypothetical improvements... "
        f"Estimated Savings: **{passenger_hours_saved:,.0f} Passenger Hours** of delay avoided!"
    )

st.markdown("<br>", unsafe_allow_html=True)

# 7. Tabbed Interface for Advanced Analysis (With Geospatial and Statistics additions)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive Overview", 
    "🛫 Airline Deep-Dive", 
    "⏱️ Temporal & Congestion Trends",
    "📖 Methodology & Statistics",
    "⚙️ Rolls-Royce SLA Optimizer"
])

# --- TAB 1: OVERVIEW (Pie + Geospatial Scatter Mapbox + Route Overlay + Causes) ---
with tab1:
    st.markdown("#### System-Wide Operations")
    colA, colB = st.columns([1, 1.8])

    with colA:
        if total_flights > 0 and "DELAY_CATEGORY" in filtered_df.columns:
            dist_data = filtered_df["DELAY_CATEGORY"].value_counts().reset_index()
            dist_data.columns = ["Category", "Count"]
            color_map = {
                "On Time": "#10b981",          # Teal/Green
                "Minor (<15 min)": "#fbbf24",  # Amber/Yellow
                "Moderate (15-60 min)": "#f97316", # Orange
                "Severe (>60 min)": "#ef4444",   # Red
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
            fig_pie.update_layout(
                margin=dict(t=40, b=0, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with colB:
        if total_flights > 0:
            with st.spinner("Rendering geospatial traffic network..."):
                # Aggregate coordinates to map points
                map_stats = (
                    filtered_df.groupby("ORIGIN_AIRPORT", observed=True)
                    .agg(
                        Total=("ARRIVAL_DELAY", "count"),
                        Delayed=("ARRIVAL_DELAY", lambda x: (x > 15).sum()),
                        Avg_Delay=("ARRIVAL_DELAY", "mean")
                    )
                    .reset_index()
                )
                map_stats["Delay Rate (%)"] = (map_stats["Delayed"] / map_stats["Total"]) * 100
                map_stats["ORIGIN_AIRPORT"] = map_stats["ORIGIN_AIRPORT"].astype(str)
                
                airports_df = load_airports()
                if not airports_df.empty:
                    map_data = map_stats.merge(airports_df, left_on="ORIGIN_AIRPORT", right_on="IATA_CODE")
                    map_data = map_data.dropna(subset=["LATITUDE", "LONGITUDE"])
                    
                    fig_map = px.scatter_mapbox(
                        map_data,
                        lat="LATITUDE",
                        lon="LONGITUDE",
                        size="Total",
                        color="Delay Rate (%)",
                        color_continuous_scale="RdYlGn_r", # Red-Yellow-Green reversed
                        size_max=35,
                        zoom=3,
                        hover_name="AIRPORT",
                        hover_data={
                            "ORIGIN_AIRPORT": True,
                            "CITY": True,
                            "STATE": True,
                            "Total": ":,",
                            "Delay Rate (%)": ":.1f",
                            "Avg_Delay": ":.1f",
                            "LATITUDE": False,
                            "LONGITUDE": False
                        },
                        title="Geospatial Airport Network (Flight Volume & Congestion Map)",
                    )
                    
                    # Map Path Overlay
                    origin_coords = airports_df[airports_df["IATA_CODE"] == selected_route_origin]
                    dest_coords = airports_df[airports_df["IATA_CODE"] == selected_route_dest]
                    
                    if not origin_coords.empty and not dest_coords.empty:
                        lat1, lon1 = origin_coords.iloc[0]["LATITUDE"], origin_coords.iloc[0]["LONGITUDE"]
                        lat2, lon2 = dest_coords.iloc[0]["LATITUDE"], dest_coords.iloc[0]["LONGITUDE"]
                        
                        # Add route path line
                        fig_map.add_trace(go.Scattermapbox(
                            lat=[lat1, lat2],
                            lon=[lon1, lon2],
                            mode="lines+markers",
                            line=dict(width=4, color="#4f46e5"),
                            marker=dict(size=12, color="#4f46e5"),
                            hoverinfo="text",
                            text=[f"Origin Path: {selected_route_origin}", f"Destination Path: {selected_route_dest}"],
                            name="Selected Route Path Overlay"
                        ))
                    
                    fig_map.update_layout(
                        mapbox_style="carto-positron",
                        margin=dict(t=40, b=0, l=0, r=0),
                        height=450,
                        showlegend=False
                    )
                    st.plotly_chart(fig_map, use_container_width=True)
                else:
                    st.warning("Geospatial database (airports.csv) missing. Map visualization bypassed.")

    st.markdown("---")
    
    # Delay Cause Attribution Chart
    col_causes, col_airports = st.columns(2)
    
    with col_causes:
        st.markdown("##### 🔍 Delay Root Cause Attribution (Attributed Minutes)")
        delayed_subset = filtered_df[filtered_df["ARRIVAL_DELAY"] > 15]
        
        if len(delayed_subset) > 0:
            delay_causes = ["Late Arriving Aircraft", "Air System Congestion", "Airline Inefficiency", "Weather Disruptions", "Security Incidents"]
            delay_cols = ["LATE_AIRCRAFT_DELAY", "AIR_SYSTEM_DELAY", "AIRLINE_DELAY", "WEATHER_DELAY", "SECURITY_DELAY"]
            
            # Compute average of each delay type
            avg_minutes = [delayed_subset[col].mean() for col in delay_cols]
            avg_minutes = [0.0 if pd.isna(x) else x for x in avg_minutes]
            
            cause_df = pd.DataFrame({"Cause": delay_causes, "Average Minutes": avg_minutes})
            cause_df = cause_df.sort_values("Average Minutes", ascending=True)
            
            fig_causes = px.bar(
                cause_df,
                x="Average Minutes",
                y="Cause",
                orientation='h',
                color="Cause",
                color_discrete_sequence=["#818cf8", "#6366f1", "#4f46e5", "#4338ca", "#3730a3"],
                labels={"Average Minutes": "Avg Minutes per Delayed Flight", "Cause": ""}
            )
            fig_causes.update_layout(
                showlegend=False,
                margin=dict(t=10, b=0, l=0, r=0),
                height=300
            )
            st.plotly_chart(fig_causes, use_container_width=True)
        else:
            st.info("No delayed flights detected in the current filtered subset.")

    with col_airports:
        st.markdown("##### 🚨 Critical Bottlenecks: Origin Airports with Highest Delays")
        if total_flights > 0:
            airport_stats = (
                filtered_df.groupby("ORIGIN_AIRPORT", observed=True)
                .agg(
                    Total=("ARRIVAL_DELAY", "count"),
                    Delayed=("ARRIVAL_DELAY", lambda x: (x > 15).sum()),
                )
                .reset_index()
            )
            airport_stats = airport_stats[airport_stats["Total"] >= 50]
            airport_stats["Delay Rate (%)"] = (airport_stats["Delayed"] / airport_stats["Total"]) * 100
            worst_airports = airport_stats.sort_values("Delay Rate (%)", ascending=False).head(10)
            
            fig_bar = px.bar(
                worst_airports,
                x="ORIGIN_AIRPORT",
                y="Delay Rate (%)",
                color="Delay Rate (%)",
                color_continuous_scale="Reds",
            )
            fig_bar.update_layout(
                xaxis_title="Airport Code",
                yaxis_title="Delay Rate (%)",
                height=300,
                margin=dict(t=10, b=0, l=0, r=0),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 2: AIRLINE DEEP-DIVE (Codes resolved to full business names) ---
with tab2:
    st.markdown("#### Carrier Performance Metrics")
    colC, colD = st.columns(2)

    with colC:
        if total_flights > 0:
            airline_stats = (
                filtered_df.groupby("AIRLINE_NAME", observed=True)
                .agg(
                    Total=("ARRIVAL_DELAY", "count"),
                    Delayed=("ARRIVAL_DELAY", lambda x: (x > 15).sum()),
                )
                .reset_index()
            )
            airline_stats["Delay Rate (%)"] = (airline_stats["Delayed"] / airline_stats["Total"]) * 100
            airline_stats = airline_stats.sort_values("Delay Rate (%)", ascending=False)

            fig_airlines = px.bar(
                airline_stats,
                y="AIRLINE_NAME",
                x="Delay Rate (%)",
                orientation="h",
                color="Delay Rate (%)",
                color_continuous_scale="Blues",
                title="Carrier Delay Rate Rankings",
            )
            fig_airlines.update_layout(
                yaxis={"categoryorder": "total ascending", "title": ""},
                margin=dict(t=40, b=0, l=0, r=0),
                height=450
            )
            st.plotly_chart(fig_airlines, use_container_width=True)

    with colD:
        if total_flights > 0:
            box_df = filtered_df[(filtered_df["ARRIVAL_DELAY"] > 15) & (filtered_df["ARRIVAL_DELAY"] < 180)]
            fig_box = px.box(
                box_df,
                x="AIRLINE_NAME",
                y="ARRIVAL_DELAY",
                color="AIRLINE_NAME",
                title="Distribution of Delay Durations by Carrier (15m - 3h)",
            )
            fig_box.update_layout(
                showlegend=False,
                xaxis_title="",
                yaxis_title="Delay Duration (mins)",
                margin=dict(t=40, b=0, l=0, r=0),
                height=450
            )
            st.plotly_chart(fig_box, use_container_width=True)

# --- TAB 3: TEMPORAL TRENDS (Route Explorer Analytics) ---
with tab3:
    st.markdown("#### Congestion & Temporal Heatmaps")
    colE, colF = st.columns(2)

    with colE:
        if total_flights > 0 and "TIME_OF_DAY" in filtered_df.columns:
            time_stats = (
                filtered_df.groupby("TIME_OF_DAY", observed=True)
                .agg(
                    Total=("ARRIVAL_DELAY", "count"),
                    Delayed=("ARRIVAL_DELAY", lambda x: (x > 15).sum()),
                )
                .reset_index()
            )
            time_stats["Delay Rate (%)"] = (time_stats["Delayed"] / time_stats["Total"]) * 100
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
            fig_time.update_traces(line_color="indigo", fillcolor="rgba(99, 102, 241, 0.2)")
            fig_time.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=400)
            st.plotly_chart(fig_time, use_container_width=True)

    with colF:
        if total_flights > 0 and "DAY_NAME" in filtered_df.columns:
            day_stats = (
                filtered_df.groupby("DAY_NAME", observed=True)
                .agg(
                    Total=("ARRIVAL_DELAY", "count"),
                    Delayed=("ARRIVAL_DELAY", lambda x: (x > 15).sum()),
                )
                .reset_index()
            )
            day_stats["Delay Rate (%)"] = (day_stats["Delayed"] / day_stats["Total"]) * 100
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
            fig_day.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=400)
            st.plotly_chart(fig_day, use_container_width=True)

    st.markdown("---")
    
    # Route Explorer Analytics
    st.markdown("#### 🛣️ Flight Route Congestion & Network Path Analyzer")
    route_flights = original_filtered_df[
        (original_filtered_df["ORIGIN_AIRPORT"] == selected_route_origin) & 
        (original_filtered_df["DESTINATION_AIRPORT"] == selected_route_dest)
    ]
    
    if len(route_flights) > 0:
        route_total = len(route_flights)
        route_delayed = (route_flights["ARRIVAL_DELAY"] > 15).sum()
        route_delay_rate = (route_delayed / route_total) * 100
        route_avg_delay = route_flights["ARRIVAL_DELAY"].mean()
        
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Route Flight Count (Sample)", f"{route_total:,}")
        col_r2.metric("Route Delay Rate", f"{route_delay_rate:.1f}%")
        col_r3.metric("Route Avg Delay", f"{route_avg_delay:.1f} min")
        
        st.info(f"📍 Flight Path highlighted on the map: **{selected_route_origin}** &rarr; **{selected_route_dest}**")
    else:
        st.info(f"No direct sample flights found on route: **{selected_route_origin}** &rarr; **{selected_route_dest}** under current filters.")

# --- TAB 4: METHODOLOGY & STATISTICS (Delay Risk Profiler) ---
with tab4:
    st.markdown("#### Scientific Rigor & Statistical Explainability")
    
    col_stat1, col_stat2 = st.columns([1.5, 1])
    
    with col_stat1:
        st.markdown("<h4 class='premium-h4'>Arrival Delay Frequency Distribution (Heavy-Tail Profile)</h4>", unsafe_allow_html=True)
        if total_flights > 0:
            vis_delays = filtered_df["ARRIVAL_DELAY"].dropna()
            vis_delays_clipped = np.clip(vis_delays, -30, 180)
            
            fig_hist = px.histogram(
                vis_delays_clipped,
                nbins=70,
                color_discrete_sequence=["#6366f1"],
                labels={"value": "Arrival Delay (minutes)"},
                title="Delay Frequency Inception (Clipped at -30m to 180m for readability)"
            )
            fig_hist.update_layout(
                showlegend=False,
                xaxis_title="Minutes relative to Schedule (Negative = Early)",
                yaxis_title="Flight Count",
                margin=dict(t=40, b=0, l=0, r=0),
                height=380
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
    with col_stat2:
        st.markdown("<h4 class='premium-h4'>Statistical Insights: Mean vs. Median</h4>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class='explain-card'>
                <strong>Mathematical Skewness Analysis:</strong><br>
                The dataset displays a classic operational reliability pattern:
                <ul>
                    <li><strong>Median Delay: -5.00 min</strong>. More than half of all flights arrive ahead of scheduled time.</li>
                    <li><strong>Average Delay: +4.40 min</strong>. The average is dragged positive by a right-skewed heavy tail.</li>
                </ul>
                This skewness is explained by Queueing Theory: delays scale non-linearly under hub congestion:
                <br><br>
                <center><strong><em>Delay &propto; &rho; / (1 - &rho;)</em></strong></center>
                <br>
                where <strong>&rho;</strong> is the runway capacity utilization. When &rho; approaches 1, a small traffic surge generates hours of cascading delays.
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("#### 🧠 ML-Powered Economic Decision Simulator")
    st.caption("Live prediction of flight delay utilizing the trained model artifact, translated into financial rebooking decisions.")
    
    col_ui1, col_ui2 = st.columns([1, 1.2])
    
    with col_ui1:
        ui_airline = st.selectbox("Select Airline", all_airlines)
        airport_volume = df["ORIGIN_AIRPORT"].value_counts()
        top_airports = sorted(airport_volume.head(50).index)
        ui_origin = st.selectbox("Select Origin Airport", top_airports, index=top_airports.index("ORD") if "ORD" in top_airports else 0)
        destinations = sorted(df[df["ORIGIN_AIRPORT"] == ui_origin]["DESTINATION_AIRPORT"].dropna().unique())
        ui_dest = st.selectbox("Select Destination", destinations)
        ui_month = st.selectbox("Select Month", list(range(1, 13)), format_func=lambda x: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][x-1])
        ui_time = st.selectbox("Select Scheduled Departure Shift", ["Morning (5am-12pm)", "Afternoon (12pm-5pm)", "Evening (5pm-9pm)", "Night (9pm-5am)"])
        ui_day = st.selectbox("Select Day of Week", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        
    with col_ui2:
        if ml_model is not None:
            # Construct inference dataframe matching training features
            inference_df = pd.DataFrame({
                "AIRLINE_NAME": [ui_airline],
                "ORIGIN_AIRPORT": [ui_origin],
                "DESTINATION_AIRPORT": [ui_dest],
                "DAY_NAME": [ui_day],
                "TIME_OF_DAY": [ui_time],
                "DISTANCE": [df[(df["ORIGIN_AIRPORT"] == ui_origin) & (df["DESTINATION_AIRPORT"] == ui_dest)]["DISTANCE"].mean() if not df[(df["ORIGIN_AIRPORT"] == ui_origin) & (df["DESTINATION_AIRPORT"] == ui_dest)].empty else 500],
                "MONTH": [ui_month]
            })
            
            # Cast categoricals
            for c in config["model"]["categorical_features"]:
                inference_df[c] = inference_df[c].astype("category")
                
            predicted_delay = ml_model.predict(inference_df)[0]
            
            st.markdown(f"##### Predicted Arrival Delay: **{predicted_delay:+.1f} minutes**")
            
            # Economic Translation (EngineWatch AOG logic equivalent)
            risk_threshold = config["model"]["risk_threshold_minutes"]
            cost_proactive = config["economic"]["proactive_rebooking_cost"]
            cost_reactive = config["economic"]["reactive_delay_penalty"]
            
            if predicted_delay > risk_threshold:
                st.error(f"🚨 **HIGH RISK**: Severe Delay > {risk_threshold} mins Predicted.")
                st.markdown(
                    f"""
                    **Economic Recommendation:** Proactively rebook priority passengers.
                    * Proactive Rebooking Cost: **${cost_proactive}**
                    * Estimated Reactive Penalty (AOG/SLA): **${cost_reactive}**
                    * Expected Value Savings per passenger: **${cost_reactive - cost_proactive}**
                    """
                )
            elif predicted_delay > 15:
                st.warning("⚠️ **MODERATE RISK**: Minor delay predicted. Monitor conditions.")
                st.markdown("**Economic Recommendation:** Standard operations. No proactive rebooking required.")
            else:
                st.success("✅ **LOW RISK**: Flight predicted to be on time.")
                st.markdown("**Economic Recommendation:** Standard operations. No proactive rebooking required.")
                
        else:
            st.error("ML Model artifact not found. Please run `python scripts/train_delay_model.py`.")

# --- TAB 5: ROLLS-ROYCE CASE STUDY (Engine Health & SLA Optimizer) ---
with tab5:
    st.markdown("#### ⚙️ Rolls-Royce Engine Health & TotalCare™ SLA Optimizer")
    st.markdown(
        """
        *This specialized module demonstrates prescriptive analytics tailored for **Engine Health Monitoring (EHM)** and 
        **TotalCare® (Power by the Hour)** fleet contract management.*
        """
    )
    
    col_rr1, col_rr2 = st.columns([1.2, 1])
    
    with col_rr1:
        st.markdown("<h4 class='premium-h4'>TotalCare® Service Level Agreement (SLA) Optimizer</h4>", unsafe_allow_html=True)
        st.caption("Simulate deploying predictive EHM analytics across the fleet to prevent mechanical delays.")
        
        # Slider to simulate EHM predictive maintenance coverage
        ehm_coverage = st.slider("Predictive Maintenance (EHM) Deployment Coverage", 0, 100, 0, 
                                 help="Percentage of the fleet equipped with real-time predictive anomaly detection.")
        
        # SLA contract penalty rate
        sla_penalty_rate = st.number_input("SLA Delay Penalty Rate ($/hour)", min_value=1000, max_value=15000, value=5000, step=500)
        
    with col_rr2:
        # Calculate SLA savings
        if "AIRLINE_DELAY" in filtered_df.columns:
            total_maint_delay_mins = filtered_df["AIRLINE_DELAY"].sum()
            # EHM prevention rate: assume predicting/preventing 40% of maintenance delays
            prevention_rate = 0.40
            mins_saved = total_maint_delay_mins * (ehm_coverage / 100.0) * prevention_rate
            
            # Scale up from 10% sample
            scaled_mins_saved = mins_saved * 10
            dollar_savings = (scaled_mins_saved / 60.0) * sla_penalty_rate
            
            st.metric("Maintenance Delay Avoided", f"{scaled_mins_saved:,.0f} mins")
            st.metric("TotalCare™ Penalty Savings", f"${dollar_savings:,.2f}")
        else:
            st.warning("Airline Delay telemetry not available in dataset.")

    st.markdown("---")
    st.markdown("<h4 class='premium-h4'>Turbine Thermal Fatigue Index vs. Flight Distance Profile</h4>", unsafe_allow_html=True)
    st.markdown(
        """
        **Aviation Engineering Context:** Takeoffs and landings subject jet engines to severe thermal transients and aerodynamic loads (wear cycles). 
        Short-haul flights (frequent takeoffs) undergo significantly higher **thermal fatigue cycles per flight hour** than long-haul flights.
        """
    )
    
    if "DISTANCE" in filtered_df.columns:
        # Categorize flights by distance
        # Copy to avoid setting with copy warning
        plot_df = filtered_df.copy()
        plot_df["DISTANCE_GROUP"] = pd.cut(plot_df["DISTANCE"], 
                                           bins=[0, 300, 700, 1200, 2000, 10000],
                                           labels=["Short Range (<300 mi)", "Short-Medium (300-700 mi)", "Medium (700-1200 mi)", "Medium-Long (1200-2000 mi)", "Long Range (>2000 mi)"])
        
        # Group by and calculate average distance
        fatigue_stats = plot_df.groupby("DISTANCE_GROUP", observed=True).agg(
            Avg_Distance=("DISTANCE", "mean")
        ).reset_index()
        
        # Turbine Fatigue Index Formula: takeoffs per 1000 flight hours * stress factor
        fatigue_stats["Takeoff Cycles per 1000 hrs"] = (1000 / (fatigue_stats["Avg_Distance"] / 500 + 0.5)).round(1)
        fatigue_stats["Turbine Thermal Fatigue (Wear Units)"] = (fatigue_stats["Takeoff Cycles per 1000 hrs"] * 1.5).round(1)
        
        fig_fatigue = px.bar(
            fatigue_stats,
            x="DISTANCE_GROUP",
            y="Turbine Thermal Fatigue (Wear Units)",
            color="Turbine Thermal Fatigue (Wear Units)",
            color_continuous_scale="Viridis",
            labels={"DISTANCE_GROUP": "Flight Range Category", "Turbine Thermal Fatigue (Wear Units)": "Fatigue Index (Per 1,000 Flight Hours)"},
            title="Estimated Turbine Blade Thermal Stress by Flight Profile"
        )
        fig_fatigue.update_layout(height=380, margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_fatigue, use_container_width=True)
