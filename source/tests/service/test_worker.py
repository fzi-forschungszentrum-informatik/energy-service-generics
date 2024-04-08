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

from esg.service.worker import execute_payload


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
