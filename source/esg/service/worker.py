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


def execute_payload(
    input_data_json, InputDataModel, payload_function, OutputDataModel
):
    """
    Directly call the payload function.

    This function uses `InputDataModel` to parse `input_data_json` to
    Python data and forwards the data to `payload_function`. Whatever
    the latter returns is serialized with `OutputDataModel`.

    Arguments:
    ----------
    input_data_json : str
        The input data for `payload_function`, not parsed yet.
    InputDataModel : Pydantic model
        The data model used to parse Python data from `input_data_json`.
    payload_function : function
        This the forecasting or optimization code that should be executed
        by the worker.
    OutputDataModel : Pydantic model
        The data model used to serialize whatever is returned by
        `payload_function`.

    Returns:
    --------
    output_data_json : str
        The result serialized as a JSON string.

    TODO: Hardcode a status update to started here? See:
          https://docs.celeryq.dev/en/stable/userguide/configuration.html#std-setting-task_track_started
    """
    input_data = InputDataModel.model_validate_json(input_data_json)
    output_data = payload_function(input_data)
    output_data_json = OutputDataModel.model_validate(
        output_data
    ).model_dump_json()
    return output_data_json
