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

import pandas as pd


# Valid input data that can be used to to check the forecasting or optimization
# code (as well as the worker).
REQUEST_INPUTS_FOOC_TEST = [
    {
        "Python": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                }
            },
            "parameters": {
                "pv_system": {
                    "azimuth_angle": 20,
                    "inclination_angle": 30,
                    "nominal_power": 5.0,
                }
            },
        },
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                }
            },
            "parameters": {
                "pv_system": {
                    "azimuth_angle": 20,
                    "inclination_angle": 30,
                    "nominal_power": 5.0,
                }
            },
        },
    }
]

# Expected output if if items defined in `REQUEST_INPUT_FOOC_TEST` are
# provided to the forecasting optimization code (or the worker).
"""
The predictions here have been generated with:
    expected_power_pd = predict_pv_power(
        lat=35.2,
        lon=-110.0,
        inclination=30,
        azimuth=20,
        peak_power=5.0,
        meteo_data=OPEN_METEO_RESPONSE_DF,
    )
    value_message_list_from_series(expected_power_pd)
"""
REQUEST_OUTPUTS_FOOC_TEST = [
    {
        "Python": {
            "power_prediction": [
                {
                    "value": None,
                    "time": pd.Timestamp("2024-04-14 13:00:00"),
                },
                {
                    "value": -0.03103448275862069,
                    "time": pd.Timestamp("2024-04-14 13:15:00"),
                },
                {
                    "value": -0.03103448275862069,
                    "time": pd.Timestamp("2024-04-14 13:30:00"),
                },
                {
                    "value": -0.03103448275862069,
                    "time": pd.Timestamp("2024-04-14 13:45:00"),
                },
                {
                    "value": -0.03103448275862069,
                    "time": pd.Timestamp("2024-04-14 14:00:00"),
                },
                {
                    "value": -0.03103448275862069,
                    "time": pd.Timestamp("2024-04-14 14:15:00"),
                },
                {
                    "value": -0.03103448275862069,
                    "time": pd.Timestamp("2024-04-14 14:30:00"),
                },
                {
                    "value": 0.15716195981910205,
                    "time": pd.Timestamp("2024-04-14 14:45:00"),
                },
                {
                    "value": 0.5581505422105254,
                    "time": pd.Timestamp("2024-04-14 15:00:00"),
                },
                {
                    "value": 0.8359556608828429,
                    "time": pd.Timestamp("2024-04-14 15:15:00"),
                },
                {
                    "value": 1.1247067830113573,
                    "time": pd.Timestamp("2024-04-14 15:30:00"),
                },
                {
                    "value": 1.3908757008598633,
                    "time": pd.Timestamp("2024-04-14 15:45:00"),
                },
                {
                    "value": 1.6435825418298649,
                    "time": pd.Timestamp("2024-04-14 16:00:00"),
                },
            ]
        },
        "JSONable": {
            "power_prediction": [
                {"value": None, "time": "2024-04-14T13:00:00"},
                {"value": -0.03103448275862069, "time": "2024-04-14T13:15:00"},
                {"value": -0.03103448275862069, "time": "2024-04-14T13:30:00"},
                {"value": -0.03103448275862069, "time": "2024-04-14T13:45:00"},
                {"value": -0.03103448275862069, "time": "2024-04-14T14:00:00"},
                {"value": -0.03103448275862069, "time": "2024-04-14T14:15:00"},
                {"value": -0.03103448275862069, "time": "2024-04-14T14:30:00"},
                {"value": 0.15716195981910205, "time": "2024-04-14T14:45:00"},
                {"value": 0.5581505422105254, "time": "2024-04-14T15:00:00"},
                {"value": 0.8359556608828429, "time": "2024-04-14T15:15:00"},
                {"value": 1.1247067830113573, "time": "2024-04-14T15:30:00"},
                {"value": 1.3908757008598633, "time": "2024-04-14T15:45:00"},
                {"value": 1.6435825418298649, "time": "2024-04-14T16:00:00"},
            ]
        },
    }
]

# Valid input and output data that should _not_ be used while testing the
# forecasting or optimization code _but only_ for testing the data models.
# This could be useful in case that running the forecasting or optimization
# code is slow or needs mocking, e.g. for data sources. The latter especially,
# as providing realistic data as mock for all cases might cause large efforts.
#
# NOTE: In this example we don't use the input data defined for the FOOC
#       tests to illustrate above that parts of the `GeographicPosition` and
#       'PVSystem' models, i.e. the `height` and `power_datapoint_id` are not
#       necessary to compute the output.
REQUEST_INPUTS_MODEL_TEST = [
    {
        "Python": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                    "height": None,
                }
            },
            "parameters": {
                "pv_system": {
                    "azimuth_angle": 20,
                    "inclination_angle": 30,
                    "nominal_power": 5.0,
                    "power_datapoint_id": 1,
                }
            },
        },
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                    "height": None,
                }
            },
            "parameters": {
                "pv_system": {
                    "azimuth_angle": 20,
                    "inclination_angle": 30,
                    "nominal_power": 5.0,
                    "power_datapoint_id": 1,
                }
            },
        },
    }
]

