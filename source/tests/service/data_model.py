"""
Data models and corresponding payload functions for utilization in
tests of the service components.

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

from typing import List

from esg.models.base import _BaseModel
from esg.models.base import _RootModel


class RequestArguments(_BaseModel):
    ints: List[int]


class FittedParameters(_BaseModel):
    weights: list[int]


class RequestOutput(_BaseModel):
    weighted_sum: int


class FitParameterArguments(_RootModel):
    root: List[RequestArguments]


class Observations(_RootModel):
    root: List[RequestOutput]


def handle_request(input_data):
    """
    A simple payload function for the request endpoint that is logically
    matching the models above.
    """
    ints = input_data.arguments.ints
    if hasattr(input_data, "parameters"):
        weights = input_data.parameters.weights
    else:
        weights = [1] * len(ints)

    weighted_sum = 0
    for i, weight in zip(ints, weights):
        weighted_sum += i * weight

    return {"weighted_sum": weighted_sum}


def fit_parameters(input_data):
    """
    A simple payload function for the fit-parameters endpoint that is logically
    matching the models above.

    NOTE: If we would want to correctly compute the weights we would need
          some linear algebra and matrix computation. For testing we just
          assume we would have computed these and take fake values instead.
    """
    first_ints = input_data.arguments.root[0].ints
    weights = range(1, len(first_ints) + 1)

    # At least make sure the values are correct, although this completely
    # depends on if the test data has been selected correspondingly.
    for args, obs in zip(
        input_data.arguments.root, input_data.observations.root
    ):
        expected_weighted_sum = obs.weighted_sum
        actual_weighted_sum = 0
        for i, weight in zip(args.ints, weights):
            actual_weighted_sum += i * weight
        assert actual_weighted_sum == expected_weighted_sum

    return {"weights": weights}
