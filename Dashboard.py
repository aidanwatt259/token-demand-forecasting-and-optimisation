import streamlit as st
import pandas as pd
import numpy as np
import pulp

# --- Page Configuration ---
st.set_page_config(page_title="Hardware Optimization Dashboard", layout="wide")
st.title("Datacenter Hardware Optimization Dashboard")

# --- 1. Neon Database Connection ---
st.header("1. Neon Database Connection Test")

# Streamlit's st.connection works natively with PostgreSQL databases like Neon.
# It requires SQLAlchemy and psycopg2-binary in your requirements.txt.
try:
    # This expects a secret named "NEON_URL" in your Streamlit secrets.
    conn = st.connection("neon", type="sql", url=st.secrets["NEON_URL"])
    
    # Uncomment the below lines to test an actual query once your database is populated:
    # df_neon = conn.query("SELECT 1 AS test_connection;", ttl="10m")
    # st.write("Data from Neon:", df_neon)
    
    st.success("Successfully connected to Neon Database!")
except Exception as e:
    st.warning("Neon Database connection is not fully configured.")
    st.info("Ensure you have added your connection string as 'NEON_URL' in Streamlit Secrets.")
    with st.expander("View connection error"):
        st.error(e)

# --- 2. Data Loading & Forecasting (Cached for Performance) ---
@st.cache_data
def load_and_prepare_data():
    BASE = 'https://github.com/HPMLL/BurstGPT/releases/download/v2.0/'
    BurstGPT_1 = pd.read_csv(BASE + 'BurstGPT_1.csv', on_bad_lines='skip')
    
    # Add relative time features
    BurstGPT_1['day'] = (BurstGPT_1['Timestamp'] // 86400).astype(int)
    seconds_into_day = BurstGPT_1['Timestamp'] % 86400
    BurstGPT_1['hour'] = (seconds_into_day // 3600).astype(int)
    
    # Filter for ChatGPT and aggregate hourly
    chat3gpt = BurstGPT_1[BurstGPT_1['Model'] == 'ChatGPT']
    hourly_demand = chat3gpt.groupby('hour')['Total tokens'].sum().reset_index()
    
    return hourly_demand

st.header("2. Hourly Token Demand Forecast")
with st.spinner("Fetching and processing data..."):
    hourly_df = load_and_prepare_data()
    st.line_chart(hourly_df, x='hour', y='Total tokens')

# --- 3. Optimization Model (DGX H100) ---
st.header("3. DGX H100 Baseline Cost Comparison")

@st.cache_data
def run_baseline_optimization(hourly_data):
    MAX_NODES = 10000
    NODE_THROUGHPUT_PER_SEC = 62413.08
    UTILIZATION_CAP = 0.80
    NODE_HOURLY_CAPACITY = NODE_THROUGHPUT_PER_SEC * 3600
    EFFECTIVE_NODE_HOURLY_CAPACITY = NODE_HOURLY_CAPACITY * UTILIZATION_CAP
    ACTIVE_POWER_KW = 10.2
    IDLE_POWER_KW = 1.8
    POWERED_OFF_KW = 0.0
    COST_PER_KWH = 0.26
    PUE = 1.2
    HOURS = 24

    demand_series = hourly_data.tail(HOURS)['Total tokens'].values
    peak_demand = np.max(demand_series) if len(demand_series) > 0 else 0
    nodes_needed_peak = int(np.ceil(peak_demand / EFFECTIVE_NODE_HOURLY_CAPACITY))
    nodes_needed_peak = max(1, min(nodes_needed_peak, MAX_NODES))

    def compute_facility_cost(active_nodes, idle_nodes, powered_off_nodes):
        hourly_node_kw = (active_nodes * ACTIVE_POWER_KW) + (idle_nodes * IDLE_POWER_KW) + (powered_off_nodes * POWERED_OFF_KW)
        facility_power_kw = hourly_node_kw * PUE
        total_kwh = facility_power_kw * HOURS
        total_cost = total_kwh * COST_PER_KWH
        return total_kwh, total_cost

    results = []
    
    # Scenario 1
    kwh_100, cost_100 = compute_facility_cost(MAX_NODES, 0, 0)
    results.append({"Scenario": "1. 100% Max Capacity (Static)", "Active Nodes": MAX_NODES, "Idle Nodes": 0, "Off Nodes": 0, "1-Day Electricity (kWh)": kwh_100, "1-Day Cost ($)": cost_100, "Daily Savings ($)": 0.00})
    
    # Scenario 2
    kwh_80_20, cost_80_20 = compute_facility_cost(int(0.80 * MAX_NODES), int(0.20 * MAX_NODES), 0)
    results.append({"Scenario": "2. Static 80% Active / 20% Idle", "Active Nodes": int(0.80 * MAX_NODES), "Idle Nodes": int(0.20 * MAX_NODES), "Off Nodes": 0, "1-Day Electricity (kWh)": kwh_80_20, "1-Day Cost ($)": cost_80_20, "Daily Savings ($)": cost_100 - cost_80_20})
    
    # Scenario 3
    kwh_peak, cost_peak = compute_facility_cost(nodes_needed_peak, 0, MAX_NODES - nodes_needed_peak)
    results.append({"Scenario": "3. Static Peak Load (80% Util Cap)", "Active Nodes": nodes_needed_peak, "Idle Nodes": 0, "Off Nodes": MAX_NODES - nodes_needed_peak, "1-Day Electricity (kWh)": kwh_peak, "1-Day Cost ($)": cost_peak, "Daily Savings ($)": cost_100 - cost_peak})

    return pd.DataFrame(results)

df_summary = run_baseline_optimization(hourly_df)

# Highlight specific metrics at the top
col1, col2 = st.columns(2)
with col1:
    st.metric("100% Capacity Cost", f"${df_summary.iloc[0]['1-Day Cost ($)']:,.2f}")
with col2:
    st.metric("Peak Load Scenario Savings", f"${df_summary.iloc[2]['Daily Savings ($)']:,.2f}")

st.dataframe(df_summary, use_container_width=True)
