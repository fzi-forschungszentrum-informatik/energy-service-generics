"""
Client software for testing the scalability demo service.

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

import os
from concurrent.futures import ThreadPoolExecutor
from time import monotonic, sleep

from esg.clients.service import GenericServiceClient
from esg.models.base import _BaseModel
from esg.service.worker import compute_request_input_model

SERVICE_BASE_URL = os.getenv("SCALABILITY_DEMO_SERVICE_BASE_URL")


class RequestArguments(_BaseModel):
    i: int


RequestInput = compute_request_input_model(
    RequestArguments=RequestArguments,
)


class RequestOutput(_BaseModel):
    i: int


def make_100_requests(client_number):

    client = GenericServiceClient(
        base_url=SERVICE_BASE_URL,
        verify=False,
        skip_verify_warning=True,
        InputModel=RequestInput,
        OutputModel=RequestOutput,
    )

    for i in range(100):
        request_number = client_number * 100 + i
        client.post_jsonable({"arguments": {"i": request_number}})

    _ = client.get_results_jsonable()

    return


pool = ThreadPoolExecutor(max_workers=100)


for _ in range(3):
    start = monotonic()
    n_results = sum([1 for _ in pool.map(make_100_requests, range(100))])

    elapsed = monotonic() - start
    print(f"Took {elapsed:.2f} seconds to execute {n_results*100} requests.")

    while monotonic() - start < 20.0:
        sleep(0.01)
