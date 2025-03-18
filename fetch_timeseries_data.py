import requests
from datetime import datetime, timedelta
import csv
import typer
from typing import Optional
import os

app = typer.Typer()

# Create the output folder if it doesn't exist
OUTPUT_FOLDER = "output_data"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# API Endpoint and payload
def fetch_data(source_id: str):
    API_ENDPOINT = "http://time-series-api.prd.int.energytoolbase.com/v3/timeseries"
    payload = {
        "sourceId": source_id,
        "channels": ["meter/site_demand", "meter/pv_power"],
        "startTime": 1698811200,
        "endTime": 1730433600,
        "resolution": "FIFTEEN_MIN"
    }

    response = requests.post(API_ENDPOINT, json=payload)
    response.raise_for_status()
    return response.json()

# Convert Unix time to human-readable date
def convert_time(unix_time):
    return datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')

# Add missing times to ensure 15-minute intervals and fill NaN values with data from last week
def fill_missing_times(rows, header):
    filled_rows = []
    current_time = rows[0][0]
    end_time = rows[-1][0]
    time_index = 0

    while current_time <= end_time:
        if time_index < len(rows) and rows[time_index][0] == current_time:
            filled_rows.append(rows[time_index])
            time_index += 1
        else:
            # Create a row with NaN values for missing times
            filled_rows.append([current_time, convert_time(current_time)] + ["NaN"] * (len(header) - 2))
        current_time += 900  # Increment by 15 minutes (900 seconds)

    # Fill NaN values with data from last week
    for i in range(len(filled_rows)):
        for j in range(2, len(header)):  # Skip the first two columns (Time (Epoch) and Time (UTC))
            if filled_rows[i][j] == "NaN":
                previous_week_time = filled_rows[i][0] - 7 * 24 * 3600  # Subtract 7 days in seconds
                # Find the corresponding row from the previous week
                for row in filled_rows:
                    if row[0] == previous_week_time:
                        filled_rows[i][j] = row[j]
                        break

    return filled_rows

# Save data to CSV
def save_to_csv(data, filename: str):
    # Handle the response structure
    time_series_data = data["data"]

    # Extract channel names and time-series data
    header = ["Time (Epoch)", "Time (UTC)"] + [channel["channel"] for channel in time_series_data]
    rows = []

    # Assuming all channels have the same timestamps
    times = time_series_data[0]["times"]
    times.reverse()  # Reverse the list to start from start time to end time
    time_series_human = [convert_time(t) for t in times]

    # Prepare rows with time and corresponding channel values
    values = {channel["channel"]: list(reversed(channel["values"])) for channel in time_series_data}  # Reverse values to match reversed times

    for i, epoch_time in enumerate(times):
        row = [epoch_time, time_series_human[i]] + [values[channel][i] for channel in header[2:]]
        rows.append(row)

    # Fill missing times
    rows = fill_missing_times(rows, header)

    # Write to CSV
    output_path = os.path.join(OUTPUT_FOLDER, filename)
    with open(output_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

@app.command()
def main(
    source_id: str = typer.Option(..., help="Source ID for the API request"),
    output_file: Optional[str] = typer.Option("output.csv", help="Output CSV file name")
):
    """
    Fetch time-series data from the API and save it to a CSV file in the output_data folder.
    """
    try:
        response_data = fetch_data(source_id)
        save_to_csv(response_data, output_file)
        typer.echo(f"Data saved to {os.path.join(OUTPUT_FOLDER, output_file)}")
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)

if __name__ == "__main__":
    app()