"""
Test classes usable for testing of clients in general

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

import pytest
import requests


class GenericCheckConnectionTests:
    """
    Tests for the common functionality that a client should check if
    the service or application is online after init.

    Parameters:
    -----------
    client_class : class
        The uninitialized class of the client.
    base_path : str
        The base path under which the service/application is reachable.
    """

    client_class = None
    base_path = "/"

    def test_connection_checked(self, httpserver):
        """
        Verify that upon init, the client tries to check the connection
        to the service.
        """

        expected_request = httpserver.expect_oneshot_request(self.base_path)
        expected_request.respond_with_data(b"")

        _ = self.client_class(base_url=httpserver.url_for(self.base_path))

        # Verify that no incorrect call was made ...
        httpserver.check_assertions()
        # ... and that the one expected valid call was made too.
        assert len(httpserver.log) == 1

    def test_raises_if_server_unavailable(self):
        """
        Client should raise if service or application are unavailable.

        TODO: Improve this by checking that there is actually nothing
              listening on port 61080.

        """

        with pytest.raises(requests.exceptions.ConnectionError):
            _ = self.client_class(
                base_url="http://localhost:61080/api12iu1i23u12"
            )


class GenericGetTests:
    """
    Tests that should work for all methods that use `GET` methods of clients.

    Parameters:
    -----------
    client_class : class
        The uninitialized class of the client.
    base_path : str
        The base path under which the service/application is reachable.
    endpoint_path : str
        The path (incl. `base_path`) which should be interacted with.
    tested_client_method : str
        Name of the method of the client which should be tested.
    get_data_jsonable : list or dict
        The data in JSONable format that is assumed to be returned by the
        service/application.
    get_data_pydantic : Pydantic model instance
        The model instance which the tested method should return.
    all_test_kwargs : list of dict
        Each item should contain a valid set of keyword arguments that
        can be provided to the tested method.
    all_expected_query_params : list of dict
        Each item contains to a dict of query parameters that correspond
        the the item in the same position of `all_test_kwargs`. I.e. these
        are the query parameters that the API call should have if the
        method is called with the keyword arguments.

    """

    client_class = None
    base_path = "/"
    endpoint_path = None
    tested_client_method = None
    get_data_jsonable = None
    get_data_pydantic = None
    all_test_kwargs = [{}]
    all_expected_query_params = [{}]

    def test_pydantic_object_returned(self, httpserver):
        """
        Verify that a expected pydantic object is returned.

        This uses the first item of `all_test_kwargs` to make sure that
        any required arguments are given to the tested method.
        """
        expected_request = httpserver.expect_oneshot_request(self.endpoint_path)
        expected_request.respond_with_json(self.get_data_jsonable)

        client = self.client_class(
            base_url=httpserver.url_for(self.base_path),
            check_on_init=False,
        )
        tested_method = getattr(client, self.tested_client_method)
        actual_return = tested_method(**self.all_test_kwargs[0])

        assert actual_return == self.get_data_pydantic

        # Verify that no incorrect call was made ...
        httpserver.check_assertions()
        # ... and that the one expected valid call was made too.
        assert len(httpserver.log) == 1

    def test_query_args_forwarded(self, httpserver):
        """
        Verify that `query_args` are forwarded to the server.
        """
        zipped = zip(self.all_test_kwargs, self.all_expected_query_params)
        for test_kwargs, expected_query_params in zipped:
            print(f"testing with kwargs: {test_kwargs}")
            httpserver.clear()
            expected_request = httpserver.expect_oneshot_request(
                self.endpoint_path, query_string=expected_query_params
            )
            expected_request.respond_with_json(self.get_data_jsonable)

            client = self.client_class(
                base_url=httpserver.url_for(self.base_path),
                check_on_init=False,
            )
            tested_method = getattr(client, self.tested_client_method)
            _ = tested_method(**test_kwargs)

            httpserver.check_assertions()


class GenericPutTests:
    """
    Tests that should work for all methods that use `PUT` methods of client.

    Parameters:
    -----------
    client_class : class
        The uninitialized class of the client.
    base_path : str
        The base path under which the EMP is reachable.
    endpoint_path : str
        The path (incl. `base_path`) which should be interacted with.
    tested_client_method : str
        Name of the method of the client which should be tested.
    put_data_pydantic : Pydantic model instance
        The model instance of the data that should be sent to the EMP.
    put_data_jsonable : list or dict
        The data in JSONable format that should be expected by the server.
    response_data_jsonable : list or dict
        The data in JSONable format that is assumed to be returned by the EMP.
    response_data_pydantic : Pydantic model instance
        The model instance which the tested method should return.
    """

    client_class = None
    base_path = "/emp/api/"
    endpoint_path = None
    tested_client_method = None
    put_data_pydantic = None
    put_data_jsonable = None
    response_data_jsonable = None
    response_data_pydantic = None

    def test_payload_pushed_to_server_and_response_returned(self, httpserver):
        """
        Verify that the payload data of the put operation is forwarded and
        that the response is parsed correctly.

        NOTE: There is no simple way with `httpserver` to verify that the
              PUT operation alone was a success, as `check_assertions()` will
              only trigger those rules that have called incorrectly, but not
              those not called at all.
        """
        expected_request = httpserver.expect_oneshot_request(
            self.endpoint_path,
            method="PUT",
            json=self.put_data_jsonable,
            headers={"Content-Type": "application/json"},
        )
        expected_request.respond_with_json(self.response_data_jsonable)

        client = self.client_class(
            base_url=httpserver.url_for(self.base_path),
            check_on_init=False,
        )
        tested_method = getattr(client, self.tested_client_method)
        actual_return = tested_method(self.put_data_pydantic)

        assert actual_return == self.response_data_pydantic

        # Verify that no incorrect call was made ...
        httpserver.check_assertions()
        # ... and that the one expected valid call was made too.
        assert len(httpserver.log) == 1
