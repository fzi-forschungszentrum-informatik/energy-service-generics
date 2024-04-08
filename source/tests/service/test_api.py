"""
Tests for `esg.service.api`

TODO Tests to define:
* All endpoints are protected by JWT:
  * Invalid Tokens fail.
  * Valid Tokens pass.

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

import os
import json
import logging
from multiprocessing import Process
from unittest.mock import patch, MagicMock
from uuid import UUID

from time import sleep

from celery import current_task
from celery import states
from celery.exceptions import Ignore
from celery.result import AsyncResult
from fastapi import FastAPI
from packaging.version import Version
import pytest
import requests

from esg.clients.service import GenericServiceClient
from esg.models.base import _BaseModel
from esg.service.api import API
from esg.service.api import uvicorn
from esg.service.exceptions import GenericUnexpectedException
from esg.service.exceptions import RequestInducedException
from esg.service.worker import execute_payload
from esg.test.tools import TestClassWithFixtures


class DummyRequestInput(_BaseModel):
    test1: float


class DummyRequestOutput(_BaseModel):
    test2: str


API_DEFAULT_KWARGS = {
    "title": "TestService",
    "description": "A nice service for testing.",
    "RequestInput": DummyRequestInput,
    "RequestOutput": DummyRequestOutput,
    "request_task": MagicMock(),
    "version": Version("0.0.1"),
}


@pytest.fixture(scope="session")
def execute_payload_task(celery_session_app, celery_session_worker):
    """
    A task for testing that implements `esg.service.worker.execute_payload`.
    """

    @celery_session_app.task
    def _execute_payload_task(input_data_json):

        def _payload_function(input_data):
            return {"test2": str(input_data.test1)}

        output_data_json = execute_payload(
            input_data_json=input_data_json,
            InputDataModel=DummyRequestInput,
            payload_function=_payload_function,
            OutputDataModel=DummyRequestOutput,
        )
        return output_data_json

    celery_session_worker.reload()

    return _execute_payload_task


@pytest.mark.skipif(uvicorn is None, reason="requires uvicorn")
class TestApiInit(TestClassWithFixtures):
    """
    Tests for `esg.service.api.API.__init__`
    """

    fixture_names = ("caplog",)

    def test_environment_variables_loaded(self):
        """
        Verify that the environment variable settings are parsed to the
        expected values.
        """
        envs = {
            "LOGLEVEL": "CRITICAL",
            "ROOT_PATH": "/test/v1",
        }

        api_kwargs = API_DEFAULT_KWARGS | {"version": Version("1.2.3")}
        with patch.dict(os.environ, envs):
            api = API(**api_kwargs)

        assert api._loglevel == logging.CRITICAL
        assert api.fastapi_app.root_path == "/test/v1"

    def test_default_environment_variables(self):
        """
        Check that the environment variables have the expected values,
        i.e. those defined in the Readme.
        """
        envs = {
            "LOGLEVEL": "",
            "ROOT_PATH": "",
        }

        api_kwargs = API_DEFAULT_KWARGS | {"version": Version("2.3.4")}
        with patch.dict(os.environ, envs):
            api = API(**api_kwargs)

        assert api._loglevel == logging.INFO
        assert api.fastapi_app.root_path == "/v2"

    def test_root_path_checked(self):
        """
        By convention the root path should contain the version info
        on the last path segment.
        """
        api_kwargs = API_DEFAULT_KWARGS | {"version": Version("2.3.4")}

        invalid_root_paths = [
            " ",  # No version at all.
            "a/v2/",  # Valid version but no leading slash.
            "/a/v2/",  # Valid version but a trailing slash.
            "/",  # No version at all but trailing and leading slash.
            "/test",  # No version at all.
            "/foo/v1",  # Wrong version number.
            "/foo/v2/bar",  # Version not at end.
        ]

        for invalid_root_path in invalid_root_paths:
            print(f"Testing {invalid_root_path}")
            with patch.dict(os.environ, {"ROOT_PATH": invalid_root_path}):
                with pytest.raises(ValueError):
                    _ = API(**api_kwargs)

    def test_version_root_path_overloads(self):
        """
        Check that we can overload the expected version number in `ROOT_PATH`.

        Here a practical scenario relevant for development deployments where
        for each branch the last commit is deployed. Additionally the commit
        ID is appended to the displayed version number.
        """
        version = "some branch (ef9eb864)"
        version_root_path = "some-branch"
        root_path = f"/test/{version_root_path}"

        envs = {
            "ROOT_PATH": root_path,
        }

        api_kwargs = API_DEFAULT_KWARGS | {
            "version": version,
            "version_root_path": version_root_path,
        }
        with patch.dict(os.environ, envs):
            # This raises if the `version_root_path` arg is ignored.
            api = API(**api_kwargs)

        assert api.fastapi_app.root_path == root_path

    def test_logger_available(self):
        """
        Verify that it is possible to use the logger of the service to create
        log messages.
        """
        api = API(**API_DEFAULT_KWARGS)

        self.caplog.clear()

        api.logger.info("A test info message")

        records = self.caplog.records
        assert len(records) == 1
        assert records[0].levelname == "INFO"
        assert records[0].message == "A test info message"

    def test_loglevel_changed(self):
        """
        Verify that it is possible to change ot logging level of the logger
        by setting the corresponding environment variable.
        """
        envs = {
            "LOGLEVEL": "WARNING",
        }

        with patch.dict(os.environ, envs):
            api = API(**API_DEFAULT_KWARGS)

        self.caplog.clear()

        # This message should not appear in the log,
        api.logger.info("A test info message")
        # .. while this message should due to LOGLEVEL set to WARNING.
        api.logger.warning("A test warning message")

        records = self.caplog.records
        assert len(records) == 1
        assert records[0].levelname == "WARNING"
        assert records[0].message == "A test warning message"

    def test_shared_objects_are_created(self):
        """
        Verify that the class objects expected by other methods are
        exposed.
        """
        api = API(**API_DEFAULT_KWARGS)
        assert isinstance(api.fastapi_app, FastAPI)

    def test_named_fastapi_args_forwarded(self):
        """
        Check that named args for FastAPI (like `description` and `title`)
        are forwarded.
        """
        test_title = ("Not Default Arg Title",)
        test_description = "A nice service for testing the description arg."

        api_kwargs = API_DEFAULT_KWARGS | {
            "title": test_title,
            "description": test_description,
        }
        api = API(**api_kwargs)

        assert api.fastapi_app.title == test_title
        assert api.fastapi_app.description == test_description


class APIInProcess:
    """
    A helper that executes the API class in a parallel process to
    make testing easier.
    """

    def __init__(self, api_kwargs):
        """
        Init and run `API` in a dedicated process.
        """
        self.api = API(**api_kwargs)

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
        sleep(0.1)
        # Compute the root path of the API.
        root_path = self.api.fastapi_app.root_path
        base_url_root = f"http://localhost:8800{root_path}"
        return base_url_root

    def __exit__(self, *_):
        self.process.terminate()
        # XXX: This is super important, as the next test will else
        #      not be able to spin up the server again.
        self.process.join()


@pytest.mark.skipif(uvicorn is None, reason="requires uvicorn")
class TestRun:
    """
    Tests for `esg.service.api.API.run`
    """

    def test_close_executed(self):
        """
        The run method should call the close method clean up.
        """
        api = API(**API_DEFAULT_KWARGS)
        api.close = MagicMock()
        # API would run forever if we would not raise.
        api.fastapi_app = MagicMock(side_effect=RuntimeError())

        with pytest.raises(RuntimeError):
            api.run()

        assert api.close.called

    def test_root_page_available(self):
        """
        The root page should serve the SwaggerUI page.
        """
        with APIInProcess(API_DEFAULT_KWARGS) as base_url_root:
            response = requests.get(f"{base_url_root}/")

        assert response.status_code == 200


class TestPostRequest:
    """
    Tests for `esg.service.api.API.post_request`.

    This includes that the method is wired up correctly to the FastAPI app.
    """

    def test_task_ID_returned(self, execute_payload_task):
        """
        Check that calling `post_request` returns an ID as expected.
        """
        api_kwargs = API_DEFAULT_KWARGS | {"request_task": execute_payload_task}

        input_data_obj = {"test1": 123.4}

        with APIInProcess(api_kwargs) as base_url_root:
            client = GenericServiceClient(
                base_url=f"{base_url_root}/",
                InputModel=DummyRequestInput,
            )

            # Raises if test API is not accessible.
            client.check_connection()

            # Check no other IDs are stored as this might make the test
            # below pass although it might should fail.
            assert len(client.task_ids) == 0

            # This will fail (return a 500) if the API implementation of
            # post_request does not work.
            client.post_request(input_data_obj)

            # Finally check that post request has returned a UUID although this
            # should already been guaranteed by Client handling the response.
            task_id = client.task_ids[0]
            assert isinstance(task_id, UUID)

    def test_task_created(self, execute_payload_task):
        """
        Verify that calling `post_request` actually leads to the creation of a
        celery task on the broker.
        """
        api_kwargs = API_DEFAULT_KWARGS | {"request_task": execute_payload_task}

        input_data_obj = {"test1": 123.4}
        expected_result = {"test2": "123.4"}

        with APIInProcess(api_kwargs) as base_url_root:
            client = GenericServiceClient(
                base_url=f"{base_url_root}/",
                InputModel=DummyRequestInput,
            )

            # Raises if test API is not accessible.
            client.check_connection()

            # Check no other IDs are stored as this might make the test
            # below pass although it might should fail.
            assert len(client.task_ids) == 0

            # This will fail (return a 500) if the API implementation of
            # post_request does not work.
            client.post_request(input_data_obj)

            # Check that celery was able to process the task.
            task_id = client.task_ids[0]
            task = AsyncResult(str(task_id))
            actual_result = json.loads(task.get(timeout=5, interval=0.1))
            assert actual_result == expected_result

    def test_input_checked(self, execute_payload_task):
        """
        Verify that calling `post_request` with body data not matching the
        schema returns a 422 with adequate error details.

        This test is necessary as `post_request` has short wired the part of
        fastAPI that is responsible for this for the sake of generality and
        saving few CPU cycles due to not needing to serialize to JSON again.

        The message format of FastAPI looks like this:

        """

        api_kwargs = API_DEFAULT_KWARGS | {"request_task": execute_payload_task}

        with APIInProcess(api_kwargs) as base_url_root:
            response = requests.post(
                f"{base_url_root}/request/",
                json={"noFieldInModel": "foo bar"},
            )

        assert response.status_code == 422

        # This is the error we would typically expect from FastAPI.
        # It seems to be mostly the output of ValidationError.errors().
        expected_error_body = {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["test1"],
                    "msg": "Field required",
                    "input": {"noFieldInModel": "foo bar"},
                    "url": "https://errors.pydantic.dev/2.6/v/missing",
                }
            ]
        }
        actual_error_body = response.json()

        assert actual_error_body == expected_error_body


@pytest.fixture(scope="session")
def execute_task_with_state(celery_session_app, celery_session_worker):
    """
    A task for testing that implements `esg.service.worker.execute_payload`.
    """

    @celery_session_app.task
    def task_with_state(state):
        current_task.update_state(state=state)
        print(f"Task updated state to: {state}")
        # Make celery not emit a SUCCESS state after returning.
        raise Ignore()

    celery_session_worker.reload()

    return task_with_state


@pytest.fixture(scope="session")
def execute_task_that_raises(celery_session_app, celery_session_worker):
    """
    A task for testing that can raise an exception.
    """

    @celery_session_app.task
    def task_that_raises(exception_name):
        if exception_name == "ValueError":
            raise ValueError()
        if exception_name == "RequestInducedException":
            raise RequestInducedException("The user fucked up.")
        if exception_name == "GenericUnexpectedException":
            raise GenericUnexpectedException()

    celery_session_worker.reload()

    return task_that_raises


class TestRequestStatus:
    """
    Tests for `esg.service.api.API.get_request_result`.

    This includes that the method is wired up correctly to the FastAPI app.
    """

    def test_celery_states_matched(self, execute_task_with_state):
        """
        Checks that the celery internal states are matched to the states
        of the framework task status.
        """
        # Map the built in states of celery to the state definitions of service
        # framework. The internal states of celery are documented here:
        # https://docs.celeryq.dev/en/stable/userguide/tasks.html#task-states
        # NOTE: There is an additional `states.REVOKED` status which is not
        #       considered here as the service framework has no functionality
        #       to cancel tasks. This might change in future.
        # NOTE: Celery matches an unknown ID to the pending state. PENDING is
        #       hence not included here.
        status_map = [
            (states.STARTED, "running"),
            (states.SUCCESS, "ready"),
            (states.FAILURE, "ready"),
            (states.RETRY, "queued"),
        ]

        with APIInProcess(API_DEFAULT_KWARGS) as base_url_root:
            for celery_state, expected_task_status_text in status_map:
                print(f"Checking celery state: {celery_state}")
                task = execute_task_with_state.delay(celery_state)
                sleep(0.05)  # Give the task a little time to start

                response = requests.get(
                    f"{base_url_root}/request/{task.id}/status/",
                )

                assert response.status_code == 200

                actual_task_status_text = response.json()["status_text"]
                assert actual_task_status_text == expected_task_status_text

    def test_pending_raises_404(self):
        """
        Celeries PENDING states means that the ID is not known. This is
        should raise a 404.
        """
        with APIInProcess(API_DEFAULT_KWARGS) as base_url_root:
            random_task_id = "12345678-1234-5678-1234-567812345678"

            response = requests.get(
                f"{base_url_root}/request/{random_task_id}/status/",
            )

            assert response.status_code == 404

    def test_exceptions_match_finished(self, execute_task_that_raises):
        """
        By definition, an exception during task execution is mapped
        to mapped to the finished state as we the cause of the error
        is only made public when retrieving the result.
        """
        test_exceptions = [
            "ValueError",
            "GenericUnexpectedException",
            "RequestInducedException",
        ]
        with APIInProcess(API_DEFAULT_KWARGS) as base_url_root:
            for test_exception in test_exceptions:
                print(f"Checking for exception: {test_exception}")
                task = execute_task_that_raises.delay(test_exception)
                sleep(0.05)  # Give the task a little time to start

                response = requests.get(
                    f"{base_url_root}/request/{task.id}/status/",
                )

                assert response.status_code == 200
                actual_task_status_text = response.json()["status_text"]
                assert actual_task_status_text == "ready"


class TestRequestResult:
    """
    Tests for `esg.service.api.API.get_request_result`.

    This includes that the method is wired up correctly to the FastAPI app.
    """

    def test_status_codes_match_state(self, execute_task_with_state):
        """
        Check that non success states are mapped to the intended HTTP errors.
        """
        # The internal states of celery are documented here:
        # https://docs.celeryq.dev/en/stable/userguide/tasks.html#task-states
        status_map = [
            (states.PENDING, 404),
            (states.STARTED, 409),
            (states.RETRY, 409),
            (states.FAILURE, 500),
        ]

        with APIInProcess(API_DEFAULT_KWARGS) as base_url_root:
            for celery_state, expected_status_code in status_map:
                print(f"Checking celery state: {celery_state}")
                task = execute_task_with_state.delay(celery_state)
                sleep(0.05)  # Give the task a little time to start

                response = requests.get(
                    f"{base_url_root}/request/{task.id}/result/",
                )

                assert response.status_code == expected_status_code

    def test_task_output_returned(self, execute_payload_task):
        """
        Check that the output of a task is returned by the endpoint.
        """
        input_data_json = json.dumps({"test1": 123.4})
        expected_result = {"test2": "123.4"}

        with APIInProcess(API_DEFAULT_KWARGS) as base_url_root:
            client = GenericServiceClient(
                base_url=f"{base_url_root}/",
                OutputModel=DummyRequestOutput,
            )

            # Raises if test API is not accessible.
            client.check_connection()

            # Start the task.
            task = execute_payload_task.delay(input_data_json)
            sleep(0.05)  # Give the task a little time to start

            # Check no other IDs are stored as this might make the test
            # below pass although it might should fail.
            client.task_ids = [task.id]

            actual_result = client.get_result_jsonable()[0]

            assert actual_result == expected_result

    def test_task_output_checked(self, execute_payload_task):
        """
        Check that the output of is checked by the API, i.e. a 500 is
        returned if the content of provided by the task does not match
        the output model.
        """
        input_data_json = json.dumps({"test1": 123.4})
        # The output model does not match the data computed by
        # `execute_payload_task`.
        api_kwargs = API_DEFAULT_KWARGS | {"RequestOutput": DummyRequestInput}

        with APIInProcess(api_kwargs) as base_url_root:
            # Start the task.
            task = execute_payload_task.delay(input_data_json)
            sleep(0.05)  # Give the task a little time to start

            response = requests.get(
                f"{base_url_root}/request/{task.id}/result/",
            )

            assert response.status_code == 500

    def test_task_with_exception_yields_500(self, execute_task_that_raises):
        """
        Check that a task that raises an exception is returned as 500.
        """
        with APIInProcess(API_DEFAULT_KWARGS) as base_url_root:
            # Start the task.
            task = execute_task_that_raises.delay("ValueError")
            sleep(0.05)  # Give the task a little time to start

            response = requests.get(
                f"{base_url_root}/request/{task.id}/result/",
            )

            assert response.status_code == 500


###############################################################################
#
#  NOTE: Leave the test below the end of the file so it will be the last one
#        in the test summary and thus the first the dev sees.
#
###############################################################################


@pytest.fixture(scope="session")
def dummy_worker_task(celery_session_app, celery_session_worker):

    @celery_session_app.task
    def _dummy_worker_task(x, y):
        return x * y

    celery_session_worker.reload()

    return _dummy_worker_task


def test_celery_tests_work_at_all(dummy_worker_task):
    """
    Test that the celery test setup works. If this test fails all other
    tests that relay on celery will likely too.
    """

    assert dummy_worker_task.delay(4, 4).get(timeout=2) == 16
