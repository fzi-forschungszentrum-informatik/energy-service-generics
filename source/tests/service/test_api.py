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
from functools import reduce
import json
import logging
from multiprocessing import Process
from unittest.mock import patch, MagicMock
from uuid import UUID
from time import sleep
from typing import Optional

from fastapi import FastAPI
from packaging.version import Version
import pytest
import requests

# To prevent tests from failing if only parts of the package are used.
try:
    from celery import current_task
    from celery import states
    from celery.exceptions import Ignore
    from celery.result import AsyncResult
    from prometheus_fastapi_instrumentator import Instrumentator
    import uvicorn

    service_extra_not_installed = False
except ModuleNotFoundError:
    current_task = None
    states = None
    Ignore = None
    AsyncResult = None
    Instrumentator = None
    uvicorn = None
    service_extra_not_installed = True


from esg.clients.service import GenericServiceClient
from esg.models.base import _BaseModel
from esg.service.api import API
from esg.service.exceptions import GenericUnexpectedException
from esg.service.exceptions import RequestInducedException
from esg.service.worker import compute_fit_parameters_input_model
from esg.service.worker import compute_request_input_model
from esg.service.worker import invoke_handle_request
from esg.service.worker import invoke_fit_parameters
from esg.test.tools import TestClassWithFixtures


def deep_get(dictionary, *keys):
    """
    Simple helper that elegantly allows to retrieve stuff from a nested dict.
    Taken from here: https://stackoverflow.com/a/36131992
    """
    return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)


class DummyRequestArguments(_BaseModel):
    argument_as_float: float


class DummyRequestOutput(_BaseModel):
    argument_as_str: str
    parameter_as_str: Optional[str] = None


class DummyFittedParameters(_BaseModel):
    parameter_as_float: float


class DummyFitParameterArguments(_BaseModel):
    argument_as_float: float


class DummyObservations(_BaseModel):
    argument_offset: float


API_DEFAULT_KWARGS = {
    "RequestArguments": DummyRequestArguments,
    "RequestOutput": DummyRequestOutput,
    "request_task": MagicMock(),
    "title": "TestService",
    "version": Version("0.0.1"),
    "FitParameterArguments": DummyFitParameterArguments,
    "Observations": DummyObservations,
    "FittedParameters": DummyFittedParameters,
    "fit_parameters_task": MagicMock(),
    "description": "A nice service for testing.",
}