REQUEST_OUTPUTS_MODEL_TEST = REQUEST_OUTPUTS_FOOC_TEST + []

# Input data which the request endpoint should reject.
INVALID_REQUEST_INPUTS = [
    # No arguments
    {
        "JSONable": {
            "parameters": {
                "pv_system": {
                    "azimuth_angle": 20,
                    "inclination_angle": 30,
                    "nominal_power": 5.0,
                    "power_datapoint_id": 1,
                }
            },
        },
    },
    # No parameters
    {
        "JSONable": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                    "height": None,
                }
            },
        },
    },
    # geographic_position not in arguments.
    {
        "JSONable": {
            "arguments": {"geographic_pos": 1.0},
            "parameters": {
                "pv_system": {
                    "azimuth_angle": 20,
                    "inclination_angle": 30,
                    "nominal_power": 5.0,
                    "power_datapoint_id": 1,
                }
            },
        },
    },
    # pv_system not in parameters
    {
        "JSONable": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                    "height": None,
                }
            },
            "parameters": {"something_else": "True"},
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
    # values not a value value message list
    {
        "JSONable": {"power_prediction": 0.25},
    },
]

# Test data for the fit parameter endpoints corresponding to the concept
# used for the request endpoint as explained above.
"""
The observations here have been generated with:
    measured_data_pd = predict_pv_power(
        lat=35.2,
        lon=-110.0,
        inclination=25,
        azimuth=15,
        peak_power=4.5,
        meteo_data=OPEN_METEO_RESPONSE_DF,
    )
    value_message_list_from_series(measured_data_pd)
"""
FIT_PARAM_INPUTS_FOOC_TEST = [
    {
        "Python": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                }
            },
            "observations": {
                # NOTE: It is necessary to roughly this much of data here as
                #       else the least square fitting might be unstable.
                "measured_power": [
                    {
                        "value": None,
                        "time": pd.Timestamp("2024-04-14 13:00:00"),
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": pd.Timestamp("2024-04-14 13:15:00"),
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": pd.Timestamp("2024-04-14 13:30:00"),
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": pd.Timestamp("2024-04-14 13:45:00"),
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": pd.Timestamp("2024-04-14 14:00:00"),
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": pd.Timestamp("2024-04-14 14:15:00"),
                    },
                    {
                        "value": 0.10452829847573523,
                        "time": pd.Timestamp("2024-04-14 14:30:00"),
                    },
                    {
                        "value": 0.41699731186894995,
                        "time": pd.Timestamp("2024-04-14 14:45:00"),
                    },
                    {
                        "value": 0.706789776069266,
                        "time": pd.Timestamp("2024-04-14 15:00:00"),
                    },
                    {
                        "value": 0.9304959204969735,
                        "time": pd.Timestamp("2024-04-14 15:15:00"),
                    },
                    {
                        "value": 1.22571942537656,
                        "time": pd.Timestamp("2024-04-14 15:30:00"),
                    },
                    {
                        "value": 1.4493471584723674,
                        "time": pd.Timestamp("2024-04-14 15:45:00"),
                    },
                    {
                        "value": 1.658779942658842,
                        "time": pd.Timestamp("2024-04-14 16:00:00"),
                    },
                ]
            },
        },
        "JSONable": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                }
            },
            "observations": {
                "measured_power": [
                    {
                        "value": None,
                        "time": "2024-04-14T13:00:00",
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": "2024-04-14T13:15:00",
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": "2024-04-14T13:30:00",
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": "2024-04-14T13:45:00",
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": "2024-04-14T14:00:00",
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": "2024-04-14T14:15:00",
                    },
                    {
                        "value": 0.10452829847573523,
                        "time": "2024-04-14T14:30:00",
                    },
                    {
                        "value": 0.41699731186894995,
                        "time": "2024-04-14T14:45:00",
                    },
                    {
                        "value": 0.706789776069266,
                        "time": "2024-04-14T15:00:00",
                    },
                    {
                        "value": 0.9304959204969735,
                        "time": "2024-04-14T15:15:00",
                    },
                    {
                        "value": 1.22571942537656,
                        "time": "2024-04-14T15:30:00",
                    },
                    {
                        "value": 1.4493471584723674,
                        "time": "2024-04-14T15:45:00",
                    },
                    {
                        "value": 1.658779942658842,
                        "time": "2024-04-14T16:00:00",
                    },
                ]
            },
        },
    }
]

