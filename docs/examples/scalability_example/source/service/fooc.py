"""
Forecasting or optimization code of the service.

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

from time import sleep

SLEEP_TIME = float(os.getenv("SLEEP_TIME") or "10")


def handle_request(input_data):
    arguments = input_data.arguments
    sleep(SLEEP_TIME)

    output_data = {"i": arguments.i}
    return output_data
