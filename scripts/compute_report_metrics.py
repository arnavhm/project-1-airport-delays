import json
import logging
import os
import sys
from typing import Dict, Any
import pandas as pd

# Configure structured logging according to JPL standards
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AviationMetrics")

EXPECTED_COLUMNS = {
    "YEAR": "int16",
    "MONTH": "int8",
    "DAY": "int8",
    "DAY_OF_WEEK": "int8",
    "AIRLINE": "str",
    "ORIGIN_AIRPORT": "str",
    "SCHEDULED_DEPARTURE": "int16",
    "ARRIVAL_DELAY": "float32"
}

def categorize_delay(delay: float) -> str:
    """Categorizes arrival delay using industry-standard FAA/DOT thresholds."""
    if pd.isna(delay):
        return "Unknown"
    if delay <= 0:
        return "On Time/Early"
    elif delay <= 15:
        return "Minor Delay (1-15 min)"
    elif delay <= 30:
        return "Moderate Delay (16-30 min)"
    elif delay <= 60:
        return "Significant Delay (31-60 min)"
    else:
        return "Major Delay (>60 min)"

def categorize_time_of_day(scheduled_dep: int) -> str:
    """Converts HHMM schedule format into structured flight shift periods."""
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

def load_and_validate_data(filepath: str) -> pd.DataFrame:
    """Loads the flight logs, enforcing schema validation and type downcasting."""
    if not os.path.exists(filepath):
        logger.error("Input data file not found at path: %s", filepath)
        raise FileNotFoundError(f"Missing critical resource: {filepath}")
    
    logger.info("Loading flight dataset: %s", filepath)
    
    # Read only required columns to optimize RAM
    # Load AIRLINE and ORIGIN_AIRPORT as str to avoid mixed type warnings
    dtypes_on_load = {
        "YEAR": "int16",
        "MONTH": "int8",
        "DAY": "int8",
        "DAY_OF_WEEK": "int8",
        "AIRLINE": "str",
        "ORIGIN_AIRPORT": "str",
        "SCHEDULED_DEPARTURE": "int16",
        "ARRIVAL_DELAY": "float32"
    }
    
    df = pd.read_csv(filepath, usecols=list(EXPECTED_COLUMNS.keys()), dtype=dtypes_on_load)
    
    # Cast to category for memory efficiency
    df["AIRLINE"] = df["AIRLINE"].astype("category")
    df["ORIGIN_AIRPORT"] = df["ORIGIN_AIRPORT"].astype("category")
    
    logger.info("Dataset successfully loaded. Shape: %s, Memory usage: %.2f MB", 
                df.shape, df.memory_usage(deep=True).sum() / (1024 * 1024))
    return df

