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
from typing import List
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from esg.clients.service import GenericServiceClient
from esg.models.base import _BaseModel
from esg.models.base import _RootModel
from generic import GenericCheckConnectionTests


class TestGenericServiceClientInit(GenericCheckConnectionTests):
    """
    Tests for `GenericServiceClient.__init__`
    """

    client_class = GenericServiceClient
    base_path = "/"


def create_client(httpserver):
    """
    Create GenericServiceClient instance.
    This expects one request to API root fired during creating the
    client. Afterwards we clean up so that the tests can work with
    httpserver as if this call would not have happened.
    """
    httpserver.expect_oneshot_request("/").respond_with_data(b"")
    client = GenericServiceClient(base_url=httpserver.url_for("/"))
    httpserver.clear_log()
    return client


class TestGenericServiceClientPostRequestJsonable:
    """
    Tests for `GenericServiceClient.post_request_jsonable`
    """

    test_task_id = uuid4()

    def post_request(self, httpserver, client):
        """
        prevent redundant code.
        """
        test_input_data = {"test": 1}
        expected_request = httpserver.expect_request(
            "/request/", method="POST", json=test_input_data
        )
        expected_request.respond_with_json(
            {"task_ID": str(self.test_task_id)}, status=201
        )

        client.post_request_jsonable(test_input_data)

    def test_endpoint_called(self, httpserver):
        """
        Verify that the POST request endpoint is called and the payload is
        forwarded.
        """

        client = create_client(httpserver)

        self.post_request(httpserver, client)

        # Check that the test server has received exactly one call.
        assert len(httpserver.log) == 1

    def test_task_ID_stored(self, httpserver):
        """
        The task ID must be stored to allow fetching results later.
        """

        client = create_client(httpserver)

        other_id = uuid4()
        client.task_ids.append(other_id)

        self.post_request(httpserver, client)

        expected_task_id = self.test_task_id
        assert expected_task_id in client.task_ids

        # Also check that the method hasn't done stupid stuff with other
        # task IDs or inserted multiple times.
        assert other_id in client.task_ids
        assert len(client.task_ids) == 2

        # Check that the test server has received exactly one call.
        assert len(httpserver.log) == 1


