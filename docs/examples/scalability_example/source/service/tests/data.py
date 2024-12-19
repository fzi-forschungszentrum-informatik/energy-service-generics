"""
Datasets nice for testing.

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

# Valid input data that can be used to to check the forecasting or optimization
# code (as well as the worker).
REQUEST_INPUTS_FOOC_TEST = [
    {
        "Python": {
            "arguments": {
                "i": 1,
            },
        },
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {
            "arguments": {
                "i": 1,
            },
        },
    }
]

# Expected output if if items defined in `REQUEST_INPUT_FOOC_TEST` are
# provided to the forecasting optimization code (or the worker).
REQUEST_OUTPUTS_FOOC_TEST = [
    {
        "Python": {
            "i": 1,
        },
        "JSONable": {
            "i": 1,
        },
    }
]

# Valid input and output data that should _not_ be used while testing the
# forecasting or optimization code _but only_ for testing the data models.
# This could be useful in case that running the forecasting or optimization
# code is slow or needs mocking, e.g. for data sources. The latter especially,
# as providing realistic data as mock for all cases might cause large efforts.
REQUEST_INPUTS_MODEL_TEST = REQUEST_INPUTS_FOOC_TEST + []

REQUEST_OUTPUTS_MODEL_TEST = REQUEST_OUTPUTS_FOOC_TEST + []

# Input data which the request endpoint should reject.
INVALID_REQUEST_INPUTS = [
    # field not provided.
    {
        "JSONable": {"arguments": {"j": 2}},
    },
]

# Output data which output model should reject.
INVALID_REQUEST_OUTPUTS = [
    # field not provided.
    {
        "JSONable": {"j": 2},
    },
]
