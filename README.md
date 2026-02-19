# Airport Operations Analysis — Flight Delay Insights (2015)

Professional, reproducible analysis of US domestic flight delays (2015).

TL;DR
- Dataset: 5,729,195 US domestic flights (2015)
- Overall delay rate (>15 min): 17.86%
- Worst airport (by delay rate, min 1000 flights): ASE — 28.70%
- Worst airline: NK — 28.75% delay rate
- Best airline: HA — 10.53% delay rate
- Peak delay period: Evening (5pm–9pm) — 24.78% delay rate
- Worst month: June — 22.64% delay rate

## 🚀 Live Interactive Dashboard
**[Click here to view the live Streamlit Dashboard](https://project-1-airport-delays-8y3xnmabymvxt8q8di4gx7.streamlit.app/)**
*Note: The live dashboard uses a 10% representative sample (~570k flights) to ensure fast load times in the web environment, while the Jupyter notebooks process the full 5.7M row dataset locally.*

This repository contains the cleaning, analysis, and visualizations used to produce the above results. It is intended as a professional portfolio piece demonstrating data engineering, analysis and visualization skills applied to aviation operations.

Contents
- `data/raw/` — original CSVs (flights.csv, airlines.csv, airports.csv). Not included in repo for size reasons.
- `data/processed/flights_clean.csv` — cleaned dataset used for analysis.
- `notebooks/` — exploratory, cleaning, and analysis notebooks.
- `reports/figures/` — exported PNG visualizations used in the report.
- `reports/analysis_summary.md` — full written findings and recommendations.
- `scripts/compute_report_metrics.py` — reproducible metric extraction used to populate reports.

Quick start
1. Create a Python environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Add original data files to `data/raw/` (download from DOT/Kaggle).  
3. Regenerate processed data by running `notebooks/02_data_cleaning.ipynb` (or run its cells).  
4. Re-run the analysis notebook to reproduce figures and `reports/analysis_summary.md`:

```bash
python -m nbconvert --to notebook --execute notebooks/03_analysis_and_visualization.ipynb \
	--ExecutePreprocessor.timeout=600 --output notebooks/03_analysis_and_visualization_executed.ipynb
```

Key results (summary)
- Total flights analyzed: 5,729,195
- Flights delayed >15 minutes: 1,023,498 (17.86%)
- Average arrival delay: 4.40 minutes (median -5.00 minutes)
- Maximum recorded delay: 1,971 minutes
- Delay distribution: On Time/Early 63.57% | Minor (1-15m) 18.56% | Moderate (16-30m) 6.82% | Significant (31-60m) 5.47% | Major (>60m) 5.57%

Top-5 airports by delay rate (min 1000 flights)
1. ASE — 28.70% (3,286 flights)
2. HPN — 23.80% (7,164 flights)
3. ORD — 23.31% (277,336 flights)
4. EGE — 23.26% (1,204 flights)
5. LBE — 23.21% (1,245 flights)

Airline highlights
- Worst airline (2015): `NK` — 28.75% delay rate
- Best airline (2015): `HA` — 10.53% delay rate

Temporal patterns
- Worst month: June (22.64% delay rate) — likely traffic and weather related
- Worst time window: Evening (5pm–9pm) — 24.78% delay rate

Reproducibility & conventions
- Delay threshold: arrival delay > 15 minutes. Code sets `IS_DELAYED = (df['ARRIVAL_DELAY'] > 15).astype(int)`.
- `SCHEDULED_DEPARTURE` is HHMM integer — hour extracted with `int(scheduled_dep) // 100`.
- Visual outputs: saved to `reports/figures/` with filenames `01_delay_distribution.png`, `02_worst_airports.png`, `03_airline_performance.png`, `04_time_of_day_delays.png`, `05_seasonal_trends.png`.
- When editing notebooks that change the data schema, update both `notebooks/02_data_cleaning.ipynb` and `notebooks/03_analysis_and_visualization.ipynb`.

Suggested next steps
- Add an automated CI step to run `scripts/compute_report_metrics.py` and verify metrics.
- Add a lightweight Streamlit dashboard to explore delays interactively.

Contact
- Arnav Hemanth Mutt — [arnavhmutt@gmail.com] 
— LinkedIn: [www.linkedin.com/in/arnav-h-987390302] 
— GitHub: [arnavhm]

License
- This project is for educational and portfolio use. Data source: US DOT BTS (2015).
