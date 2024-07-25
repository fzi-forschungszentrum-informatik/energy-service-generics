"""
Tests for `data_model.py`

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

from esg.service.worker import compute_request_input_model
from esg.service.worker import compute_fit_parameters_input_model
from esg.test.generic_tests import GenericMessageSerializationTest

from data_model import RequestArguments
from data_model import FittedParameters
from data_model import RequestOutput
from data_model import FitParameterArguments
from data_model import Observations
from .data import REQUEST_INPUTS_MODEL_TEST
from .data import REQUEST_OUTPUTS_MODEL_TEST
from .data import INVALID_REQUEST_INPUTS
from .data import INVALID_REQUEST_OUTPUTS
from .data import FIT_PARAM_INPUTS_MODEL_TEST
from .data import FIT_PARAM_OUTPUTS_MODEL_TEST
from .data import INVALID_FIT_PARAM_INPUTS
from .data import INVALID_FIT_PARAM_OUTPUTS


RequestInput = compute_request_input_model(
    RequestArguments=RequestArguments,
    FittedParameters=FittedParameters,
)


class TestRequestInput(GenericMessageSerializationTest):
    """
    Tests for the `RequestArguments` and `FittedParameters` data models.
    """

    ModelClass = RequestInput
    msgs_as_python = [m["Python"] for m in REQUEST_INPUTS_MODEL_TEST]
    msgs_as_jsonable = [m["JSONable"] for m in REQUEST_INPUTS_MODEL_TEST]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in INVALID_REQUEST_INPUTS]


class TestRequestOutput(GenericMessageSerializationTest):
    """
    Tests for the `RequestArguments` and `FittedParameters` data models.
    """

    ModelClass = RequestOutput
    msgs_as_python = [m["Python"] for m in REQUEST_OUTPUTS_MODEL_TEST]
    msgs_as_jsonable = [m["JSONable"] for m in REQUEST_OUTPUTS_MODEL_TEST]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in INVALID_REQUEST_OUTPUTS]


FitParametersInput = compute_fit_parameters_input_model(
    FitParameterArguments=FitParameterArguments,
    Observations=Observations,
)


class TestFitParametersInput(GenericMessageSerializationTest):
    """
    Tests for the `RequestArguments` and `FittedParameters` data models.
    """

    ModelClass = FitParametersInput
    msgs_as_python = [m["Python"] for m in FIT_PARAM_INPUTS_MODEL_TEST]
    msgs_as_jsonable = [m["JSONable"] for m in FIT_PARAM_INPUTS_MODEL_TEST]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in INVALID_FIT_PARAM_INPUTS]


class TestFitParametersOutput(GenericMessageSerializationTest):
    """
    Tests for the `RequestArguments` and `FittedParameters` data models.
    """

    ModelClass = FittedParameters
    msgs_as_python = [m["Python"] for m in FIT_PARAM_OUTPUTS_MODEL_TEST]
    msgs_as_jsonable = [m["JSONable"] for m in FIT_PARAM_OUTPUTS_MODEL_TEST]
    invalid_msgs_as_jsonable = [
        m["JSONable"] for m in INVALID_FIT_PARAM_OUTPUTS
    ]
