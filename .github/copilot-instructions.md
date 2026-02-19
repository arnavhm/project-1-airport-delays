# Copilot instructions — project-1-airport-delays

Purpose: help AI coding agents be productive in this repository by calling out the project's structure, conventions, and common developer workflows.

- Repo layout: data/ (raw, processed), notebooks/, reports/figures/, requirements.txt.
- Primary dataset: [data/processed/flights_clean.csv](data/processed/flights_clean.csv).
- Main analysis notebooks: [notebooks/02_data_cleaning.ipynb](notebooks/02_data_cleaning.ipynb) (data prep) and [notebooks/03_analysis_and_visualization.ipynb](notebooks/03_analysis_and_visualization.ipynb) (visuals & summary).

Quick start
- Create a Python environment and install dependencies:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Regenerate processed data: run the data-cleaning notebook or execute its cells. Processed CSV is expected at `data/processed/flights_clean.csv`.
- Run the full analysis (headless) with nbconvert:
  - `jupyter nbconvert --to notebook --execute notebooks/03_analysis_and_visualization.ipynb --ExecutePreprocessor.timeout=600 --output notebooks/03_analysis_and_visualization_executed.ipynb`

Project-specific conventions (do not change without checking notebooks)
- Delay definition: a flight is considered "delayed" when `ARRIVAL_DELAY > 15` minutes. Code frequently creates `IS_DELAYED = (df['ARRIVAL_DELAY'] > 15).astype(int)`.
- Delay categories: see the `categorize_delay` function in the analysis notebook — labels used are `On Time/Early`, `Minor Delay (1-15 min)`, `Moderate Delay (16-30 min)`, `Significant Delay (31-60 min)`, `Major Delay (>60 min)`.
- Time-of-day logic: `SCHEDULED_DEPARTURE` is treated as HHMM integer; hour extracted with `int(scheduled_dep) // 100`. Time buckets use exact string keys like `Morning (5am-12pm)` etc.
- Aggregation columns expected: `YEAR`, `MONTH`, `AIRLINE`, `ORIGIN_AIRPORT`, `ARRIVAL_DELAY`, `SCHEDULED_DEPARTURE`. Many cells rely on these names and types.
- Visualization outputs: images are saved to `reports/figures/` (notebooks create the directory with `os.makedirs('../reports/figures', exist_ok=True)`).
- Plotting style: notebooks set `sns.set_style('whitegrid')` and adjust `plt.rcParams` centrally — follow this when adding new figures to maintain consistency.

Debugging & testing notes
- There are no automated tests in the repo. To validate changes:
  - Run the modified notebook (or selected cells) interactively in JupyterLab, or use the nbconvert command above for a full run.
  - Inspect generated figures in `reports/figures/` and verify printed summary tables in the executed notebook.
- Common failure modes: missing `data/processed/flights_clean.csv`, unexpected NA types in `SCHEDULED_DEPARTURE`, or notebooks assuming `IS_DELAYED` exists. Add defensive checks when modifying code that runs earlier notebooks.

When editing notebooks
- Keep code changes minimal and run the notebook end-to-end. If updating data schema (column rename / type), update both `02_data_cleaning.ipynb` and `03_analysis_and_visualization.ipynb` consistently.
- Prefer saving an executed copy when committing changes: e.g., `03_analysis_and_visualization_executed.ipynb` during debugging — but avoid committing large binary outputs unless requested.

Helpful file references
- Analysis & visuals: [notebooks/03_analysis_and_visualization.ipynb](notebooks/03_analysis_and_visualization.ipynb)
- Data cleaning: [notebooks/02_data_cleaning.ipynb](notebooks/02_data_cleaning.ipynb)
- Processed data: [data/processed/flights_clean.csv](data/processed/flights_clean.csv)

If anything above is unclear or you want the instructions expanded (for CI, pre-commit hooks, or PR review rules), tell me which area and I will iterate.
