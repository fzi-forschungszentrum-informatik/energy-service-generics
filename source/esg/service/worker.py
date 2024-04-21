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

from esg.models.base import _BaseModel


def compute_request_input_model(RequestArguments, FittedParameters=None):
    """
    Arguments:
    ----------
    RequestArguments : pydantic model
        A model defining the structure of the  arguments that are required
        to compute a request.
    FittedParameters : pydantic model
        A model defining the structure of the fitted parameters required
        to compute a request.

    Returns:
    --------
    RequestInput : pydantic model
        A Model defining the structure and documentation of the input data,
        i.e. the data that is necessary to process a request.
    """
    if FittedParameters is not None:

        class RequestInput(_BaseModel):
            arguments: RequestArguments
            parameters: FittedParameters

    else:

        class RequestInput(_BaseModel):
            arguments: RequestArguments

    return RequestInput


def compute_fit_parameters_input_model(
    FitParametersArguments, FitParametersObservations
):
    """
    Arguments:
    ----------
    FitParametersArguments : pydantic model
        A model defining the structure of the  arguments that are required
        to fit the parameters.
    FitParametersObservations : pydantic model
        A model defining the structure of the true observed data used for
        fitting the parameters.

    Returns:
    --------
    FitParametersInput : pydantic model
        A Model defining the structure and documentation of the input data,
        i.e. the data that is necessary to fit the parameters.
    """

    class FitParametersInput(_BaseModel):
        arguments: FitParametersArguments
        observations: FitParametersObservations

    return FitParametersInput


def compute_fit_parameters_output_model(FittedParameters):
    """
    Arguments:
    ----------
    FittedParameters : pydantic model
        A model defining the structure of the fitted parameters required
        to compute a request.

    Returns:
    --------
    FitParametersOutput : pydantic model
        A Model defining the structure and documentation of the output data
        emitted by the fit-parameters process.
    """

    class FitParametersOutput(_BaseModel):
        parameters: FittedParameters

    return FitParametersOutput


def execute_payload(
    input_data_json, InputDataModel, payload_function, OutputDataModel
):
    """
    Invoke the payload function and manage JSON de-/serialization.

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
    TODO: Add two additional optional arguments `input_data_split_function`
          and `output_data_merge_function`. If both a provided split the input
          and apply it to payload function one by one. In this case push
          intermediate updates of the status too. You might even expand this
          later with a functionality that detects if payload_function is
          actually a celery task, in which case we could submit all jobs at
          once and collect the results.
    TODO: Check the docstrings.
    """
    input_data = InputDataModel.model_validate_json(input_data_json)
    output_data = payload_function(input_data)
    output_data_json = OutputDataModel.model_validate(
        output_data
    ).model_dump_json()
    return output_data_json


def execute_handle_request(
    input_data_json,
    RequestArguments,
    handle_request_function,
    RequestOutput,
    FittedParameters=None,
):
    """
    Invoke `execute_payload` but with models adapted for the request case.

    Arguments:
    ----------
    input_data_json : str
        The input data for `handle_request_function`, not parsed yet.
    RequestArguments : pydantic model
        A model defining the structure of the  arguments that are required
        to compute a request.
    FittedParameters : pydantic model
        A model defining the structure of the fitted parameters required
        to compute a request.
    handle_request_function : function
        This the forecasting or optimization code that should be executed
        by the worker.
    RequestOutput : Pydantic model
        A model defining the structure of response data to requests.

    Returns:
    --------
    output_data_json : str
        The result serialized as a JSON string.
    """
    RequestInputModel = compute_request_input_model(
        RequestArguments=RequestArguments,
        FittedParameters=FittedParameters,
    )
    output_data_json = execute_payload(
        InputDataModel=RequestInputModel,
        input_data_json=input_data_json,
        payload_function=handle_request_function,
        OutputDataModel=RequestOutput,
    )
    return output_data_json
