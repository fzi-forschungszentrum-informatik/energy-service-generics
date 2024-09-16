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
from copy import deepcopy
from multiprocessing import Process
from uuid import uuid1
from time import sleep

import pytest

from esg.models.task import TaskId, TaskStatus


def async_return(return_value=None, loop=None):
    """
    A small helper that allows a MagicMock to be used in place of a
    async function. Use with MagicMock(return_value=async_return())
    """
    f = asyncio.Future(loop=loop)
    f.set_result(return_value)
    return f


def copy_test_data(original_data, add_to_python=None, add_to_jsonable=None):
    """
    Makes a deep copy of test data and allows adding fields and values.

    Arguments:
    ----------
    original_data : list
        The original data that should be copied. Expects that the input
        follows the convention introduced in `esg.test.data`, i.e. is a
        list containing dicts each containing a "Python" and "JSONable" part.
    add_to_python : dict
        Dict of fields and values that should be added under "Python"

    Returns:
    --------
    data_copy : list
        The expected copy of `original_data` appended with the additional data
        if specified.
    """
    data_copy = deepcopy(original_data)

    if add_to_python is not None:
        for item in data_copy:
            item["Python"].update(add_to_python)

    if add_to_jsonable is not None:
        for item in data_copy:
            item["JSONable"].update(add_to_jsonable)

    return data_copy


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


class GenericServiceMock:
    """
    A tool to mock external services using the ESG framework.
    """

    def __init__(self, httpserver):
        self.httpserver = httpserver

    def get_base_url(self):
        """
        Return the base_url of the mocked service.

        Returns.
        --------
        base_url : str
            The root URL of the service API, e.g. `http://localhost:8800`
        """
        return self.httpserver.url_for("")[:-1]

    def add_expected_call(
        self, endpoint, response_jsonable, body_jsonable=None, check_body=False
    ):
        """
        Make the service mock expect request or fit-parameters call.

        Arguments:
        ----------
        endpoint : str
            Usually either `"request"` or `"fit-parameters"`.
        response_jsonable : something JSONable
            If matched, this will be returned to the client.
        body_jsonable : something JSONable
            The server will only respond if POST call contains
            a similar parsed JSON object as body.
            NOTE: None doesn't seem to disable the check, it seems to say
                  we expect an empty body.
        check_body : bool
            If `False` will ignore `body_jsonable`.
        """
        expected_root_request = self.httpserver.expect_request(
            "/", method="GET"
        )
        expected_root_request.respond_with_json({})

        task_uuid = str(uuid1())

        if check_body:
            expected_post_request = self.httpserver.expect_request(
                f"/{endpoint}/", json=body_jsonable, method="POST"
            )
        else:
            expected_post_request = self.httpserver.expect_request(
                f"/{endpoint}/", method="POST"
            )

        expected_post_request.respond_with_json(
            TaskId(task_ID=task_uuid).model_dump_jsonable()
        )

        expected_status_request = self.httpserver.expect_request(
            f"/{endpoint}/{task_uuid}/status/", method="GET"
        )
        expected_status_request.respond_with_json(
            TaskStatus(status_text="running").model_dump_jsonable()
        )

        expected_result_request = self.httpserver.expect_request(
            f"/{endpoint}/{task_uuid}/result/", method="GET"
        )
        expected_result_request.respond_with_json(response_jsonable)
