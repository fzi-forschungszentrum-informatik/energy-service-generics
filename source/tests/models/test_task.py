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

import uuid
import json

from esg.models import task


class TestTaskId:
    def test_data_to_json(self):
        """
        Test conversion to JSON for all fields.
        """
        expected_json_content = {
            "task_ID": str(uuid.uuid1()),
        }
        actual_json = task.TaskId(**expected_json_content).model_dump_json()
        assert json.loads(actual_json) == expected_json_content

    def test_json_to_data(self):
        """
        Test JSON can be parsed to Python objects.
        """
        test_uuid = str(uuid.uuid1())
        test_json = """
            {
                "task_ID": "%s"
            }
        """
        test_json = test_json % test_uuid
        expected_data = {
            "task_ID": test_uuid,
        }
        actual_data = task.TaskId.model_validate_json(test_json)
        assert actual_data == task.TaskId(**expected_data)


class TestTaskStatus:
    def test_data_to_json(self):
        """
        Test conversion to JSON for all fields.
        """
        expected_json_content = {
            "status_text": "running",
            "percent_complete": 27.1,
            "ETA_seconds": 15.7,
        }
        actual_json = task.TaskStatus(**expected_json_content).model_dump_json()
        assert json.loads(actual_json) == expected_json_content

    def test_json_to_data(self):
        """
        Test JSON can be parsed to Python objects.
        """
        test_json = """
            {
                "status_text": "running",
                "percent_complete": 27.1,
                "ETA_seconds": 15.7
            }
        """
        expected_data = {
            "status_text": "running",
            "percent_complete": 27.1,
            "ETA_seconds": 15.7,
        }
        actual_data = task.TaskStatus.model_validate_json(test_json)
        assert actual_data.model_dump() == expected_data

    def test_data_to_json_without_optional(self):
        """
        Test conversion to JSON if only non optional values are provided.
        """
        expected_json_content = {
            "status_text": "running",
            "percent_complete": None,
            "ETA_seconds": None,
        }
        actual_json = task.TaskStatus(
            status_text=expected_json_content["status_text"]
        ).model_dump_json()
        print(actual_json)
        assert json.loads(actual_json) == expected_json_content

    def test_json_to_data_without_optional(self):
        """
        Test JSON can be parsed to Python objects even if only non optional
        values are given in the JSON.
        """
        test_json = """
            {
                "status_text": "running"
            }
        """
        expected_data = {
            "status_text": "running",
            "percent_complete": None,
            "ETA_seconds": None,
        }
        actual_data = task.TaskStatus.model_validate_json(test_json)
        assert actual_data.model_dump() == expected_data
