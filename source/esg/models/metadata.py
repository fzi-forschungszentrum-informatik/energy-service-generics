"""
Generic definitions of metadata, i.e. data typically used as input for
services.

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
from datetime import timedelta
from datetime import timezone

from typing import List
from typing import Optional

from pydantic import Field
from pydantic import HttpUrl
from pydantic import model_validator

from esg.models.base import _BaseModel


class GeographicPosition(_BaseModel):
    """
    Defines the position of a point somewhere on Earth's surface.
    """

    latitude: float = Field(
        ...,
        examples=[49.01365],
        ge=-90.0,
        le=90.0,
        description=(
            "Latitude angle (North: +, South: -) of the position in degree."
        ),
    )
    longitude: float = Field(
        ...,
        examples=[8.40444],
        ge=-180.0,
        le=180.0,
        description=(
            "Longitude angle (West: -, East: +) of the position in degree."
        ),
    )


class GeographicPositionWithHeight(GeographicPosition):
    """
    Defines the position of a point somewhere _above_ Earth's surface.
    """

    height: float = Field(
        examples=[75.3],
        ge=0.0,
        # 1000m Seems a sane limit for know just prevent people from
        # accidentally requesting strange high heights. Beyond it
        # has no critical function and is hence also not tested for.
        le=1000.0,
        description=("Height above ground surface in meters."),
    )


class PVSystem(_BaseModel):
    """
    Minimal metadata of a PV system (beyond position) required to estimate
    the power production of that plant.
    """

    azimuth_angle: float = Field(
        examples=[0],
        ge=-90.0,
        le=90.0,
        description=(
            "The azimuth angle indicates the deviation of a photovoltaic "
            "module from the South. As coordinates are counted clockwise, "
            "for the East negative values are used, for the West "
            "positive ones. The unit of the azimuth angle is degrees °. "
        ),
    )
    inclination_angle: float = Field(
        examples=[30],
        ge=0,
        le=90,
        description=(
            "The inclination angle describes the deviation "
            "of the photovoltaic modules from the horizontal, "
            "e.g. an inclination angle of 0° indicates that "
            "the module faces right up."
            "The unit of the inclination angle is degrees °. "
        ),
    )
    nominal_power: float = Field(
        examples=[15],
        ge=0.0,
        description=(
            "The nominal power is a quantity specified in the "
            "data sheet of the PV module and measured at "
            "Standard Test Conditions (STC) by the manufacturer. "
            "The unit of the nominal power is kWp."
        ),
    )


# NOTE: In case you need it in future. A PV System with associated power
#       datapoint could be like this.
# TODO: Add the tests before using it.
# class PVSystemWithPowerDatapoint(PVSystem):
#     power_datapoint_id: int = Field(
#         examples=[1],
#         description=(
#             "The id of the datapoint which is used to store forecasts "
#             "of power production and measurements of the same, at least "
#             "if such measurements exist."
#         ),
#     )


class Plant(_BaseModel):
    """
    Defines the metadata necessary to compute optimized schedules or forecasts
    for a physical entity, e.g. a PV plant or a building.

    This model contains all types of metadata defined above, but all optional.
    The idea is that this model should be able to store plant data for all
    types of forecasting or optimization algorithms. On the other hand some
    metadata will likely be unknown for some plants. Hence we do not force
    the presence of the metadata groups.
    """

    id: Optional[int] = Field(
        default=None,
        examples=[1],
        description=("The ID of plant object in the central database."),
    )
    name: str = Field(
        ...,
        min_length=3,
        examples=["Karlsruhe city center"],
        description=(
            "A meaningful name for the plant. Should be short but precise. "
            "May be used in plots to analyse the product quality etc."
        ),
    )
    geographic_position: Optional[GeographicPosition] = Field(
        default=None,
        description=(
            "The position of the plant on Earth. Is required for "
            " computing weather forecast data etc."
        ),
    )
    geographic_position_with_height: Optional[GeographicPositionWithHeight] = (
        Field(
            default=None,
            description=(
                "The position of the plant above Earth's surface. E.g. for "
                "wind power plants."
            ),
        )
    )
    pv_system: Optional[PVSystem] = Field(
        default=None,
        description=(
            "Metadata of the photovoltaic plant. Is required for "
            "forecasting the photovoltaic power production of the plant"
        ),
    )


class Service(_BaseModel):
    """
    Defines the general metadata of a service.
    """

    id: Optional[int] = Field(
        None,
        examples=[1],
        description=("The ID of product object in the central database."),
    )
    name: str = Field(
        ...,
        min_length=3,
        examples=["PV Forecast"],
        description=(
            "A meaningful name for the product. Should be short but precise. "
            "Is used in e.g. in plots to analyses the product quality."
        ),
    )
    service_url: HttpUrl = Field(
        ...,
        examples=["https://service-provider.example.com/pv_forecast/v1/"],
        description=("The URL of the product service."),
    )


class Coverage(_BaseModel):
    """
    Defines the time span covered by a forecast or optimization output.
    """

    from_time: datetime = Field(
        ...,
        examples=[datetime.now(tz=timezone.utc) - timedelta(seconds=900)],
        description=(
            "The covered time span by a forecast or optimized schedule is "
            "equal or larger this date and time."
        ),
    )
    to_time: datetime = Field(
        ...,
        examples=[datetime.now(tz=timezone.utc) + timedelta(days=1)],
        description=(
            "The covered time span by this product run is less " "this value."
        ),
    )
    available_at: Optional[datetime] = Field(
        default=None,
        description=(
            "If set will make the service use only information available "
            "before this date and time. This is relevant for generating "
            "training data for ML applications."
        ),
    )

    @model_validator(mode="after")
    def validate_from_time_lte_to_time(cls, data):
        error_message = "`from_time` must be larger or equal `to_time`."
        if data.from_time > data.to_time:
            raise ValueError(error_message)
        return data


class CoverageDelta(_BaseModel):
    """
    Like `Coverage` but relative to a time defined elsewhere.

    This is useful to express information like, e.g. a forecast that usually
    covers the next 24 hours.
    """

    from_delta: timedelta = Field(
        ...,
        examples=[-900],
        description=(
            "For any run given time a request task of a service is created "
            "this time defines the difference of this time to the time the "
            "coverage of the task begins or should begin. E.g. "
            "if a task is created at `2022-02-02T03:00:52` and `from_delta' "
            "is `P0DT01H15M00S` then we expect coverage from to be "
            "set to `2022-02-02T04:15:52`."
        ),
    )
    to_delta: timedelta = Field(
        ...,
        examples=[89940],
        description=(
            "For any run given time a request task of a service is created "
            "this time defines the difference of this time to the time the "
            "coverage of the task ends or should end."
            "E.g. if a task is created at `2022-02-02T03:00:52` and `to_delta' "
            "is `P0DT05H15M00S` then we expect coverage to to be "
            "set to `2022-02-02T08:15:52`."
        ),
    )


class RequestTask(_BaseModel):
    """
    Metadata of a request task from the perspective of the calling entity.

    This should contain all information required to repeat a task for any
    arbitrary service, i.e. to resubmit the task to the service.
    """

    id: Optional[int] = Field(
        default=None,
        examples=[1],
        description=(
            "The ID of request task if stored in a database. "
            "NOTE: This is NOT the ID of the task used internally by "
            "the service."
        ),
    )
    service_id: int = Field(
        ...,
        examples=[1],
        description=(
            "The ID of the corresponding service metadata item in the "
            "central database."
        ),
    )
    plant_ids: List[int] = Field(
        default=list(),
        examples=[[1]],
        description=(
            "The IDs of the corresponding plant metadata items in the "
            "central database."
        ),
    )
    coverage: Coverage


class RequestTemplate(_BaseModel):
    """
    Collects the information necessary to generate a `RequestTask`.

    This is particularly useful for those situations where some software
    might regularly issue requests to services on behalf of one or more
    final users. This item can then store the metadata with which the software
    can derive the data necessary for the request, in particular the service
    URL, the plant metadata and coverage values.
    """

    id: Optional[int] = Field(
        default=None,
        examples=[1],
        description=(
            "The ID of request template if stored in a database. "
            "NOTE: This is NOT the ID of the task used internally by "
            "the service NOR the ID of the derived `RequestTask`"
        ),
    )
    service_id: int = Field(
        ...,
        examples=[1],
        description=(
            "The ID of the corresponding service metadata item in the "
            "central database."
        ),
    )
    plant_ids: List[int] = Field(
        default=list(),
        examples=[[1]],
        description=(
            "The IDs of the corresponding plant metadata items in the "
            "central database."
        ),
    )
    coverage_delta: CoverageDelta