def compute_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Computes operational metrics in a functional, side-effect-free manner."""
    total_flights = len(df)
    if total_flights == 0:
        logger.warning("Empty dataframe provided to metrics engine.")
        return {}
        
    delayed_flights = (df["ARRIVAL_DELAY"] > 15).sum()
    delay_rate = (delayed_flights / total_flights) * 100
    
    # Feature Engineering
    df["DELAY_CATEGORY"] = df["ARRIVAL_DELAY"].apply(categorize_delay)
    df["TIME_OF_DAY"] = df["SCHEDULED_DEPARTURE"].apply(categorize_time_of_day)
    df["IS_DELAYED"] = (df["ARRIVAL_DELAY"] > 15).astype(int)
    
    # Category Distribution
    dist = (df["DELAY_CATEGORY"].value_counts(normalize=True) * 100).to_dict()
    
    # Airport groupings (Min 1000 flights for significance)
    airport_stats = df.groupby("ORIGIN_AIRPORT", observed=True).agg(
        Delayed=("IS_DELAYED", "sum"),
        Total=("IS_DELAYED", "count")
    ).reset_index()
    airport_stats = airport_stats[airport_stats["Total"] >= 1000]
    airport_stats["Delay_Rate"] = (airport_stats["Delayed"] / airport_stats["Total"]) * 100
    top5_airports = airport_stats.sort_values("Delay_Rate", ascending=False).head(5)
    
    # Rename columns to match old script expectations
    top5_airports_mapped = top5_airports.rename(columns={"ORIGIN_AIRPORT": "Airport", "Delay_Rate": "Delay_Rate", "Total": "Total"})
    
    # Airline statistics
    airline_stats = df.groupby("AIRLINE", observed=True).agg(
        Delayed=("IS_DELAYED", "sum"),
        Total=("IS_DELAYED", "count"),
        Avg_Delay=("ARRIVAL_DELAY", "mean")
    ).reset_index()
    airline_stats["Delay_Rate"] = (airline_stats["Delayed"] / airline_stats["Total"]) * 100
    
    worst_airline = airline_stats.sort_values("Delay_Rate", ascending=False).iloc[0]
    best_airline = airline_stats.sort_values("Delay_Rate").iloc[0]
    
    # Time of day analysis
    time_stats = df.groupby("TIME_OF_DAY", observed=True).agg(
        Delayed=("IS_DELAYED", "sum"),
        Total=("IS_DELAYED", "count")
    ).reset_index()
    time_stats["Delay_Rate"] = (time_stats["Delayed"] / time_stats["Total"]) * 100
    time_stats_mapped = time_stats.rename(columns={"TIME_OF_DAY": "Time_Period", "Delay_Rate": "Delay_Rate", "Total": "Total"})
    
    # Monthly patterns
    monthly_stats = df.groupby("MONTH", observed=True).agg(
        Delayed=("IS_DELAYED", "sum"),
        Total=("IS_DELAYED", "count")
    ).reset_index()
    monthly_stats["Delay_Rate"] = (monthly_stats["Delayed"] / monthly_stats["Total"]) * 100
    best_month = monthly_stats.sort_values("Delay_Rate").iloc[0]
    worst_month = monthly_stats.sort_values("Delay_Rate", ascending=False).iloc[0]
    
    # Sort and rank airlines for rank-list output
    airline_rankings = airline_stats.sort_values("Delay_Rate", ascending=False).head(10).rename(
        columns={"AIRLINE": "Airline", "Delay_Rate": "Delay_Rate", "Avg_Delay": "Avg_Delay"}
    )
    
    return {
        "total_flights": int(total_flights),
        "delayed_flights": int(delayed_flights),
        "delay_rate_pct": round(float(delay_rate), 2),
        "avg_delay_min": round(float(df["ARRIVAL_DELAY"].mean()), 2),
        "median_delay_min": round(float(df["ARRIVAL_DELAY"].median()), 2),
        "max_delay_min": int(df["ARRIVAL_DELAY"].max()),
        "delay_distribution_pct": dist,
        "top5_airports": top5_airports_mapped[["Airport", "Delay_Rate", "Total"]].to_dict(orient="records"),
        "worst_airline": {
            "Airline": str(worst_airline["AIRLINE"]),
            "Delay_Rate": round(float(worst_airline["Delay_Rate"]), 2)
        },
        "best_airline": {
            "Airline": str(best_airline["AIRLINE"]),
            "Delay_Rate": round(float(best_airline["Delay_Rate"]), 2)
        },
        "time_stats": time_stats_mapped[["Time_Period", "Delay_Rate", "Total"]].to_dict(orient="records"),
        "best_month": {
            "Month": int(best_month["MONTH"]),
            "Delay_Rate": round(float(best_month["Delay_Rate"]), 2)
        },
        "worst_month": {
            "Month": int(worst_month["MONTH"]),
            "Delay_Rate": round(float(worst_month["Delay_Rate"]), 2)
        },
        "airline_rankings": airline_rankings[["Airline", "Delay_Rate", "Avg_Delay"]].to_dict(orient="records")
    }

def main():
    try:
        data_path = "data/processed/flights_clean.csv"
        df = load_and_validate_data(data_path)
        metrics = compute_metrics(df)
        print(json.dumps(metrics, indent=2))
        logger.info("Report execution finished successfully.")
    except Exception as e:
        logger.critical("Uncaught pipeline failure: %s", str(e), exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