@pytest.fixture(scope="session")
def dummy_tasks(celery_session_app, celery_session_worker):
    """
    Tasks for testing for both cases, request and fit-parameters.
    """

    @celery_session_app.task
    def request_task(input_data_json):
        def handle_request(input_data):
            """Compute outputs matching the dummy models defined above."""
            print("`handle_request` input: ", input_data.model_dump_json())
            output = {
                "argument_as_str": str(input_data.arguments.argument_as_float)
            }
            if hasattr(input_data.parameters, "parameter_as_float"):
                # This is a request for a service that can fit parameters.
                output["parameter_as_str"] = str(
                    input_data.parameters.parameter_as_float
                )
            return output

        output_data_json = invoke_handle_request(
            input_data_json=input_data_json,
            RequestArguments=DummyRequestArguments,
            FittedParameters=DummyFittedParameters,
            handle_request_function=handle_request,
            RequestOutput=DummyRequestOutput,
        )
        return output_data_json

    @celery_session_app.task
    def fit_parameters_task(input_data_json):
        def fit_parameters(input_data):
            """Compute outputs matching the dummy models defined above."""
            print("`fit_parameters` input: ", input_data.model_dump_json())
            parameter_as_float = input_data.arguments.argument_as_float
            offset = input_data.observations.argument_offset
            parameter_as_float += offset
            output = {"parameter_as_float": parameter_as_float}
            return output

        output_data_json = invoke_fit_parameters(
            input_data_json=input_data_json,
            FitParameterArguments=DummyFitParameterArguments,
            Observations=DummyObservations,
            fit_parameters_function=fit_parameters,
            FittedParameters=DummyFittedParameters,
        )
        return output_data_json

    celery_session_worker.reload()

    dummy_tasks = {
        "request_task": request_task,
        "fit_parameters_task": fit_parameters_task,
    }
    return dummy_tasks


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
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

    def test_models_computed_request_only(self):
        """
        Verify that the data models are computed correctly for the case that
        only request endpoints should be available.
        """
        api_kwargs = API_DEFAULT_KWARGS | {"fit_parameters_task": None}
        api = API(**api_kwargs)

        ExpectedRequestInput = compute_request_input_model(
            RequestArguments=DummyRequestArguments,
        )
        expected_ri_schema = ExpectedRequestInput.model_json_schema()
        ExpectedRequestOutput = DummyRequestOutput
        expected_ro_schema = ExpectedRequestOutput.model_json_schema()

        assert api.RequestInput.model_json_schema() == expected_ri_schema
        assert api.RequestOutput.model_json_schema() == expected_ro_schema

    def test_models_computed_fit_parameters(self):
        """
        Verify that the data models are computed correctly for the case that
        request and fit-parameters endpoints should be available.
        """
        api = API(**API_DEFAULT_KWARGS)

        ExpectedRequestInput = compute_request_input_model(
            RequestArguments=DummyRequestArguments,
            FittedParameters=DummyFittedParameters,
        )
        expected_ri_schema = ExpectedRequestInput.model_json_schema()
        ExpectedRequestOutput = DummyRequestOutput
        expected_ro_schema = ExpectedRequestOutput.model_json_schema()
        ExpectedFitParametersInput = compute_fit_parameters_input_model(
            FitParameterArguments=DummyFitParameterArguments,
            Observations=DummyObservations,
        )
        expected_fpi_schema = ExpectedFitParametersInput.model_json_schema()
        ExpectedFitParametersOutput = DummyFittedParameters
        expected_fpo_schema = ExpectedFitParametersOutput.model_json_schema()

        assert api.RequestInput.model_json_schema() == expected_ri_schema
        assert api.RequestOutput.model_json_schema() == expected_ro_schema
        assert api.FitParametersInput.model_json_schema() == expected_fpi_schema
        assert (
            api.FitParametersOutput.model_json_schema() == expected_fpo_schema
        )

    def test_input_models_in_schema_request_only(self):
        """
        This is about the approach introduced in the FastAPI docs how
        the OpenAPI schema can be extended with the `model_json_schema()`
        output of the model as documented here:
        https://fastapi.tiangolo.com/advanced/path-operation-advanced-configuration/#custom-openapi-path-operation-schema

        This approach does not seem to work as expected as the output of
        `model_json_schema()` is not directly compatible with OpenAPI, i.e.
        it contains an item `"$devs"` that mus be placed in the components
        section of the OpenAPI schema. This test verifies that the model data
        is placed in the correct part of the schema.
        """
        api_kwargs = API_DEFAULT_KWARGS | {"fit_parameters_task": None}
        api = API(**api_kwargs)

        schema = api.fastapi_app.openapi()

        schema_relevant_part = deep_get(
            schema,
            "paths",
            "/request/",
            "post",
            "requestBody",
            "content",
            "application/json",
            "schema",
        )
        # If this fails the call above is very likely wrong.
        assert schema_relevant_part is not None

        assert "arguments" in schema_relevant_part["properties"]
        # Should only be in there for services with fit parameters.
        assert "parameters" not in schema_relevant_part["properties"]
        # This may be added if the output of `model_json_schema()` is added
        # directly. It is not valid OpenAPI syntax and causes an error.
        assert "$defs" not in schema_relevant_part

        # Verify that the reference to the components section is correct.
        expected_references = {
            "arguments": "#/components/schemas/DummyRequestArguments"
        }
        for key, expected_ref in expected_references.items():
            actual_ref = schema_relevant_part["properties"][key]["$ref"]
            assert actual_ref == expected_ref

        # Verify that the corresponding item exists in the components section.
        for expected_ref in expected_references.values():
            print(f"Checking for existence of {expected_ref}")
            component_entry = deep_get(schema, *expected_ref.split("/")[1:])
            # Assert that the expected entry exists.
            assert component_entry is not None

    def test_input_models_in_schema_fit_parameters(self):
        """
        Like `test_input_models_in_schema_request_only` above but now for the
        case that fit parameters is used too.
        """
        api = API(**API_DEFAULT_KWARGS)

        schema = api.fastapi_app.openapi()

        # For the request part.
        schema_relevant_part = deep_get(
            schema,
            "paths",
            "/request/",
            "post",
            "requestBody",
            "content",
            "application/json",
            "schema",
        )
        # If this fails the call above is very likely wrong.
        assert schema_relevant_part is not None

        assert "arguments" in schema_relevant_part["properties"]
        # Should only be in there for services with fit parameters.
        assert "parameters" in schema_relevant_part["properties"]
        # This may be added if the output of `model_json_schema()` is added
        # directly. It is not valid OpenAPI syntax and causes an error.
        assert "$defs" not in schema_relevant_part

        # Verify that the reference to the components section is correct.
        expected_references = {
            "arguments": "#/components/schemas/DummyRequestArguments",
            "parameters": "#/components/schemas/DummyFittedParameters",
        }
        for key, expected_ref in expected_references.items():
            actual_ref = schema_relevant_part["properties"][key]["$ref"]
            assert actual_ref == expected_ref

        # Verify that the corresponding item exists in the components section.
        for expected_ref in expected_references.values():
            print(f"Checking for existence of {expected_ref}")
            component_entry = deep_get(schema, *expected_ref.split("/")[1:])
            # Assert that the expected entry exists.
            assert component_entry is not None

        #######################################################################
        # Again for the fit-parameters part
        schema_relevant_part = deep_get(
            schema,
            "paths",
            "/fit-parameters/",
            "post",
            "requestBody",
            "content",
            "application/json",
            "schema",
        )
        # If this fails the call above is very likely wrong.
        assert schema_relevant_part is not None

        assert "arguments" in schema_relevant_part["properties"]
        # Should only be in there for services with fit parameters.
        assert "observations" in schema_relevant_part["properties"]
        # This may be added if the output of `model_json_schema()` is added
        # directly. It is not valid OpenAPI syntax and causes an error.
        assert "$defs" not in schema_relevant_part

        # Verify that the reference to the components section is correct.
        expected_references = {
            "arguments": "#/components/schemas/DummyFitParameterArguments",
            "observations": "#/components/schemas/DummyObservations",
        }
        for key, expected_ref in expected_references.items():
            actual_ref = schema_relevant_part["properties"][key]["$ref"]
            assert actual_ref == expected_ref

        # Verify that the corresponding item exists in the components section.
        for expected_ref in expected_references.values():
            print(f"Checking for existence of {expected_ref}")
            component_entry = deep_get(schema, *expected_ref.split("/")[1:])
            # Assert that the expected entry exists.
            assert component_entry is not None


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


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
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


