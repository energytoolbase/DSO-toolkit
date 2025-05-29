# Chronos Model Performance Comparison

This repository contains my research on evaluating the performance of the **Chronos** model and comparing it with our current forecaster in the `forecast-model` package.

## Main Scripts

* **`chronosMultipleSite.py`** and **`chronosMultipleSiteFineTuned.py`**
  These scripts train the Chronos model across multiple sites. You can:

  * Assign different item IDs to different sites and train a single model for all of them.
  * Try a single item for a single site for more focused testing.

  Output is saved to:

  * `output-mul/` for the base Chronos model
  * `output-mul-FT/` for the fine-tuned Chronos model

* **`getDataset.py`**
  Fetches time series and weather data via API clients. It uses `mock.py` to mock the service client classes. Data is saved in the `data/` directory.

## Custom Forecasters

The `custom_forecasters` scripts are used to:

* Run forecasts using our current forecaster from the `forecast-model` package
* Plot and compare the results

Output is saved to the `output-custom/` directory.

## Environment Setup

Make sure to clone the `forecast-model` repository in the same directory to access its classes and methods.

### Required Python Packages

You'll need the following Python packages installed:

* `pandas`
* `numpy`
* `matplotlib`
* `scikit-learn`
* `pytz`
* `autogluon.timeseries`

You can install them with:

```bash
pip install pandas numpy matplotlib scikit-learn pytz autogluon.timeseries
```
