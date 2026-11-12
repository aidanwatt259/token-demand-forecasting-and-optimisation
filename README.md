# ⚡ Datacenter Hardware Optimization Dashboard

## Overview
This repository contains a production-ready, interactive simulation dashboard for optimizing hardware dispatch in a large-scale DGX H100 datacenter. It bridges the gap between raw LLM token demand forecasting and physical hardware operations. 

By applying vectorized mathematical optimization, the system calculates the exact minimum number of active nodes required to meet predicted token demand without exceeding an 80% utilization cap. This approach eliminates idle power waste, strictly enforces SLA compliance, and drastically reduces OPEX.

## Key Features
* **Vectorized Hardware Optimization:** Uses high-speed, in-memory Pandas calculations to determine the exact hardware required per hour, bypassing the overhead and version-conflict risks of traditional linear solvers (like PuLP).
* **Interactive "What-If" Simulator:** Allows datacenter operators to instantly model different operational scenarios by adjusting electricity costs, facility PUE, maximum hardware limits, and utilization caps.
* **Dynamic Cost & Power Tracking:** Automatically translates active and state-gated hardware counts into facility-wide power draw (kW) and financial cost ($).
* **Live Dashboards:** Visualizes hardware utilization curves, peak power constraints, and hourly scheduling action plans using interactive Plotly charts.

## Technologies Used
* **Python 3.x**
* **Streamlit:** Frontend web application framework
* **Pandas & NumPy:** Vectorized optimization logic and data manipulation
* **Plotly:** Interactive data visualization

## Repository Structure
* `dashboard.py`: The main Streamlit application containing both the frontend interface and the Pandas optimization logic.
* `forecast.csv`: Fixed dataset containing the 24-hour token demand forecast.
* `requirements.txt`: The required Python dependencies for local and cloud deployment.

## How to Run Locally

1. **Clone or download this repository** to your local machine.
2. **Open your terminal** and navigate to the project folder:
   ```bash
   cd path/to/datacenter-dashboard
