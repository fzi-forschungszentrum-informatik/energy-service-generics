"""
Code of the worker component.

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

from esg.service.worker import celery_app_from_environ
from esg.service.worker import invoke_fit_parameters
from esg.service.worker import invoke_handle_request

from data_model import RequestArguments, RequestOutput
from data_model import FittedParameters, Observations
from data_model import FitParameterArguments
from fooc import fit_parameters, handle_request

app = celery_app_from_environ()


@app.task
def request_task(input_data_json):
    return invoke_handle_request(
        input_data_json=input_data_json,
        RequestArguments=RequestArguments,
        FittedParameters=FittedParameters,
        handle_request_function=handle_request,
        RequestOutput=RequestOutput,
    )


@app.task
def fit_parameters_task(input_data_json):
    return invoke_fit_parameters(
        input_data_json=input_data_json,
        FitParameterArguments=FitParameterArguments,
        Observations=Observations,
        fit_parameters_function=fit_parameters,
        FittedParameters=FittedParameters,
    )
