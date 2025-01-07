"""
Generic Tests that can be reused to accelerate test implementation.

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

import json

from pydantic import ValidationError
import pytest

from esg.clients.service import GenericServiceClient
from esg.test.tools import APIInProcess
from esg.test.tools import TestClassWithFixtures


class GenericMessageSerializationTest:
    """
    A generic set of tests to verify that the data can be serialized between
    the expected representations.

    Attributes:
    -----------
    ModelClass : pydantic model class
        The model that is used to serialize/deserialize the data.
    msgs_as_python : list of anything.
        The Python representation of the as defined in `testdata`.
        Each item in the list is treated as distinct message to
        verify correct operation for.
    msgs_as_jsonable : list of anything.
        Similar to `data_as_python` but for JSONable representation.
        See the `testdata` module docstring for a discussion why we
        use JSONable representation instead of direct JSON.
    invalid_msgs_as_jsonable : list of anything.
        Similar to `msgs_as_jsonable` but messages that are expected
        to cause an error during validation.
    """

    ModelClass = None
    msgs_as_python = None
    msgs_as_jsonable = None
    invalid_msgs_as_jsonable = None

    def test_python_to_jsonable(self):
        """
        Verify that the model can be used to generate the expected JSONable
        output.
        """
        test_messages = zip(self.msgs_as_python, self.msgs_as_jsonable)
        for msg_as_python, expected_msg_as_jsonable in test_messages:

            model_instance = self.ModelClass.model_validate(msg_as_python)
            actual_msg_as_jsonable = model_instance.model_dump_jsonable()

            assert actual_msg_as_jsonable == expected_msg_as_jsonable

    def test_python_to_json(self):
        """
        Verify that the model can be used to generate the expected JSON output.
        """
        test_messages = zip(self.msgs_as_python, self.msgs_as_jsonable)
        for msg_as_python, expected_msg_as_jsonable in test_messages:

            model_instance = self.ModelClass.model_validate(msg_as_python)
            actual_msg_as_json = model_instance.model_dump_json()
            actual_msg_as_jsonable = json.loads(actual_msg_as_json)

            assert actual_msg_as_jsonable == expected_msg_as_jsonable

    def test_jsonable_to_python_object(self):
        """
        Check that the model can be used to parse the JSONable representation.
        """
        test_messages = zip(self.msgs_as_python, self.msgs_as_jsonable)
        for msg_as_python, msg_as_jsonable in test_messages:

            expected_msg_as_obj = self.ModelClass.model_validate(msg_as_python)
            actual_msg_as_obj = self.ModelClass.model_validate(msg_as_jsonable)

            assert actual_msg_as_obj == expected_msg_as_obj

    def test_json_to_python_object(self):
        """
        Check that the model can be used to parse the JSON representation.
        """
        test_messages = zip(self.msgs_as_python, self.msgs_as_jsonable)
        for msg_as_python, msg_as_jsonable in test_messages:

            expected_msg_as_obj = self.ModelClass.model_validate(msg_as_python)
            msg_as_json = json.dumps(msg_as_jsonable)
            actual_msg_as_obj = self.ModelClass.model_validate_json(msg_as_json)

            assert actual_msg_as_obj == expected_msg_as_obj

    def test_validation_error_raised_for_invalid_jsonable(self):
        """
        Verify that each invalid message provided to `model_validate()`triggers
        a `ValidationError`
        """
        for invalid_msg_as_jsonable in self.invalid_msgs_as_jsonable:
            with pytest.raises(ValidationError):
                _ = self.ModelClass.model_validate(invalid_msg_as_jsonable)
                # This will only be executed if the test fails.
                print(invalid_msg_as_jsonable)

    def test_validation_error_raised_for_invalid_json(self):
        """
        Verify that each invalid message provided to `model_validate_json()`
        triggers a `ValidationError`
        """
        for invalid_msg_as_jsonable in self.invalid_msgs_as_jsonable:
            invalid_msg_as_json = json.dumps(invalid_msg_as_jsonable)
            with pytest.raises(ValidationError):
                _ = self.ModelClass.model_validate_json(invalid_msg_as_json)
                # This will only be executed if the test fails.
                print(invalid_msg_as_jsonable)


class GenericMessageSerializationTestBEMcom(GenericMessageSerializationTest):
    """
    Extends `GenericMessageSerializationTest` with tests about serialization
    from and to BEMCom message format.

    Attributes:
    -----------
    ModelClass : pydantic model class
        The model that is used to serialize/deserialize the data.
    msgs_as_python : list of anything.
        The Python representation of the as defined in `testdata`.
        Each item in the list is treated as distinct message to
        verify correct operation for.
    msgs_as_jsonable : list of anything.
        Similar to `data_as_python` but for JSONable representation.
        See the `testdata` module docstring for a discussion why we
        use JSONable representation instead of direct JSON.
    msgs_as_bemcom : list of anything.
        Similar to `msgs_as_jsonable` but for the BEMCom representation.
    invalid_msgs_as_jsonable : list of anything.
        Similar to `msgs_as_jsonable` but messages that are expected
        to cause an error during validation.
    """

    ModelClass = None
    msgs_as_bemcom = None

    def test_python_to_jsonable_bemcom(self):
        """
        Verify that the model can be used to generate the expected JSONable
        output in BEMCom format.
        """
        test_messages = zip(self.msgs_as_python, self.msgs_as_bemcom)
        for msg_as_python, expected_msg_as_bemcom in test_messages:

            model_instance = self.ModelClass.model_validate(msg_as_python)
            actual_msg_as_bemcom = model_instance.model_dump_jsonable_bemcom()

            assert actual_msg_as_bemcom == expected_msg_as_bemcom

    def test_python_to_json_bemcom(self):
        """
        Verify that the model can be used to generate the expected JSON output
        in BEMCom format.
        """
        test_messages = zip(self.msgs_as_python, self.msgs_as_bemcom)
        for msg_as_python, expected_msg_as_bemcom in test_messages:

            model_instance = self.ModelClass.model_validate(msg_as_python)
            actual_msg_as_json_bemcom = model_instance.model_dump_json_bemcom()
            actual_msg_as_bemcom = json.loads(actual_msg_as_json_bemcom)

            assert actual_msg_as_bemcom == expected_msg_as_bemcom

    def test_bemcom_jsonable_to_python_object(self):
        """
        Check that the model can be used to parse BEMcom messages that
        have already been processed with `json.loads`
        """
        test_messages = zip(self.msgs_as_python, self.msgs_as_bemcom)
        for msg_as_python, msg_as_bemcom in test_messages:

            expected_msg_as_obj = self.ModelClass.model_validate(msg_as_python)
            actual_msg_as_obj = self.ModelClass.model_validate_bemcom(
                msg_as_bemcom
            )

            assert actual_msg_as_obj == expected_msg_as_obj

    def test_bemcom_json_to_python_object(self):
        """
        Check that the model can be used to parse the BEMCom messages
        represented as JSON string.
        """
        test_messages = zip(self.msgs_as_python, self.msgs_as_bemcom)
        for msg_as_python, msg_as_bemcom in test_messages:
            expected_msg_as_obj = self.ModelClass.model_validate(msg_as_python)
            msg_as_json = json.dumps(msg_as_bemcom)
            actual_msg_as_obj = self.ModelClass.model_validate_json_bemcom(
                msg_as_json
            )

            assert actual_msg_as_obj == expected_msg_as_obj


class GenericWorkerTaskTest(TestClassWithFixtures):
    """
    Tests for checking that the worker tasks are correctly implemented.

    Attributes:
    -----------
    fixture_names : list of str
        If provided, any fixture names listed here will be added to all tests.
    tested_task : method decorated as Celery task.
        The task that should be tested.
    input_data_jsonable : list of anything.
        The JSONable representation of the input data that should be
        used for testing.
    output_data_jsonable : list of anything.
        Similar to `input_data_jsonable` but now to expected output
        for each item in the input.
    """

    fixture_names = ()
    task_to_test = None
    input_data_jsonable = None
    output_data_jsonable = None

    def assert_output_equal(
        self, actual_output_jsonable, expected_output_jsonable
    ):
        """
        Allows us to overload the way how the jsonables are compared.

        This is useful in case that you e.g. wish to accept slight variations.
        """
        assert actual_output_jsonable == expected_output_jsonable

    def test_direct_call_possible(self):
        """
        Checks that the worker task logic is working is intended.
        """
        for i, input_jsonable in enumerate(self.input_data_jsonable):
            expected_output_jsonable = self.output_data_jsonable[i]
            input_json = json.dumps(input_jsonable)
            actual_output_json = self.task_to_test(input_json)
            actual_output_jsonable = json.loads(actual_output_json)

            self.assert_output_equal(
                actual_output_jsonable, expected_output_jsonable
            )

    def test_sync_call_possible(self):
        """
        In addition to `test_direct_call_possible` check that the celery
        stuff works too. This should fail if `task_to_test` is not a valid
        celery task (as opposed to `test_direct_call_possible` which may work
        for normal functions too. Credit goes to:
        https://celery.school/unit-testing-celery-tasks#heading-strategy-3-call-the-task-synchronously
        """
        for i, input_jsonable in enumerate(self.input_data_jsonable):
            expected_output_jsonable = self.output_data_jsonable[i]
            input_json = json.dumps(input_jsonable)
            async_result = self.task_to_test.s(input_json).apply()
            actual_output_json = async_result.get()
            actual_output_jsonable = json.loads(actual_output_json)

            self.assert_output_equal(
                actual_output_jsonable, expected_output_jsonable
            )


class GenericFOOCTest(TestClassWithFixtures):
    """
    Rudimentary test for the forecasting or optimization component.

    NOTE: This is very basic, it just checks that the computation is OK, i.e.
          that the computed output matches the expected output. You likely
          want to add more sophisticated tests for your forecasting or
          optimization code.

    Attributes:
    -----------
    fixture_names : list of str
        If provided, any fixture names listed here will be added to all tests.
    InputDataModel : Pydantic model
        The data model used to parse Python data from `input_data_json`.
    payload_function : function
        This the forecasting or optimization code that should be tested.
    OutputDataModel : Pydantic model
        The data model used to serialize whatever is returned by
        `payload_function`.
    input_data_jsonable : list of anything.
        The JSONable representation of the input data that should be
        used for testing.
    output_data_jsonable : list of anything.
        Similar to `input_data_jsonable` but now to expected output
        for each item in the input.
    """

    fixture_names = ()
    InputDataModel = None
    payload_function = None
    OutputDataModel = None
    input_data_jsonable = None
    output_data_jsonable = None

    def assert_output_equal(
        self, actual_output_jsonable, expected_output_jsonable
    ):
        """
        Allows us to overload the way how the jsonables are compared.

        This is useful in case that you e.g. wish to accept slight variations.
        """
        assert actual_output_jsonable == expected_output_jsonable

    def get_payload_function(self):
        """
        Seems that Python doesn't allow us to define `payload_function` as
        an attribute as Python will else treat as class method and add `self`
        to the arguments. Hence, each child of this generic test class will
        need to overload this method to return the actual tested payload
        function.
        """
        raise NotImplementedError("Overload this method to make the test work")

    def test_output_as_expected(self):
        """
        Check that the computed outputs match the expected ones.
        """
        payload_function = self.get_payload_function()
        for i, input_jsonable in enumerate(self.input_data_jsonable):
            expected_output_jsonable = self.output_data_jsonable[i]
            input_data = self.InputDataModel.model_validate(input_jsonable)
            output_data = payload_function(input_data)
            actual_output = self.OutputDataModel.model_validate(output_data)
            actual_output_jsonable = json.loads(actual_output.model_dump_json())

            self.assert_output_equal(
                actual_output_jsonable, expected_output_jsonable
            )


class GenericAPITest:
    """
    Generic Tests for API Instances.

    This basically just verifies that the models are wired up correctly as
    validating the tasks too would require a full integration with the worker.


    Attributes:
    -----------
    tested_api : API instance
        This is the initialized API class that should be tested.
    celery_app : Celery app
        The app that is used by `request_task` and  `fit_parameters_task`
        of the API.
    endpoint : str
        Either `request` or `fit_parameters`.
    InputDataModel : Pydantic model
        The data model used to parse Python data from `input_data_json`.
    OutputDataModel : Pydantic model
        The data model used to serialize whatever is returned by
        `payload_function`.
    input_data_jsonable : list of anything.
        The JSONable representation of the input data that should be
        used for testing.
    output_data_jsonable : list of anything.
        Similar to `input_data_jsonable` but now to expected output
        for each item in the input.
    """

    tested_api = None
    celery_app = None
    endpoint = None
    InputDataModel = None
    OutputDataModel = None
    input_data_jsonable = None
    output_data_jsonable = None

    def setup_method(self):
        """
        Just to make sure typos in endpoint definition are brought to the
        attention of the dev.
        """
        if self.endpoint not in ["request", "fit-parameters"]:
            raise RuntimeError("Invalid endpoint.")

    def setup_class(cls):
        """
        Prevents that API tests block for ca. 30 seconds per test as the
        `wait_for_task_id_available` method waits for a confirmation that
        tasks have been picked up by a worker. However, the latter will never
        happen if the API is tested without the actual worker running.
        """

        async def wait_for_task_mock(*args, **kwargs):
            return

        cls.tested_api.wait_for_task_id_available = wait_for_task_mock

    def test_input_models_correct(self):
        """
        Verify that the configured input data model is able to process
        the input test data.
        """
        with APIInProcess(self.tested_api) as base_url_root:
            client = GenericServiceClient(
                base_url=f"{base_url_root}/",
                endpoint=self.endpoint,
                InputModel=self.InputDataModel,
            )

            # Raises if test API is not accessible.
            client.check_connection()

            # Check no other IDs are stored as this might make the test
            # below pass although it should fail.
            assert len(client.task_ids) == 0

            for i, input_data_jsonable_i in enumerate(self.input_data_jsonable):
                # This will fail (i.e. return a non 200 status code which
                # makes the client raise an exception) if the input model is
                # not set up correctly.
                client.post_jsonable(input_data_jsonable_i)

                # Check that the API returned an ID for the task, which means
                # that processing the data and setting up the task has worked.
                assert len(client.task_ids) == i + 1

    def test_output_models_correct(self):
        """
        Verify that the configured output data model is able to process
        the output test data.

        NOTE: If the output data model is indeed not correctly wired up you will
              likely see this test fail with a HTTP 500 error and this log line:
              "Task computed data not matching the `RequestOutput` model."
        """
        with APIInProcess(self.tested_api) as base_url_root:
            client = GenericServiceClient(
                base_url=f"{base_url_root}/",
                endpoint=self.endpoint,
                InputModel=self.InputDataModel,
            )

            # Raises if test API is not accessible.
            client.check_connection()

            # Prevents possibly wired errors in tests by making sure no other
            # tasks ids are known to the client.
            client.task_ids = []

            in_out_data_jsonable = zip(
                self.input_data_jsonable, self.output_data_jsonable
            )

            task = getattr(
                # The `replace` makes the "fit-parameters" into fit_parameters
                # as this matches the name of the corresponding task in the API.
                self.tested_api,
                f"{self.endpoint}_task".replace("-", "_"),
            )
            for in_data_jsonable, out_data_jsonable in in_out_data_jsonable:

                task_instance = task.delay(
                    input_data_json=json.dumps(in_data_jsonable)
                )

                self.celery_app.backend.mark_as_done(
                    task_instance.id, json.dumps(out_data_jsonable)
                )
                client.task_ids.append(task_instance.id)

            actual_output_data = client.get_results_jsonable()
            assert actual_output_data == self.output_data_jsonable


class GenericEndToEndServiceTests:
    """
    Checks that the service can be used end to end.

    This checks some functionality that is not directly defined by
    the Service but it's parent class. It is checked here again for
    those functions that affect the usage of the service.

    TODO: Refactor this!
            * This should get a URL of the service which must be online already.
            * You need to handle authentication.
            * Add handling of fit parameters by defining which endpoint is used.
            * You might even be able to automatically import the data models,
              which would this test make work out of the box from inside the
              container of a service.
            * The main idea is that this tests checks weather the service
              works. It should issue a valid request, check the status (we
              might introduce a time limit here), and finally fetches the
              result. If everything can be done without errors the service is
              fine.
            * It's not the job of this test to validate that FOOC is implemented
              correctly, this is done by the dedicated FOOC tests.
              Reason: Mocking live service to use certain input data is likely
              not possible with reasonable effort.


    Attributes:
    -----------
    service : Service class instance.
        This is the service class to be tested, e.g. `ExampleService()`
    test_client: fastapi.fastapi.testclient.TestClient instance
        This is the test client to fake service operation.
        E.g. `TestClient(self.service.app)`
    inputs_jsonable : list of dict (JSONable representation)
        A list of input objects that that are presented to the service.
    expected_outputs_jsonable : list of dict (JSONable representation)
        A list of output objects that will be expected to be returned.
    """

    service = None
    test_client = None
    inputs_jsonable = None
    expected_outputs_jsonable = None

    def test_service_root_online(self):
        """
        If this is ok the FastApi app should be able to start up.
        """
        response = self.test_client.get("/")
        assert response.status_code == 200

    def test_request_id_returned(self):
        """
        Verify that upon creating a request we get a request_ID back.
        """
        test_data = zip(self.inputs_jsonable, self.expected_outputs_jsonable)
        for input_data_jsonable, expected_output_data_jsonable in test_data:
            response = self.test_client.post(
                "/request/", data=json.dumps(input_data_jsonable)
            )
            assert response.status_code == 201
            assert "request_ID" in response.model_dump_json()

    def test_status_text_is_returned(self):
        """
        Check that we can access a status text directly after posting a request.
        """
        test_data = zip(self.inputs_jsonable, self.expected_outputs_jsonable)
        for input_data_jsonable, expected_output_data_jsonable in test_data:
            response = self.test_client.post(
                "/request/", data=json.dumps(input_data_jsonable)
            )
            request_ID = response.model_dump_json()["request_ID"]
            response = self.test_client.get(
                "/request/%s/status/" % request_ID,
            )
            assert response.status_code == 200
            assert "status_text" in response.model_dump_json()

    def test_result_can_be_obtained_and_status_becomes_ready(self):
        """
        Validate that the result of the request can be retrieved and contains
        the expected data. Also verify that the status of the request is
        "ready" once the result is available.
        """
        test_data = zip(self.inputs_jsonable, self.expected_outputs_jsonable)
        for input_data_jsonable, expected_output_data_jsonable in test_data:
            response = self.test_client.post(
                "/request/", data=json.dumps(input_data_jsonable)
            )
            request_ID = response.model_dump_json()["request_ID"]
            response = self.test_client.get(
                "/request/%s/result/" % request_ID,
            )
            assert response.status_code == 200
            assert response.model_dump_json() == expected_output_data_jsonable

            # Once the result is ready the status should be set to "ready", it
            # easier to test this way as polling here until ready is set and
            # then retrieve the result as the /request/{request_ID}/result/
            # endpoint should be able to wait until the result is ready.
            response = self.test_client.get(
                "/request/%s/status/" % request_ID,
            )
            assert response.status_code == 200
            assert response.model_dump_json()["status_text"] == "ready"
