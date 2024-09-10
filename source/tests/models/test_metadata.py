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


class TestGeographicPositionWithHeight(GenericMessageSerializationTest):

    ModelClass = metadata.GeographicPositionWithHeight
    msgs_as_python = [m["Python"] for m in td.geographic_positions_with_height]
    msgs_as_jsonable = [
        m["JSONable"] for m in td.geographic_positions_with_height
    ]
    invalid_msgs_as_jsonable = [
        m["JSONable"] for m in td.invalid_geographic_positions_with_height
    ]


class TestPVSystem(GenericMessageSerializationTest):

    ModelClass = metadata.PVSystem
    msgs_as_python = [m["Python"] for m in td.pv_systems]
    msgs_as_jsonable = [m["JSONable"] for m in td.pv_systems]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_pv_systems]


class TestPlant(GenericMessageSerializationTest):

    ModelClass = metadata.Plant
    msgs_as_python = [m["Python"] for m in td.plants]
    msgs_as_jsonable = [m["JSONable"] for m in td.plants]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_plants]


class TestService(GenericMessageSerializationTest):

    ModelClass = metadata.Service
    msgs_as_python = [m["Python"] for m in td.services]
    msgs_as_jsonable = [m["JSONable"] for m in td.services]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_services]


class TestCoverage(GenericMessageSerializationTest):

    ModelClass = metadata.Coverage
    msgs_as_python = [m["Python"] for m in td.coverages]
    msgs_as_jsonable = [m["JSONable"] for m in td.coverages]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_coverages]


class TestCoverageDelta(GenericMessageSerializationTest):

    ModelClass = metadata.CoverageDelta
    msgs_as_python = [m["Python"] for m in td.coverage_deltas]
    msgs_as_jsonable = [m["JSONable"] for m in td.coverage_deltas]
    invalid_msgs_as_jsonable = [
        m["JSONable"] for m in td.invalid_coverage_deltas
    ]


class TestRequestTask(GenericMessageSerializationTest):

    ModelClass = metadata.RequestTask
    msgs_as_python = [m["Python"] for m in td.request_tasks]
    msgs_as_jsonable = [m["JSONable"] for m in td.request_tasks]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_request_tasks]
