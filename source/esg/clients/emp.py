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

from typing import List

from esg.clients.base import HttpBaseClient
from esg.models.base import _RootModel
from esg.models.datapoint import DatapointList
from esg.models.datapoint import PutSummary
from esg.models.datapoint import ValueDataFrame
from esg.models.datapoint import ValueMessageByDatapointId
from esg.models.datapoint import ValueMessageListByDatapointId
from esg.models.metadata import Service
from esg.models.metadata import RequestTask
from esg.models.metadata import Plant


class ServiceList(_RootModel):
    root: List[Service]


class RequestTaskList(_RootModel):
    root: List[RequestTask]


class PlantList(_RootModel):
    root: List[Plant]


class EmpClient(HttpBaseClient):
    """
    A client to communicate with the EMP v1 API.

    Raises:
    -------
        All methods will indirectly raise a `requests.exceptions.HTTPError`
        if anything goes wrong.
    """

    def check_connection(self):
        """
        Test connection by calling the API root.
        """
        self.get("/")

    def get_datapoint_metadata_latest(self, query_params=None):
        """
        Returns datapoints matching the requested filter parameters.

        Arguments:
        ----------
        query_params : dict of string.
            The filter parameters. See API docs.

        Returns:
        --------
        datapoint_list : esg.models.datapoint.DatapointById instance
            The datapoints matching the query.
        """
        response = self.get("/datapoint/metadata/latest/", params=query_params)
        datapoint_list = DatapointList.model_validate_json(response.content)
        return datapoint_list

    def put_datapoint_metadata_latest(self, datapoint_list):
        """
        Update or create datapoint in DB.

        Arguments:
        ----------
        datapoint_list : esg.models.datapoint.DatapointList instance
            List of datapoints to update or create.

        Returns:
        --------
        datapoint_list : esg.models.datapoint.DatapointList instance
            The version of the input that is now in DB.
        """
        response = self.put(
            "/datapoint/metadata/latest/",
            json=datapoint_list.model_dump_jsonable(),
        )
        datapoint_list = DatapointList.model_validate_json(response.content)
        return datapoint_list

    def get_datapoint_value_latest(self, query_params=None):
        """
        Return the latest values for datapoints targeted by the filter.

        Arguments:
        ----------
        query_params : dict of string.
            The filter parameters. See API docs.

        Returns:
        --------
        value_msgs_by_dp_id : esg.models.datapoint.ValueMessageByDatapointId
            The matching value messages sorted by datapoint id.
        """
        response = self.get("/datapoint/value/latest/", params=query_params)
        value_msgs_by_dp_id = ValueMessageByDatapointId.model_validate_json(
            response.content
        )
        return value_msgs_by_dp_id

    def put_datapoint_value_latest(self, value_msgs_by_dp_id):
        """
        Update or create one or more historic value messages for each of one
        or more datapoints.

        Arguments:
        ----------
        value_msgs_by_dp_id : esg.models.datapoint.ValueMessageByDatapointId
            The matching value messages sorted by datapoint id.

        Returns:
        --------
        put_summary : esg.models.datapoint.PutSummary instance
            The summary how many items have been updated and created.
        """
        response = self.put(
            "/datapoint/value/latest/",
            json=value_msgs_by_dp_id.model_dump_jsonable(),
        )
        put_summary = PutSummary.model_validate_json(response.content)
        return put_summary

    def get_datapoint_value_history(self, query_params=None):
        """
        Return the history values for datapoints targeted by the filter.

        Arguments:
        ----------
        query_params : dict of string.
            The filter parameters. See API docs.

        Returns:
        --------
        value_msgs_by_dp_id : esg.models.datapoint.ValueMessageListByDatapointId
            The matching value message lists sorted by datapoint id.
        """
        response = self.get("/datapoint/value/history/", params=query_params)
        value_msgs_by_dp_id = ValueMessageListByDatapointId.model_validate_json(
            response.content
        )
        return value_msgs_by_dp_id

    def put_datapoint_value_history(self, value_msgs_by_dp_id):
        """
        Update or create one or more historic value messages for each of one
        or more datapoints.

        Arguments:
        ----------
        value_msgs_by_dp_id : esg.models.datapoint.ValueMessageListByDatapointId
            The matching value message lists sorted by datapoint id.

        Returns:
        --------
        put_summary : esg.models.datapoint.PutSummary instance
            The summary how many items have been updated and created.
        """
        response = self.put(
            "/datapoint/value/history/",
            json=value_msgs_by_dp_id.model_dump_jsonable(),
        )
        put_summary = PutSummary.model_validate_json(response.content)
        return put_summary

    def get_datapoint_value_history_at_interval(
        self, interval, query_params=None
    ):
        """
        Return the history values for datapoints targeted by the filter.

        Arguments:
        ----------
        interval : timedelta
            The interval to which the data should be aggregated.
        query_params : dict of string.
            The filter parameters. See API docs.

        Returns:welcome
        --------
        value_dataframe : esg.models.datapoint.ValueDataFrame
            Pydantic version of DataFrame data.
        """
        # Format to a string that Postgres understands.
        interval = f"{interval.days} days {interval.seconds} seconds"
        if query_params is None:
            query_params = {}
        query_params["interval"] = interval

        response = self.get(
            "/datapoint/value/history/at_interval/", params=query_params
        )
        value_dataframe = ValueDataFrame.model_validate_json(response.content)
        return value_dataframe

    def get_service_latest(self, query_params=None):
        """
        Return the latest values for services targeted by the filter.

        Arguments:
        ----------
        query_params : dict of string.
            The filter parameters. See API docs.

        Returns:
        --------
        service_list : esg.models.metadata.ProductList
            The response content that has read from DB.
        """
        response = self.get("/service/latest/", params=query_params)
        service_list = ServiceList.model_validate_json(response.content)
        return service_list

    def get_service_by_name(self, name):
        """
        Returns a single service item by exact name match.

        This is a shortcut as it is a common pattern.

        Arguments:
        ----------
        name : str
            The value of the name field the target service item.

        Returns:
        --------
        service : esg.models.metadata.Product
            A single service item.

        Raises:
        -------
        ValueError:
            If no service with such name could be found.
        """
        all_matched_services = self.get_service_latest(
            query_params={"name__regex": "^{}$".format(name)}
        )
        # Due to the exact match above, this should be exactly one item in here.
        if len(all_matched_services.root) == 1:
            service = all_matched_services.root[0]
            return service
        else:
            raise ValueError("No service with such name: {}".format(name))

    def put_service_latest(self, service_list):
        """
        Update or create one or more service entries.

        Arguments:
        ----------
        service_list : esg.models.metadata.ProductList
            The content as pydantic instance.

        Returns:
        --------
        service_list : esg.models.metadata.ProductList
            The response content that has been written to DB,
            as pydantic instance.
        """
        response = self.put(
            "/service/latest/", json=service_list.model_dump_jsonable()
        )
        service_list = ServiceList.model_validate_json(response.content)
        return service_list

    # def create_request_task_from_product(self, product, available_at=None):
    #     """
    #     Creates a RequestTask instance from a Product instance.

    #     TODO: This needs some tests.
    #     TODO: This must be adapted to RequestTemplate and RequestTask models
    #           and endpoints.

    #     Arguments:
    #     ----------
    #     product : esg.models.metadata.Product
    #         The corresponding product as pydantic instance.
    #     available_at : datetime
    #         If specified will use this time as `available_at` field and
    #         to compute `coverage_from`/`coverage_to`.
    #     """
    #     if available_at is None:
    #         available_at = datetime.now(tz=timezone.utc)

    #     coverage_from = available_at + product.coverage_from
    #     coverage_to = available_at + product.coverage_to

    #     request_task = RequestTask(
    #         product_id=product.id,
    #         available_at=available_at,
    #         coverage_from=coverage_from,
    #         coverage_to=coverage_to,
    #     )
    #     return request_task

    def get_request_task_latest(self, query_params=None):
        """
        Return the latest values for request tasks targeted by the filter.

        Arguments:
        ----------
        query_params : dict of string.
            The filter parameters. See API docs.

        Returns:
        --------
        request_task_list : esg.models.metadata.RequestTaskList
            The response content that has read from DB.
        """
        response = self.get("/request_task/latest/", params=query_params)
        request_task_list = RequestTaskList.model_validate_json(
            response.content
        )
        return request_task_list

    def put_request_task_latest(self, request_task_list):
        """
        Update or create one or more product entries.

        Arguments:
        ----------
        request_task_list : esg.models.metadata.RequestTaskList
            The content as pydantic instance.

        Returns:
        --------
        request_task_list : esg.models.metadata.RequestTaskList
            The response content that has been written to DB,
            as pydantic instance.
        """
        response = self.put(
            "/request_task/latest/",
            json=request_task_list.model_dump_jsonable(),
        )
        request_task_list = RequestTaskList.model_validate_json(
            response.content
        )
        return request_task_list

    def get_plant_latest(self, query_params=None):
        """
        Return the latest plants targeted by the filter.

        Arguments:
        ----------
        query_params : dict of string.
            The filter parameters. See API docs.

        Returns:
        --------
        plant_list : esg.models.metadata.PlantList
            The response content that has read from DB.
        """
        response = self.get("/plant/latest/", params=query_params)
        plant_list = PlantList.model_validate_json(response.content)
        return plant_list

    def put_plant_latest(self, plant_list):
        """
        Update or create one or more plant entries.

        Arguments:
        ----------
        plant_list : esg.models.metadata.PlantList
            The content as pydantic instance.

        Returns:
        --------
        plant_list : esg.models.metadata.PlantList
            The response content that has been written to DB,
            as pydantic instance.
        """
        response = self.put(
            "/plant/latest/", json=plant_list.model_dump_jsonable()
        )
        plant_list = PlantList.model_validate_json(response.content)
        return plant_list
