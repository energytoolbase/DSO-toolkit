# This script uses forecast-model package to run our current forecaster
import pandas as pd
import numpy as np
# === Custom forecast_models imports ===
from forecast_models.models.forecaster import Forecaster, ModelConfig
from datetime import datetime
import time
import tracemalloc
start_time = time.time()
tracemalloc.start()

# Fix for older NumPy versions
np.float = float

# ---------- CUSTOM FORECASTER ----------
model_config = ModelConfig.load_config_from_json("s3://i-kan-train/default_configs/ml-configs/site/model_config_v7.json")
model_config.dataset_config.dataset_location = "data/policeData-1year.csv"
model_config.dataset_config.timezone = "America/Chicago"
model_config.dataset_config.test_size_days = 2

forecaster = Forecaster(model_config=model_config, inference_only=False)
forecaster.train()
score, forecasts = forecaster.score(return_forecasts=True)

# Format and save custom forecaster output
forecasts.index.name = "start_time"
forecasts = forecasts.reset_index()
forecasts["start_time"] = pd.to_datetime(forecasts["start_time"]).dt.tz_convert("UTC")

forecasts.to_csv("output-custom/custom_forecaster_full_forecasts_1year-police.csv", index=False)