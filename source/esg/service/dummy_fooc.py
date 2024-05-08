"""
Dummy Forecasting or optimization code of the service.

This file can be used to provide a fooc.py file to the API component that
has a valid signature but not the actual code. This allows the API to
import the tasks from the worker without requiring to install all dependencies
the worker code might have.

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


def handle_request(input_data):
    raise NotImplementedError()


def fit_parameters(input_data):
    raise NotImplementedError()
