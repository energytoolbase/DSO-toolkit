"""Mock service client classes."""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import pytz
from forecast_models.data_models import LoadTypes
from forecast_models.data_sources.grid_gateway_api.enums import EmsType, MetaDataType
from forecast_models.data_sources.grid_gateway_api.models import (
    EmsOracleServiceResult,
    IdResult,
    SiteResult,
    WireguardResult,
)
from forecast_models.electric_billing_api.models import BillCalculationResponse, PowerSeries

MOCK_ORACLE_VERSION = "15.0.2"


class MockGridGatewayClient:
    """A Mock class to interact with the grid-gateway."""

    def __init__(self, **kwargs):
        """Mock method to initialize a grid-gateway client object.

        Args:
            kwargs (any): Other arguments not necessary for mock purposes.
        """

    def query_sites_with_oracle(self) -> List[str]:
        """Mock method to return a list of sites which have oracle service.

        Returns:
            List[str], a list of sites
        """
        return ["rio-museum", "tennsco", "plas-tech"]

    def query_site_meta_data(
        self,
        meta_type: MetaDataType,
        **kwargs,
    ) -> Union[IdResult, EmsOracleServiceResult, SiteResult, WireguardResult]:
        """Mock method to query the meta data of a site.

        Args:
            meta_type (MetaDataType): The meta data type that need to be queried.
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            Union[IdResult, EmsOracleServiceResult, SiteResult, WireguardResult]: Based on the
            given `meta_type`, will return one of IdResult, EmsOracleServiceResult, SiteResult,
            WireguardResult.
        """
        match meta_type:
            case MetaDataType.id:
                return IdResult(id="378dea26558697211aea196b5e309954")
            case MetaDataType.site:
                return SiteResult(
                    id=30,
                    latitude=35.0971616,
                    longitude=-106.6681164,
                    ems_type=EmsType.prod,
                    timezone="America/Denver",
                    data_start_date=datetime(2017, 9, 24, 0, 0, tzinfo=timezone.utc),
                )
            case MetaDataType.ems_oracle_service:
                return EmsOracleServiceResult(
                    version=MOCK_ORACLE_VERSION,
                    forecast_config_file_path="s3://i-kan-train-ci-read/30/forecast-configs/forecast_config_30_v0.0.2.json",
                    error_config_file_path="s3://i-kan-train-ci-read/30/error-configs/error_config_30_v0.0.1.json",
                    model_pipeline_enabled=True,
                    forecast_config_created=True,
                )

    def query_load_types_need_forecast(self, **kwargs) -> List:
        """Mock method to get the meter load types (site and/or PV) of the given site that need forecasts. We should get the traces \
        from this function AS WELL AS check if Oracle Service is configured for the site to guarantee that these load \
        type(s) need a forecast.

        Args:
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            List: List of load types that need a forecast that the site has.
        """
        return [LoadTypes.site.value, LoadTypes.pv.value]

    def update_oracle_data_for_a_gateway(
        self,
        **kwargs,
    ):
        """Mock method to update Oracle data for a site in the grid-gateway.

        Args:
            kwargs (any): Other arguments not necessary for mock purposes.
        """
        pass

    def sync_ems(
        self,
        **kwargs,
    ):
        """Mock method to sync salt based on data in grid-gateway.

        Args:
            kwargs (any): Other arguments not necessary for mock purposes.
        """
        pass

    def get_billing_periods(self, *args, **kwargs) -> List[Dict[str, datetime]]:
        """Mock method to return billing periods.

        Args:
            args (any): Other arguments not necessary for mock purposes.
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            List[Dict(str, datetime)]: dummy billing periods
        """
        billing_periods = [
            {
                "start": datetime(2023, 7, 7, 6, 0, tzinfo=pytz.UTC),
                "end": datetime(2023, 8, 8, 6, 0, tzinfo=pytz.UTC),
            },
            {
                "start": datetime(2023, 6, 7, 6, 0, tzinfo=pytz.UTC),
                "end": datetime(2023, 7, 7, 6, 0, tzinfo=pytz.UTC),
            },
        ]
        return billing_periods

    def get_ess_control_settings(self, *args, **kwargs) -> Dict:
        """Mock method to return ess control settings.

        Args:
            args (any): Other arguments not necessary for mock purposes.
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            Dict: Dummy ess control settings
        """
        return {
            "has_pv_charging_requirement": True,
            "can_export_ess_energy": False,
            "peak_shaving": True,
            "peak_shaving_can_target_tou_periods": True,
            "energy_arbitrage": False,
            "energy_arbitrage_controller": "max_savings_with_dynamic_schedule_controller",
        }

    def get_ess_system_settings(self, *args, **kwargs) -> Dict:
        """Mock method to return ess system settings.

        Args:
            args (any): Other arguments not necessary for mock purposes.
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            Dict: Dummy ess system settings
        """
        return {
            "inverter_qty": 1,
            "battery_qty": 1,
            "simple_total_energy_capacity": 176.0,
            "simple_charge_efficiency": 0.97,
            "simple_discharge_efficiency": 0.94,
            "simple_max_power_charge": 110.0,
            "simple_max_power_discharge": 110.0,
            "aes_system_type": "simple",
            "simple_system_coupling": "ac",
        }

    def get_rate_schedule_id(self, *args, **kwargs) -> int:
        """Mock method to return rate schedule id.

        Args:
            args (any): Other arguments not necessary for mock purposes.
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            int: Dummy rate schedule id
        """
        return 4041095


