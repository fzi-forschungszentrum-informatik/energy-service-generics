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

from esg.models import task
from esg.test import data as td
from esg.test.generic_tests import GenericMessageSerializationTest


class TestTaskId(GenericMessageSerializationTest):

    ModelClass = task.TaskId
    msgs_as_python = [m["Python"] for m in td.task_ids]
    msgs_as_jsonable = [m["JSONable"] for m in td.task_ids]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_task_ids]


class TestTaskStatus(GenericMessageSerializationTest):

    ModelClass = task.TaskStatus
    msgs_as_python = [m["Python"] for m in td.task_statuses]
    msgs_as_jsonable = [m["JSONable"] for m in td.task_statuses]
    invalid_msgs_as_jsonable = [m["JSONable"] for m in td.invalid_task_statuses]
