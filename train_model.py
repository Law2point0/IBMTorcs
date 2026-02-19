import pandas as pd


def process_telemetry(telemetry_data, csv_path='example_telemetry.csv'):
  print(telemetry_data)
  if not telemetry_data:
    return
  row = {}
  for k, v in telemetry_data.items():
    if isinstance(v, list):
      for i, x in enumerate(v):
        row[f"{k}_{i}"] = x
    else:
      row[k] = v
  import csv
  with open(csv_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=sorted(row.keys()))
    writer.writeheader()
    writer.writerow(row)

def assign_sector(distance):
  if distance < 550:
    return 1
  elif distance < 825:
    return 2
  elif distance < 1150:
    return 3
  elif distance < 1620:
    return 4
  elif distance < 2000:
    return 5
  elif distance < 2470:
    return 6
  elif distance < 2550:
    return 7
  elif distance < 2800:
    return 8
  elif distance < 3050:
    return 9
  elif distance < 3300:
    return 10
  else:
    return 11
  return None


telemetry = pd.read_csv("telemetry.csv")
sector_data = pd.read_csv("sector_output.csv")

telemetry["sector"] = telemetry["distFromStart"].apply(assign_sector)

merged = pd.merge(telemetry, sector_data, on="sector", how="left")
merged.groupby(["lap","sector"]).size()
merged.isna().sum()
merged.to_csv("merged_telemetry.csv", index=False)
#merged.to_parquet("merged_telemetry-p.parquet")

