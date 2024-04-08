"""
Generic definitions of task related data types (aka. messages)
in pydantic for serialization (e.g. to JSON) and for auto generation
of endpoint schemas in services.

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

from enum import Enum
from uuid import UUID
from typing import Optional

from pydantic import Field
from typing import Dict
from typing import List

from esg.models.base import _BaseModel


class TaskId(_BaseModel):
    """
    This is the expected response for the POST /task/ endpoint.
    """

    task_ID: UUID = Field(
        None,
        description=(
            "The ID of the created task. Must use this ID to task "
            "the status or result of the task."
        ),
    )


class TaskStatusTextEnum(str, Enum):
    """
    The three states in which the task can be.

    The result can be retrieved immediately if the state is `ready`.
    Otherwise tasking the result will block until the result is ready.
    """

    queued = "queued"
    running = "running"
    ready = "ready"


class TaskStatus(_BaseModel):
    """
    The expected response for the GET /task/{task_id}/status/ endpoint.
    """

    status_text: TaskStatusTextEnum = Field(
        None,
        examples=["running"],
    )
    percent_complete: Optional[float] = Field(
        None,
        examples=[27.1],
        description=(
            "An estimate how much of the task has already been processed "
            "in percent. Is `null` if the service does not provide this "
            "information."
        ),
    )
    ETA_seconds: Optional[float] = Field(
        None,
        examples=[15.7],
        description=(
            "An estimate how long it will take until the task is completely "
            "processed. Is `null` if the service cannot (maybe only "
            "temporarily) provide such an estimate."
        ),
    )


###############################################################################
#
# It should not be necessary to use these model directly. They are mainly here
# to allow completing the API schema with the error messages.
#
###############################################################################


class HTTPError(_BaseModel):
    """
    This is the default FastAPI format for error messages.
    """

    detail: str = Field(examples=["Some error message."])


class HTTPValidationErrorDetail(_BaseModel):
    """
    This format results from the `request_validation_exception_handler`
    function of FastAPI which returns the output of the pydantic validation
    error directly parsed as JSON. See here:
    https://github.com/tiangolo/fastapi/blob/0.110.0/fastapi/exception_handlers.py#L20
    """

    type: str = Field(
        title="Error Type",
        examples=["missing"],
    )
    loc: List[str] = Field(
        title="Location",
        examples=[["test1"]],
    )
    msg: str = Field(
        title="Message",
        examples=["Field required"],
    )
    input: Optional[Dict[str, str]] = Field(
        examples=[{"noFieldInModel": "foo bar"}],
        description=(
            "Specifies which part of the input has caused the error. "
            "May not be available if validation is carried out with older "
            "versions of pydantic."
        ),
    )
    url: Optional[str] = Field(
        examples=["https://errors.pydantic.dev/2.6/v/missing"],
        description=(
            "URL supplying additional help for this error. "
            "May not be available if validation is carried out with older "
            "versions of pydantic."
        ),
    )


class HTTPValidationError(_BaseModel):
    """
    This is the error format for validation errors used by FastAPI.
    """

    detail: HTTPValidationErrorDetail
