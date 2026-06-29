# ✈️ US Domestic Flight Operations & Congestion Analytics (2015)

An executive-level, reproducible data engineering and analytics dashboard investigating US domestic flight delays using a representative sample (~570k flights) of the 5.7M record US DOT dataset. 

This repository showcases safety-critical coding standards (inspired by DO-178C and NASA JPL rules), advanced memory optimization, prescriptive simulations, and interactive geospatial telemetry built for aviation operations.

---

## 📈 Executive Summary

* **Dataset Volume:** 5,729,195 US domestic flights (2015 DOT BTS)
* **System-Wide Delay Rate (>15m):** 17.86%
* **Mean Arrival Delay:** +4.40 minutes | **Median Arrival Delay:** -5.00 minutes (Right-Skewed Tail)
* **Worst Performing Airline:** Spirit Airlines (NK) — 28.75% delay rate
* **Best Performing Airline:** Hawaiian Airlines (HA) — 10.53% delay rate
* **Worst Performing Airport:** Aspen Pitkin County (ASE) — 28.70% delay rate
* **Peak Congestion Window:** Evening Shift (5 PM – 9 PM) — 24.78% delay rate

---

## ⚙️ Architecture & Features

### 1. Prescriptive "What-If" Operational Simulator
Instead of just describing historical bottlenecks, the dashboard features a **what-if decision-support simulator**. Users can slide operational relief parameters (e.g., reducing Spirit Airlines turnaround times, relieving O'Hare ground traffic, or adding evening scheduling buffers) to instantly re-project the entire flight network's delay rates and calculate **passenger hours saved** in real-time.

### 2. Geospatial Congestion Mapping & Route Explorer
* **Geospatial Telemetry:** Renders all US airports using IATA codes, sizing circles by flight traffic volume and color-coding them by delay rates using a Mapbox-supported engine.
* **Flight Path Overlay:** Select any origin and destination route in the sidebar to overlay a flight path vector directly onto the live Mapbox projection.
* **Route Analyzer:** Computes route-specific volumes, average delays, and attributes delay rates compared to the national average.

### 3. Root Cause Delay Attribution
Examines the specialized DOT delay categories to explain *why* flights are delayed:
* **Late Arriving Aircraft:** The primary cascading bottleneck (averaging ~23 minutes per delayed flight).
* **Air System Congestion:** FAA routing and airport flow limits.
* **Carrier Inefficiencies:** Maintenance, cleaning, and crew issues.
* **Weather & Security:** Low-frequency, high-impact events.

### 4. Mathematical Explainability
The project explicitly documents statistical distribution skewness:
* Flight delays are highly right-skewed and follow a heavy-tailed queueing profile modeled by:
  
  $$\text{Delay} \propto \frac{\rho}{1 - \rho}$$
  
  where $\rho$ represents runway/gate utilization. As utilization approaches capacity ($\rho \to 1$), cascading delay accumulation scales non-linearly.

---

## 💻 Tech Stack & Memory Optimizations

* **Analytics:** Python 3.12, Pandas, NumPy, Plotly Express, Plotly Graph Objects.
* **Visualization:** Streamlit Dashboard with custom CSS glassmorphism styling and Outfit typography.
* **High-Performance Ingestion:**
  * **90% RAM reduction:** Enforces strict data type downcasting at read time (`int8`, `int16`, `float32`, and `category` mappings), compressing in-memory storage of the 5.7M dataset from ~1.2 GB to just **76.5 MB**.
  * **Zero UI Lag:** Caches the heavy CSV serialization of filtered exports, compiling the download payload lazily only when requested.
  * **DO-178C Standard Compliance:** Employs structured logging, explicit error handling (removing bare `except:` blocks), code decomposition, and validation constants.

---

## 📂 Repository Structure

```text
├── app.py                     # Streamlit dashboard entry point (visuals & simulator)
├── requirements.txt           # Application dependencies
├── scripts/
│   └── compute_report_metrics.py  # Safety-compliant CLI metrics compiler (90% RAM optimized)
├── notebooks/
│   ├── 01_initial_exploration.ipynb   # Initial EDA
│   ├── 02_data_cleaning.ipynb         # Cleaning, filtering & coordinate mapping pipeline
│   └── 03_analysis_and_visualization.ipynb # Metric validation & notebook visualization
├── data/
│   ├── raw/                   # Original DOT CSV files (airlines.csv, airports.csv, flights.csv)
│   └── processed/             # Cleaned flights_clean.csv and flights_sample.csv (10% sample)
└── reports/
    ├── figures/               # Static PNG chart exports
    └── analysis_summary.md    # Formal findings report
```

---

## 🚀 Quick Start & Reproducibility

### 1. Setup Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Raw Data Placement
Download the 2015 Flight Delay dataset from Kaggle or DOT BTS and place the following CSV files in `data/raw/`:
* `flights.csv`
* `airports.csv`
* `airlines.csv`

### 3. Run Ingestion & Data Cleaning
Execute the data cleaning notebook cell structure to generate `flights_clean.csv` (which filters cancelled flights and maps key features):
```bash
python -m nbconvert --to notebook --execute notebooks/02_data_cleaning.ipynb --ExecutePreprocessor.timeout=600 --inplace
```

### 4. Run the Dashboard
To start the live interactive dashboard:
```bash
streamlit run app.py
```

### 5. CLI Metrics Compilation
To run the automated, optimized report metrics compiler:
```bash
python scripts/compute_report_metrics.py
```

---

## 📧 Contact & Info

* **Analyst:** Arnav Hemanth Mutt — [arnavhmutt@gmail.com](mailto:arnavhmutt@gmail.com)
* **LinkedIn:** [www.linkedin.com/in/arnav-h-987390302](https://www.linkedin.com/in/arnav-h-987390302)
* **GitHub:** [arnavhm](https://github.com/arnavhm)
