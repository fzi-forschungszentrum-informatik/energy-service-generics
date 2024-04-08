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

from celery import Celery
from esg.service.worker import execute_payload

from data_model import RequestInput
from data_model import RequestOutput


app = Celery(
    __name__,
    broker_url="filesystem://",
    broker_transport_options={
        "data_folder_in": "/celery/broker/",
        "data_folder_out": "/celery/broker/",
    },
    result_backend="file:///celery/results/",
)


def compute_request(input_data):
    return {"test2": str(input_data.test1)}


@app.task
def request_task(input_data_json):
    output_data_json = execute_payload(
        input_data_json=input_data_json,
        InputDataModel=RequestInput,
        payload_function=compute_request,
        OutputDataModel=RequestOutput,
    )
    return output_data_json
