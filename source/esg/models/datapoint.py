"""
Generic definitions of datapoint related data types (aka. messages)
in pydantic for serialization (e.g. to JSON) and for auto generation
of endpoint schemas.

In particular this defines models for handling the following message types:
- Datapoint Value
- Datapoint Setpoint
- Datapoint Schedule

See also the BEMCom documentation on message types:
https://bemcom.readthedocs.io/en/latest/03_message_format.html

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

from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Dict
from typing import List
from typing import Optional

from pydantic import Field
from pydantic import model_validator

from esg.models.base import _BaseModel
from esg.models.base import _RootModel


class DatapointType(str, Enum):
    """
    Valid values for Datapoint.type.
    """

    sensor = "Sensor"
    actuator = "Actuator"


class DatapointDataFormat(str, Enum):
    """
    Defines the data format of the datapoint, i.e. which additional metadata
    we can expect.

    The formats have the following meanings:
      numeric: The value of the datapoint can be stored as a float.
      text: The value of the datapoint can be stored as a string.
      generic: No additional information.
      bool: A bool, i.e. only True (1) or False (0).
      unknown: Unknown format.
    """

    generic_numeric = "Generic Numeric"
    continuous_numeric = "Continuous Numeric"
    discrete_numeric = "Discrete Numeric"
    bool = "Boolean"
    unknown = "Unknown"


class Datapoint(_BaseModel):
    """
    Devices are abstracted as a set of datapoints.

    A datapoint represents one source of information. Devices will typically
    emit information on more then one datapoints. E.g. climate sensor in a
    room might publish temperature and humidity measurements. Both will be
    treated as individual datapoints as this allows us to abstract away the
    complexity of the devices.

    Each datapoint object contains the metadata necessary to interpret
    the datapoint.
    """

    id: Optional[int] = Field(
        default=None,
        examples=[1337],
        description=("The ID of the datapoint in the central DB."),
    )
    origin: Optional[str] = Field(
        default=None,
        examples=["HoLL BEMCom Instance"],
        description=(
            "This name is used if the datapoint metadata is (partly) "
            "configured in an external application (e.g. BEMCom) and should "
            "be used in the current service (e.g. the EMP). This effectively "
            "allows the current application to use additional datapoints that "
            "do not exist in the external service, which is handy for "
            "mocking UIs and stuff."
        ),
    )
    origin_id: Optional[str] = Field(
        default=None,
        examples=["2"],
        description=(
            "In combination with `origin`, this field allows matching the "
            "ids of the external application with id maintained by the current "
            "application. Note: this field is a string as not all external "
            "applications might use integers as IDs, e.g. consider MQTT topics."
        ),
    )
    short_name: Optional[str] = Field(
        default=None,
        examples=["T_zone_s"],
        description=("A short name to identify the datapoint."),
    )
    type: DatapointType = Field(
        ...,
        examples=["sensor"],
        description=(
            "Datapoints can either be of type `sensor` (readable) or "
            "`actuator` (writeable)."
        ),
    )
    data_format: DatapointDataFormat = Field(
        default=DatapointDataFormat.unknown,
        examples=["Generic Numeric"],
        description=(
            "Format of the datapoint value. Additionally defines which meta"
            "data is available for it. See Enum docs for details."
        ),
    )
    description: str = Field(
        default="",
        examples=["Zone Temperature Second Floor."],
        description=(
            "A human readable description of the datapoint targeted on "
            "users of the API without knowledge about hardware details."
        ),
    )
    #
    ##########################################################################
    #
    # Below all metadata fields that may or may not be populated for a
    # particular datapoint depending on the data_format and type.
    #
    ##########################################################################
    #
    allowed_values: Optional[List[float]] = Field(
        default=None,
        description=(
            "Allowed values. Applicable to discrete valued datapoints only."
        ),
    )
    min_value: Optional[float] = Field(
        default=None,
        description=(
            "The minimal expected value of the datapoint. None means no "
            "constraint. Only applicable to `Continuous Numeric` datapoints."
        ),
    )
    max_value: Optional[float] = Field(
        default=None,
        description=(
            "The maximum expected value of the datapoint. None means no "
            "constraint. Only applicable to `Continuous Numeric` datapoints."
        ),
    )
    unit: str = Field(
        default="",
        description=(
            "The unit in SI notation, e.g.  Mg*m*s^-2 aka. kN. "
            "Only applicable to `Numeric` datapoints."
        ),
    )


class DatapointList(_RootModel):
    """
    A list of one or more datapoints.
    """

    root: List[Datapoint] = Field(
        ...,
        examples=[
            [
                {
                    "id": 1,
                    "origin": "emp_demo_dp_interface",
                    "origin_id": "1",
                    "short_name": "Test Datapoint 1",
                    "type": "Sensor",
                    "data_format": "Continuous Numeric",
                    "description": (
                        "Example for continuous datapoint defined by an "
                        "external application."
                    ),
                    "allowed_values": None,
                    "min_value": 19,
                    "max_value": 25,
                    "unit": "°C",
                },
                {
                    "id": 2,
                    "origin": None,
                    "origin_id": None,
                    "short_name": "Test Datapoint 2",
                    "type": "Sensor",
                    "data_format": "Discrete Numeric",
                    "description": (
                        "Example for discrete datapoint defined directly "
                        "in EMP."
                    ),
                    "allowed_values": [21.0, 22.0, 23.0],
                    "min_value": None,
                    "max_value": None,
                    "unit": "°C",
                },
            ]
        ],
    )


class DatapointById(_RootModel):
    """
    A dict of datapoints by ID for simple access in applications.
    """

    root: Dict[str, Datapoint] = Field(
        ...,
        examples=[
            {
                "1": {
                    "id": 1,
                    "origin": "emp_demo_dp_interface",
                    "origin_id": "1",
                    "short_name": "Test Datapoint 1",
                    "type": "Sensor",
                    "data_format": "Continuous Numeric",
                    "description": (
                        "Example for continuous datapoint defined by an "
                        "external application."
                    ),
                    "allowed_values": None,
                    "min_value": 19,
                    "max_value": 25,
                    "unit": "°C",
                },
                "2": {
                    "id": 2,
                    "origin": None,
                    "origin_id": None,
                    "short_name": "Test Datapoint 2",
                    "type": "Sensor",
                    "data_format": "Discrete Numeric",
                    "description": (
                        "Example for discrete datapoint defined directly "
                        "in EMP."
                    ),
                    "allowed_values": [21.0, 22.0, 23.0],
                    "min_value": None,
                    "max_value": None,
                    "unit": "°C",
                },
            }
        ],
        description=(
            "Note that dict key (ID) is a string here due to limitations "
            "in OpenAPI. See description of `Datapoint` type for additional "
            "details."
        ),
    )


class _Value(_RootModel):
    """
    A single value item, here as a separate model to prevent redundancy
    while constructing the more complex types below.
    """

    root: Optional[float] = Field(
        examples=[22.1],
        description=(
            "The value (always a float). This value can "
            "e.g. be a measured value of a sensor datapoint or "
            "a set value pushed to an actuator datapoint."
        ),
    )


class _Time(_RootModel):
    """
    Like `_Value` but for the corresponding timestamp.
    """

    root: datetime = Field(
        ...,
        examples=[datetime.now(tz=timezone.utc)],
        description=(
            "The time corresponding to the value was measured or the "
            "message was created."
        ),
    )


class ValueMessage(_BaseModel):
    """
    Represents one value at one point in time.
    """

    # Note: The example values are taken just fine from `_Value` and `_Time`.
    value: Optional[_Value]
    time: _Time


class ValueMessageByDatapointId(_RootModel):
    """
    A single value message for zero or more Datapoints, e.g. to report the
    last values of multiple Datapoints.
    """

    root: Dict[str, ValueMessage] = Field(
        ...,
        examples=[
            {
                "1": {
                    "value": 24.2,
                    "time": "2022-04-25T10:32:58.593870+00:00",
                },
                "2": {"value": 1.0, "time": "2022-04-25T10:04:39+00:00"},
            }
        ],
        description=(
            "Note that dict key (datapoint ID) is a string (and not an "
            " integer) due to limitations in OpenAPI. See description "
            "of the child model for additional details about the payload."
        ),
    )


class ValueMessageList(_RootModel):
    """
    Represents a list of Value Messages, e.g. a time series of measured values.
    """

    root: List[ValueMessage] = Field(
        ...,
        examples=[
            [
                {"value": 24.2, "time": "2022-04-25T10:32:58.593870+00:00"},
                {"value": 1.0, "time": "2022-04-25T10:34:39+00:00"},
            ]
        ],
    )


class ValueMessageListByDatapointId(_RootModel):
    """
    Contains one or more value messages for one or more datapoints.
    Only preferable over `ValueDataFrame` if time values are not aligned.
    """

    root: Dict[str, ValueMessageList] = Field(
        ...,
        examples=[
            {
                "1": [
                    {"value": 1.0, "time": "2022-04-25T10:13:47+00:00"},
                    {"value": 0.0, "time": "2022-04-25T10:27:07+00:00"},
                ],
                "2": [
                    {"value": 21.0, "time": "2022-04-25T10:13:06+00:00"},
                    {"value": 22.0, "time": "2022-04-25T10:13:19+00:00"},
                ],
            }
        ],
        description=(
            "Note that dict key (datapoint ID) is a string (and not an "
            " integer) due to limitations in OpenAPI. See description "
            "of the child model for additional details about the payload."
        ),
    )


class ValueDataFrameColumn(_RootModel):
    """
    A list of values, equivalent to one column in pandas DataFrame.
    """

    root: List[_Value]


class ValueDataFrame(_BaseModel):
    """
    A pandas DataFrame like representation of datapoint values. The `values`
    field holds a dict with datapoint IDs as keys and lists of values as items.
    The `times` field contains the corresponding time values applicable to
    all datapoint value columns.
    """

    # Note that it is not possible to embed `List[_Value]` directly into
    # `Dict` as this would break `construct_recursive` on this model.
    values: Dict[str, ValueDataFrameColumn] = Field(
        ...,
        examples=[
            {
                "1": [22.1, None, 22.3],
                "42": [1.0, 1.0, 0.0],
            }
        ],
    )
    times: List[_Time] = Field(
        ...,
        examples=[
            [
                "2022-01-03T18:00:00+00:00",
                "2022-01-03T18:15:00+00:00",
                "2022-01-03T18:30:00+00:00",
            ]
        ],
    )

    @model_validator(mode="before")
    def check_times_and_values_same_size(cls, data):
        """ """
        len_of_index = len(data.get("times"))
        for column_name in data.get("values"):
            len_of_column = len(data.get("values").get(column_name))
            error_msg = (
                "Length ({}) of values column '{}' doesn't match length of "
                "times index ({})".format(
                    len_of_column, column_name, len_of_index
                )
            )
            assert len_of_column == len_of_index, error_msg

        return data


class ScheduleItem(_BaseModel):
    """
    Represents the optimized actuator value for one interval in time.
    """

    from_timestamp: Optional[datetime] = Field(
        ...,
        examples=[datetime.now(tz=timezone.utc)],
        description=(
            "The time that `value` should be applied. Can be `null` in "
            "which case `value` should be applied immediately after the "
            "schedule is received by the controller."
        ),
    )
    to_timestamp: Optional[datetime] = Field(
        ...,
        examples=[datetime.now(tz=timezone.utc)],
        description=(
            "The time that `value` should no longer be applied. Can be "
            "`null` in which case `value` should be applied forever, "
            "or more realistically, until a new schedule is received."
        ),
    )
    # TODO: Might want to add a validator that checks if value matches the
    #       constraints defined in the corresponding datapoint. Something
    #       similar has already been implemented in BEMCom. See here:
    #       https://github.com/fzi-forschungszentrum-informatik/BEMCom/blob/927763a5a3c05eceb6bfb0b48e4b47600e2889ff/services/apis/django-api/source/api/ems_utils/message_format/serializers.py#L31
    value: _Value = Field(
        description=(
            "The value that should be sent to the actuator datapoint.\n"
            "The value must be larger or equal min_value (as listed in the "
            "datapoint metadata) if the datapoints data format is "
            "continuous_numeric.\n"
            "The value must be smaller or equal max_value (as listed in the "
            "datapoint metadata) if the datapoints data format is "
            "continuous_numeric.\n"
            "The value must be in the list of acceptable_values (as listed "
            "in the datapoint metadata) if the datapoints data format is "
            "discrete."
        ),
    )


class Schedule(_RootModel):
    """
    A schedule, i.e. a list holding zero or more `ScheduleItem`.
    """

    root: List[ScheduleItem]


class ScheduleMessage(_BaseModel):
    """
    The schedule is a list of actuator values computed by an optimization
    algorithm that should be executed on the specified actuator datapoint
    as long as the setpoint constraints are not violated.
    """

    schedule: Schedule
    time: _Time


class ScheduleMessageByDatapointId(_RootModel):
    """
    A single schedule message for zero or more Datapoints, e.g. to report the
    last schedules of multiple Datapoints.
    """

    root: Dict[str, ScheduleMessage] = Field(
        ...,
        examples=[
            {
                "1": {
                    "schedule": [
                        {
                            "from_timestamp": "2022-02-22T03:00:00+00:00",
                            "to_timestamp": "2022-02-22T03:15:00+00:00",
                            "value": "21.0",
                        }
                    ],
                    "time": "2022-04-22T01:21:32.000100+00:00",
                },
                "2": {
                    "schedule": [
                        {
                            "from_timestamp": None,
                            "to_timestamp": "2022-02-22T03:00:00+00:00",
                            "value": "null",
                        },
                        {
                            "from_timestamp": "2022-02-22T03:00:00+00:00",
                            "to_timestamp": "2022-02-22T03:15:00+00:00",
                            "value": '"true"',
                        },
                        {
                            "from_timestamp": "2022-02-22T03:15:00+00:00",
                            "to_timestamp": None,
                            "value": "false",
                        },
                    ],
                    "time": "2022-04-22T01:21:25+00:00",
                },
            }
        ],
        description=(
            "Note that dict key (datapoint ID) is a string (and not an "
            " integer) due to limitations in OpenAPI. See description "
            "of the child model for additional details about the payload."
        ),
    )


class ScheduleMessageList(_RootModel):
    """
    Represents a list of schedule messages.
    """

    root: List[ScheduleMessage] = Field(
        ...,
        examples=[
            [
                {
                    "schedule": [
                        {
                            "from_timestamp": "2022-02-22T03:00:00+00:00",
                            "to_timestamp": "2022-02-22T03:15:00+00:00",
                            "value": "21.0",
                        }
                    ],
                    "time": "2022-04-22T01:21:32.000100+00:00",
                },
                {
                    "schedule": [
                        {
                            "from_timestamp": None,
                            "to_timestamp": "2022-02-22T03:00:00+00:00",
                            "value": "null",
                        },
                        {
                            "from_timestamp": "2022-02-22T03:00:00+00:00",
                            "to_timestamp": "2022-02-22T03:15:00+00:00",
                            "value": '"true"',
                        },
                        {
                            "from_timestamp": "2022-02-22T03:15:00+00:00",
                            "to_timestamp": None,
                            "value": "false",
                        },
                    ],
                    "time": "2022-04-22T01:21:25+00:00",
                },
            ]
        ],
    )


class ScheduleMessageListByDatapointId(_RootModel):
    """
    Contains one or more schedule messages for one or more datapoints.
    """

    root: Dict[str, ScheduleMessageList] = Field(
        ...,
        examples=[
            {
                "1": [
                    {
                        "schedule": [
                            {
                                "from_timestamp": "2022-02-22T03:00:00+00:00",
                                "to_timestamp": "2022-02-22T03:15:00+00:00",
                                "value": "21.0",
                            }
                        ],
                        "time": "2022-04-22T01:21:32.000100+00:00",
                    },
                    {
                        "schedule": [
                            {
                                "from_timestamp": None,
                                "to_timestamp": "2022-02-22T03:00:00+00:00",
                                "value": "null",
                            },
                            {
                                "from_timestamp": "2022-02-22T03:00:00+00:00",
                                "to_timestamp": "2022-02-22T03:15:00+00:00",
                                "value": '"true"',
                            },
                            {
                                "from_timestamp": "2022-02-22T03:15:00+00:00",
                                "to_timestamp": None,
                                "value": "false",
                            },
                        ],
                        "time": "2022-04-22T01:21:25+00:00",
                    },
                ],
            }
        ],
        description=(
            "Note that dict key (datapoint ID) is a string (and not an "
            " integer) due to limitations in OpenAPI. See description "
            "of the child model for additional details about the payload."
        ),
    )


class SetpointItem(_BaseModel):
    """
    Represents the user demand for one interval in time.
    """

    from_timestamp: Optional[datetime] = Field(
        ...,
        examples=[datetime.now(tz=timezone.utc)],
        description=(
            "The time that the setpoint should be applied. Can be `null` in "
            "which case it should be applied immediately after the "
            "setpoint is received by the controller."
        ),
    )
    to_timestamp: Optional[datetime] = Field(
        ...,
        examples=[datetime.now(tz=timezone.utc)],
        description=(
            "The time that the setpoint should no longer be applied. Can be "
            "`null` in which case it should be applied forever, "
            "or more realistically, until a new setpoint is received."
        ),
    )
    # TODO: Might want to add a validator that checks if `preferred_value`,
    #       `acceptable_values`, `min_value` and `max_value` match the
    #       constraints defined in the corresponding datapoint. Something
    #       similar has already been implemented in BEMCom. See here:
    #       https://github.com/fzi-forschungszentrum-informatik/BEMCom/blob/927763a5a3c05eceb6bfb0b48e4b47600e2889ff/services/apis/django-api/source/api/ems_utils/message_format/serializers.py#L31
    preferred_value: Optional[_Value] = Field(
        ...,
        description=(
            "Specifies the preferred setpoint of the user. This value should "
            "be send to the actuator datapoint by the controller if either no "
            "schedule is applicable, or the current value of the corresponding "
            "sensor datapoint is out of range of `acceptable_values` (for "
            "discrete datapoints) or not between `min_value` and `max_value` "
            "(for continuous datapoints) as defined in this setpoint item.\n"
            "Furthermore, the value of `preferred_value` must match the "
            "requirements of the actuator datapoint, i.e. it must be in "
            "`acceptable_values` (for discrete datapoints) or between "
            "`min_value` and `max_value` (for continuous datapoints) as "
            "specified in the corresponding fields of the actuator datapoint."
        ),
    )
    acceptable_values: Optional[List[_Value]] = Field(
        default=None,
        description=(
            "Specifies the flexibility of the user regarding the sensor "
            "datapoint for discrete values. That is, it specifies the actually "
            "realized values the user is willing to accept. Consider e.g. the "
            "scenario where a room with a discrete heating control has "
            "currently 16°C. If the user specified this field with [20, 21, 22]"
            " it means that only these three temperature values are "
            "acceptable. This situation would cause the controller to "
            "immediately send the preferred_value to the actuator datapoint, "
            "even if the schedule would define a value that lays within the "
            "acceptable range."
        ),
    )
    min_value: Optional[float] = Field(
        default=None,
        description=(
            "Similar to `acceptable_values` but defines the minimum value"
            "the user is willing to accept for continuous datapoints."
        ),
    )
    max_value: Optional[float] = Field(
        default=None,
        description=(
            "Similar to `acceptable_values` but defines the maximum value"
            "the user is willing to accept for continuous datapoints."
        ),
    )


class Setpoint(_RootModel):
    """
    A setpoint, i.e. a list holding zero or more `SetpointItem`.
    """

    root: List[SetpointItem]


class SetpointMessage(_BaseModel):
    """
    The setpoint specifies the demand of the users of the system. The setpoint
    must hold a preferred_value which is the value the user would appreciate
    most, and can additionally define flexibility of values the user would also
    accept. The setpoint message is used by optimization algorithms as
    constraints while computing schedules, as well as by controller services
    to ensure that the demand of the user is always met.
    """

    setpoint: Setpoint
    time: _Time


class SetpointMessageByDatapointId(_RootModel):
    """
    A single setpoint message for zero or more Datapoints, e.g. to report the
    last setpoints of multiple Datapoints.
    """

    root: Dict[str, SetpointMessage] = Field(
        ...,
        examples=[
            {
                "1": {
                    "setpoint": [
                        {
                            "from_timestamp": "2022-02-22T03:00:00+00:00",
                            "to_timestamp": "2022-02-22T03:15:00+00:00",
                            "preferred_value": "21.0",
                            "acceptable_values": None,
                            "max_value": 23.2,
                            "min_value": 17.4,
                        }
                    ],
                    "time": "2022-04-22T01:21:32.000100+00:00",
                },
                "2": {
                    "setpoint": [
                        {
                            "from_timestamp": None,
                            "to_timestamp": "2022-02-22T03:00:00+00:00",
                            "preferred_value": "null",
                            "acceptable_values": None,
                            "max_value": None,
                            "min_value": None,
                        },
                        {
                            "from_timestamp": "2022-02-22T03:00:00+00:00",
                            "to_timestamp": "2022-02-22T03:15:00+00:00",
                            "preferred_value": '"true"',
                            "acceptable_values": ['"true"', '"other string"'],
                            "max_value": None,
                            "min_value": None,
                        },
                        {
                            "from_timestamp": "2022-02-22T03:15:00+00:00",
                            "to_timestamp": None,
                            "preferred_value": "false",
                            "acceptable_values": ["true", "false"],
                            "max_value": None,
                            "min_value": None,
                        },
                    ],
                    "time": "2022-04-22T01:21:25+00:00",
                },
            }
        ],
        description=(
            "Note that dict key (datapoint ID) is a string (and not an "
            " integer) due to limitations in OpenAPI. See description "
            "of the child model for additional details about the payload."
        ),
    )


class SetpointMessageList(_RootModel):
    """
    Represents a list of setpoint messages.
    """

    root: List[SetpointMessage] = Field(
        ...,
        examples=[
            [
                {
                    "setpoint": [
                        {
                            "from_timestamp": "2022-02-22T03:00:00+00:00",
                            "to_timestamp": "2022-02-22T03:15:00+00:00",
                            "preferred_value": "21.0",
                            "acceptable_values": None,
                            "max_value": 23.2,
                            "min_value": 17.4,
                        }
                    ],
                    "time": "2022-04-22T01:21:32.000100+00:00",
                },
                {
                    "setpoint": [
                        {
                            "from_timestamp": None,
                            "to_timestamp": "2022-02-22T03:00:00+00:00",
                            "preferred_value": "null",
                            "acceptable_values": None,
                            "max_value": None,
                            "min_value": None,
                        },
                        {
                            "from_timestamp": "2022-02-22T03:00:00+00:00",
                            "to_timestamp": "2022-02-22T03:15:00+00:00",
                            "preferred_value": '"true"',
                            "acceptable_values": ['"true"', '"other string"'],
                            "max_value": None,
                            "min_value": None,
                        },
                        {
                            "from_timestamp": "2022-02-22T03:15:00+00:00",
                            "to_timestamp": None,
                            "preferred_value": "false",
                            "acceptable_values": ["true", "false"],
                            "max_value": None,
                            "min_value": None,
                        },
                    ],
                    "time": "2022-04-22T01:21:25+00:00",
                },
            ]
        ],
    )


class SetpointMessageListByDatapointId(_RootModel):
    """
    Contains one or more setpoint messages for one or more datapoints.
    """

    root: Dict[str, SetpointMessageList] = Field(
        ...,
        examples=[
            {
                "1": [
                    {
                        "setpoint": [
                            {
                                "from_timestamp": "2022-02-22T03:00:00+00:00",
                                "to_timestamp": "2022-02-22T03:15:00+00:00",
                                "preferred_value": "21.0",
                                "acceptable_values": None,
                                "max_value": 23.2,
                                "min_value": 17.4,
                            }
                        ],
                        "time": "2022-04-22T01:21:32.000100+00:00",
                    },
                    {
                        "setpoint": [
                            {
                                "from_timestamp": None,
                                "to_timestamp": "2022-02-22T03:00:00+00:00",
                                "preferred_value": "null",
                                "acceptable_values": None,
                                "max_value": None,
                                "min_value": None,
                            },
                            {
                                "from_timestamp": "2022-02-22T03:00:00+00:00",
                                "to_timestamp": "2022-02-22T03:15:00+00:00",
                                "preferred_value": '"true"',
                                "acceptable_values": [
                                    '"true"',
                                    '"other string"',
                                ],
                                "max_value": None,
                                "min_value": None,
                            },
                            {
                                "from_timestamp": "2022-02-22T03:15:00+00:00",
                                "to_timestamp": None,
                                "preferred_value": "false",
                                "acceptable_values": ["true", "false"],
                                "max_value": None,
                                "min_value": None,
                            },
                        ],
                        "time": "2022-04-22T01:21:25+00:00",
                    },
                ],
            }
        ],
        description=(
            "Note that dict key (datapoint ID) is a string (and not an "
            " integer) due to limitations in OpenAPI. See description "
            "of the child model for additional details about the payload."
        ),
    )


class ForecastMessage(_BaseModel):
    """
    A forecast for a datapoint value for one point in time.
    """

    mean: float = Field(
        ...,
        examples=[21.5],
        description=("The expected value at `time`."),
    )
    std: Optional[float] = Field(
        default=None,
        examples=[1.0],
        description=(
            "The standard deviation (uncertainty) of `mean` at `time`. "
            "This assumes that the forecast error is Gaussian distributed."
        ),
    )
    p05: Optional[float] = Field(
        default=None,
        examples=[19.85],
        description=(
            "The 5% percentile of the forecast, i.e. it is predicted that "
            "finally observed value is larger then this value with a "
            "probability of 95%."
        ),
    )
    p10: Optional[float] = Field(
        default=None,
        examples=[20.22],
        description=(
            "The 10% percentile of the forecast, i.e. it is predicted that "
            "finally observed value is larger then this value with a "
            "probability of 90%."
        ),
    )
    p25: Optional[float] = Field(
        default=None,
        examples=[20.83],
        description=(
            "The 25% percentile of the forecast, i.e. it is predicted that "
            "finally observed value is larger then this value with a "
            "probability of 75%."
        ),
    )
    p50: Optional[float] = Field(
        default=None,
        examples=[21.5],
        description="The 50% percentile of the forecast, i.e. the median.",
    )
    p75: Optional[float] = Field(
        default=None,
        examples=[22.17],
        description=(
            "The 75% percentile of the forecast, i.e. it is predicted that "
            "finally observed value is smaller then this value with a "
            "probability of 75%."
        ),
    )
    p90: Optional[float] = Field(
        default=None,
        examples=[22.78],
        description=(
            "The 90% percentile of the forecast, i.e. it is predicted that "
            "finally observed value is smaller then this value with a "
            "probability of 90%."
        ),
    )
    p95: Optional[float] = Field(
        default=None,
        examples=[23.15],
        description=(
            "The 95% percentile of the forecast, i.e. it is predicted that "
            "finally observed value is smaller then this value with a "
            "probability of 95%."
        ),
    )
    time: _Time


class ForecastMessageList(_RootModel):
    """
    A list of forecast messages, e.g. a full forecast for a datapoint
    for multiple times in the future.
    """

    root: List[ForecastMessage] = Field(
        ...,
        examples=[
            [
                {
                    "mean": 21.0,
                    "std": 1.0,
                    "p05": 19.35,
                    "p10": 19.72,
                    "p25": 20.33,
                    "p50": 21.0,
                    "p75": 21.67,
                    "p90": 22.28,
                    "p95": 22.65,
                    "time": "2022-02-22T02:45:00+00:00",
                },
                {
                    "mean": 21.2,
                    "std": 1.1,
                    "p05": 19.39,
                    "p10": 19.79,
                    "p25": 20.46,
                    "p50": 21.2,
                    "p75": 21.94,
                    "p90": 22.61,
                    "p95": 23.01,
                    "time": "2022-02-22T03:45:00+00:00",
                },
            ]
        ],
    )


class ForecastMessageListByDatapointId(_RootModel):
    """
    Contains forecasts for one or more defined datapoints.
    """

    root: Dict[str, ForecastMessageList] = Field(
        ...,
        examples=[
            {
                "1": [
                    {
                        "mean": 21.0,
                        "std": 1.0,
                        "p05": 19.35,
                        "p10": 19.72,
                        "p25": 20.33,
                        "p50": 21.0,
                        "p75": 21.67,
                        "p90": 22.28,
                        "p95": 22.65,
                        "time": "2022-02-22T02:45:00+00:00",
                    },
                    {
                        "mean": 21.2,
                        "std": 1.1,
                        "p05": 19.39,
                        "p10": 19.79,
                        "p25": 20.46,
                        "p50": 21.2,
                        "p75": 21.94,
                        "p90": 22.61,
                        "p95": 23.01,
                        "time": "2022-02-22T03:45:00+00:00",
                    },
                ],
            }
        ],
        description=(
            "Note that dict key (datapoint ID) is a string (and not an "
            " integer) due to limitations in OpenAPI. See description "
            "of the child model for additional details about the payload."
        ),
    )


class PutSummary(_BaseModel):
    """
    A summary for put operations.
    """

    objects_created: int = Field(
        ...,
        examples=[10],
        description="Number of objects that have been created in database.",
    )
    objects_updated: int = Field(
        ...,
        examples=[1],
        description="Number of objects that have been updated in database.",
    )
