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

import os
from pathlib import Path

# To prevent tests from failing if only parts of the package are used.
try:
    from celery import Celery

except ModuleNotFoundError:
    Celery = None

from esg.models.base import _BaseModel


def celery_app_from_environ():
    """
    Instantiates a Celery app with configuration loaded from environment vars.

    NOTE: This is an incomplete set of settings. For a more generic approach
          you may want to implement something like this approach here:
          https://celery.school/celery-config-env-vars
    """
    name = os.getenv("CELERY__NAME")
    if not name:
        raise ValueError(
            "No name for the celery app defined. Try setting the "
            "`CELERY__NAME` environment variable to non empty string"
        )

    # Set some option which seem generally useful for all transport types.
    generic_useful_options = {
        # Seems sane to retry the connection, might be that the container
        # of a potential broker takes longer to boot then the worker.
        # Besides, if we don't set this explicitly we'll get a super
        # annoying deprecation warning in the logs. See for details:
        # https://docs.celeryq.dev/en/stable/userguide/configuration.html#broker-connection-retry-on-startup
        "broker_connection_retry_on_startup": True,
        # No running state (will 404 instead) of tasks without this option.
        # Background is that the `STARTED` state is not communicated by default.
        # See further:
        # https://docs.celeryq.dev/en/latest/userguide/tasks.html#started
        # as well as:
        # https://github.com/fzi-forschungszentrum-informatik/energy-service-generics/blob/3a7c91d4dd0c6b245c780051d43b8f60606c01c0/source/esg/service/api.py#L72
        "task_track_started": True,
    }

    broker_url = os.getenv("CELERY__BROKER_URL")
    result_backend = os.getenv("CELERY__RESULT_BACKEND")
    if not broker_url:
        raise ValueError(
            "Broker URL not defined. Try setting the "
            "`CELERY__BROKER_URL` environment variable to non empty string"
        )
    elif broker_url == "filesystem://":
        # The CELERY__FS_TRANSPORT_BASE_FOLDER replaces the need to parse
        # redundant information for `broker_transport_options` and
        # `result_backend`
        base_folder = os.getenv("CELERY__FS_TRANSPORT_BASE_FOLDER")
        if not base_folder:
            raise ValueError("CELERY__FS_TRANSPORT_BASE_FOLDER can't be empty.")

        # Create the necessary sub-folders.
        broker_folder = Path(base_folder) / "broker"
        broker_folder.mkdir(parents=True, exist_ok=True)
        results_folder = Path(base_folder) / "results"
        results_folder.mkdir(parents=True, exist_ok=True)

        app = Celery(
            name,
            broker_url="filesystem://",
            broker_transport_options={
                "data_folder_in": f"{broker_folder}/",
                "data_folder_out": f"{broker_folder}/",
            },
            result_backend=f"file://{results_folder}/",
            **generic_useful_options,
        )
        return app
    elif result_backend:
        # Result backend specified? Ok use whatever is there.
        app = Celery(
            name,
            broker_url=broker_url,
            result_backend=result_backend,
            **generic_useful_options,
        )
        return app
    elif "amqp://" in broker_url:
        # AMQP and no results backend? -> Use AMQP as results backend too.
        app = Celery(
            name,
            broker_url=broker_url,
            result_backend="rpc://",
            **generic_useful_options,
        )
        return app
    else:
        raise ValueError(
            f'`CELERY__BROKER_URL` set to `"{broker_url}"` which is not '
            "recognized as valid option by `celery_app_from_environ`. Check "
            "the source of the function for valid options."
        )


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


def compute_fit_parameters_input_model(FitParameterArguments, Observations):
    """
    Arguments:
    ----------
    FitParameterArguments : pydantic model
        A model defining the structure of the  arguments that are required
        to fit the parameters.
    Observations : pydantic model
        A model defining the structure of the true observed data used for
        fitting the parameters.

    Returns:
    --------
    FitParametersInput : pydantic model
        A Model defining the structure and documentation of the input data,
        i.e. the data that is necessary to fit the parameters.
    """

    class FitParametersInput(_BaseModel):
        arguments: FitParameterArguments
        observations: Observations

    return FitParametersInput


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
    """
    input_data = InputDataModel.model_validate_json(input_data_json)
    output_data = payload_function(input_data)
    output_data_json = OutputDataModel.model_validate(
        output_data
    ).model_dump_json()
    return output_data_json


def invoke_handle_request(
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
    InputModel = compute_request_input_model(
        RequestArguments=RequestArguments,
        FittedParameters=FittedParameters,
    )
    output_data_json = execute_payload(
        InputDataModel=InputModel,
        input_data_json=input_data_json,
        payload_function=handle_request_function,
        OutputDataModel=RequestOutput,
    )
    return output_data_json


def invoke_fit_parameters(
    input_data_json,
    FitParameterArguments,
    Observations,
    fit_parameters_function,
    FittedParameters,
):
    """
    Invoke `execute_payload` but with models adapted for the request case.

    Arguments:
    ----------
    input_data_json : str
        The input data for `handle_request_function`, not parsed yet.
    FitParameterArguments : pydantic model
        A model defining the structure of the  arguments that are required
        to fit the parameters.
    Observations : pydantic model
        A model defining the structure of the true observed data used for
        fitting the parameters.
    fit_parameters_function : function
        This the code that fits the parameters that should be executed
        by the worker.
    FittedParameters : pydantic model
        A model defining the structure of the fitted parameters required
        to compute a request.

    Returns:
    --------
    output_data_json : str
        The result serialized as a JSON string.
    """
    InputModel = compute_fit_parameters_input_model(
        FitParameterArguments=FitParameterArguments, Observations=Observations
    )
    output_data_json = execute_payload(
        InputDataModel=InputModel,
        input_data_json=input_data_json,
        payload_function=fit_parameters_function,
        OutputDataModel=FittedParameters,
    )
    return output_data_json
