"""
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

from esg.clients.service import GenericServiceClient
from esg.models.base import _BaseModel
from esg.models.datapoint import ValueMessageList
from esg.models.metadata import GeographicPosition, PVSystem
from esg.service.worker import compute_request_input_model
from pydantic import Field

SERVICE_BASE_URL = os.getenv("SERVICE_BASE_URL")


class RequestArguments(_BaseModel):
    geographic_position: GeographicPosition


class FittedParameters(_BaseModel):
    pv_system: PVSystem


RequestInput = compute_request_input_model(
    RequestArguments=RequestArguments, FittedParameters=FittedParameters
)


class RequestOutput(_BaseModel):
    power_prediction: ValueMessageList = Field(
        description="Prediction of power production in W"
    )


client = GenericServiceClient(
    base_url=SERVICE_BASE_URL,
    InputModel=RequestInput,
    OutputModel=RequestOutput,
)

client.post_obj(
    input_data_obj={
        "arguments": {
            "geographic_position": {"latitude": 49.01365, "longitude": 8.40444}
        },
        "parameters": {
            "pv_system": {
                "azimuth_angle": 0,
                "inclination_angle": 30,
                "nominal_power": 15,
            }
        },
    }
)

print(client.get_results_obj())