class PostEndpointTests:
    """
    Generic tests for `post_request` and `post_fit_parameters`.

    This includes that the methods are wired up correctly to the FastAPI app.

    Attributes:
    -----------
    endpoint : str
        Corresponds to the `endpoint` argument of `GenericServiceClient`
    valid_input_data_obj : dict
        A piece of valid input data in object representation.
    expected_result_jsonable : dict
        The result that can be expected if `valid_input_data_obj` is used as
        input for the corresponding task.
    invalid_input_data_jsonable : dict
        A piece of invalid input data in jsonable form.
    expected_error_jsonable : dict
        The body of the error message that is expected once
        `invalid_input_data_jsonable` is used as input for the corresponding
        task.
    """

    endpoint = None
    valid_input_data_obj = None
    expected_result_jsonable = None
    invalid_input_data_jsonable = None
    expected_error_jsonable = None

    def test_task_ID_returned(self, dummy_tasks):
        """
        Check that calling the post endpoint returns an ID as expected.
        """
        api_kwargs = API_DEFAULT_KWARGS | dummy_tasks

        if self.endpoint == "request":
            InputModel = compute_request_input_model(
                RequestArguments=DummyRequestArguments,
                FittedParameters=DummyFittedParameters,
            )
        elif self.endpoint == "fit-parameters":
            InputModel = compute_fit_parameters_input_model(
                FitParameterArguments=DummyRequestArguments,
                Observations=DummyObservations,
            )
        else:
            raise RuntimeError("Invalid endpoint.")
        with APIInProcess(api_kwargs) as base_url_root:
            client = GenericServiceClient(
                base_url=f"{base_url_root}/",
                endpoint=self.endpoint,
                InputModel=InputModel,
            )

            # Raises if test API is not accessible.
            client.check_connection()

            # Check no other IDs are stored as this might make the test
            # below pass although it might should fail.
            assert len(client.task_ids) == 0

            # This will fail (return a 500) if the API implementation of
            # post_request does not work.
            client.post_obj(self.valid_input_data_obj)

            # Finally check that post request has returned a UUID although this
            # should already been guaranteed by Client handling the response.
            task_id = client.task_ids[0]
            assert isinstance(task_id, UUID)

    def test_task_created(self, dummy_tasks):
        """
        Verify that calling a post endpoint actually leads to the creation of a
        celery task on the broker.
        """
        api_kwargs = API_DEFAULT_KWARGS | dummy_tasks
        if self.endpoint == "request":
            InputModel = compute_request_input_model(
                RequestArguments=DummyRequestArguments,
                FittedParameters=DummyFittedParameters,
            )
        elif self.endpoint == "fit-parameters":
            InputModel = compute_fit_parameters_input_model(
                FitParameterArguments=DummyRequestArguments,
                Observations=DummyObservations,
            )
        else:
            raise RuntimeError("Invalid endpoint.")
        with APIInProcess(api_kwargs) as base_url_root:
            print(
                "Test sets up Client with InputModel: "
                f"{InputModel.model_json_schema()}"
            )
            client = GenericServiceClient(
                base_url=f"{base_url_root}/",
                endpoint=self.endpoint,
                InputModel=InputModel,
            )

            # Raises if test API is not accessible.
            client.check_connection()

            # Check no other IDs are stored as this might make the test
            # below pass although it might should fail.
            assert len(client.task_ids) == 0

            # This will fail (return a 500) if the API implementation of
            # post_request does not work.
            client.post_obj(self.valid_input_data_obj)

            # Check that celery was able to process the task.
            task_id = client.task_ids[0]
            task = AsyncResult(str(task_id))
            actual_result = json.loads(task.get(timeout=5, interval=0.1))
            assert actual_result == self.expected_result_jsonable

    def test_input_checked(self, dummy_tasks):
        """
        Verify that calling `post_request` with body data not matching the
        schema returns a 422 with adequate error details.

        This test is necessary as `post_request` has short wired the part of
        fastAPI that is responsible for this for the sake of generality and
        saving few CPU cycles due to not needing to serialize to JSON again.
        """
        api_kwargs = API_DEFAULT_KWARGS | dummy_tasks

        with APIInProcess(api_kwargs) as base_url_root:
            response = requests.post(
                f"{base_url_root}/{self.endpoint}/",
                json=self.invalid_input_data_jsonable,
            )

        assert response.status_code == 422

        actual_error_body = response.json()
        print(actual_error_body)
        assert actual_error_body == self.expected_error_jsonable


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
class TestPostRequest(PostEndpointTests):
    """
    Tests for `esg.service.api.API.post_request`.
    """

    endpoint = "request"
    valid_input_data_obj = {
        "arguments": {"argument_as_float": 123.4},
        "parameters": {"parameter_as_float": 78.9},
    }
    expected_result_jsonable = {
        "argument_as_str": "123.4",
        "parameter_as_str": "78.9",
    }
    invalid_input_data_jsonable = {"arguments": {"noFieldInModel": "foo bar"}}
    # This is the error we would typically expect from FastAPI.
    # It seems to be mostly the output of ValidationError.errors().
    expected_error_jsonable = {
        "detail": [
            {
                "type": "missing",
                "loc": ["arguments", "argument_as_float"],
                "msg": "Field required",
                "input": {"noFieldInModel": "foo bar"},
                "url": "https://errors.pydantic.dev/2.7/v/missing",
            },
            {
                "type": "missing",
                "loc": ["parameters"],
                "msg": "Field required",
                "input": {"arguments": {"noFieldInModel": "foo bar"}},
                "url": "https://errors.pydantic.dev/2.7/v/missing",
            },
        ]
    }


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
class TestPostFitParameters(PostEndpointTests):
    """
    Tests for `esg.service.api.API.post_fit_parameters`.
    """

    endpoint = "fit-parameters"
    valid_input_data_obj = {
        "arguments": {"argument_as_float": 123.4},
        "observations": {"argument_offset": 26.6},
    }
    expected_result_jsonable = {
        "parameter_as_float": 150.0,
    }
    invalid_input_data_jsonable = {"arguments": {"noFieldInModel": "foo bar"}}
    # This is the error we would typically expect from FastAPI.
    # It seems to be mostly the output of ValidationError.errors().
    expected_error_jsonable = {
        "detail": [
            {
                "type": "missing",
                "loc": ["arguments", "argument_as_float"],
                "msg": "Field required",
                "input": {"noFieldInModel": "foo bar"},
                "url": "https://errors.pydantic.dev/2.7/v/missing",
            },
            {
                "type": "missing",
                "loc": ["observations"],
                "msg": "Field required",
                "input": {"arguments": {"noFieldInModel": "foo bar"}},
                "url": "https://errors.pydantic.dev/2.7/v/missing",
            },
        ]
    }


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


