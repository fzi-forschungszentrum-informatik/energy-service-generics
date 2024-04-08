"""
Utility functions for timestamps and datetime objects.

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

from datetime import datetime, timezone


def datetime_from_timestamp(timestamp, tz_aware=True):
    """
    Convert timestamp to datetime object.

    Arguments:
    ----------
    timestamp: int
        Milliseconds since 1.1.1970 UTC
    tz_aware: bool
        If true make datetime object timezone aware, i.e. in UTC.

    Returns:
    --------
    dt: datetime object
        Corresponding datetime object
    """
    # This returns the local time.
    dt = datetime.fromtimestamp(timestamp / 1000.0)
    # So we recompute it to UTC.
    dt = dt.astimezone(timezone.utc)
    if not tz_aware:
        # Remove timezone if not requested.
        dt = dt.replace(tzinfo=None)
    return dt


def timestamp_utc_now():
    """
    Compute current timestamp.

    Returns:
    --------
    ts_utc_now : int
        The rounded timestamp of the current UTC time in milliseconds.
    """
    return round(datetime.now(tz=timezone.utc).timestamp() * 1000)


def datetime_to_pretty_str(dt):
    """
    Convert datetime object to string similar to ISO 8601 but more compact.

    Arguments:
    ----------
    dt: datetime object
        ... for which the string will be generated.

    Returns:
    --------
    dt_str: string
        The pretty string representation of the datetime object.
    """
    dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt_str
