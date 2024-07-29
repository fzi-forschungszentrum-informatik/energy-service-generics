"""
Tests for `api.py`

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
from esg.test.generic_tests import GenericAPITest

from api import api as tested_api
from data_model import RequestArguments
from data_model import FittedParameters
from data_model import RequestOutput
from data_model import FitParameterArguments
from data_model import Observations
from worker import app
from .data import REQUEST_INPUTS_FOOC_TEST
from .data import REQUEST_OUTPUTS_FOOC_TEST
from .data import FIT_PARAM_INPUTS_FOOC_TEST
from .data import FIT_PARAM_OUTPUTS_FOOC_TEST

RequestInput = compute_request_input_model(
    RequestArguments=RequestArguments,
    FittedParameters=FittedParameters,
)


class TestRequestEndpoint(GenericAPITest):
    tested_api = tested_api
    celery_app = app
    endpoint = "request"
    InputDataModel = RequestInput
    OutputDataModel = RequestOutput
    input_data_jsonable = [m["JSONable"] for m in REQUEST_INPUTS_FOOC_TEST]
    output_data_jsonable = [m["JSONable"] for m in REQUEST_OUTPUTS_FOOC_TEST]


FitParametersInput = compute_fit_parameters_input_model(
    FitParameterArguments=FitParameterArguments,
    Observations=Observations,
)


class TestFitParametersEndpoint(GenericAPITest):
    tested_api = tested_api
    celery_app = app
    endpoint = "fit-parameters"
    InputDataModel = FitParametersInput
    OutputDataModel = FittedParameters
    input_data_jsonable = [m["JSONable"] for m in FIT_PARAM_INPUTS_FOOC_TEST]
    output_data_jsonable = [m["JSONable"] for m in FIT_PARAM_OUTPUTS_FOOC_TEST]
