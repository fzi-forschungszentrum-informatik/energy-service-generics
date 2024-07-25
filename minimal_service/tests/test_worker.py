"""
Tests for `worker.py`

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

from esg.test.generic_tests import GenericWorkerTaskTest

from worker import fit_parameters_task, request_task
from .data import REQUEST_INPUTS_FOOC_TEST
from .data import REQUEST_OUTPUTS_FOOC_TEST
from .data import FIT_PARAM_INPUTS_FOOC_TEST
from .data import FIT_PARAM_OUTPUTS_FOOC_TEST


class TestRequestTask(GenericWorkerTaskTest):
    task_to_test = request_task
    input_data_jsonable = [m["JSONable"] for m in REQUEST_INPUTS_FOOC_TEST]
    output_data_jsonable = [m["JSONable"] for m in REQUEST_OUTPUTS_FOOC_TEST]


class TestFitParametersTask(GenericWorkerTaskTest):
    task_to_test = fit_parameters_task
    input_data_jsonable = [m["JSONable"] for m in FIT_PARAM_INPUTS_FOOC_TEST]
    output_data_jsonable = [m["JSONable"] for m in FIT_PARAM_OUTPUTS_FOOC_TEST]
