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

NOTE: Need to change something here? Check if the examples services need to
      be adjusted too!
"""

from typing import List

from esg.models.base import _BaseModel
from pydantic import Field


class RequestArguments(_BaseModel):
    x: List[float] = Field(
        description=(
            "The X coordinates for which the linear regression should "
            "be computed"
        ),
        examples=[[0.5, 3.0, 6.0]],
    )


class FittedParameters(_BaseModel):
    w: float = Field(
        description="Slope of the linear model.",
        examples=[0.5],
    )


class RequestOutput(_BaseModel):
    f: List[float] = Field(
        description="The computed output of the linear regression.",
        examples=[[0.25, 1.5, 3.0]],
    )


FitParameterArguments = RequestArguments


class Observations(_BaseModel):
    y: List[float] = Field(
        description="Observed values used for training the model.",
        examples=[[0.5, 1.5, 2.75]],
    )