FIT_PARAM_OUTPUTS_FOOC_TEST = [
    {
        "Python": {
            "pv_system": {
                "azimuth_angle": 15.0,
                "inclination_angle": 25.0,
                "nominal_power": 4.5,
                "power_datapoint_id": None,
            }
        },
        # NOTE: No difference to Python as no data types included that JSON
        #       cannot handle natively, like datetimes etc.
        "JSONable": {
            "pv_system": {
                "azimuth_angle": 15.0,
                "inclination_angle": 25.0,
                "nominal_power": 4.5,
                "power_datapoint_id": None,
            }
        },
    }
]

# Again don't use the FOOC data here, see explanation at comment above
# `REQUEST_INPUTS_MODEL_TEST`.
FIT_PARAM_INPUTS_MODEL_TEST = [
    {
        "Python": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                    "height": None,
                }
            },
            "observations": {
                "measured_power": [
                    {
                        "value": None,
                        "time": pd.Timestamp("2024-04-14 13:00:00"),
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": pd.Timestamp("2024-04-14 13:15:00"),
                    },
                ]
            },
        },
        "JSONable": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                    "height": None,
                }
            },
            "observations": {
                "measured_power": [
                    {
                        "value": None,
                        "time": "2024-04-14T13:00:00",
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": "2024-04-14T13:15:00",
                    },
                ]
            },
        },
    }
]

FIT_PARAM_OUTPUTS_MODEL_TEST = FIT_PARAM_OUTPUTS_FOOC_TEST + []

INVALID_FIT_PARAM_INPUTS = [
    # No arguments
    {
        "JSONable": {
            "observations": {
                "measured_power": [
                    {
                        "value": None,
                        "time": "2024-04-14T13:00:00",
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": "2024-04-14T13:15:00",
                    },
                ]
            },
        },
    },
    # No observations
    {
        "JSONable": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                    "height": None,
                }
            },
        },
    },
    # no geographic_position in arguments
    {
        "JSONable": {
            "arguments": {"nope": "no coords"},
            "observations": {
                "measured_power": [
                    {
                        "value": None,
                        "time": "2024-04-14T13:00:00",
                    },
                    {
                        "value": -0.027931034482758618,
                        "time": "2024-04-14T13:15:00",
                    },
                ]
            },
        },
    },
    # No measured power in observations
    {
        "JSONable": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                    "height": None,
                }
            },
            "observations": {"some measurements": "not there"},
        },
    },
    # Measured power not a value message list.
    {
        "JSONable": {
            "arguments": {
                "geographic_position": {
                    "latitude": 35.2,
                    "longitude": -110.0,
                    "height": None,
                }
            },
            "observations": {"measured_power": [0.1, 0.2]},
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
    # Fitted PV System is empty.
    {
        "JSONable": {"pv_system": None},
    },
    {
        "JSONable": {"pv_system": {}},
    },
]

OPEN_METEO_RESPONSE = {
    "latitude": 32.204494,
    "longitude": -110.8978,
    "generationtime_ms": 0.06103515625,
    "utc_offset_seconds": 0,
    "timezone": "GMT",
    "timezone_abbreviation": "GMT",
    "elevation": 777.0,
    "minutely_15_units": {
        "time": "iso8601",
        "shortwave_radiation": "W/m²",
        "diffuse_radiation": "W/m²",
        "direct_normal_irradiance": "W/m²",
    },
    "minutely_15": {
        "time": [
            # This would be more entries in reality but trimmed here.
            "2024-04-14T13:00",
            "2024-04-14T13:15",
            "2024-04-14T13:30",
            "2024-04-14T13:45",
            "2024-04-14T14:00",
            "2024-04-14T14:15",
            "2024-04-14T14:30",
            "2024-04-14T14:45",
            "2024-04-14T15:00",
            "2024-04-14T15:15",
            "2024-04-14T15:30",
            "2024-04-14T15:45",
            "2024-04-14T16:00",
        ],
        "shortwave_radiation": [
            0.0,
            11.0,
            52.0,
            103.0,
            157.0,
            214.0,
            281.0,
            342.0,
            386.0,
            433.0,
            520.0,
            577.0,
            631.0,
        ],
        "diffuse_radiation": [
            0.0,
            8.0,
            26.0,
            41.0,
            69.0,
            86.0,
            57.0,
            78.0,
            169.0,
            202.0,
            115.0,
            99.0,
            117.0,
        ],
        "direct_normal_irradiance": [
            0.0,
            45.9,
            280.4,
            442.5,
            452.5,
            515.3,
            742.6,
            745.8,
            535.6,
            507.6,
            804.6,
            869.3,
            864.7,
        ],
    },
}

OPEN_METEO_RESPONSE_DF = pd.DataFrame(
    index=pd.to_datetime(OPEN_METEO_RESPONSE["minutely_15"]["time"]),
    data={
        "ghi": OPEN_METEO_RESPONSE["minutely_15"]["shortwave_radiation"],
        "dhi": OPEN_METEO_RESPONSE["minutely_15"]["diffuse_radiation"],
        "dni": OPEN_METEO_RESPONSE["minutely_15"]["direct_normal_irradiance"],
    },
)
