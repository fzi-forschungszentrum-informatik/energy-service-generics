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

# Valid input data that can be used to to check the forecasting or optimization
# code (as well as the worker).
REQUEST_INPUTS_FOOC_TEST = [
    {
        "Python": {"arguments": {"x": [0.5, 3, 6]}, "parameters": {"w": 0.5}},
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {"arguments": {"x": [0.5, 3, 6]}, "parameters": {"w": 0.5}},
    }
]

# Expected output if if items defined in `REQUEST_INPUT_FOOC_TEST` are
# provided to the forecasting optimization code (or the worker).
REQUEST_OUTPUTS_FOOC_TEST = [
    {
        "Python": {"f": [0.25, 1.5, 3]},
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {"f": [0.25, 1.5, 3]},
    }
]

# Valid input and output data that should _not_ be used while testing the
# forecasting or optimization code _but only_ for testing the data models.
# This could be useful in case that running the forecasting or optimization
# code is slow or needs mocking, e.g. for data sources. The latter especially,
# as providing realistic data as mock for all cases might cause large efforts.
#
# NOTE: In this example we add no additional test data beyond what is defined
#       in for `FOOC_TESTING` as the data models are super simple.
REQUEST_INPUTS_MODEL_TEST = REQUEST_INPUTS_FOOC_TEST + []

REQUEST_OUTPUTS_MODEL_TEST = REQUEST_OUTPUTS_FOOC_TEST + []

# Input data which the request endpoint should reject.
INVALID_REQUEST_INPUTS = [
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
INVALID_REQUEST_OUTPUTS = [
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

# Test data for the fit parameter endpoints corresponding to the concept
# used for the request endpoint as explained above.
FIT_PARAM_INPUTS_FOOC_TEST = [
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

FIT_PARAM_OUTPUTS_FOOC_TEST = [
    {
        "Python": {"w": 0.5},
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {"w": 0.5},
    }
]

FIT_PARAM_INPUTS_MODEL_TEST = FIT_PARAM_INPUTS_FOOC_TEST + []

FIT_PARAM_OUTPUTS_MODEL_TEST = FIT_PARAM_OUTPUTS_FOOC_TEST + []

INVALID_FIT_PARAM_INPUTS = [
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

INVALID_FIT_PARAM_OUTPUTS = [
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