class MockWeatherAPIClient:
    """This mock class is design to fetch data from ETB internal weather API."""

    def __init__(self, **kwargs):
        """Inits weather api client.

        Args:
            kwargs (any): Other arguments not necessary for mock purposes.
        """

    def retrieve_weather_data(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        **kwargs,
    ) -> pd.DataFrame:
        """Mock method to retrieve weather data from the ETB internal weather API. Can be either condition (historical) or forecast \
        (future) data, depending on the url.

        Args:
            start_datetime (datetime): start datetime of weather interval
            end_datetime (datetime): end datetime of weather interval
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            pd.DataFrame: weather data
        """
        df = pd.read_csv("tests/data/weather_data.csv")
        df.index = pd.to_datetime(df["start_time"])
        df = df.drop(columns=["start_time"])
        # Subtract and add 45 minutes to start and endtime to account for 1 hour interval of weather data.
        return df.loc[
            start_datetime - timedelta(minutes=45) : end_datetime + timedelta(minutes=45)
        ]


class MockTimeSeriesAPIClient:
    """Mock client for the Time Series API."""

    GATEWAY_ID_KEY = "gateway_id"

    def __init__(self, **kwargs):
        """Mock method that initializes the Time Series API Client.

        Args:
            kwargs (any): Other arguments not necessary for mock purposes.
        """

    def get_timeseries_data(
        self,
        load_types: List[str],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Mock method that retrieves timeseries data for the given site and load types between the start time and end time. The start and end times must be in UTC.

        Args:
            load_types (List[str]): List of load type data to retrieve.
            start_time (Optional[datetime]): Start of data retrieval. Typically, this should be the start time given by the \
            grid gateway for this site.
            end_time (Optional[datetime]): End of data retrieval. The data retrieved is exclusive of this point.
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            pd.DataFrame: Dataframe of query results.
        """
        df = pd.read_csv("tests/data/rio-museum.csv")
        df.index = pd.to_datetime(df["Date"] + " " + df["Time"])
        data = (
            df.rename(columns={"Current Demand": "site", "Solar PV Power": "pv"})
            .tz_localize("UTC")
            .loc[:, load_types]
        )
        if start_time:
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=pytz.UTC)
            data = data.loc[start_time:, :]

        if end_time:
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=pytz.UTC)
            data = data.loc[:end_time, :]
        return data


class MockElectricBillingAPIClient:
    """Mock client for the electric billing API."""

    def __init__(self, **kwargs):
        """Mock method that initializes the electric billing API Client.

        Args:
            kwargs (any): Other arguments not necessary for mock purposes.
        """

    def compute_ess_trace(
        self, *args, **kwargs
    ) -> Tuple[List[PowerSeries], List[PowerSeries], List[PowerSeries]]:
        """Mock method to return simulated ess trace.

        Args:
            args (any): Other arguments not necessary for mock purposes.
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            Tuple[List[PowerSeries], List[PowerSeries], List[PowerSeries]]: Dummy power series.
        """
        start_date = datetime(2023, 6, 7, 6, 0, tzinfo=pytz.UTC).astimezone(
            pytz.timezone("America/Denver")
        )
        end_date = datetime(2023, 8, 8, 6, 0, tzinfo=pytz.UTC).astimezone(
            pytz.timezone("America/Denver")
        )
        date_range = pd.date_range(start_date, end_date, freq="1D")
        ess_power_series = [
            PowerSeries(date=date_time.strftime("%m-%d-%Y"), power=[10] * 96)
            for date_time in date_range
        ]
        site_power_series = [
            PowerSeries(date=date_time.strftime("%m-%d-%Y"), power=[100] * 96)
            for date_time in date_range
        ]
        pv_power_series = [
            PowerSeries(date=date_time.strftime("%m-%d-%Y"), power=[20] * 96)
            for date_time in date_range
        ]
        return ess_power_series, site_power_series, pv_power_series

    def calculate_bills(self, *args, **kwargs) -> BillCalculationResponse:
        """Mock method to return bills.

        Args:
            args (any): Other arguments not necessary for mock purposes.
            kwargs (any): Other arguments not necessary for mock purposes.

        Returns:
            BillCalculationResponse: Dummy bills.
        """
        statements = []
        rate_schedule = {"id": 123, "effective_date": "test", "name": "test", "utility": "test"}
        charges = {
            "customer": 120.0,
            "nbc": 30.5,
            "demand": 45.75,
            "energy": 60.25,
            "energy_charge_after_credit": 55.25,
            "energy_after_true_up": 50.0,
            "true_up_credit": 5.0,
            "total_before_credit_adjustment": 256.5,
            "total_after_credit_adjustment": 251.5,
            "cumulative_energy_credit": 10.0,
            "cumulative_energy_charge": 150.0,
            "change_in_cumulative_energy_charge": 5.0,
        }
        demand = {
            "import": 50.0,
            "export": 30.0,
            "date": "2023-06-07T00:00:00Z",
            "index": 42,
            "tou_period_id": "onPeak",
        }

        for time_delta in range(1000, 3000, 1000):
            statement = {"start": 0 + time_delta, "end": 100 + time_delta, "season": "summer"}
            statement.update(
                {
                    "rate_schedule": rate_schedule,
                    "min_demand": demand,
                    "max_demand": demand,
                    "charges": charges,
                    "load_factor": 0.1,
                }
            )
            statements.append(statement)
        return BillCalculationResponse(statements=statements)