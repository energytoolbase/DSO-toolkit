# Fetch TimeSeries Data

This script fetches time-series data from TimeSeries API and saves it to a CSV file in the `output_data` folder.

## Features
- Fetches time-series data for specified channels (e.g., `meter/site_demand`, `meter/pv_power`).
- Saves data to a CSV file.
- Fills missing data points using values from the previous week.

## Prerequisites
- Python 3.8 or higher
- Required Python packages (see `requirements.txt`)

## Installation
1. Clone the repository:
      `https://github.com/energytoolbase/DSO-toolkit.git`
2. Install the required dependencies:
      `pip install -r requirements.txt`
3. Run the script with the following command:
      `python fetch_timeseries_data.py --source-id <SOURCE_ID> --output-file <OUTPUT_FILE>`

      Example:`python fetch_timeseries_data.py --source-id 54b2da23ae95412e9aa5cf09bfbf3b12 --output-file Sahuarita.csv`

      Output: The script generates a CSV file in the `output_data` folder with the following columns:
              `Time (Epoch)`: Unix timestamp.
              `Time (UTC)`: Human-readable timestamp.
              `meter/site_demand`: Site demand data.
              `meter/pv_power`: PV power data.
