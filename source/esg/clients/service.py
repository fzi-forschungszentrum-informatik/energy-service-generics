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

import logging
import time

from esg.clients.base import HttpBaseClient
from esg.models.task import TaskId
from esg.models.task import TaskStatus

logger = logging.getLogger(__name__)


class GenericServiceClient(HttpBaseClient):
    """
    A client to communicate with data and product services.

    The intended usage concept is:
        * Create a class instance.
        * create one or more requests.
        * wait for all results to be finished.
        * Retrieve all results at once.

    Raises:
    -------
        All methods will indirectly raise a `requests.exceptions.HTTPError`
        if anything goes wrong.
    """

    def __init__(
        self,
        base_url,
        endpoint="request",
        verify=True,
        skip_verify_warning=False,
        username=None,
        password=None,
        InputModel=None,
        OutputModel=None,
    ):
        """
        Arguments:
        ----------
        base_url : str
            The root URL of the service API, e.g. `http://localhost:8800`
        endpoint : str
            The endpoint type to use. Services should all have a `"request"`
            endpoint. Some additionally a `"fit-parameters"` endpoint. Others
        verify: bool
            If set to `False` will disable certificate checking.
            Useful if self signed certificates are used but a potential
            security risk. See also the requests docs on the topic:
            https://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification
        skip_verify_warning: bool
            Allows you to mute the warning you usually get if you set `verify`
            to `False`. In some cases, e.g. benchmarking, this is a good idea
            to reduce noise in the logs.
        username: str
            The username to use for HTTP basic auth. Only used in combination
            with `password`.
        password: str
            The username to use for HTTP basic auth. Only used in combination
            with `username`.
        InputModel : esg.models.base._BaseModel related
            The pydantic model that should be used to parse the
            input data in `self.submit_request`.
        OutputModel : esg.models.base._BaseModel related
            The pydantic model that should be used to parse the
            output data in `self.fetch_result`.
        """
        logger.info("Starting up GenericServiceClient")

        if endpoint not in ["request", "fit-parameters"]:
            logger.warning(
                f'Client configured to use endpoint `"{endpoint}"` '
                'which is not one of the standardized endpoints (`"request"` '
                'or `"fit-parameters"`) for services.'
            )

        self.endpoint = endpoint
        self.InputModel = InputModel
        self.OutputModel = OutputModel

        super().__init__(
            base_url=base_url,
            verify=verify,
            skip_verify_warning=skip_verify_warning,
            username=username,
            password=password,
        )

        # Stores created tasks.
        self.task_ids = []
        # This is here to prevent `fetch_results_jsonable` from
        # needing to check again if all results are finished if
        # `wait_for_results` has been called before already.
        self.all_tasks_finished = False

    def check_connection(self):
        """
        Test connection by calling the API root.
        """
        self.get("/")

    def post_jsonable(self, input_data_as_jsonable):
        """
        Calls POST endpoint of service.

        This will store the task_ID in an attribute so you don't have to.

        Arguments:
        ----------
        input_data_as_jsonable: python object
            The input data for computing the request in JSONable representation.
        """
        response = self.post(f"/{self.endpoint}/", json=input_data_as_jsonable)

        # Check that the response contained the payload we expect and
        # store the task ID for fetching results later.
        task_id = TaskId.model_validate(response.json()).task_ID
        self.task_ids.append(task_id)

    def post_obj(self, input_data_obj):
        """
        Like `post_jsonable` but for a python object as input.

        This will use `self.InputModel` to parse and validate the object.

        Arguments:
        ----------
        input_data_obj: dict
            The input data for computing the request as _BaseModel instance.
        """
        input_data = self.InputModel.model_validate(input_data_obj)
        input_data_jsonable = input_data.model_dump_jsonable()
        self.post_jsonable(input_data_as_jsonable=input_data_jsonable)

    def wait_for_results(self, max_retries=300, retry_wait=1):
        """
        Blocks until all tasks are finished

        This will start with the first request and ask the product service
        if it is finished already. If not it will wait one second and ask
        again. Once the first request is finished it will continue with the
        second request and so on. That way we don't need to request the
        status of all tasks every second but won't have a major
        drawback as we want to block until ALL finished anyways.

        Note: The maximum runtime of this method (timeout) is:
              `max_retries * retry_wait` in seconds.

        Arguments:
        ----------
        max_retries: int
            Maximum total number of times the request status is checked
            before it assuming the tasks have failed.
        retry_wait: int
            How many seconds to wait after a not ready status before
            the script fetches the next status.

        Raises:
        -------
        RuntimeError:
            If number of status requests exceeded `max_retries` while
            waiting for tasks to become ready.

        """
        # Shortcut, e.g. if called again by `fetch_result_jsonable`
        if self.all_tasks_finished:
            return

        task_ids_to_check = self.task_ids.copy()
        current_task_id = task_ids_to_check.pop(0)
        for _ in range(max_retries):
            while True:
                status_url = f"/{self.endpoint}/{current_task_id}/status/"
                response = self.get(status_url)
                task_status = TaskStatus.model_validate(response.json())

                # If not ready, wait a bit and try again.
                if task_status.status_text != "ready":
                    time.sleep(retry_wait)
                    break

                # If previous task is ready, directly try the next one.
                if task_ids_to_check:
                    current_task_id = task_ids_to_check.pop(0)
                else:
                    # Nothing left to check.
                    break

            if task_status.status_text == "ready" and not task_ids_to_check:
                # This point will only be reached if all tasks are ready.
                self.all_tasks_finished = True
                return

        raise RuntimeError("Timeout while waiting for tasks to complete")

    def get_results_jsonable(self):
        """
        Returns a list of task results, one for each task and in the
        same order.

        Returns:
        --------
        output_data_jsonable : list
            List of the results in JSONable representation, each item is a dict
            or list. The list contains one item for each task.
        """
        # Fetching not ready results may block and cause nasty errors like
        # gateway timeouts and stuff.
        self.wait_for_results()

        output_data_jsonable = []
        while self.task_ids:
            task_id = self.task_ids.pop(0)
            result_url = f"/{self.endpoint}/{task_id}/result/"
            response = self.get(result_url)
            output_data_jsonable.append(response.json())

        return output_data_jsonable

    def get_results_obj(self):
        """
        Like `get_results_jsonable` but for a python object as output.

        This will use `self.OutputModel` to parse and validate the items
        in the list of responses.

        Returns:
        --------
        output_data : list of pydantic models
            A list of responses, one item per task. Each response item
            parsed as pydantic model using `self.OutputModel`
        """
        output_data_jsonable = self.get_results_jsonable()
        output_data = []
        for jsonable_item in output_data_jsonable:
            obj = self.OutputModel.model_validate(jsonable_item)
            output_data.append(obj)

        return output_data
