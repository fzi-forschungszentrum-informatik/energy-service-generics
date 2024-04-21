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

from packaging.version import Version

from esg.service.api import API

from data_model import RequestArguments, RequestOutput
from data_model import FittedParameters, Observations
from data_model import FitParameterArguments
from worker import request_task, fit_parameters_task

api = API(
    RequestArguments=RequestArguments,
    RequestOutput=RequestOutput,
    FittedParameters=FittedParameters,
    Observations=Observations,
    FitParameterArguments=FitParameterArguments,
    request_task=request_task,
    fit_parameters_task=fit_parameters_task,
    title="PV Power Prediction Example Service",
    version=Version("0.0.1"),
)

if __name__ == "__main__":
    api.run()
