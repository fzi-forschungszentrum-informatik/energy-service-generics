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
from multiprocessing import Process
from time import sleep

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


class APIInProcess:
    """
    A helper that executes the API class in a parallel process to
    make testing easier.
    """

    def __init__(self, api):
        """
        Put the `API` instance in a dedicated process.

        Arguments:
        ----------
        api : Initialized API class.
        """
        self.api = api

        def _run_API(api):
            api.run()

        self.process = Process(
            target=_run_API,
            kwargs={"api": self.api},
            daemon=True,
        )

    def __enter__(self):
        self.process.start()
        # Give uvicorn some time to start up.
        sleep(0.2)
        # Compute the root path of the API.
        root_path = self.api.fastapi_app.root_path
        base_url_root = f"http://localhost:8800{root_path}"
        return base_url_root

    def __exit__(self, *_):
        self.process.terminate()
        # XXX: This is super important, as the next test will else
        #      not be able to spin up the server again.
        self.process.join()
