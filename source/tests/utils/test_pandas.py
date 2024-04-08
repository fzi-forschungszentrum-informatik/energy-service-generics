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

from datetime import datetime
from datetime import timezone

import pytest

try:
    import pandas as pd

except ModuleNotFoundError:
    pd = None

from esg.models.datapoint import ValueMessageList
from esg.models.datapoint import ValueDataFrame
from esg.utils.pandas import series_from_value_message_list
from esg.utils.pandas import value_message_list_from_series
from esg.utils.pandas import dataframe_from_value_dataframe
from esg.utils.pandas import value_dataframe_from_dataframe


@pytest.fixture(scope="class")
def add_test_data(request):
    """
    Define some shared datasets for the tests.

    mixed: Values contain mixed types of values like float, str, None, ...
    float: Values contain only float values.
    """
    request.cls.value_msg_series = pd.Series(
        index=[
            datetime(2022, 2, 22, 2, 52, tzinfo=timezone.utc),
            datetime(2022, 2, 22, 2, 53, tzinfo=timezone.utc),
            datetime(2022, 2, 22, 2, 54, tzinfo=timezone.utc),
        ],
        data=[2.1, None, -2.3],
    )
    request.cls.value_msg_list_jsonable = [
        {
            "value": 2.1,
            "time": "2022-02-22T02:52:00Z",
        },
        {
            "value": None,
            "time": "2022-02-22T02:53:00Z",
        },
        {
            "value": -2.3,
            "time": "2022-02-22T02:54:00Z",
        },
    ]


@pytest.mark.usefixtures("add_test_data")
@pytest.mark.skipif(pd is None, reason="requires pandas")
class TestSeriesFromValueList:
    def test_series_parsed_correctly(self):
        """
        Check that float only value message lists are parsed as float correctly.
        """
        expected_series = self.value_msg_series
        value_msg_list = ValueMessageList(self.value_msg_list_jsonable)

        actual_series = series_from_value_message_list(value_msg_list)

        # NOTE: The `check_index_type` is used here as pandas else complains:
        # E       Attribute "dtype" are different
        # E       [left]:  datetime64[ns, UTC]
        # E       [right]: datetime64[ns, UTC]
        # Which doesn't seem to be different at all?
        pd.testing.assert_series_equal(
            actual_series, expected_series, check_index_type=False
        )


@pytest.mark.usefixtures("add_test_data")
@pytest.mark.skipif(pd is None, reason="requires pandas")
class TestValueListFromSeries:
    def test_value_message_list_created_correctly(self):
        """
        Verify that value message list is created correctly for series
        holding floats as values incl. a NaN.
        """
        expected_value_message_list = ValueMessageList(
            self.value_msg_list_jsonable
        )

        actual_value_message_list = value_message_list_from_series(
            self.value_msg_series
        )

        assert actual_value_message_list == expected_value_message_list


@pytest.fixture(scope="class")
def add_test_dataframe(request):
    request.cls.test_data_as_pandas = pd.DataFrame(
        index=[
            datetime(2022, 2, 22, 2, 52, tzinfo=timezone.utc),
            datetime(2022, 2, 22, 2, 53, tzinfo=timezone.utc),
            datetime(2022, 2, 22, 2, 54, tzinfo=timezone.utc),
        ],
        data={
            # Ints incl. a NaN
            "1": [1, 2, None],
            # Floats incl. a NaN
            "23": [2.1, None, -2.3],
        },
    )
    request.cls.test_data_as_jsonable = {
        "times": [
            "2022-02-22T02:52:00Z",
            "2022-02-22T02:53:00Z",
            "2022-02-22T02:54:00Z",
        ],
        "values": {
            "1": [1.0, 2.0, None],
            "23": [2.1, None, -2.3],
        },
    }


@pytest.mark.usefixtures("add_test_dataframe")
@pytest.mark.skipif(pd is None, reason="requires pandas")
class TestDataframeFromValueDataframe:
    def test_dataframe_parsed_correctly(self):
        """
        Check that the a pandas DataFrame is correctly parsed from pydantic
        input.
        """
        expected_dataframe = self.test_data_as_pandas

        actual_dataframe = dataframe_from_value_dataframe(
            ValueDataFrame(**self.test_data_as_jsonable)
        )

        # NOTE: The `check_index_type` is used here as pandas else complains:
        # E       Attribute "dtype" are different
        # E       [left]:  datetime64[ns, UTC]
        # E       [right]: datetime64[ns, UTC]
        # Which doesn't seem to be different at all?
        pd.testing.assert_frame_equal(
            actual_dataframe, expected_dataframe, check_index_type=False
        )


@pytest.mark.usefixtures("add_test_dataframe")
@pytest.mark.skipif(pd is None, reason="requires pandas")
class TestValueDataframeFromDataframe:
    def test_pydantic_parsed_correctly(self):
        """
        Check that the a pydantic instance is correctly parsed from pandas
        dataframe.
        """
        expected_df_as_jsonable = self.test_data_as_jsonable

        actual_df_as_pydantic = value_dataframe_from_dataframe(
            self.test_data_as_pandas
        )
        actual_df_as_jsonable = actual_df_as_pydantic.model_dump_jsonable()

        assert actual_df_as_jsonable == expected_df_as_jsonable
