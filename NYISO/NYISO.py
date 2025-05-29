# Script: Detect smart peak hours using monthly year-over-year load adjustments

import os
import zipfile
import pandas as pd
import numpy as np
from datetime import datetime

# === Configuration ===
data_folder = 'NYiso'  # Set to your zip data folder
os.makedirs('output_plots', exist_ok=True)

# === Step 1: Load Data ===
def read_csv_from_zip(zip_path):
    data_frames = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for csv_file in zip_ref.namelist():
                if csv_file.lower().endswith('.csv'):
                    try:
                        with zip_ref.open(csv_file) as f:
                            for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
                                try:
                                    f.seek(0)
                                    df = pd.read_csv(f,
                                                     usecols=['Time Stamp', 'Integrated Load'],
                                                     encoding=encoding,
                                                     on_bad_lines='warn')
                                    if all(col in df.columns for col in ['Time Stamp', 'Integrated Load']):
                                        data_frames.append(df)
                                        break
                                except Exception:
                                    continue
                    except Exception:
                        continue
    except Exception:
        pass
    return data_frames

# Read and combine
all_dfs = []
for zip_file in os.listdir(data_folder):
    if zip_file.endswith('palIntegrated_csv.zip'):
        zip_path = os.path.join(data_folder, zip_file)
        all_dfs.extend(read_csv_from_zip(zip_path))

df = pd.concat(all_dfs, ignore_index=True)
df.dropna(subset=['Integrated Load'], inplace=True)
df['Time Stamp'] = pd.to_datetime(df['Time Stamp'], errors='coerce')
df.dropna(subset=['Time Stamp'], inplace=True)

# === Step 2: Time Features ===
df['Year'] = df['Time Stamp'].dt.year
df['Month'] = df['Time Stamp'].dt.month
df['Hour'] = df['Time Stamp'].dt.hour
df['Date'] = df['Time Stamp'].dt.date

# === Step 3: Compute Monthly 98th Percentiles ===
monthly_thresholds = df.groupby(['Year', 'Month'])['Integrated Load'].quantile(0.99).reset_index()
monthly_thresholds.rename(columns={'Integrated Load': 'BaseThreshold'}, inplace=True)

# === Step 4: Calculate YoY Change and Adjusted Threshold ===
monthly_thresholds['AdjustedThreshold'] = np.nan

# Build adjusted thresholds based on prior year change
for idx, row in monthly_thresholds.iterrows():
    year = row['Year']
    month = row['Month']
    base = row['BaseThreshold']

    # Look up prior year for the same month
    prior = monthly_thresholds[(monthly_thresholds['Year'] == year - 1) &
                               (monthly_thresholds['Month'] == month)]
    if not prior.empty:
        prior_value = prior['BaseThreshold'].values[0]
        yoy_change = (base - prior_value) / prior_value
        # Apply prior month's YoY change to next year's threshold
        adjusted = base * (1 + 0.5 * yoy_change) + 1000

        monthly_thresholds.loc[idx, 'AdjustedThreshold'] = adjusted
    else:
        monthly_thresholds.loc[idx, 'AdjustedThreshold'] = base  # No adjustment for first year

# === Step 5: Merge Thresholds and Filter Peaks ===
df = df.merge(monthly_thresholds, on=['Year', 'Month'], how='left')

# Define peak hours window
start_hour = 15
end_hour = 18

# Flag potential peaks using adjusted monthly threshold
potential_peaks = df[
    (df['Hour'] >= start_hour) &
    (df['Hour'] <= end_hour) &
    (df['Integrated Load'] > df['AdjustedThreshold'])
].copy()

# === Step 6: Group Consecutive Hours into Periods ===
potential_peaks = potential_peaks.sort_values('Time Stamp')
potential_peaks['time_diff'] = potential_peaks['Time Stamp'].diff().dt.total_seconds() / 3600
potential_peaks['new_group'] = potential_peaks['time_diff'] > 1
potential_peaks['group_id'] = potential_peaks['new_group'].cumsum()

peak_periods = potential_peaks.groupby(['group_id', potential_peaks['Time Stamp'].dt.date]).agg(
    Date=('Time Stamp', 'first'),
    startTime=('Time Stamp', lambda x: x.min().time()),
    endTime=('Time Stamp', lambda x: (x.max() + pd.Timedelta(hours=1)).time())
).reset_index(drop=True)

# === Step 7: Save Outputs ===
potential_peaks.to_csv('smart_potential_peaks.csv', index=False)
monthly_thresholds.to_csv('smart_monthly_thresholds.csv', index=False)
peak_periods.to_csv('smart_peak_periods.csv', index=False)

print("Saved:")
print("- smart_potential_peaks.csv")
print("- smart_monthly_thresholds.csv")
print("- smart_peak_periods.csv")
# === Step 8: Count Predicted Peaks Per Year ===
peak_counts_by_year = potential_peaks.groupby(potential_peaks['Time Stamp'].dt.year).size().reset_index(name='Peak Count')
peak_counts_by_year.rename(columns={'Time Stamp': 'Year'}, inplace=True)
peak_counts_by_year.to_csv('smart_peak_counts_by_year.csv', index=False)

print("Peak counts by year:")
print(peak_counts_by_year.to_string(index=False))
print("- Saved as 'smart_peak_counts_by_year.csv'")
