"""
Pytest fixtures that provided for all tests of the service.

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

import pytest

from .data import OPEN_METEO_RESPONSE


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
