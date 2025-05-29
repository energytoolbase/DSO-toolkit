# This script trains Chronos with more than one item id we use this to train one model on multiple sites.
# ========================
# 1. Prepare the data
# ========================
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor
import pytz
from datetime import datetime, timedelta
import time
import tracemalloc

# ========== Timing and Memory Profiling ==========
start_time = time.time()
tracemalloc.start()

# ========== Helper Function to Force UTC Timezone ==========
def force_utc_tz(series):
    return series.apply(lambda x: x.tz_convert("UTC") if x.tzinfo else x.tz_localize("UTC"))

# Make sure output-mul folder exists
os.makedirs('output-mul', exist_ok=True)

# File paths
file_paths = [
    "data/demoData-1year.csv",
    "data/kyLibData-1year.csv",
    "data/petcoData-1year.csv",
    "data/policeData-1year.csv",
    "data/tryStarData-1year.csv",
]

# Initialize an empty list
dataframes = []

# Process each file and assign unique item_id
for idx, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path)
    df = df[["date_time", "site"]].copy()
    df.rename(columns={"date_time": "timestamp"}, inplace=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df.dropna(subset=["timestamp"], inplace=True)
    df["timestamp"] = df["timestamp"].apply(lambda x: x.tz_localize(None))  # remove tz for Chronos
    df["item_id"] = idx
    dataframes.append(df)

# Concatenate all DataFrames
full_df = pd.concat(dataframes, ignore_index=True)

# Set up for Chronos (must be timezone-naive)
ts_data = TimeSeriesDataFrame(full_df.set_index(["item_id", "timestamp"]))

# Save if needed
full_df.to_csv("output-mul/chronos_ready_dataset.csv", index=False)
print("Data prepared for Chronos.")

# ========================
# 2. Train Chronos model on ALL item_ids
# ========================
prediction_length = 96  # 1 day if 15-min data

predictor = TimeSeriesPredictor(
    target="site",
    prediction_length=prediction_length,
    eval_metric="MAE",
    freq="15min"
)

predictor.fit(ts_data, presets="bolt_small", time_limit=1200)
print("Chronos model trained on ALL item_ids.")

# ========================
# 3. Walk-Forward Forecast for ALL item_ids
# ========================
walk_forward_results = []

test_start_dt = datetime(2025, 1, 1)
test_end_dt = datetime(2025, 1, 3)

for item_id in ts_data.item_ids:
    target_series = ts_data.loc[item_id]["site"]

    try:
        test_start_idx = target_series.index.get_loc(test_start_dt)
        test_end_idx = target_series.index.get_loc(test_end_dt)
    except KeyError:
        print(f"[WARNING] Item {item_id} does not have data for test range. Skipping.")
        continue

    for i in range(test_start_idx, test_end_idx - prediction_length + 1):
        context = target_series.iloc[:i]
        context_df = context.reset_index()
        context_df["item_id"] = item_id
        ts_context = TimeSeriesDataFrame(context_df.set_index(["item_id", "timestamp"]))

        try:
            pred = predictor.predict(ts_context)
            forecast_values = pred.loc[item_id]["mean"].values[:prediction_length]
            result = {
                "item_id": item_id,
                "start_time": target_series.index[i].tz_localize("UTC")
            }
            result.update({f"target_{j + 1}": forecast_values[j] for j in range(prediction_length)})
            walk_forward_results.append(result)
        except Exception as e:
            print(f"[ERROR] Forecasting failed at item {item_id} step {i}: {e}")

walk_df = pd.DataFrame(walk_forward_results)
walk_df.to_csv("output-mul/chronos_walk_forward_forecasts.csv", index=False)
print("Walk-forward forecasts saved for ALL item_ids.")

# ========================
# 4. Evaluate and Plot Results
# ========================
chronos_df = pd.read_csv("output-mul/chronos_walk_forward_forecasts.csv")

# Load actuals again
actual_dfs = []
for idx, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path)
    df = df[["date_time", "site"]].copy()
    df.rename(columns={"date_time": "timestamp"}, inplace=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df.dropna(subset=["timestamp"], inplace=True)
    df["timestamp"] = force_utc_tz(df["timestamp"])
    df["item_id"] = idx
    actual_dfs.append(df)

actual_df = pd.concat(actual_dfs, ignore_index=True)
actual_df = actual_df[['item_id', 'timestamp', 'site']].rename(columns={'site': 'actual'})

# Reshape forecast DataFrame
def reshape_forecast(df, model_name):
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['start_time'] = force_utc_tz(df['start_time'])
    df_long = df.melt(id_vars=['item_id', 'start_time'], var_name='target', value_name=model_name)
    df_long['step'] = df_long['target'].str.extract(r'target_(\d+)').astype(int)
    df_long['timestamp'] = df_long['start_time'] + pd.to_timedelta((df_long['step'] - 1) * 15, unit='min')
    df_long['timestamp'] = force_utc_tz(df_long['timestamp'])
    return df_long[['item_id', 'timestamp', model_name, 'step']]

chronos_long = reshape_forecast(chronos_df.copy(), 'chronos')

# Merge and plot per item
for item_id in range(5):
    merged = pd.merge(
        chronos_long[chronos_long['item_id'] == item_id],
        actual_df[actual_df['item_id'] == item_id],
        on='timestamp',
        how='inner'
    )
    merged.dropna(inplace=True)

    # Errors
    errors = merged.groupby('step').apply(lambda df: pd.Series({
        'mae_chronos': mean_absolute_error(df['actual'], df['chronos']),
        'rmse_chronos': mean_squared_error(df['actual'], df['chronos'], squared=False),
    })).reset_index()

    errors.to_csv(f"output-mul/errors_by_target_chronos_item{item_id}.csv", index=False)
    print(f"Errors computed for item {item_id}.")

    # MAE plot
    plt.figure(figsize=(12, 5))
    plt.plot(errors['step'], errors['mae_chronos'], label=f'Chronos MAE - item {item_id}', color='blue')
    plt.xlabel("Forecast Step (15-min intervals)")
    plt.ylabel("MAE")
    plt.title(f"Chronos MAE by Forecast Step (Item {item_id})")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"output-mul/chronos_mae_item{item_id}.png")
    plt.close()

    # RMSE plot
    plt.figure(figsize=(12, 5))
    plt.plot(errors['step'], errors['rmse_chronos'], label=f'Chronos RMSE - item {item_id}', color='blue')
    plt.xlabel("Forecast Step (15-min intervals)")
    plt.ylabel("RMSE")
    plt.title(f"Chronos RMSE by Forecast Step (Item {item_id})")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"output-mul/chronos_rmse_item{item_id}.png")
    plt.close()

    # Actual vs Forecast
    avg_forecast = merged.groupby('timestamp').agg({
        'actual': 'first',
        'chronos': 'mean'
    }).reset_index()

    plt.figure(figsize=(14, 6))
    plt.plot(avg_forecast['timestamp'], avg_forecast['actual'], label='Actual', color='black', linewidth=1.5)
    plt.plot(avg_forecast['timestamp'], avg_forecast['chronos'], label='Chronos Forecast (avg)', color='blue', alpha=0.7)
    plt.title(f"Actual vs Chronos Forecasted Values (Item {item_id})")
    plt.xlabel("Timestamp")
    plt.ylabel("Site Load")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"output-mul/chronos_actual_vs_forecast_item{item_id}.png")
    plt.close()

    print(f"Plots saved for item {item_id}.")

print("All 5 item_ids done completely!")

# ========================
# 5. Report Runtime and Memory
# ========================
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 10**6:.2f} MB")
print(f"Peak memory usage: {peak / 10**6:.2f} MB")
tracemalloc.stop()

end_time = time.time()
print(f"Total script runtime: {end_time - start_time:.2f} seconds")
