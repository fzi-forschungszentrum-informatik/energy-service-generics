"""
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

from esg.models import metadata
from esg.test import data as td
from esg.test.generic_tests import GenericMessageSerializationTest


class TestGeographicPosition(GenericMessageSerializationTest):

    ModelClass = metadata.GeographicPosition
    msgs_as_python = [m["Python"] for m in td.geographic_positions]
    msgs_as_jsonable = [m["JSONable"] for m in td.geographic_positions]
    invalid_msgs_as_jsonable = [
        m["JSONable"] for m in td.invalid_geographic_positions
    ]


class TestGeographicPositionList(GenericMessageSerializationTest):

    ModelClass = metadata.GeographicPositionList
    # Note the additional outer list brackets around the messages here,
    # compared to `TestGeographicPosition` defined above.
    # This defines that `test_messages` only contain a single element
    # which holds all the value messages defined in `testdata`.
    msgs_as_python = [[m["Python"] for m in td.geographic_positions]]
    msgs_as_jsonable = [[m["JSONable"] for m in td.geographic_positions]]
    invalid_msgs_as_jsonable = [
        [m["JSONable"] for m in td.invalid_geographic_positions]
    ]


# This is just here to make `TestGeographicPositionDict` more readable.
enum_gp = list(enumerate(td.geographic_positions))
inv_enum_gp = list(enumerate(td.invalid_geographic_positions))


class TestGeographicPositionDict(GenericMessageSerializationTest):

    ModelClass = metadata.GeographicPositionDict
    msgs_as_python = [{str(i): m["Python"] for i, m in enum_gp}]
    msgs_as_jsonable = [{str(i): m["JSONable"] for i, m in enum_gp}]
    invalid_msgs_as_jsonable = [{str(i): m["JSONable"] for i, m in inv_enum_gp}]


class TestPVSystem(GenericMessageSerializationTest):

    ModelClass = metadata.PVSystem
    msgs_as_python = [m["Python"] for m in td.pv_systems]
    msgs_as_jsonable = [m["JSONable"] for m in td.pv_systems]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_pv_systems]


class TestPVSystemList(GenericMessageSerializationTest):

    ModelClass = metadata.PVSystemList
    # Note the additional outer list brackets around the messages here,
    # compared to `TestPVSystem` defined above.
    # This defines that `test_messages` only contain a single element
    # which holds all the value messages defined in `testdata`.
    msgs_as_python = [[m["Python"] for m in td.pv_systems]]
    msgs_as_jsonable = [[m["JSONable"] for m in td.pv_systems]]
    invalid_msgs_as_jsonable = [[m["JSONable"] for m in td.invalid_pv_systems]]


# This is just here to make `TestPVSystemDict` more readable.
enum_pvs = list(enumerate(td.pv_systems))
inv_enum_pvs = list(enumerate(td.invalid_pv_systems))


class TestPVSystemDict(GenericMessageSerializationTest):

    ModelClass = metadata.PVSystemDict
    msgs_as_python = [{str(i): m["Python"] for i, m in enum_pvs}]
    msgs_as_jsonable = [{str(i): m["JSONable"] for i, m in enum_pvs}]
    invalid_msgs_as_jsonable = [
        {str(i): m["JSONable"] for i, m in inv_enum_pvs}
    ]


class TestPlant(GenericMessageSerializationTest):

    ModelClass = metadata.Plant
    msgs_as_python = [m["Python"] for m in td.plants]
    msgs_as_jsonable = [m["JSONable"] for m in td.plants]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_plants]


class TestPlantList(GenericMessageSerializationTest):

    ModelClass = metadata.PlantList
    # Also check that empty lists are allowed
    msgs_as_python = [[], [m["Python"] for m in td.plants]]
    msgs_as_jsonable = [[], [m["JSONable"] for m in td.plants]]
    invalid_msgs_as_jsonable = [[m["JSONable"] for m in td.invalid_plants]]


class TestProduct(GenericMessageSerializationTest):

    ModelClass = metadata.Product
    msgs_as_python = [m["Python"] for m in td.products]
    msgs_as_jsonable = [m["JSONable"] for m in td.products]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_products]


class TestProductList(GenericMessageSerializationTest):

    ModelClass = metadata.ProductList
    # Also check that empty lists are allowed
    msgs_as_python = [[], [m["Python"] for m in td.products]]
    msgs_as_jsonable = [[], [m["JSONable"] for m in td.products]]
    invalid_msgs_as_jsonable = [[m["JSONable"] for m in td.invalid_products]]


class TestProductRun(GenericMessageSerializationTest):

    ModelClass = metadata.ProductRun
    msgs_as_python = [m["Python"] for m in td.product_runs]
    msgs_as_jsonable = [m["JSONable"] for m in td.product_runs]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_product_runs]


class TestProductRunList(GenericMessageSerializationTest):

    ModelClass = metadata.ProductRunList
    # Also check that empty lists are allowed
    msgs_as_python = [[], [m["Python"] for m in td.product_runs]]
    msgs_as_jsonable = [[], [m["JSONable"] for m in td.product_runs]]
    invalid_msgs_as_jsonable = [
        [m["JSONable"] for m in td.invalid_product_runs]
    ]
