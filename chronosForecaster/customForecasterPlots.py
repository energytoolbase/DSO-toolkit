# This script is for ploting the results from our current forecaster
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

# === Load data ===
custom_df = pd.read_csv("output-custom/custom_forecaster_full_forecasts_1year-police.csv")
actual_df = pd.read_csv("data/policeData-1year.csv")

# === Function to reshape forecast ===
def reshape_forecast(df, model_name):
    df['start_time'] = pd.to_datetime(df['start_time'])
    df_long = df.melt(id_vars='start_time', var_name='target', value_name=model_name)
    df_long['step'] = df_long['target'].str.extract(r'target_(\d+)').astype(int)
    df_long['timestamp'] = df_long['start_time'] + pd.to_timedelta((df_long['step'] - 1) * 15, unit='min')
    return df_long[['timestamp', model_name, 'step']]

# === Reshape forecast ===
custom_long = reshape_forecast(custom_df.copy(), 'custom')

# === Prepare actual values ===
actual_df['timestamp'] = pd.to_datetime(actual_df['date_time'])
actual_df = actual_df[['timestamp', 'site']].rename(columns={'site': 'actual'})

# === Merge forecast with actuals ===
merged = pd.merge(custom_long, actual_df, on='timestamp', how='inner')
merged.dropna(inplace=True)

# === Compute error per step ===
errors = merged.groupby('step').apply(lambda df: pd.Series({
    'mae_custom': mean_absolute_error(df['actual'], df['custom']),
    'rmse_custom': mean_squared_error(df['actual'], df['custom'], squared=False),
})).reset_index()

# === Save to CSV ===
errors.to_csv("output-custom/errors_by_target_custom_only-1year-police.csv", index=False)

# === Filter for one day (96 steps) ===
errors_one_day = errors[errors['step'].between(1, 96)]

# === Plot MAE ===
plt.figure(figsize=(12, 5))
plt.plot(errors_one_day['step'], errors_one_day['mae_custom'], label='Custom MAE', color='orange')
plt.xlabel("Forecast Step (15-min intervals)")
plt.ylabel("MAE")
plt.title("Custom Forecaster: MAE by Forecast Step")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# === Plot RMSE ===
plt.figure(figsize=(12, 5))
plt.plot(errors_one_day['step'], errors_one_day['rmse_custom'], label='Custom RMSE', color='orange')
plt.xlabel("Forecast Step (15-min intervals)")
plt.ylabel("RMSE")
plt.title("Custom Forecaster: RMSE by Forecast Step")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# === Aggregate forecast for plotting ===
avg_forecast = merged.groupby('timestamp').agg({
    'actual': 'first',
    'custom': 'mean'
}).reset_index()

# === Plot Actual vs Custom Forecast ===
plt.figure(figsize=(14, 6))
plt.plot(avg_forecast['timestamp'], avg_forecast['actual'], label='Actual', color='black', linewidth=1.5)
plt.plot(avg_forecast['timestamp'], avg_forecast['custom'], label='Custom Forecast (avg)', color='orange', alpha=0.7)
plt.title("Actual vs Custom Forecasted Values (Averaged Across Walk-Forward)")
plt.xlabel("Timestamp")
plt.ylabel("Site Load")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
