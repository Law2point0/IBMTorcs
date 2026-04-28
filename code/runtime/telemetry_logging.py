import csv
import datetime


def log_file_name():
  timestamp = datetime.datetime.now().strftime("%d_%b_%H_%M_%S")
  return timestamp


def log_telemetry(S, R, writer_state, next_log_time, log_interval_sec):
  writer, file_handle = writer_state
  cur_time = S.get("curLapTime", None)

  # ---------- WRITE HEADER ONCE ----------
  if writer is None and S:
    header = []

    # Server state
    for k, v in S.items():
      if isinstance(v, list):
        for i in range(len(v)):
          header.append(f"{k}_{i}")
      else:
          header.append(f"{k}")

    for k, v in R.items():
      if isinstance(v, list):
        for i in range(len(v)):
          header.append(f"{k}_{i}")
      else:
        header.append(f"{k}")

    writer = csv.writer(file_handle)
    writer.writerow(header)
    file_handle.flush()
  if cur_time is not None and cur_time < next_log_time - log_interval_sec:
    next_log_time = log_interval_sec
  if writer and cur_time is not None and cur_time >= next_log_time:
    row = []
    for v in S.values():
      if isinstance(v, list):
        row.extend(v)
      else:
        row.append(v)
    for v in R.values():
      if isinstance(v, list):
        row.extend(v)
      else:
        row.append(v)
    writer.writerow(row)
    file_handle.flush()
    next_log_time += log_interval_sec
  return (writer, file_handle), next_log_time