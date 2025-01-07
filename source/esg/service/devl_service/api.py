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

from esg.service.api import API

from .data_model import RequestArguments, RequestOutput
from .data_model import FittedParameters, Observations
from .data_model import FitParameterArguments
from .worker import request_task, fit_parameters_task

api = API(
    RequestArguments=RequestArguments,
    RequestOutput=RequestOutput,
    request_task=request_task,
    title="Minimal Viable Service",
    FitParameterArguments=FitParameterArguments,
    FittedParameters=FittedParameters,
    Observations=Observations,
    fit_parameters_task=fit_parameters_task,
    description=(
        "This service is only intended for development of the package "
        "and allows to verify interactively how changes in the source "
        "code affect a service, which is particularly important for "
        "code segments that are hard to test, like e.g. related to "
        "the interactive documentation. To this end it implements a "
        "super simple 1D linear regression."
    ),
)

if __name__ == "__main__":
    api.run()