class StatusEndpointTests:
    """
    Generic tests for `get_status`.

    This includes that the methods are wired up correctly to the FastAPI app.

    Attributes:
    -----------
    endpoint : str
        Corresponds to the `endpoint` argument of `GenericServiceClient`
    """

    endpoint = None

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

        api_kwargs = API_DEFAULT_KWARGS
        with APIInProcess(api_kwargs) as base_url_root:
            for celery_state, expected_task_status_text in status_map:
                print(f"Checking celery state: {celery_state}")
                task = execute_task_with_state.delay(celery_state)
                sleep(0.05)  # Give the task a little time to start

                response = requests.get(
                    f"{base_url_root}/{self.endpoint}/{task.id}/status/",
                )

                assert response.status_code == 200

                actual_task_status_text = response.json()["status_text"]
                assert actual_task_status_text == expected_task_status_text

    def test_pending_raises_404(self):
        """
        Celeries PENDING states means that the ID is not known. This is
        should raise a 404.
        """
        api_kwargs = API_DEFAULT_KWARGS
        with APIInProcess(api_kwargs) as base_url_root:
            random_task_id = "12345678-1234-5678-1234-567812345678"

            response = requests.get(
                f"{base_url_root}/{self.endpoint}/{random_task_id}/status/",
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
        api_kwargs = API_DEFAULT_KWARGS
        with APIInProcess(api_kwargs) as base_url_root:
            for test_exception in test_exceptions:
                print(f"Checking for exception: {test_exception}")
                task = execute_task_that_raises.delay(test_exception)
                sleep(0.05)  # Give the task a little time to start

                response = requests.get(
                    f"{base_url_root}/{self.endpoint}/{task.id}/status/",
                )

                assert response.status_code == 200
                actual_task_status_text = response.json()["status_text"]
                assert actual_task_status_text == "ready"


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
class TestRequestStatus(StatusEndpointTests):
    """
    Tests for `esg.service.api.API.get_status`, here especially that the method
    can be reached from the request endpoint.
    """

    endpoint = "request"


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
class TestFitParametersStatus(StatusEndpointTests):
    """
    Tests for `esg.service.api.API.get_status`, here especially that the method
    can be reached from the fit-parameter endpoint.
    """

    endpoint = "fit-parameters"


class ResultEndpointTests:
    """
    Generic tests for `get_request_result` and `get_fit_parameters_result`.

    This includes that the methods are wired up correctly to the FastAPI app.

    Attributes:
    -----------
    endpoint : str
        Corresponds to the `endpoint` argument of `GenericServiceClient`.
    valid_input_data_json : dict
        A piece of valid input data in JSON representation.
    expected_result_jsonable : dict
        The result that can be expected if `valid_input_data_obj` is used as
        input for the corresponding dummy task.
    InvalidOutputModel : Pydantic Model
        A model that does not match the output of the dummy task.
    """

    endpoint = None
    valid_input_data_json = None
    expected_result_jsonable = None
    InvalidOutputModel = None

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

        api_kwargs = API_DEFAULT_KWARGS
        with APIInProcess(api_kwargs) as base_url_root:
            for celery_state, expected_status_code in status_map:
                print(f"Checking celery state: {celery_state}")
                task = execute_task_with_state.delay(celery_state)
                sleep(0.05)  # Give the task a little time to start

                response = requests.get(
                    f"{base_url_root}/{self.endpoint}/{task.id}/result/",
                )

                assert response.status_code == expected_status_code

    def test_task_output_returned(self, dummy_tasks):
        """
        Check that the output of a task is returned by the endpoint.
        """
        if self.endpoint == "request":
            dummy_task = dummy_tasks["request_task"]
        elif self.endpoint == "fit-parameters":
            dummy_task = dummy_tasks["fit_parameters_task"]
        else:
            raise ValueError(f"Encountered unknown endpoint: {self.endpoint}")
        api_kwargs = API_DEFAULT_KWARGS
        with APIInProcess(api_kwargs) as base_url_root:
            client = GenericServiceClient(
                base_url=f"{base_url_root}/",
                endpoint=self.endpoint,
                OutputModel=DummyRequestOutput,
            )

            # Raises if test API is not accessible.
            client.check_connection()

            # Start the task.
            task = dummy_task.delay(self.valid_input_data_json)
            sleep(0.05)  # Give the task a little time to start

            # Check no other IDs are stored as this might make the test
            # below pass although it might should fail.
            client.task_ids = [task.id]

            actual_result = client.get_results_jsonable()[0]

            assert actual_result == self.expected_result_jsonable

    def test_task_output_checked(self, dummy_tasks):
        """
        Check that the output of is checked by the API, i.e. a 500 is
        returned if the content of provided by the task does not match
        the output model.
        """
        if self.endpoint == "request":
            dummy_task = dummy_tasks["request_task"]
        elif self.endpoint == "fit-parameters":
            dummy_task = dummy_tasks["fit_parameters_task"]
        else:
            raise ValueError(f"Encountered unknown endpoint: {self.endpoint}")
        api_kwargs = API_DEFAULT_KWARGS | {
            "RequestOutput": self.InvalidOutputModel,
            "FittedParameters": self.InvalidOutputModel,
        }

        with APIInProcess(api_kwargs) as base_url_root:
            # Start the task.
            task = dummy_task.delay(self.valid_input_data_json)
            sleep(0.05)  # Give the task a little time to start

            response = requests.get(
                f"{base_url_root}/{self.endpoint}/{task.id}/result/",
            )

            assert response.status_code == 500

    def test_task_with_exception_yields_500(self, execute_task_that_raises):
        """
        Check that a task that raises an exception is returned as 500.
        """
        api_kwargs = API_DEFAULT_KWARGS
        with APIInProcess(api_kwargs) as base_url_root:
            # Start the task.
            task = execute_task_that_raises.delay("ValueError")
            sleep(0.05)  # Give the task a little time to start

            response = requests.get(
                f"{base_url_root}/{self.endpoint}/{task.id}/result/",
            )

            assert response.status_code == 500


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
class TestRequestResult(ResultEndpointTests):
    """
    Tests for `esg.service.api.API.get_request_result`.

    This includes that the method is wired up correctly to the FastAPI app.
    """

    endpoint = "request"
    valid_input_data_json = json.dumps(
        {
            "arguments": {"argument_as_float": 123.4},
            "parameters": {"parameter_as_float": 78.9},
        }
    )
    expected_result_jsonable = {
        "argument_as_str": "123.4",
        "parameter_as_str": "78.9",
    }
    InvalidOutputModel = DummyRequestArguments


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
class TestFitParametersResult(ResultEndpointTests):
    """
    Tests for `esg.service.api.API.get_fit_parameters_result`.

    This includes that the method is wired up correctly to the FastAPI app.
    """

    endpoint = "fit-parameters"
    valid_input_data_json = json.dumps(
        {
            "arguments": {"argument_as_float": 123.4},
            "observations": {"argument_offset": 26.6},
        }
    )
    expected_result_jsonable = {
        "parameter_as_float": 150.0,
    }
    InvalidOutputModel = DummyRequestArguments


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


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
def test_celery_tests_work_at_all(dummy_worker_task):
    """
    Test that the celery test setup works. If this test fails all other
    tests that relay on celery will likely too.
    """

    assert dummy_worker_task.delay(4, 4).get(timeout=2) == 16
