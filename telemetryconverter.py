import pandas as pd

SECTORS = {
        1: (0, 1376),
        2: (1376, 2837),
        3: (2837, 3601.72)
    }

def load_and_clean(csv_path):
    df = pd.read_csv(csv_path)

    # Keep only useful columns
    df = df[[
        "curLapTime",
        "distFromStart",
        "speedX",
        "rpm",
        "gear",
        "angle",
        "trackPos",
        "accel",
        "brake",
        "steer"
    ]]

    return df


def split_laps(df):
    laps = []
    current_lap = []
    prev_distance = df.iloc[0]["distFromStart"]

    for _, row in df.iterrows():
        current_distance = row["distFromStart"]

        if current_distance + 5 < prev_distance:
            laps.append(pd.DataFrame(current_lap))
            current_lap = []

        current_lap.append(row)
        prev_distance = current_distance

    if current_lap:
        laps.append(pd.DataFrame(current_lap))

    return laps


def analyze_sector(sector_df):
    avg_speed = sector_df["speedX"].mean()
    min_speed = sector_df["speedX"].min()
    max_brake = sector_df["brake"].max()

    # Brake start
    braking = sector_df[sector_df["brake"] > 0.1]
    brake_start = braking["distFromStart"].iloc[0] if not braking.empty else None

    brake_duration = (
        braking["curLapTime"].max() - braking["curLapTime"].min()
        if not braking.empty else 0
    )

    # Throttle reapply
    throttle = sector_df[sector_df["accel"] > 0.2]
    throttle_start = throttle["distFromStart"].iloc[0] if not throttle.empty else None

    sector_time = (
    sector_df["curLapTime"].max() -
    sector_df["curLapTime"].min()
    )

    return {
        "avg_speed": round(avg_speed, 2),
        "min_speed": round(min_speed, 2),
        "max_brake": round(max_brake, 2),
        "brake_start": round(brake_start, 2) if brake_start is not None else None,
        "brake_duration": round(brake_duration, 3),
        "sector_time": round(sector_time, 3),
        "throttle_reapply": round(throttle_start, 2) if throttle_start is not None else None
        
    }


def process_lap(lap_df):
    lap_results = []

    for sector_id, (start, end) in SECTORS.items():
        sector_df = lap_df[
            (lap_df["distFromStart"] >= start) &
            (lap_df["distFromStart"] < end)
        ]

        if sector_df.empty:
            continue

        sector_data = analyze_sector(sector_df)
        sector_data["sector"] = sector_id
        lap_results.append(sector_data)

    return lap_results


def run_pipeline(csv_path):
    df = load_and_clean(csv_path)
    laps = split_laps(df)

    results = run_pipeline("telemetry.csv")

    for lap_number, lap_df in enumerate(laps, start=1):
        lap_analysis = process_lap(lap_df)
        results.append({
            "lap": lap_number,
            "sectors": lap_analysis
        })

    return results

def get_fastest_lap(laps):
    fastest = None
    best_time = float("inf")

    for lap in laps:
        lap_time = sum(sector["sector_time"] for sector in lap["sectors"])
        if lap_time < best_time:
            best_time = lap_time
            fastest = lap

    return fastest

def save_results(results, output_path):
    rows = []

    for lap in results:
        for sector in lap["sectors"]:
            row = {"lap": lap["lap"], **sector}
            rows.append(row)

    pd.DataFrame(rows).to_csv(output_path, index=False)
    
if __name__ == "__main__":
    results = run_pipeline("telemetry.csv")
    save_results(results, "processed_output.csv")

