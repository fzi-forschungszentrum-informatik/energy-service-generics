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

import json

from pydantic import BaseModel
from pydantic import ValidationError
import pytest
from typing import List

from esg.models.base import _BaseModel
from esg.service.worker import compute_request_input_model
from esg.service.worker import compute_fit_parameters_input_model
from esg.service.worker import compute_fit_parameters_output_model
from esg.service.worker import execute_payload
from esg.service.worker import execute_handle_request

from data_model import FittedParameters
from data_model import FitParametersArguments
from data_model import FitParametersObservations
from data_model import fit_parameters
from data_model import handle_request
from data_model import RequestArguments
from data_model import RequestOutput


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
            arguments: FitParametersArguments
            observations: FitParametersObservations

        expected_schema = FitParametersInput.model_json_schema()

        ActualModel = compute_fit_parameters_input_model(
            FitParametersArguments=FitParametersArguments,
            FitParametersObservations=FitParametersObservations,
        )
        actual_schema = ActualModel.model_json_schema()

        assert actual_schema == expected_schema


class TestComputeFitParametersOutputModel:
    """
    Tests for `esg.service.worker.compute_fit_parameters_output_model`.
    """

    def test_model_correct(self):
        """
        Check that the model is correct for the standard case.
        """

        class FitParametersOutput(_BaseModel):
            parameters: FittedParameters

        expected_schema = FitParametersOutput.model_json_schema()

        ActualModel = compute_fit_parameters_output_model(
            FittedParameters=FittedParameters,
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


class TestExecuteHandleRequest:
    """
    Tests for `esg.service.worker.execute_handle_request`
    """

    def test_without_parameters(self):
        """
        Test `execute_handle_request` with a practical example. The edge
        cases should already be handled by the tests for `execute_payload`.
        """
        input_data_json = json.dumps({"arguments": {"ints": [1, 2, 3, 4]}})
        expected_output_data_jsonable = {"weighted_sum": 10}

        actual_output_data_json = execute_handle_request(
            input_data_json=input_data_json,
            RequestArguments=RequestArguments,
            handle_request_function=handle_request,
            RequestOutput=RequestOutput,
        )
        actual_output_data_jsonable = json.loads(actual_output_data_json)

        assert actual_output_data_jsonable == expected_output_data_jsonable

    def test_with_parameters(self):
        """
        Test `execute_handle_request` with a practical example. The edge
        cases should already be handled by the tests for `execute_payload`.
        """
        input_data_json = json.dumps(
            {
                "arguments": {"ints": [1, 2, 3, 4]},
                "parameters": {"weights": [1, 2, 1, 1]},
            },
        )
        expected_output_data_jsonable = {"weighted_sum": 12}

        actual_output_data_json = execute_handle_request(
            input_data_json=input_data_json,
            RequestArguments=RequestArguments,
            FittedParameters=FittedParameters,
            handle_request_function=handle_request,
            RequestOutput=RequestOutput,
        )
        actual_output_data_jsonable = json.loads(actual_output_data_json)

        assert actual_output_data_jsonable == expected_output_data_jsonable


class TestExecuteFitParameters:
    """
    Tests for `esg.service.worker.execute_fit_parameters`

    TODO !
    """
