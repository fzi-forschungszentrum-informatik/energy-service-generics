"""
Definition of the data models for de-/serializing data and the docs.

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

from esg.models.base import _BaseModel
from esg.models.datapoint import ValueMessageList
from esg.models.metadata import GeographicPosition, PVSystem
from pydantic import Field


class RequestArguments(_BaseModel):
    geographic_position: GeographicPosition


class RequestOutput(_BaseModel):
    power_prediction: ValueMessageList = Field(
        description="Prediction of power production in W"
    )

class FitParameterArguments(_BaseModel):
    geographic_position: GeographicPosition

class Observations(_BaseModel):
    measured_power: ValueMessageList = Field(
        description="Measured power production in W"
    )

class FittedParameters(_BaseModel):
    pv_system: PVSystem

