"""
Tests for `esg.service.worker`

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
from pathlib import Path

from pydantic import BaseModel
from pydantic import ValidationError
import pytest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from typing import List

# To prevent tests from failing if only parts of the package are used.
try:
    from celery import Celery

    service_extra_not_installed = False
except ModuleNotFoundError:
    Celery = None
    service_extra_not_installed = True

from esg.models.base import _BaseModel
from esg.service.worker import celery_app_from_environ
from esg.service.worker import compute_request_input_model
from esg.service.worker import compute_fit_parameters_input_model
from esg.service.worker import execute_payload
from esg.service.worker import invoke_handle_request
from esg.service.worker import invoke_fit_parameters

from data_model import FittedParameters
from data_model import FitParameterArguments
from data_model import Observations
from data_model import fit_parameters
from data_model import handle_request
from data_model import RequestArguments
from data_model import RequestOutput


@pytest.mark.skipif(
    service_extra_not_installed,
    reason="requires installation with `service` extra.",
)
class TestCeleryAppFromEnviron:
    """
    Tests for `esg.service.worker.celery_app_from_environ`.
    """

    def test_no_name_raises(self):
        """
        Celery must have a name to prevent clashes if several services use the
        same transport.
        """
        with patch.dict(os.environ, {}):
            with pytest.raises(ValueError) as exc_info:
                celery_app_from_environ()

            assert "CELERY__NAME" in str(exc_info.value)

    def test_empty_fs_folder_raises(self):
        """
        Can't have a filesystem transport if the corresponding folder is not
        created.
        """
        test_environ = {
            "CELERY__NAME": "test",
            "CELERY__BROKER_URL": "filesystem://",
        }
        with patch.dict(os.environ, test_environ):
            with pytest.raises(ValueError) as exc_info:
                celery_app_from_environ()
            assert "CELERY__FS_TRANSPORT_BASE_FOLDER" in str(exc_info.value)

    def test_empty_broker_url_raises(self):
        """
        The broker URL is THE variable on which the app is configured. Thus,
        it can't be empty.
        """
        test_environ = {
            "CELERY__NAME": "test",
        }
        with patch.dict(os.environ, test_environ):
            with pytest.raises(ValueError) as exc_info:
                celery_app_from_environ()
            assert "CELERY__BROKER_URL" in str(exc_info.value)

    def test_unknown_broker_url_raises(self):
        """
        The broker URL is THE variable on which the app is configured. Thus,
        it must take one of the well defined values.
        """
        test_environ = {
            "CELERY__NAME": "test",
            "CELERY__BROKER_URL": "definitely not supported",
        }
        with patch.dict(os.environ, test_environ):
            with pytest.raises(ValueError) as exc_info:
                celery_app_from_environ()
            assert "CELERY__BROKER_URL" in str(exc_info.value)

    @staticmethod
    def verify_generic_options_in_app(app):
        """
        Prevents redundant code by allowing several functions to check if the
        `generic_useful_options` have been forwarded to the Celery app.
        """
        assert app.conf.broker_connection_retry_on_startup is True

    def test_fs_transport_creates_folders_and_returns_app(self):
        """
        This is the desired aspect for filesystem transport, that the folders
        are created and the app configured.
        """
        with TemporaryDirectory() as tmp_dir:

            # Check that the folders exist not yet
            tmp_dir_path = Path(tmp_dir)
            broker_path = tmp_dir_path / "broker"
            results_path = tmp_dir_path / "results"
            assert broker_path.is_dir() is False
            assert results_path.is_dir() is False

            test_environ = {
                "CELERY__NAME": "test_name",
                "CELERY__BROKER_URL": "filesystem://",
                "CELERY__FS_TRANSPORT_BASE_FOLDER": tmp_dir,
            }
            with patch.dict(os.environ, test_environ):
                app = celery_app_from_environ()

            # Check that the folders have been created.
            assert broker_path.is_dir()
            assert results_path.is_dir()

            # Check that we have received a Celery app.
            assert isinstance(app, Celery)

            # Check that the expected settings have been set.
            assert app.main == "test_name"
            assert app.conf.broker_url == "filesystem://"
            assert app.conf.broker_transport_options == {
                "data_folder_in": f"{broker_path}/",
                "data_folder_out": f"{broker_path}/",
            }
            assert app.conf.result_backend == f"file://{results_path}/"

            # Finally, check for the generic options.
            self.verify_generic_options_in_app(app)


class TestComputeRequestInputModel:
    """
    Tests for `esg.service.worker.compute_request_input_model`.
    """

    def test_model_correct_for_request_args_and_fitted_parameters(self):
        """
        Check that the model is correct if both args are provided.
        """

        class RequestInput(_BaseModel):
            arguments: RequestArguments
            parameters: FittedParameters

        expected_schema = RequestInput.model_json_schema()

        ActualModel = compute_request_input_model(
            RequestArguments=RequestArguments,
            FittedParameters=FittedParameters,
        )
        actual_schema = ActualModel.model_json_schema()

        assert actual_schema == expected_schema

    def test_model_correct_for_request_args_only(self):
        """
        Check that the model is correct if only request args model is provided.
        """

        class RequestInput(_BaseModel):
            arguments: RequestArguments

        expected_schema = RequestInput.model_json_schema()

        ActualModel = compute_request_input_model(
            RequestArguments=RequestArguments
        )
        actual_schema = ActualModel.model_json_schema()

        assert actual_schema == expected_schema


class TestComputeFitParametersInputModel:
    """
    Tests for `esg.service.worker.compute_fit_parameters_input_model`.
    """

    def test_model_correct(self):
        """
        Check that the model is correct for the standard case.
        """

        class FitParametersInput(_BaseModel):
            arguments: FitParameterArguments
            observations: Observations

        expected_schema = FitParametersInput.model_json_schema()

        ActualModel = compute_fit_parameters_input_model(
            FitParameterArguments=FitParameterArguments,
            Observations=Observations,
        )
        actual_schema = ActualModel.model_json_schema()

        assert actual_schema == expected_schema


class TestExecutePayload:
    """
    Tests for `esg.service.worker.execute_payload`
    """

    class DemoInputDataModel(BaseModel):
        ints: List[int]

    class DemoOutputDataModel(BaseModel):
        sum: int

    @staticmethod
    def demo_payload_function(input_data):
        _sum = 0
        for i in input_data.ints:
            _sum += i
        return {"sum": _sum}

    def test_end_to_end(self):
        """
        The functionality of `execute_payload` is rather limited.
        Thus, this tests checks all the basic functionality, i.e. that:
          * the input is parsed.
          * the payload function is called.
          * the output is serialized.
        """
        input_data_json = json.dumps({"ints": [1, 2, 3, 4]})
        expected_output_data_jsonable = {"sum": 10}

        actual_output_data_json = execute_payload(
            input_data_json=input_data_json,
            InputDataModel=self.DemoInputDataModel,
            payload_function=self.demo_payload_function,
            OutputDataModel=self.DemoOutputDataModel,
        )
        actual_output_data_jsonable = json.loads(actual_output_data_json)

        assert actual_output_data_jsonable == expected_output_data_jsonable

    def test_input_data_model_used(self):
        """
        Verify that the `InputDataModel` is utilized.
        """
        input_data_json = json.dumps({"ints": "not an int"})

        with pytest.raises(ValidationError):
            _ = execute_payload(
                input_data_json=input_data_json,
                InputDataModel=self.DemoInputDataModel,
                payload_function=self.demo_payload_function,
                OutputDataModel=self.DemoOutputDataModel,
            )

    def test_output_data_model_used(self):
        """
        Verify that the `OutputDataModel` is utilized.
        """
        input_data_json = json.dumps({"ints": [1, 2, 3, 4]})

        def payload_function_non_conform_output(input_data):
            return {"sum": "not an int"}

        with pytest.raises(ValidationError):
            _ = execute_payload(
                input_data_json=input_data_json,
                InputDataModel=self.DemoInputDataModel,
                payload_function=payload_function_non_conform_output,
                OutputDataModel=self.DemoOutputDataModel,
            )


class TestInvokeHandleRequest:
    """
    Tests for `esg.service.worker.invoke_handle_request`
    """

    def test_without_parameters(self):
        """
        Test `invoke_handle_request` with a practical example. The edge
        cases should already be handled by the tests for `execute_payload`.
        """
        input_data_json = json.dumps({"arguments": {"ints": [1, 2, 3, 4]}})
        expected_output_data_jsonable = {"weighted_sum": 10}

        actual_output_data_json = invoke_handle_request(
            input_data_json=input_data_json,
            RequestArguments=RequestArguments,
            handle_request_function=handle_request,
            RequestOutput=RequestOutput,
        )
        actual_output_data_jsonable = json.loads(actual_output_data_json)

        assert actual_output_data_jsonable == expected_output_data_jsonable

    def test_with_parameters(self):
        """
        Test `invoke_handle_request` with a practical example. The edge
        cases should already be handled by the tests for `execute_payload`.
        """
        input_data_json = json.dumps(
            {
                "arguments": {"ints": [1, 2, 3, 4]},
                "parameters": {"weights": [1, 2, 1, 1]},
            },
        )
        expected_output_data_jsonable = {"weighted_sum": 12}

        actual_output_data_json = invoke_handle_request(
            input_data_json=input_data_json,
            RequestArguments=RequestArguments,
            FittedParameters=FittedParameters,
            handle_request_function=handle_request,
            RequestOutput=RequestOutput,
        )
        actual_output_data_jsonable = json.loads(actual_output_data_json)

        assert actual_output_data_jsonable == expected_output_data_jsonable


class TestInvokeFitParameters:
    """
    Tests for `esg.service.worker.invoke_fit_parameters`
    """

    def test_fit_called(self):
        """
        Test `invoke_fit_parameters` with a practical example. The edge
        cases should already be handled by the tests for `execute_payload`.
        """
        input_data_json = json.dumps(
            {
                "arguments": [{"ints": [1, 2, 3, 4]}, {"ints": [6, 7, 8, 9]}],
                "observations": [{"weighted_sum": 30}, {"weighted_sum": 80}],
            },
        )
        expected_output_data_jsonable = {"weights": [1, 2, 3, 4]}
        actual_output_data_json = invoke_fit_parameters(
            input_data_json=input_data_json,
            FitParameterArguments=FitParameterArguments,
            Observations=Observations,
            fit_parameters_function=fit_parameters,
            FittedParameters=FittedParameters,
        )
        actual_output_data_jsonable = json.loads(actual_output_data_json)

        assert actual_output_data_jsonable == expected_output_data_jsonable
