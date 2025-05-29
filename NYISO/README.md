# Smart Peak Hour Detection

This script analyzes historical load data from NYISO to identify smart peak hours by computing monthly year-over-year (YoY) adjustments to peak load thresholds. It processes time-stamped load data, applies a dynamic threshold based on the 99th percentile, adjusts it using previous years' trends, and groups consecutive peak hours into identifiable periods.

## Structure

- `smart_potential_peaks.csv` — All detected hourly periods that exceed the adjusted threshold during peak hours (3–6 PM).
- `smart_monthly_thresholds.csv` — Monthly thresholds and their year-over-year adjusted counterparts.
- `smart_peak_periods.csv` — Final grouped peak periods with start and end times.
- `smart_peak_counts_by_year.csv` — Number of peak hour events detected per year.

## Data Requirements

Before running the script, **you must download and extract the historical NYISO load data ZIP files**.

Place all downloaded `.zip` files (ending with `palIntegrated_csv.zip`) inside a folder named:

   ```
   NYiso/
   ```

The folder should be in the same directory as the script.

The script automatically reads and processes all matching zip files in the `NYiso/` folder.
