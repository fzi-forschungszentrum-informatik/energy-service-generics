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

from typing import Dict
from typing import List
from typing import Optional

from pydantic import Field
from pydantic import HttpUrl

from esg.models.base import _BaseModel
from esg.models.base import _RootModel


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
    Defines the position of a point somewhere above Earth's surface.
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
            "Is used in e.g. in plots to analyses the product quality."
        ),
    )
    product_ids: List[int] = Field(
        default=list(),
        examples=[[1]],
        description=(
            "A list of product IDs that should be computed for this plant."
        ),
    )
    geographic_position: Optional[GeographicPosition] = Field(
        default=None,
        description=(
            "The position of the plant on earth. Is required for "
            " computing weather forecast data etc."
        ),
    )
    pv_system: Optional[PVSystem] = Field(
        default=None,
        description=(
            "Metadata of the photovoltaic plant. Is required for "
            "forecasting the photovoltaic power production of the plant"
        ),
    )


class Product(_BaseModel):
    """
    Defines the metadata for a product.
    """

    id: Optional[int] = Field(
        default=None,
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
    coverage_from: timedelta = Field(
        ...,
        examples=[-900],
        description=(
            "For any run given time a product run is started this is the "
            "difference between the start time and the begin of the covered "
            "time range, i.e. the time range for which forecasts or schedules "
            "are computed. E.g. if a run started at `2022-02-02T03:00:52` "
            "and `coverage_from` is `P0DT01H15M00S` then we expect the first "
            "forecasted value at time larger or equal `2022-02-02T04:15:52`."
        ),
    )
    coverage_to: timedelta = Field(
        ...,
        examples=[89940],
        description=(
            "For any run given time a product run is started this is the "
            "difference between the start time and the end of the covered "
            "time range, i.e. the time range for which forecasts or schedules "
            "are computed. E.g. if a run started at `2022-02-02T03:00:52` "
            "and `coverage_from` is `P0DT05H15M00S` then we expect the last "
            "forecasted value at time less then `2022-02-02T08:15:52`."
        ),
    )


class ProductRun(_BaseModel):
    """
    Identifies the computed result of a product service at a certain
    point in time. This should carry all information to repeat that
    computation if required.
    """

    id: Optional[int] = Field(
        default=None,
        examples=[1],
        description=("The ID of product run object in the central database."),
    )
    product_id: int = Field(
        ...,
        examples=[1],
        description=(
            "The ID of the corresponding product object in the "
            "central database."
        ),
    )
    plant_ids: List[int] = Field(
        default=list(),
        examples=[[1]],
        description=(
            "The IDs of the corresponding plant objects in the "
            "central database."
        ),
    )
    available_at: datetime = Field(
        default=datetime.now(tz=timezone.utc),
        description=(
            "Will be forwarded to product services and trigger those to "
            "compute only with data that has been available at this time."
        ),
    )
    coverage_from: datetime = Field(
        ...,
        examples=[datetime.now(tz=timezone.utc) - timedelta(seconds=900)],
        description=(
            "The covered time span by this product run is equal or larger "
            "this value."
        ),
    )
    coverage_to: datetime = Field(
        ...,
        examples=[datetime.now(tz=timezone.utc) + timedelta(days=1)],
        description=(
            "The covered time span by this product run is less " "this value."
        ),
    )