class TestGenericServiceClientPostRequest:
    """
    Tests for `GenericServiceClient.post_request`
    """

    def test_post_request_jsonable_called(self, httpserver):
        """
        Verify that input data is converted using the model and that
        `post_request_jsonable` is called to call the service.
        """

        class InputModel(_BaseModel):
            test: datetime

        client = create_client(httpserver)
        client.InputModel = InputModel
        client.post_request_jsonable = MagicMock()

        test_input_data_obj = {
            "test": datetime(2022, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
            # this should be removed by the model.
            "test2": 1,
        }
        client.post_request(input_data_obj=test_input_data_obj)

        assert client.post_request_jsonable.called

        call_args = client.post_request_jsonable.call_args
        expected_input_data_jsonable = {"test": "2022-01-02T03:04:05Z"}
        actual_input_data_jsonable = call_args.kwargs["input_data_as_jsonable"]
        assert actual_input_data_jsonable == expected_input_data_jsonable

    def test_post_request_jsonable_called_for_root_model(self, httpserver):
        """
        Like `test_post_request_jsonable_called` above but this time for a
        model with a list as root.

        """

        class ListItem(_BaseModel):
            test: datetime

        class InputModel(_RootModel):
            root: List[ListItem]

        client = create_client(httpserver)
        client.InputModel = InputModel
        client.post_request_jsonable = MagicMock()

        test_input_data_obj = [
            {
                "test": datetime(2022, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
                # this should be removed by the model.
                "test2": 1,
            }
        ]
        client.post_request(input_data_obj=test_input_data_obj)

        assert client.post_request_jsonable.called

        call_args = client.post_request_jsonable.call_args
        expected_input_data_jsonable = [{"test": "2022-01-02T03:04:05Z"}]
        actual_input_data_jsonable = call_args.kwargs["input_data_as_jsonable"]
        assert actual_input_data_jsonable == expected_input_data_jsonable


class TestGenericServiceClientWaitForResults:
    """
    Tests for `GenericServiceClient.wait_for_results`
    """

    test_task_ids = [uuid4(), uuid4(), uuid4()]

    # JSONable representation of valid request status responses.
    status_running = {
        "status_text": "running",
        "percent_complete": None,
        "ETA_seconds": None,
    }
    status_ready = {
        "status_text": "ready",
        "percent_complete": None,
        "ETA_seconds": None,
    }

    def call_wait_for_results(self, httpserver, client, max_retries=3):
        """
        prevent redundant code.

        This will make the first call to status for the first task_id
        return "running" and subsequent calls will return "ready".
        Note that this will also cause errors (HTTP 500) if `wait_for_results`
        doesn't request in order or requests too often.
        """
        client.task_ids = self.test_task_ids

        expected_request_1 = httpserver.expect_ordered_request(
            "/request/{}/status/".format(self.test_task_ids[0]), method="GET"
        )
        expected_request_1.respond_with_json(self.status_running, status=200)

        expected_request_2 = httpserver.expect_ordered_request(
            "/request/{}/status/".format(self.test_task_ids[0]), method="GET"
        )
        expected_request_2.respond_with_json(self.status_ready, status=200)

        expected_request_3 = httpserver.expect_ordered_request(
            "/request/{}/status/".format(self.test_task_ids[1]), method="GET"
        )
        expected_request_3.respond_with_json(self.status_running, status=200)

        expected_request_4 = httpserver.expect_ordered_request(
            "/request/{}/status/".format(self.test_task_ids[1]), method="GET"
        )
        expected_request_4.respond_with_json(self.status_ready, status=200)

        expected_request_5 = httpserver.expect_ordered_request(
            "/request/{}/status/".format(self.test_task_ids[2]), method="GET"
        )
        expected_request_5.respond_with_json(self.status_ready, status=200)

        client.wait_for_results(retry_wait=0, max_retries=max_retries)

    def test_status_for_all_tasks_fetched(self, httpserver):
        """
        Check that the status of all three items in `test_task_ids` has
        been fetched. Based on `self.call_wait_for_results` the method
        should need exactly 5 calls to the status endpoint for this.
        """
        client = create_client(httpserver)
        self.call_wait_for_results(httpserver, client)

    def test_all_tasks_finished_set(self, httpserver):
        """
        We expect this flat to be set once everything is done.
        """
        client = create_client(httpserver)
        self.call_wait_for_results(httpserver, client)

        assert client.all_tasks_finished is True

    def test_client_task_ids_not_changed(self, httpserver):
        """
        Verify that the method hasn't altered `client.task_ids`.
        It is need to fetch the results.


        """
        client = create_client(httpserver)
        self.call_wait_for_results(httpserver, client)

        # Should be OK if it is as long as before the call.
        assert len(client.task_ids) == 3

    def test_raises_on_timeout(self, httpserver):
        """
        Verify a timeout raises as documented in the docstring.
        """
        client = create_client(httpserver)
        with pytest.raises(RuntimeError):
            self.call_wait_for_results(httpserver, client, max_retries=1)


class TestGenericServiceClientGetResultJsonable:
    """
    Tests for `GenericServiceClient.get_result_jsonable`
    """

    test_task_ids = [uuid4(), uuid4(), uuid4()]
    test_output_data = [
        {"out": "2022-01-02T03:04:05+00:00"},
        {"out": "2022-01-02T03:04:06+00:00"},
        {"out": "2022-01-02T03:04:07+00:00"},
    ]

    def get_result(self, httpserver, client):
        """
        prevent redundant code.
        """
        expected_request_1 = httpserver.expect_ordered_request(
            "/request/{}/result/".format(self.test_task_ids[0]),
            method="GET",
        )
        expected_request_1.respond_with_json(
            self.test_output_data[0], status=200
        )

        expected_request_2 = httpserver.expect_ordered_request(
            "/request/{}/result/".format(self.test_task_ids[1]),
            method="GET",
        )
        expected_request_2.respond_with_json(
            self.test_output_data[1], status=200
        )

        expected_request_2 = httpserver.expect_ordered_request(
            "/request/{}/result/".format(self.test_task_ids[2]),
            method="GET",
        )
        expected_request_2.respond_with_json(
            self.test_output_data[2], status=200
        )

        # Mock prevents that we need to define additional expected tasks.
        client.wait_for_results = MagicMock()
        client.task_ids = self.test_task_ids.copy()

        return client.get_result_jsonable()

    def test_wait_for_results_called(self, httpserver):
        """
        If not fetching the result may block and cause nasty errors like
        gateway timeouts and stuff.
        """
        client = create_client(httpserver)
        client.wait_for_results = MagicMock()

        _ = self.get_result(httpserver, client)

        assert client.wait_for_results.called

    def test_endpoint_called(self, httpserver):
        """ """
        client = create_client(httpserver)
        client.wait_for_results = MagicMock()

        _ = self.get_result(httpserver, client)

        assert len(httpserver.log) == 3

    def test_task_ids_cleared_after_fetched(self, httpserver):
        """
        Verify that the task IDs that have been fetched already will
        be removed. Else the client will continue to fetch all previous
        results too.
        """
        client = create_client(httpserver)
        client.wait_for_results = MagicMock()

        _ = self.get_result(httpserver, client)

        assert len(client.task_ids) == 0

    def test_results_correct_and_in_order(self, httpserver):
        """
        Ordering is important here, as this is the only link to the tasks.
        """
        client = create_client(httpserver)
        client.wait_for_results = MagicMock()

        output_data_jsonable = self.get_result(httpserver, client)

        assert output_data_jsonable == self.test_output_data


class TestGenericServiceClientGetResult:
    """
    Tests for `GenericServiceClient.get_result`
    """

    def test_get_result_jsonable_called(self, httpserver):
        """
        Verify that output data is converted using the model and that
        `get_result_jsonable` is called to retrieve the result.
        """

        class OutputModel(_BaseModel):
            out: datetime

        test_output_data = [
            {"out": "2022-01-02T03:04:05+00:00"},
            {"out": "2022-01-02T03:04:06+00:00"},
            {"out": "2022-01-02T03:04:07+00:00"},
        ]

        client = create_client(httpserver)
        client.OutputModel = OutputModel
        client.get_result_jsonable = MagicMock(return_value=test_output_data)

        actual_output_data = client.get_results()

        assert client.get_result_jsonable.called

        expected_output_data = [
            OutputModel.model_validate(i) for i in test_output_data
        ]

        assert actual_output_data == expected_output_data

    def test_get_result_jsonable_called_for_root_model(self, httpserver):
        """
        Like `test_get_result_jsonable_called` but for `OutputModel` containing
        a list as root element.
        """

        class ListItem(_BaseModel):
            out: datetime

        class OutputModel(_RootModel):
            root: List[ListItem]

        test_output_data = [
            [{"out": "2022-01-02T03:04:05+00:00"}],
            [{"out": "2022-01-02T03:04:06+00:00"}],
            [{"out": "2022-01-02T03:04:07+00:00"}],
        ]

        client = create_client(httpserver)
        client.OutputModel = OutputModel
        client.get_result_jsonable = MagicMock(return_value=test_output_data)

        actual_output_data = client.get_results()

        assert client.get_result_jsonable.called

        expected_output_data = [
            OutputModel.model_validate(i) for i in test_output_data
        ]

        assert actual_output_data == expected_output_data
