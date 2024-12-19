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
from esg.service.worker import invoke_handle_request

from data_model import RequestArguments, RequestOutput
from fooc import handle_request


import os
from pathlib import Path
from celery import Celery


app = celery_app_from_environ()


@app.task
def request_task(input_data_json):
    return invoke_handle_request(
        input_data_json=input_data_json,
        RequestArguments=RequestArguments,
        handle_request_function=handle_request,
        RequestOutput=RequestOutput,
    )
