import json
import pandas as pd

PATH = "data/processed/flights_clean.csv"


def categorize_delay(delay):
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


def main():
    df = pd.read_csv(PATH)
    total_flights = len(df)
    delayed_flights = (df["ARRIVAL_DELAY"] > 15).sum()
    delay_rate = delayed_flights / total_flights * 100
    avg_delay = df["ARRIVAL_DELAY"].mean()
    med_delay = df["ARRIVAL_DELAY"].median()
    max_delay = df["ARRIVAL_DELAY"].max()

    df["DELAY_CATEGORY"] = df["ARRIVAL_DELAY"].apply(categorize_delay)
    dist = df["DELAY_CATEGORY"].value_counts(normalize=True) * 100

    # Airports
    df["IS_DELAYED"] = (df["ARRIVAL_DELAY"] > 15).astype(int)
    airport_stats = (
        df.groupby("ORIGIN_AIRPORT").agg({"IS_DELAYED": ["sum", "count"]}).reset_index()
    )
    airport_stats.columns = ["Airport", "Delayed", "Total"]
    airport_stats = airport_stats[airport_stats["Total"] >= 1000]
    airport_stats["Delay_Rate"] = (
        airport_stats["Delayed"] / airport_stats["Total"] * 100
    )
    top5_airports = airport_stats.sort_values("Delay_Rate", ascending=False).head(5)

    # Airlines
    airline_stats = (
        df.groupby("AIRLINE")
        .agg({"IS_DELAYED": ["sum", "count"], "ARRIVAL_DELAY": "mean"})
        .reset_index()
    )
    airline_stats.columns = ["Airline", "Delayed", "Total", "Avg_Delay"]
    airline_stats["Delay_Rate"] = (
        airline_stats["Delayed"] / airline_stats["Total"] * 100
    )
    worst_airline = airline_stats.sort_values("Delay_Rate", ascending=False).iloc[0]
    best_airline = airline_stats.sort_values("Delay_Rate").iloc[0]

    # Time of day
    def tod(s):
        try:
            h = int(s) // 100
        except:
            return "Unknown"
        if 5 <= h < 12:
            return "Morning (5am-12pm)"
        elif 12 <= h < 17:
            return "Afternoon (12pm-5pm)"
        elif 17 <= h < 21:
            return "Evening (5pm-9pm)"
        else:
            return "Night (9pm-5am)"

    df["TIME_OF_DAY"] = df["SCHEDULED_DEPARTURE"].apply(tod)
    time_stats = (
        df.groupby("TIME_OF_DAY").agg({"IS_DELAYED": ["sum", "count"]}).reset_index()
    )
    time_stats.columns = ["Time_Period", "Delayed", "Total"]
    time_stats["Delay_Rate"] = time_stats["Delayed"] / time_stats["Total"] * 100

    # Monthly
    monthly_stats = (
        df.groupby("MONTH").agg({"IS_DELAYED": ["sum", "count"]}).reset_index()
    )
    monthly_stats.columns = ["Month", "Delayed", "Total"]
    monthly_stats["Delay_Rate"] = (
        monthly_stats["Delayed"] / monthly_stats["Total"] * 100
    )
    best_month = monthly_stats.sort_values("Delay_Rate").iloc[0]
    worst_month = monthly_stats.sort_values("Delay_Rate", ascending=False).iloc[0]

    out = {
        "total_flights": int(total_flights),
        "delayed_flights": int(delayed_flights),
        "delay_rate_pct": round(float(delay_rate), 2),
        "avg_delay_min": round(float(avg_delay), 2),
        "median_delay_min": round(float(med_delay), 2),
        "max_delay_min": int(max_delay),
        "delay_distribution_pct": dist.to_dict(),
        "top5_airports": top5_airports[["Airport", "Delay_Rate", "Total"]].to_dict(
            orient="records"
        ),
        "worst_airline": {
            "Airline": worst_airline["Airline"],
            "Delay_Rate": round(float(worst_airline["Delay_Rate"]), 2),
        },
        "best_airline": {
            "Airline": best_airline["Airline"],
            "Delay_Rate": round(float(best_airline["Delay_Rate"]), 2),
        },
        "time_stats": time_stats[["Time_Period", "Delay_Rate", "Total"]].to_dict(
            orient="records"
        ),
        "best_month": {
            "Month": int(best_month["Month"]),
            "Delay_Rate": round(float(best_month["Delay_Rate"]), 2),
        },
        "worst_month": {
            "Month": int(worst_month["Month"]),
            "Delay_Rate": round(float(worst_month["Delay_Rate"]), 2),
        },
        "airline_rankings": airline_stats.sort_values("Delay_Rate", ascending=False)[
            ["Airline", "Delay_Rate", "Avg_Delay"]
        ]
        .head(10)
        .to_dict(orient="records"),
    }

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
