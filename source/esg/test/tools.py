"""
Helper methods for writing tests, both for stuff residing in the this
package but also for derived services and other programs.

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

import asyncio

import pytest


def async_return(return_value=None, loop=None):
    """
    A small helper that allows a MagicMock to be used in place of a
    async function. Use with MagicMock(return_value=async_return())
    """
    f = asyncio.Future(loop=loop)
    f.set_result(return_value)
    return f


class TestClassWithFixtures:
    """
    Allows the use of pytest fixtures as attributes in test classes.
    """

    fixture_names = ()

    @pytest.fixture(autouse=True)
    def auto_injector_fixture(self, request):
        names = self.fixture_names
        for name in names:
            setattr(self, name, request.getfixturevalue(name))
