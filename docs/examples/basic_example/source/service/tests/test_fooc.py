"""
Tests for content of fooc.py

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
from unittest.mock import patch

from esg.utils.pandas import value_message_list_from_series
from esg.service.worker import compute_request_input_model
from esg.service.worker import compute_fit_parameters_input_model
import pandas as pd
import pytest

from service.fooc import predict_pv_power, fetch_meteo_data
from service.fooc import handle_request, fit_parameters
from service.data_model import RequestArguments
from service.data_model import FittedParameters, Observations
from service.data_model import FitParameterArguments
from .data import OPEN_METEO_RESPONSE, OPEN_METEO_RESPONSE_DF

RequestInput = compute_request_input_model(
    RequestArguments=RequestArguments,
    FittedParameters=FittedParameters,
)

FitParametersInput = compute_fit_parameters_input_model(
    FitParameterArguments=FitParameterArguments,
    Observations=Observations,
)


class OpenMeteoHttpServer:
    """
    Helper class for tests thad would interact with Open Meteo.
    """

    def __init__(self, httpserver):
        self.httpserver = httpserver

    def add_request(self, lat, lon, past_days):
        expected_request = self.httpserver.expect_oneshot_request(
            "/v1/forecast",
            query_string={
                "latitude": str(lat),
                "longitude": str(lon),
                "minutely_15": (
                    "shortwave_radiation,diffuse_radiation,"
                    "direct_normal_irradiance"
                ),
                "past_days": str(past_days),
                "forecast_days": "1",
            },
        )
        expected_request.respond_with_json(OPEN_METEO_RESPONSE)


@pytest.fixture
def open_meteo_httpserver(httpserver):
    oma_test_url = httpserver.url_for("")[:-1]
    om_httpserver = OpenMeteoHttpServer(httpserver=httpserver)
    with patch.dict(os.environ, {"OPEN_METEO_API_URL": oma_test_url}):
        yield om_httpserver


def test_predict_pw_power():
    """
    Check that the PV model generally works and produces the expected output.
    """
    expected_power = (
        pd.Series(
            index=[
                pd.Timestamp("2017-04-01 12:00:00-0700", tz="US/Arizona"),
                pd.Timestamp("2017-04-01 13:00:00-0700", tz="US/Arizona"),
            ],
            # Has been computed with checked inputs by pvlib.
            data=[187.42544617515875, 186.28669899250573],
        )
        / 290
        * 2.5
    )
    meteo_data = pd.DataFrame(
        [[1050, 1000, 100], [1050, 1000, 100]],
        columns=["ghi", "dni", "dhi"],
        index=[
            pd.Timestamp("20170401 1200", tz="US/Arizona"),
            pd.Timestamp("20170401 1300", tz="US/Arizona"),
        ],
    )
    actual_power = predict_pv_power(
        lat=32.2,
        lon=-110.9,
        inclination=20,
        azimuth=20,
        peak_power=2.5,
        meteo_data=meteo_data,
    )
    # Allow some slight deviations as pvlib updates seem to affect the
    # computed numbers a bit.
    pd.testing.assert_series_equal(actual_power, expected_power, rtol=0.005)


def test_fetch_meteo_data(open_meteo_httpserver):
    """
    Verify that the `fetch_meteo_data` can parse the data in the open
    meteo format to a dataframe matching the needs of `predict_pv_power`.
    """
    open_meteo_httpserver.add_request(
        lat=32.2,
        lon=-110.9,
        past_days=2,
    )

    meteo_data = fetch_meteo_data(lat=32.2, lon=-110.9, past_days=2)
    pd.testing.assert_frame_equal(meteo_data, OPEN_METEO_RESPONSE_DF)

    # Furthermore verify that the output of `fetch_meteo_data` is compatible
    # with the format expected by `predict_pv_power`. This needs no `assert`,
    # it's fine if no exception is raised.
    _ = predict_pv_power(
        lat=32.2,
        lon=-110.9,
        inclination=20,
        azimuth=15,
        peak_power=1.0,
        meteo_data=meteo_data,
    )


def test_handle_request(open_meteo_httpserver):
    """
    Check that handle request returns the expected prediction.
    """
    expected_power_pd = predict_pv_power(
        lat=35.2,
        lon=-110.0,
        inclination=30,
        azimuth=20,
        peak_power=5.0,
        meteo_data=OPEN_METEO_RESPONSE_DF,
    )
    expected_output = {
        "power_prediction": value_message_list_from_series(expected_power_pd)
    }

    input_data = RequestInput(
        arguments={
            "geographic_position": {
                "latitude": 35.2,
                "longitude": -110.0,
            }
        },
        parameters={
            "pv_system": {
                "azimuth_angle": 20,
                "inclination_angle": 30,
                "nominal_power": 5.0,
            }
        },
    )

    open_meteo_httpserver.add_request(
        lat=35.2,
        lon=-110.0,
        past_days=0,
    )

    actual_output = handle_request(input_data=input_data)
    assert actual_output == expected_output


def test_fit_parameters(open_meteo_httpserver):
    """
    Verify that `fit_parameters` can recover the parameters from
    pseudo measurements.
    """
    measured_data_pd = predict_pv_power(
        lat=35.2,
        lon=-110.0,
        inclination=25,
        azimuth=15,
        peak_power=4.5,
        meteo_data=OPEN_METEO_RESPONSE_DF,
    )
    # Remove parts of the index to make it more interesting:
    measured_data_pd = measured_data_pd.iloc[:-12]

    expected_output = {
        "pv_system": {
            "azimuth_angle": 15,
            "inclination_angle": 25,
            "nominal_power": 4.5,
        }
    }

    input_data = FitParametersInput(
        arguments={
            "geographic_position": {
                "latitude": 35.2,
                "longitude": -110.0,
            }
        },
        observations={
            "measured_power": value_message_list_from_series(measured_data_pd)
        },
    )

    open_meteo_httpserver.add_request(
        lat=35.2,
        lon=-110.0,
        past_days=90,
    )

    actual_output = fit_parameters(input_data=input_data)
    assert actual_output == expected_output
