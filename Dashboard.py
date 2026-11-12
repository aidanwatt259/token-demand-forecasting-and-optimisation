

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Datacenter Optimization", layout="wide")
st.title("⚡ Datacenter Hardware Optimization Dashboard")

# 2. Load Fixed Data (Replace with pd.read_csv('your_forecast.csv'))
@st.cache_data
def load_fixed_data():
    # Generating mock 24-hour token demand data for the fixed dataset
    hours = np.arange(24)
    # Simulate a daily curve: lower at night, peaking mid-day
    base_demand = 1000000 + 500000 * np.sin(np.pi * (hours - 6) / 12)
    # Add some random noise
    tokens = base_demand + np.random.normal(0, 50000, 24) 
    
    df = pd.DataFrame({
        'hour': hours,
        'Total tokens': tokens.clip(min=100000) # Ensure no negative tokens
    })
    return df

df_forecast = load_fixed_data()

# 3. Sidebar - Operator Inputs
st.sidebar.header("⚙️ Operator Parameters")

MAX_NODES = st.sidebar.number_input("Max Hardware Nodes", min_value=1000, max_value=50000, value=10000, step=1000)
COST_PER_KWH = st.sidebar.slider("Electricity Cost ($/kWh)", min_value=0.05, max_value=0.50, value=0.26, step=0.01)
PUE = st.sidebar.number_input("Facility PUE", min_value=1.0, max_value=2.0, value=1.2, step=0.05)
UTILIZATION_CAP = st.sidebar.slider("Utilization Cap (%)", min_value=50, max_value=100, value=80, step=5) / 100.0

st.sidebar.markdown("---")
st.sidebar.subheader("Hardware Specs")
NODE_THROUGHPUT = st.sidebar.number_input("Node Throughput (tokens/sec)", value=62413.08)
ACTIVE_POWER_KW = st.sidebar.number_input("Active Power per Node (kW)", value=10.2)
IDLE_POWER_KW = st.sidebar.number_input("Idle Power per Node (kW)", value=1.8)

# 4. Optimization Math (Runs instantly when sliders change)
NODE_HOURLY_CAPACITY = NODE_THROUGHPUT * 3600  
EFFECTIVE_NODE_HOURLY_CAPACITY = NODE_HOURLY_CAPACITY * UTILIZATION_CAP  
DEMAND_MULTIPLIER = 4000 # Scaling factor from previous model

df = df_forecast.copy()
df['Scaled Tokens'] = df['Total tokens'] * DEMAND_MULTIPLIER

# Calculate required active nodes
df['Active Nodes'] = np.ceil(df['Scaled Tokens'] / EFFECTIVE_NODE_HOURLY_CAPACITY).clip(upper=MAX_NODES).astype(int)
df['Off Nodes'] = MAX_NODES - df['Active Nodes']

# Calculate state changes (Turn on / Turn off)
df['Delta'] = df['Active Nodes'].diff().fillna(0).astype(int)
df['Action Required'] = df['Delta'].apply(lambda x: f"Turn ON {x}" if x > 0 else (f"Turn OFF {abs(x)}" if x < 0 else "No Change"))

# Power and Cost
df['Total IT Power (kW)'] = (df['Active Nodes'] * ACTIVE_POWER_KW) + (df['Off Nodes'] * IDLE_POWER_KW)
df['Facility Power (kW)'] = df['Total IT Power (kW)'] * PUE
df['Hourly Cost ($)'] = df['Facility Power (kW)'] * COST_PER_KWH
df['Time'] = df['hour'].apply(lambda x: f"{int(x):02d}:00")

# 5. Dashboard Visualizations

# Top-level KPIs
total_daily_cost = df['Hourly Cost ($)'].sum()
peak_power = df['Facility Power (kW)'].max()
peak_active_nodes = df['Active Nodes'].max()

col1, col2, col3 = st.columns(3)
col1.metric("Total Daily Power Cost", f"${total_daily_cost:,.2f}")
col2.metric("Peak Facility Power", f"{peak_power:,.0f} kW")
col3.metric("Peak Active Nodes", f"{peak_active_nodes:,} / {MAX_NODES:,}")

st.markdown("---")

# Charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Hardware Utilization Curve")
    # Plotly line chart for Active vs Off Nodes
    fig_nodes = px.line(df, x='Time', y='Active Nodes', markers=True, title="Active Nodes per Hour")
    fig_nodes.add_hline(y=MAX_NODES, line_dash="dash", line_color="red", annotation_text="Max Capacity")
    st.plotly_chart(fig_nodes, use_container_width=True)

with chart_col2:
    st.subheader("Hourly Power Cost")
    # Plotly bar chart for cost
    fig_cost = px.bar(df, x='Time', y='Hourly Cost ($)', title="Cost Breakdown per Hour", color_discrete_sequence=['#2ecc71'])
    st.plotly_chart(fig_cost, use_container_width=True)

# Detailed Data Table
st.subheader("Hourly Dispatch Schedule")
display_cols = ['Time', 'Action Required', 'Active Nodes', 'Off Nodes', 'Facility Power (kW)', 'Hourly Cost ($)']
st.dataframe(df[display_cols].style.format({
    'Facility Power (kW)': '{:,.2f}',
    'Hourly Cost ($)': '${:,.2f}'
}), use_container_width=True)