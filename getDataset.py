# This script is for fetching the data and the features
import pandas as pd
import numpy as np
import pytz
from datetime import datetime
from forecast_models.constants import FORECAST_FREQUENCY_STRING
from forecast_models.data_sources.weather_api import WeatherEndpoint, WeatherProvider
from mock import (MockTimeSeriesAPIClient, MockWeatherAPIClient)
from forecast_models.data_sources.time_series_api import (APIEnvironment as TimeSeriesAPIEnvironment)
from forecast_models.data_sources.time_series_api import TimeSeriesAPIClient
from forecast_models.data_sources.weather_api import WeatherAPIClient
from enum import Enum

# === Fix for seaborn compatibility with older NumPy versions ===
np.float = float


# ---------- SETUP ----------
class TimespanConstants:
    start = "start_datetime"
    end = "end_datetime"

class ModelLoadType:
    site = "site"

class ClientModuleMap(Enum):
    mock_weather_api_module = MockWeatherAPIClient
    forecast_models_weather_api_module = WeatherAPIClient
    mock_time_series_api_module = MockTimeSeriesAPIClient
    forecast_models_time_series_api_module = TimeSeriesAPIClient

def get_weather_api_client(api_module, host, client_id, client_secret):
    return ClientModuleMap[api_module].value(
        host=host,
        client_id=client_id,
        client_key=client_secret
    )

def get_time_series_api_client(api_module, env):
    return ClientModuleMap[api_module].value(
        environment=TimeSeriesAPIEnvironment(env) if env else None
    )

def generate_timestamps(start, end, freq):
    return pd.date_range(start=start, end=end, freq=freq)

class DataSource:
    def __init__(self, **kwargs):
        self.site_name = "ky-library"
        self.gateway_id = "0ec23c4dffccb687a9f2b48a624df98a"
        self.latitude = 38.00101
        self.longitude = -85.70554
        self.time_series_client = get_time_series_api_client(kwargs['time_series_api_module'], kwargs['time_series_api_environment'])
        self.weather_api_client = get_weather_api_client(
            kwargs['weather_api_module'],
            kwargs['weather_api_host'],
            kwargs['weather_api_client_id'],
            kwargs['weather_api_client_secret']
        )

    def retrieve_meter_data(self, timespan, measurement):
        return self.time_series_client.get_timeseries_data(
            site_name=self.site_name,
            gateway_id=self.gateway_id,
            load_types=measurement,
            start_time=timespan[TimespanConstants.start],
            end_time=timespan[TimespanConstants.end],
        )

    def retrieve_weather_api_data(self, timespan):
        return self.weather_api_client.retrieve_weather_data(
            lat=self.latitude,
            lon=self.longitude,
            provider=WeatherProvider.WeatherBit,
            start_datetime=timespan[TimespanConstants.start],
            end_datetime=timespan[TimespanConstants.end],
            endpoint_type=WeatherEndpoint.Condition,
        )

    def get_meter_and_weather_data(self, timespan):
        meter = self.retrieve_meter_data(timespan, ["site"])
        weather = self.retrieve_weather_api_data(timespan)
        return pd.merge(meter, weather, left_index=True, right_index=True, how="inner")

# ---------- PARAMETERS ----------
start_dt = datetime(2024, 1, 1, tzinfo=pytz.UTC)
end_dt = datetime(2025, 4, 1, tzinfo=pytz.UTC)
timespan = {TimespanConstants.start: start_dt, TimespanConstants.end: end_dt}
timestamp_index = generate_timestamps(start_dt, end_dt, FORECAST_FREQUENCY_STRING)

# ---------- FETCH DATA ----------
data_source = DataSource(
    time_series_api_environment="prd",
    weather_api_module=ClientModuleMap.forecast_models_weather_api_module.name,
    weather_api_host="https://weather.stg.energytoolbase.com",
    weather_api_client_id="6F3g4eSRLWYHSSxn4g3j93aW0zq3PckZ",
    weather_api_client_secret="yphO2UvGHCt3iwapO6Ylq2ydSN4Xlv8pzMAgaY7mzo9DAbXQR0sMAXBAyqtJe_DE",
    time_series_api_module=ClientModuleMap.forecast_models_time_series_api_module.name
)

df = data_source.get_meter_and_weather_data(timespan)
df.index.name = "date_time"
df = df.reindex(timestamp_index).interpolate(method="time").reset_index()
df.rename(columns={"index": "date_time"}, inplace=True)
df.to_csv("kyLibData.csv", index=False)