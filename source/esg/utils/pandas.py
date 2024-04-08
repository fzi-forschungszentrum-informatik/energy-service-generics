"""
Some utility methods to parse time series to Pandas objects and vice versa.

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

try:
    import pandas as pd
    from numpy import nan as np_nan

except ModuleNotFoundError:
    pd = None

from esg.models.datapoint import ValueMessageList
from esg.models.datapoint import ValueDataFrame


def _check_pandas_available():
    if pd is None:
        raise ModuleNotFoundError(
            "This function requires pandas to work.  If you are "
            "using docker consider using a tag with `-pandas`."
        )


def series_from_value_message_list(value_message_list):
    """
    Parses a pandas.Series from the content of a `ValueMessageList` instance.

    Arguments:
    ----------
    value_message_list : ValueMessageList instance
        As defined in esg.models.datapoint.ValueMessageList

    Returns:
    --------
    series : pandas.Series
        A series holding the same information as the value_message_list.
    """
    _check_pandas_available()
    msg_as_dict = value_message_list.model_dump()
    times = [m["time"] for m in msg_as_dict]
    values = [m["value"] for m in msg_as_dict]
    series = pd.Series(index=times, data=values)

    return series


def value_message_list_from_series(series):
    """
    Transforms a pandas.Series into a `ValueMessageList` instance.

    Arguments:
    ----------
    series : pandas.Series
        A series holding the same information as the value_message_list.

    Returns:
    --------
    value_message_list : ValueMessageList instance
        As defined in esg.models.datapoint.ValueMessageList
    """
    _check_pandas_available()
    value_messages = []
    for time, value in series.items():
        if value != value:
            # This should only be true for NaN values.
            value = None
        value_messages.append({"value": value, "time": time})
    value_message_list = ValueMessageList(value_messages)
    return value_message_list


def dataframe_from_value_dataframe(value_dataframe):
    """
    Parse Pydantic object to Pandas dataframe.

    Arguments:
    ----------
    value_dataframe : ValueDataFrame instance.
        The pydantic object representation of the data.

    Returns:
    --------
    pandas_dataframe : pandas.DataFrame
        The pandas dataframe representation of the data.
    """
    _check_pandas_available()
    value_dataframe_as_dict = value_dataframe.model_dump()
    pandas_dataframe = pd.DataFrame(
        index=value_dataframe_as_dict["times"],
        data=value_dataframe_as_dict["values"],
    )
    return pandas_dataframe


def value_dataframe_from_dataframe(pandas_dataframe):
    """
    Parse Pydantic object from Pandas dataframe.

    Arguments:
    ----------
    pandas_dataframe : pandas.DataFrame
        The pandas dataframe representation of the data.

    Returns:
    --------
    value_dataframe : ValueDataFrame instance.
        The pydantic object representation of the data.
    """
    _check_pandas_available()
    pandas_dataframe_non_nan = pandas_dataframe.replace(np_nan, None)
    value_dataframe = ValueDataFrame(
        times=pandas_dataframe_non_nan.index,
        values=pandas_dataframe_non_nan.to_dict(orient="list"),
    )
    return value_dataframe
