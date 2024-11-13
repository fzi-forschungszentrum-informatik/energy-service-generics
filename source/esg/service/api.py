"""
The generic parts of the API component of services.

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
import sys
import json
import logging
from unittest.mock import patch
from uuid import UUID
from typing import Annotated

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import Response
from fastapi.security.open_id_connect_url import OpenIdConnect
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

# To prevent tests from failing if only parts of the package are used.
try:
    from celery import states
    from celery.result import AsyncResult
    from prometheus_fastapi_instrumentator import Instrumentator
    import uvicorn
except ModuleNotFoundError:
    states = None
    AsyncResult = None
    Instrumentator = None
    uvicorn = None

from esg.models.task import HTTPError
from esg.models.task import HTTPValidationError
from esg.models.task import TaskId
from esg.models.task import TaskStatus
from esg.service.exceptions import GenericUnexpectedException
from esg.service.worker import compute_fit_parameters_input_model
from esg.service.worker import compute_request_input_model
from esg.utils.jwt import AccessTokenChecker


# Map the built in states of celery to the state definitions of service
# framework. The internal states of celery are documented here:
# https://docs.celeryq.dev/en/stable/userguide/tasks.html#task-states
# NOTE: There is an additional `states.REVOKED` status which is not
#       considered here as the service framework has no functionality
#       to cancel tasks. This might change in future.
# NOTE: Celery matches an unknown ID to the pending state. PENDING is
#       hence not included here.
if states is not None:
    TASK_STATUS_MAP = {
        states.STARTED: "running",
        states.SUCCESS: "ready",
        states.FAILURE: "ready",
        states.RETRY: "queued",
    }
else:
    # Prevents tests from failing if only parts of the package are used.
    TASK_STATUS_MAP = None


class FastAPIExtendedModels(FastAPI):
    """
    A simple extension to FastAPI that allows manually adding models to
    the OpenAPI schema.
    """

    def __init__(self, *args, post_body_models_by_path=None, **kwargs):
        """
        Arguments:
        ----------
        post_body_models_by_path : dict[path, Pydantic Model]
            The models that should be added by the path they should be added
            to. E.g. {"/fit-parameters/"): SomeModel}. Only for Models that
            describe the body of a post call.
        """
        super().__init__(*args, **kwargs)
        if post_body_models_by_path is None:
            post_body_models_by_path = {}
        self.post_body_models_by_path = post_body_models_by_path

    def openapi(self):
        """
        Add code to add models to the `openapi` method of `FastAPI`.

        See the FastAPI code here to understand what's going on.
        https://github.com/tiangolo/fastapi/blob/a94ef3351e0a25ffa45d131b9ba9b0f7f7c31fe5/fastapi/applications.py#L966C9-L966C22
        """
        if not self.openapi_schema:
            super().openapi()

            paths = self.openapi_schema["paths"]
            for path, model in self.post_body_models_by_path.items():
                model_schema = model.model_json_schema(
                    ref_template="#/components/schemas/{model}"
                )
                model_defs = model_schema.pop("$defs")
                paths[path]["post"]["requestBody"] = {
                    "content": {"application/json": {"schema": model_schema}}
                }
                self.openapi_schema["components"]["schemas"].update(model_defs)

        return self.openapi_schema


class API:
    """
    API component for services that implements the `/request/` endpoints.

    Attributes:
    -----------
    post_request_responses : dict
        Allows defining additional responses for the POST /request/ endpoint.
        This information is solely used for extending the API schema.
    get_request_status_responses : dict
        Like above but for GET /request/{request_ID}/status/
    get_request_result_responses : dict
        Like above but for GET /request/{request_ID}/result/
    post_request_description : string
        Allows defining the description text for the POST /request/ endpoint.
        This information is solely used for extending the API schema.
    get_request_status_description : dict
        Like above but for GET /request/{request_ID}/status/
    get_request_result_description : dict
        Like above but for GET /request/{request_ID}/result/

    """

    # Manually add the validation error back to responses. FastAPI usually
    # adds this response automatically but does not so if the endpoint
    # uses `Response` as argument instead of models, which is the case for
    # the post methods of the API.
    post_request_responses = {
        422: {
            "model": HTTPValidationError,
            "description": "Validation Error.",
        }
    }

    # This endpoint should only fail if the ID is unknown.
    get_request_status_responses = {
        404: {
            "model": HTTPError,
            "description": "No task with the provided ID exists.",
        }
    }

    # Besides the 404 it could also happen that an error during processing
    # the request occurred. See the docstrings of `GenericUnexpectedException`
    # and `RequestInducedException` for details.
    get_request_result_responses = {
        # NOTE: This should not happen, it means that the input validation
        #       has failed. If you want to reenable this add a test that checks
        #       that `RequestInducedException` thrown in a task is forwarded
        #       to the API and raised there again.
        # 400: {
        #     "model": HTTPError,
        #     "description": (
        #         "Returned if processing the task yields an error that "
        #         "is related to the request arguments. The detail string "
        #         "provides additional information on the error source."
        #     ),
        # },
        404: get_request_status_responses[404],
        409: {
            "model": HTTPError,
            "description": ("The task is not ready yet."),
        },
        500: {
            "model": HTTPError,
            "description": (
                "Processing the task has caused some unexpected "
                "error. Please contact the provider of the service for "
                "support."
            ),
        },
    }

    # By default, the responses for the request endpoint should be fine
    # for the fit parameters endpoints too.
    post_fit_parameters_responses = post_request_responses.copy()
    get_fit_parameters_status_responses = get_request_status_responses.copy()
    get_fit_parameters_result_responses = get_request_result_responses.copy()

    # Here the description texts for the six endpoints. FastAPI uses
    # the docstrings by default. However, these contain a lot if internal
    # stuff that is not relevant for the user. Hence the here the option
    # to set these explicitly.
    post_request_description = (
        "Create a request task (for e.g. a forecast or optimized schedule) "
        "that is computed in the background."
    )
    get_request_status_description = "Return the status of a request task."
    get_request_result_description = "Return the result of a request task."
    post_fit_parameters_description = (
        "Create a task to fit parameters in the background."
    )
    get_fit_parameters_status_description = (
        "Return the status of a fit parameters task."
    )
    get_fit_parameters_result_description = (
        "Return the result of a fit parameters task."
    )

    def __init__(
        self,
        RequestArguments,
        RequestOutput,
        request_task,
        title,
        FitParameterArguments=None,
        Observations=None,
        FittedParameters=None,
        fit_parameters_task=None,
        description=None,
        version_root_path=None,
        fastapi_kwargs={},
    ):
        """
        Init basic stuff like the logger and configure the REST API.

        Configuration is partly taken from arguments and partly from
        environment variables. Here anything that is likely be set in the
        source code of the derived service is expected as argument. Any
        configuration that users want to change for single instances of
        the services are environment variables, e.g. the log level or
        credentials.

        Environment variables:
        ----------------------
        LOGLEVEL : str
            The loglevel to use for *all* loggers. Defaults to logging.INFO.
        VERSION : str
            The version of the service. Is used to extend the schema
            documentation and to check the `ROOT_PATH`.
        ROOT_PATH : str
            Allows serving the service under a subpath, e.g.
            `"https://example.com/service-1/v1/"` would require setting
            `ROOT_PATH` to `"/service-1/v1/"`. Note that by convention we
            require the last element of the root path to contain the major
            part of the version number.
        AUTH_JWT_ISSUER : str
            The service will only allow access with a valid JWT token
            if this variable is set. Corresponds to `expected_issuer`
            argument of `esg.utils.jwt.AccessTokenChecker`. See docstring
            there for details.
        AUTH_JWT_AUDIENCE : str
            Only used if `AUTH_JWT_ISSUER` is set. Corresponds to
            `expected_audience` argument of `esg.utils.jwt.AccessTokenChecker`.
            See docstring there for details.
        AUTH_JWT_ROLE_CLAIM : list of str as JSON encoded str
            Only used if `AUTH_JWT_ISSUER` is set. Corresponds to
            `expected_role_claim` arg of `esg.utils.jwt.AccessTokenChecker`.
            See docstring there for details.
        AUTH_JWT_ROLES : list of str as JSON encoded str
            Only used if `AUTH_JWT_ISSUER` is set. Corresponds to
            `expected_roles` argument of `esg.utils.jwt.AccessTokenChecker`.
            See docstring there for details.

        Arguments:
        ----------
        RequestArguments : pydantic model
            A model defining the structure of the  arguments that are required
            to compute a request.
        RequestOutput : pydantic model
            A Model defining the structure and documentation of the output data,
            i.e. the result of the request.
        request_task : Celery task
            This is the function that is called to process calls to the
            POST /request/ endpoint. Note that this function must be wrapped
            by Celery's task decorator. See here for details:
            https://docs.celeryq.dev/en/stable/userguide/tasks.html
        title : str
            The title (aka name) of the service. Forwarded to FastAPI, see also:
            https://fastapi.tiangolo.com/tutorial/metadata/
        FitParameterArguments : pydantic model
            A model defining the structure of the  arguments that are required
            to fit the parameters.
        Observations : pydantic model
            A model defining the structure of the true observed data used for
            fitting the parameters.
        FittedParameters : pydantic model
            A model defining the structure of the fitted parameters required
            to compute a request.
        fit_parameters_task : Celery task
            Like `request_task` but for the POST /fit-parameters/ endpoint.
        description : str
            The description of the service. Forwarded to FastAPI, see also:
            https://fastapi.tiangolo.com/tutorial/metadata/
        version_root_path : str or None
            Can be used to specify the version name expected in root path.
            If `None` or empty will default to `f"v{VERSION.major}"` in case
            the version number appears to be a semantic version number. In any
            case defaults to `VERSION`.
        fastapi_kwargs : dict
            Additional keyword arguments passed to FastAPI(), May be useful
            to extend schema docs.
        """
        if Instrumentator is None or uvicorn is None:
            raise ModuleNotFoundError(
                "Running a service requires `uvicorn` and "
                "`prometheus_fastapi_instrumentator` to work. If you are "
                "using docker consider using a tag with `-service`."
            )

        # These two must always be available.
        self.RequestOutput = RequestOutput
        self.request_task = request_task

        if fit_parameters_task is None:
            # No fitting parameters means we don't have parameters
            # in the request model.
            self.RequestInput = compute_request_input_model(
                RequestArguments=RequestArguments,
            )
        else:
            # Fitting parameters is enabled, all models must be set up.
            self.RequestInput = compute_request_input_model(
                RequestArguments=RequestArguments,
                FittedParameters=FittedParameters,
            )
            self.FitParametersInput = compute_fit_parameters_input_model(
                FitParameterArguments=FitParameterArguments,
                Observations=Observations,
            )
            self.FitParametersOutput = FittedParameters
            self.fit_parameters_task = fit_parameters_task

        # Log everything to stdout by default, i.e. to docker container logs.
        # This comes on top as we want to emit our initial log message as soon
        # as possible to support debugging if anything goes wrong.
        self._logger_name = "service"
        self.logger = logging.getLogger(self._logger_name)

        # Assumes that a logger that has a handler assigned to it does not
        # need another one additionally. This prevents that multiple copies
        # of log messages are displayed while running tests.
        if not self.logger.handlers:
            stream_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(levelname)-10s%(asctime)s - %(message)s"
            )
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)
        self.logger.setLevel(logging.INFO)

        self.logger.info("Initiating API.")

        # Parse the requested log level from environment variables and
        # configure all loggers accordingly.
        self._loglevel = getattr(logging, (os.getenv("LOGLEVEL") or "INFO"))
        self.logger.info(
            "Changing log level for all loggers to %s", self._loglevel
        )
        for logger_name in logging.root.manager.loggerDict:
            logging.getLogger(logger_name).setLevel(self._loglevel)

        # Load and check root path for service.
        version = os.getenv("VERSION")
        if not version:
            raise ValueError(
                "Service needs a version for operation. Try setting the "
                "`VERSION` environment variable."
            )

        if version_root_path is None:
            version_parts = version.split(".")
            if len(version_parts) > 1 and version_parts[0].isdigit():
                # OK, so there is at least one dot that could separate a major
                # and minor version and the major part is an int.
                version_root_path = f"v{version_parts[0]}"
            elif "(" == version[-10] and ")" == version[-1]:
                # Allow development versions too. That is a version like
                # `f"{branch_name}({short_commit_id})"`
                version_root_path = f"{version.split('(')[0]}"
            else:
                version_root_path = f"{version}"

        fastapi_root_path = os.getenv("ROOT_PATH") or f"/{version_root_path}"
        if fastapi_root_path[0] != "/" or fastapi_root_path[-1] == "/":
            raise ValueError(
                "`ROOT_PATH` must have a leading and no trailing slash. "
                f"Got instead: {fastapi_root_path}"
            )
        if fastapi_root_path.split("/")[-1] != version_root_path:
            raise ValueError(
                "`ROOT_PATH` must contain a version information as last "
                f"path element.\nExpected to find: {version_root_path}\n"
                f"Got instead: {fastapi_root_path}"
            )

        post_body_models_by_path = {"/request/": self.RequestInput}
        if fit_parameters_task is not None:
            post_body_models_by_path["/fit-parameters/"] = (
                self.FitParametersInput
            )

        # Set up Authentication and Authorization if requested.
        jwt_issuer = os.getenv("AUTH_JWT_ISSUER") or None
        if jwt_issuer is not None:
            jwt_audience = os.getenv("AUTH_JWT_AUDIENCE")
            jwt_role_claim = json.loads(
                os.getenv("AUTH_JWT_ROLE_CLAIM") or "null"
            )
            jwt_roles = json.loads(os.getenv("AUTH_JWT_ROLES") or "null")

            self.access_token_checker = AccessTokenChecker(
                expected_issuer=jwt_issuer,
                expected_audience=jwt_audience,
                expected_role_claim=jwt_role_claim,
                expected_roles=jwt_roles,
            )

            # The FastAPI docs are not very complete here. This was found here:
            # https://github.com/HarryMWinters/fastapi-oidc/issues/1
            fastapi_oauth2 = OpenIdConnect(
                openIdConnectUrl=self.access_token_checker.get_well_known_url(),
                scheme_name="OpenID Connect Authentication",
            )

            dependencies = [
                Depends(self.validate_jwt),
                Depends(fastapi_oauth2),
            ]

            # Extend the schema with status code only existing for services
            # with enabled auth.
            auth_errors = {
                401: {
                    "model": HTTPError,
                    "description": "Invalid access token provided.",
                },
                403: {
                    "model": HTTPError,
                    "description": (
                        "Returned if no access token is provided but the "
                        "service expects one or if a valid token was provided "
                        "but lacking the necessary roles to access the service."
                    ),
                },
            }
            self.post_request_responses.update(auth_errors)
            self.get_request_status_responses.update(auth_errors)
            self.get_request_result_responses.update(auth_errors)
            self.post_fit_parameters_responses.update(auth_errors)
            self.get_fit_parameters_status_responses.update(auth_errors)
            self.get_fit_parameters_result_responses.update(auth_errors)

        else:
            dependencies = None

        # General settings for the REST API.
        self.fastapi_app = FastAPIExtendedModels(
            title=title,
            description=description,
            docs_url="/",
            redoc_url=None,
            root_path=fastapi_root_path,
            version=version,
            dependencies=dependencies,
            post_body_models_by_path=post_body_models_by_path,
            **fastapi_kwargs,
        )

        # Setup the request endpoints.
        self.fastapi_app.post(
            "/request/",
            status_code=status.HTTP_201_CREATED,
            response_model=TaskId,
            responses=self.post_request_responses,
            description=self.post_request_description,
            tags=["request"],
        )(self.post_request)
        self.fastapi_app.get(
            "/request/{task_id}/status/",
            response_model=TaskStatus,
            responses=self.get_request_status_responses,
            description=self.get_request_status_description,
            tags=["request"],
        )(self.get_status)
        self.fastapi_app.get(
            "/request/{task_id}/result/",
            response_model=RequestOutput,
            responses=self.get_request_result_responses,
            description=self.get_request_result_description,
            tags=["request"],
        )(self.get_request_result)

        if fit_parameters_task is not None:
            # Setup for the fit-parameters endpoints in a similar manner
            # to the request endpoints above.
            self.fastapi_app.post(
                "/fit-parameters/",
                status_code=status.HTTP_201_CREATED,
                response_model=TaskId,
                responses=self.post_fit_parameters_responses,
                description=self.post_fit_parameters_description,
                tags=["fit-parameters"],
            )(self.post_fit_parameters)
            self.fastapi_app.get(
                "/fit-parameters/{task_id}/status/",
                response_model=TaskStatus,
                responses=self.get_fit_parameters_status_responses,
                description=self.get_fit_parameters_status_description,
                tags=["fit-parameters"],
            )(self.get_status)
            self.fastapi_app.get(
                "/fit-parameters/{task_id}/result/",
                response_model=FittedParameters,
                responses=self.get_fit_parameters_result_responses,
                description=self.get_fit_parameters_result_description,
                tags=["fit-parameters"],
            )(self.get_fit_parameters_result)

    def validate_jwt(
        self,
        request: Request,
        authorization: Annotated[
            str | None, Header(include_in_schema=False)
        ] = None,
    ):
        """
        This checks that the JWT provided by the user is actually valid.

        NOTE: The usual way of getting the token is to Depend on the OIDC
              schema, see here:
              https://fastapi.tiangolo.com/tutorial/security/first-steps/
              However, this is not possible here as the security schema is
              only defined in `__init__` and can't be accessed as argument
              of this method. Hence a little workaround.
        """
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="No authorization header in request.",
            )
        auth_split = authorization.split("Bearer ")
        if len(auth_split) < 2:
            raise HTTPException(
                status_code=401,
                detail="No bearer token in authorization header.",
            )
        token = auth_split[1]

        try:
            user_id, granted_roles = self.access_token_checker.check_token(
                token
            )
        except InvalidTokenError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Token validation failed. Error was: {str(e)}",
            )

        # NOTE: This is super nice for logging but not covered in the tests.
        request.scope["user_id"] = user_id

        # This might be used in future. It is currently not.
        request.scope["granted_roles"] = granted_roles

    async def post_request(self, request: Request):
        """
        Handle post calls to the request endpoint.

        This checks that the user data matches the related input data model
        and creates a task that is computed by the worker.
        """
        # Validate that the sent data matches the input schema...
        raw_body = await request.body()
        try:
            _ = self.RequestInput.model_validate_json(raw_body)
        except ValidationError as exc:
            # This does the same thing FastAPI does on ValidationErrors. See:
            # https://github.com/tiangolo/fastapi/blob/master/docs_src/handling_errors/tutorial006.py
            return await request_validation_exception_handler(request, exc)

        # ... and forward the JSON data to the worker.
        # Here we use the JSON originally sent by the client to prevent
        # that we need to serialize the parsed data again.
        task = self.request_task.delay(input_data_json=raw_body)

        return TaskId(task_ID=task.id)

    async def post_fit_parameters(self, request: Request):
        """
        Handle post calls to the fit-parameters endpoint.

        This checks that the user data matches the related input data model
        and creates a task that is computed by the worker.
        """
        # Validate that the sent data matches the input schema...
        raw_body = await request.body()
        try:
            _ = self.FitParametersInput.model_validate_json(raw_body)
        except ValidationError as exc:
            # This does the same thing FastAPI does on ValidationErrors. See:
            # https://github.com/tiangolo/fastapi/blob/master/docs_src/handling_errors/tutorial006.py
            return await request_validation_exception_handler(request, exc)

        # ... and forward the JSON data to the worker.
        # Here we use the JSON originally sent by the client to prevent
        # that we need to serialize the parsed data again.
        task = self.fit_parameters_task.delay(input_data_json=raw_body)

        return TaskId(task_ID=task.id)

    async def get_status(self, task_id: UUID):
        """
        This method triggers the computation of the status response.

        It does this for both endpoints, i.e. for GET /request/{task_ID}/status/
        and for GET /fit-parameters/{task_ID}/status/ as there is no change in
        logic and Celery apparently does not differentiate the IDs of tasks
        by the corresponding method.

        Arguments:
        ----------
        task_id : UUID
            As returned by POST /request/ or /fit-parameters/

        Returns:
        --------
        task_status : esg.models.task.TaskStatus instance
            The status info of the task.

        Raises:
        -------
        fastapi.HTTPException
            If the task does not exist.

        TODO: You might want to make sure here that a task created
              but not started yet might emit a state that matches the
              `"queued"` state. However, this seems to be a
              celery config variable that does this.
        """
        task = AsyncResult(str(task_id))
        task_state = task.state

        if task_state == states.PENDING:
            error_msg = "Could not find task with ID: %s"
            self.logger.info(error_msg, task_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg % task_id,
            )

        self.logger.debug(f"Celery state of task is: {task_state}")
        task_status_text = TASK_STATUS_MAP[task_state]

        task_status = TaskStatus(status_text=task_status_text)
        return task_status

    async def get_result(self, task_id: UUID):
        """
        Fetches the result from the celery backend and handles errors.

        Arguments:
        ----------
        task_id : UUID
            As returned by POST /request/

        Returns:
        --------
        output_data_json : str
            The result of the task.

        Raises:
        -------
        fastapi.HTTPException
            If the task does not exist or is not ready yet.
        esg.services.base.GenericUnexpectedException
            Upon unexpected errors during handling the request,
            see Exception docstring for details.
        esg.services.base.RequestInducedException
            Upon request induced errors during handling the request,
            see Exception docstring for details.
        """
        task = AsyncResult(str(task_id))
        task_state = task.state

        if task_state == states.PENDING:
            error_msg = "Could not find task with ID: %s"
            self.logger.info(error_msg, task_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg % task_id,
            )
        elif task_state in states.UNREADY_STATES:
            error_msg = "Task is not ready yet. ID was: %s"
            self.logger.info(error_msg, task_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg % task_id,
            )
        elif task_state == states.FAILURE:
            self.logger.info("Failed task encountered for ID: %s", task_id)
            raise GenericUnexpectedException()

        # Fetch the result.
        output_data_json = task.get()
        return output_data_json

    async def get_request_result(self, task_id: UUID):
        """
        This method fetches the result of a task, it thus answers any calls
        to the  GET /request/{task_ID}/result/ endpoint.

        Arguments:
        ----------
        task_id : UUID
            As returned by POST /request/

        Returns:
        --------
        response : fastapi.responses.JSONResponse instance
            The validated output data in a JSON response object.
        """
        output_data_json = await self.get_result(task_id=task_id)
        if output_data_json is None:
            self.logger.error("Task returned no data!")
            raise GenericUnexpectedException()

        # Verify that the output matches the API docs.
        try:
            self.RequestOutput.model_validate_json(output_data_json)
        except ValidationError:
            # TODO: Verify here that not the wrong endpoint has been used.
            #       Give the user a hint if so.
            self.logger.error(
                "Task computed data not matching the `RequestOutput` model."
            )
            raise GenericUnexpectedException()

        # Directly return the JSON data. This saves a few CPU
        # cycles by preventing that the data is serialized again.
        response = Response(
            content=output_data_json, media_type="application/json"
        )
        return response

    async def get_fit_parameters_result(self, task_id: UUID):
        """
        This method fetches the result of a task, it thus answers any calls
        to the  GET /fit-parameters/{task_ID}/result/ endpoint.

        Arguments:
        ----------
        task_id : UUID
            As returned by POST /fit-parameters/

        Returns:
        --------
        response : fastapi.responses.JSONResponse instance
            The validated output data in a JSON response object.
        """
        output_data_json = await self.get_result(task_id=task_id)

        # Verify that the output matches the API docs.
        try:
            self.FitParametersOutput.model_validate_json(output_data_json)
        except ValidationError:
            self.logger.error(
                "Task computed data not matching the `FitParametersOutput` "
                "model."
            )
            raise GenericUnexpectedException()

        # Directly return the JSON data. This saves a few CPU
        # cycles by preventing that the data is serialized again.
        response = Response(
            content=output_data_json, media_type="application/json"
        )
        return response

    def close(self):
        """
        Place here anything that needs to be done to clean up.

        That is nothing for the default case of the `API` class as essentials
        parts for graceful shutdown are integrated in the `run` method.
        """
        pass

    @staticmethod
    def get_client_addr(scope):
        """
        Extend the uvicorn access logs with a user ID, should it exists.

        Extended version that adds a user ID to the access logs. Original code:
        https://github.com/encode/uvicorn/blob/14ffba8316eb606cd026d1a3b01d9d90e47e868c/uvicorn/protocols/utils.py#L45
        """
        client = scope.get("client")
        if not client:
            return ""

        user_id = scope.get("user_id")
        if not user_id:
            user_id = "Anonymous"

        return "%s:%d" % client + " - %s" % user_id

    def run(self):
        """
        Run the FastAPI app with uvicorn.
        """
        self.logger.info("Initiating API execution.")

        try:
            # Exposes a Prometheus endpoint for monitoring.
            # Instrumentator().instrument(self.fastapi_app).expose(
            #     self.fastapi_app, include_in_schema=False
            # )

            # Extends the access log with a username. This patches the uvicorn
            # function `get_client_addr` used here:
            # https://github.com/encode/uvicorn/blob/14ffba8316eb606cd026d1a3b01d9d90e47e868c/uvicorn/protocols/http/h11_impl.py#L466
            # NOTE: This patch here as well as the custom implementation of
            #       `get_client_addr` are currently not covered in the tests.
            #       Be extra careful if changing something here.
            with patch(
                "uvicorn.protocols.utils.get_client_addr", self.get_client_addr
            ):
                # Serve the REST endpoint.
                # NOTE: uvicorn handles SIGTERM signals for us, that is, this
                #       line below will block until SIGTERM or SIGINT is
                #       received. Afterwards the finally statement is executed.
                uvicorn.run(
                    self.fastapi_app,
                    host="0.0.0.0",
                    port=8800,
                )
        except Exception:
            self.logger.exception(
                "Exception encountered while serving the API."
            )
            raise
        finally:
            # This should be called on system exit and keyboard interrupt.
            self.logger.info("Shutting down API.")
            self.close()
            self.logger.info("API shutdown completed. Good bye!")
