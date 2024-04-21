"""
Forecasting or optimization code of the service.

Copyright 2024 FZI Research Center for Information Technology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-FileCopyrightText: 2024 FZI Research Center for Information Technology
SPDX-License-Identifier: Apache-2.0
"""

import os

from esg.utils.pandas import series_from_value_message_list
from esg.utils.pandas import value_message_list_from_series
import pandas as pd
from pvlib.pvsystem import retrieve_sam, PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
import requests
from scipy.optimize import least_squares

OPEN_METEO_API_URL_DEFAULT = "https://api.open-meteo.com"


def fetch_meteo_data(lat, lon, past_days=0):
    """
    Fetch relevant NWP data for the PV forecast from Open Meteo API.

    Arguments:
    ----------
    lat : float
        Latitude in degree.
    lon : float
        Longitude in degree.
    past_days : int
        Number of days in past for which the Forecast should be computed too.
        Up to 90 days is supported by the API. Use for fitting parameters.

    Environment Variables:
    ----------------------
    OPEN_METEO_API_URL:
        The Base URL of the Open Meteo API. Option is used in tests.
        Defaults to to `OPEN_METEO_API_URL_DEFAULT`.

    Returns:
    --------
    meteo_data : pd.DataFrame
        Irradiance data in format expected by pvlib.
    """

    open_meteo_api_url = os.getenv("OPEN_METEO_API_URL")
    if not open_meteo_api_url:
        open_meteo_api_url = OPEN_METEO_API_URL_DEFAULT

    # Fetch the data from Open Meteo API in their JSON format.
    response = requests.get(
        f"{open_meteo_api_url}/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "minutely_15": (
                "shortwave_radiation,diffuse_radiation,direct_normal_irradiance"
            ),
            "past_days": past_days,
            "forecast_days": 1,
        },
    )
    response.raise_for_status()
    meteo_data_json = response.json()["minutely_15"]

    # Convert to pandas DataFrame
    meteo_data = pd.DataFrame(
        index=pd.to_datetime(meteo_data_json.pop("time")), data=meteo_data_json
    )
    name_map = {
        "shortwave_radiation": "ghi",
        "diffuse_radiation": "dhi",
        "direct_normal_irradiance": "dni",
    }
    meteo_data.rename(name_map, axis=1, inplace=True)

    return meteo_data


def predict_pv_power(lat, lon, inclination, azimuth, peak_power, meteo_data):
    """
    Predict PV power generation.

    NOTE: This uses `pvlib` for computing the power. `pvlib` requires more
          details about the modelled PV system then we wish to use as inputs
          here. In order to make this example as simple as possible, while
          still relatively realistic we arbitrary select the type of the
          PV panels, the inverter and the options related to the temperature
          model of the system.

    Arguments:
    ----------
    lat : float
        Latitude in degree.
    lon : float
        Longitude in degree.
    inclination : float
        The angle between the panels and a horizontal line in degree.
    azimuth : float
        Angle between the direction of the panels and south in degree.
    peak_power : float
        Peak power of the PV system to predict.
    meteo_data : pd.DataFrame
        Irradiance data in format expected by pvlib.

    Returns:
    --------
    pv_power : pd.Series
        Predicted power of the PV System, in same unit as `peak_power`.
    """
    # Convert azimuth angle from ESG definition to `pvlib`
    azimuth = azimuth + 180

    # Predict PV power generation with `pvlib`.
    tmp = TEMPERATURE_MODEL_PARAMETERS["sapm"]["close_mount_glass_glass"]
    mps = retrieve_sam("SandiaMod")["LG_LG290N1C_G3__2013_"]
    ips = retrieve_sam("cecinverter")["SolarCity__H6"]
    system = PVSystem(
        surface_tilt=inclination,
        surface_azimuth=azimuth,
        module_parameters=mps,
        inverter_parameters=ips,
        temperature_model_parameters=tmp,
    )
    location = Location(latitude=lat, longitude=lon)
    mc = ModelChain(system, location)
    ac_power = mc.run_model(meteo_data).results.ac

    # Scale The power to the peak power. Note that the LG panel above has
    # is rated at 290Wp.
    pv_power = ac_power / 290 * peak_power

    # The panel has a rated peak power of 290W
    return pv_power


def fit_with_least_squares(lat, lon, meteo_data, measured_power):
    """
    Fit the parameters of `PVSystem` with ordinary least squares.

    This fits the azimuth and inclination angles as well as the
    peak power of the system. The main reason why this function is
    not part of `fit_parameters` below is to make the code of the
    latter small enough for usage in a publication.

    NOTE: This method only works as expected if `measured_power` contains
          index values (timestamps) that are exactly aligned with the index
          values `meteo_data`, i.e. that are aligned precisely to a 15 minute
          interval. This should be improved for a production service, but
          is considered good enough for the example.

    Arguments:
    ----------
    lat : float
        Latitude in degree.
    lon : float
        Longitude in degree.
    meteo_data : pd.DataFrame
        Irradiance data in format expected by pvlib.
    measured_power : pd.Series
        The measured power that is used for fitting.

    Returns:
    --------
    parameters : dict
        The fitted parameters `azimuth_angle`, `inclination_angle`
        and `nominal_power`.
    """
    # Prepare the time series, i.e. ensure that both series are
    # have values on the same times.
    measured_power = measured_power.reindex(meteo_data.index).dropna()
    meteo_data = meteo_data.reindex(measured_power.index)

    def worker(x, lat, lon, meteo_data):
        azimuth, inclination, peak_power = x
        pv_prediction = predict_pv_power(
            lat=lat,
            lon=lon,
            inclination=inclination,
            azimuth=azimuth,
            peak_power=peak_power,
            meteo_data=meteo_data,
        )
        residual = pv_prediction - measured_power
        return residual

    result = least_squares(
        worker,
        # A Panel facing south with 25° inclination and 10kW peak seems like
        # a fair guess to start with.
        x0=[0, 25, 10],
        kwargs={"lat": lat, "lon": lon, "meteo_data": meteo_data},
    )
    azimuth, inclination, peak_power = result.x.round(2)

    parameters = {
        "pv_system": {
            "azimuth_angle": azimuth,
            "inclination_angle": inclination,
            "nominal_power": peak_power,
        }
    }

    return parameters


def handle_request(input_data):
    arguments = input_data.arguments
    parameters = input_data.parameters
    meteo_data = fetch_meteo_data(
        lat=arguments.geographic_position.latitude,
        lon=arguments.geographic_position.longitude,
    )
    pv_power = predict_pv_power(
        lat=arguments.geographic_position.latitude,
        lon=arguments.geographic_position.longitude,
        azimuth=parameters.pv_system.azimuth_angle,
        inclination=parameters.pv_system.inclination_angle,
        peak_power=parameters.pv_system.nominal_power,
        meteo_data=meteo_data,
    )
    output_data = {"power_prediction": value_message_list_from_series(pv_power)}
    return output_data


def fit_parameters(input_data):
    arguments = input_data.arguments
    measured_power = series_from_value_message_list(
        input_data.observations.measured_power
    )
    meteo_data = fetch_meteo_data(
        lat=arguments.geographic_position.latitude,
        lon=arguments.geographic_position.longitude,
        past_days=90,
    )
    measured_power = series_from_value_message_list(
        input_data.observations.measured_power
    )
    fitted_pv_system = fit_with_least_squares(
        lat=arguments.geographic_position.latitude,
        lon=arguments.geographic_position.longitude,
        meteo_data=meteo_data,
        measured_power=measured_power,
    )
    output_data = {"parameters": fitted_pv_system}

    return output_data
