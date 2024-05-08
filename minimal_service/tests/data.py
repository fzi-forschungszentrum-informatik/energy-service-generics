"""
Data that can be used in tests.

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

# Valid input data for the request endpoint.
REQUEST_INPUT_SAMPLES = [
    {
        "Python": {"arguments": {"x": [0.5, 3, 6]}, "parameters": {"w": 0.5}},
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {"arguments": {"x": [0.5, 3, 6]}, "parameters": {"w": 0.5}},
    }
]

# Output expected if data from `REQUEST_INPUT_SAMPLES` is used to compute a
# request task
REQUEST_OUTPUT_FOR_INPUT_SAMPLES = [
    {
        "Python": {"f": [0.25, 1.5, 3]},
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {"f": [0.25, 1.5, 3]},
    }
]

# Valid output data for the request endpoint.
# Might want to add additional examples for testing the data models.
REQUEST_OUTPUT_SAMPLES = [] + REQUEST_OUTPUT_FOR_INPUT_SAMPLES

# Input data which the request endpoint should reject.
INVALID_REQUEST_INPUT_SAMPLES = [
    # No arguments
    {
        "JSONable": {"parameters": {"w": 0.5}},
    },
    # No parameters
    {
        "JSONable": {"arguments": {"x": [0.5, 3, 6]}},
    },
    # x not list
    {
        "JSONable": {"arguments": {"x": 0.5}, "parameters": {"w": 0.5}},
    },
    # w not float
    {
        "JSONable": {
            "arguments": {"x": [0.5, 3, 6]},
            "parameters": {"w": [1.0]},
        },
    },
]

# Output data which output model should reject.
INVALID_REQUEST_OUTPUT_SAMPLES = [
    # No return value.
    {
        "JSONable": None,
    },
    # Empty dict returned
    {
        "JSONable": {},
    },
    # values not a list
    {
        "JSONable": {"f": 0.25},
    },
]

# Valid input data for the fit-parameters endpoint.
FIT_PARAMETERS_INPUT_SAMPLES = [
    {
        "Python": {
            "arguments": {"x": [0.5, 6, 6]},
            "observations": {"y": [0.25, 3.25, 2.75]},
        },
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {
            "arguments": {"x": [0.5, 6, 6]},
            "observations": {"y": [0.25, 3.25, 2.75]},
        },
    }
]

# Output expected if data from `FIT_PARAMETERS_INPUT_SAMPLES` is used to
# compute a fit-parameters task
FIT_PARAMETERS_OUTPUT_FOR_INPUT_SAMPLES = [
    {
        "Python": {"w": 0.5},
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {"w": 0.5},
    }
]

# Valid output data for the fit-parameters endpoint.
# Might want to add additional examples for testing the data models.
FIT_PARAMETERS_OUTPUT_SAMPLES = [] + FIT_PARAMETERS_OUTPUT_FOR_INPUT_SAMPLES

# Input data which the request endpoint should reject.
INVALID_FIT_PARAMETERS_INPUT_SAMPLES = [
    # No arguments
    {
        "JSONable": {"observations": {"y": [0.5, 1.5, 2.75]}},
    },
    # No observations
    {
        "JSONable": {"arguments": {"x": [0.5, 3, 6]}},
    },
    # x not list
    {
        "JSONable": {
            "arguments": {"x": 0.5},
            "observations": {"y": [0.5, 1.5, 2.75]},
        },
    },
    # y not list
    {
        "JSONable": {
            "arguments": {"x": [0.5, 3, 6]},
            "observations": {"y": 0.5},
        },
    },
]

# Output data which output model should reject.
INVALID_FIT_PARAMETERS_OUTPUT_SAMPLES = [
    # No return value.
    {
        "JSONable": None,
    },
    # Empty dict returned
    {
        "JSONable": {},
    },
    # value is a list instead of a float.
    {
        "JSONable": {"w": [0.25]},
    },
]
