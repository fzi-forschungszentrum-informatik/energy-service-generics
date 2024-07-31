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

from esg.test.tools import copy_test_data


class TestCopyTestData:
    """
    Tests for esg.test.tools.copy_test_data
    """

    def test_data_correct(self):
        """
        Check that the data returned contains the data of the input.
        """
        original_data = [
            {
                "Python": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
                "JSONable": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
            },
        ]

        actual_data_copy = copy_test_data(original_data=original_data)

        expected_data_copy = original_data
        assert expected_data_copy == actual_data_copy

    def test_is_deepcopy(self):
        """
        Check that that an actual copy of the data is made.

        It is important that it is a deepcopy, as else modifications made to
        the data might affect the original data too.
        """
        original_data = [
            {
                "Python": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
                "JSONable": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
            },
        ]

        actual_data_copy = copy_test_data(original_data=original_data)

        assert id(original_data) != id(actual_data_copy)
        assert id(original_data[0]) != id(actual_data_copy[0])

    def test_add_data_to_python(self):
        """
        Check that is possible to add a field and value to the Python part.
        """
        original_data = [
            {
                "Python": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
                "JSONable": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
            },
        ]

        actual_data_copy = copy_test_data(
            original_data=original_data, add_to_python={"height": 30.0}
        )

        expected_data_copy = [
            {
                "Python": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                    "height": 30.0,
                },
                "JSONable": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
            },
        ]

        assert actual_data_copy == expected_data_copy

    def test_add_data_to_jsonable(self):
        """
        Check that is possible to add a field and value to the JSONable part.
        """
        original_data = [
            {
                "Python": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
                "JSONable": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
            },
        ]

        actual_data_copy = copy_test_data(
            original_data=original_data, add_to_jsonable={"height": 30.0}
        )

        expected_data_copy = [
            {
                "Python": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                },
                "JSONable": {
                    "latitude": 49.01365,
                    "longitude": 8.40444,
                    "height": 30.0,
                },
            },
        ]

        assert actual_data_copy == expected_data_copy
