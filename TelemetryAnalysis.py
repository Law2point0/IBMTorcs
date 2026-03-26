import os
import ollama
import csv
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

# MODEL SELECTION
GRANITE_MICRO = 'hf.co/ibm-granite/granite-4.0-micro-GGUF:Q4_K_M'
MODEL = GRANITE_MICRO

# LOAD & PREPROCESS DATA
def load_data(file_path):
    df = pd.read_csv(file_path)

    # Remove duplicate columns if present
    df = df.loc[:, ~df.columns.duplicated()]

    # Compute total speed
    df["speed"] = np.sqrt(
        df["speedX"]**2 + df["speedY"]**2 + df["speedZ"]**2
    )

    return df



# LAP DETECTION
def detect_laps(df):
    laps = []
    current_lap = []
    prev_dist = df.iloc[0]["distFromStart"]

    for _, row in df.iterrows():
        if row["distFromStart"] < prev_dist:
            laps.append(pd.DataFrame(current_lap))
            current_lap = []

        current_lap.append(row)
        prev_dist = row["distFromStart"]

    if current_lap:
        laps.append(pd.DataFrame(current_lap))

    return laps


# SECTOR ANALYSIS
def compute_sectors(lap_df, track_length, num_sectors=3):
    sectors = {i: [] for i in range(num_sectors)}

    for _, row in lap_df.iterrows():
        sector = int((row["distFromStart"] / track_length) * num_sectors)
        sector = min(sector, num_sectors - 1)
        sectors[sector].append(row["speed"])

    sector_speeds = {
        k: np.mean(v) if v else 0 for k, v in sectors.items()
    }

    return sector_speeds


# OVERTAKE DETECTION
def detect_overtakes(df):
    overtakes = 0
    losses = 0

    prev_pos = df.iloc[0]["racePos"]

    for _, row in df.iterrows():
        if row["racePos"] < prev_pos:
            overtakes += 1
        elif row["racePos"] > prev_pos:
            losses += 1

        prev_pos = row["racePos"]

    return overtakes, losses

# BUILD SUMMARY
def build_summary(df, laps):
    summary = {}

    # Lap times
    lap_times = [lap["curLapTime"].max() for lap in laps if not lap.empty]

    summary["lap_count"] = len(laps)
    summary["best_lap"] = min(lap_times) if lap_times else None
    summary["avg_lap"] = np.mean(lap_times) if lap_times else None

    # Speed stats
    summary["max_speed"] = df["speed"].max()
    summary["avg_speed"] = df["speed"].mean()

    # Overtakes
    overtakes, losses = detect_overtakes(df)
    summary["overtakes"] = overtakes
    summary["positions_lost"] = losses

    # Fuel usage
    summary["fuel_used"] = df["fuel"].iloc[0] - df["fuel"].iloc[-1]

    return summary


# QUERY GRANITE
def query_granite(summary):
    prompt = f"""
You are a professional race engineer.

Analyze this telemetry summary and provide insights and coaching advice:

{summary}

Focus on:
- Driving consistency
- Speed performance
- Overtaking effectiveness
- Potential mistakes
- Suggestions for improvement
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a professional race engineer."},
            {"role": "user", "content": prompt}
        ],
        options={
            "temperature": 0.3,
            "num_predict": 300
        }
    )

    return response["message"]["content"]

    response = requests.post(
        GEN_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    return response.json()


# MAIN PIPELINE
def main(csv_file):
    df = load_data(csv_file)

    laps = detect_laps(df)

    summary = build_summary(df, laps)

    print("Telemetry Summary:")
    print(summary)

    print("\nQuerying Granite...\n")
    result = query_granite(summary)

    print("Granite Analysis:\n")
    print(result)
if __name__ == "__main__":
    main("telemetry.csv")