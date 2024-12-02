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

import json
import logging
from urllib3 import disable_warnings

import requests


logger = logging.getLogger(__name__)


class HttpBaseClient:
    """
    Generic setup and configuration for HTTP(s) clients.

    This client implements wrappers around the fundamental http
    methods GET, POST, PUT and DELETE. All methods expect a `relative_url`
    which is appended to `base_url` to compute the final URL.

    Check out this page to get some inspiration on advanded stuff like
    retries and timeouts:
    https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
    """

    def __init__(
        self,
        base_url,
        verify=True,
        skip_verify_warning=False,
        username=None,
        password=None,
        check_on_init=True,
    ):
        """
        Set up the session for all requests.

        Arguments:
        ----------
        base_url: str
            The root URL of the API, e.g. `http://localhost:8080/api`
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
        check_on_init: bool
            If `True` will call `check_connection` on init should it exist.
        """
        self.base_url = base_url
        self.verify = verify

        # urllib3 would emit one warning for EVERY call without verification.
        if not self.verify:
            disable_warnings()
            if skip_verify_warning is False:
                # This is basically the same warning urllib3 emits, but just once.
                logger.warning(
                    "Client will make unverified HTTPS request to host `{}`. "
                    "Adding certificate verification is strongly advised."
                    "".format(self.base_url)
                )

        self.http = requests.Session()

        if username is None or password is None:
            self.auth = None
        else:
            self.auth = requests.auth.HTTPBasicAuth(
                username=username, password=password
            )

        # Automatically check the status code for every request.
        def assert_status_hook(response, *args, **kwargs):
            # Log validation errors, these contain more information about
            # what went wrong.
            if response.status_code in [400, 422]:
                try:
                    error_detail = json.dumps(response.json(), indent=4)
                except requests.exceptions.JSONDecodeError:
                    # Some errors are not JSON, especially those
                    # directly returned by Django in DEBUG model
                    error_detail = response.text
                logger.error(
                    "HTTP request returned error: \n{}".format(error_detail)
                )

            response.raise_for_status()

        self.http.hooks["response"] = [assert_status_hook]

        # If the child has defined a method to check a connection
        # we want to call it automatically.
        if check_on_init and hasattr(self, "check_connection"):
            logger.info("Testing connection to target API.")
            self.check_connection()

    def compute_full_url(self, relative_url):
        """
        Computes a full URL based on `self.base_url` and `relative_url`
        """
        # The strings are here in case someone provided a Path object.
        full_url = str(self.base_url)
        relative_url = str(relative_url)

        # People may not take care and leave a trailing slash at `base_url`
        # and provide a leading slash too. Remove these, they are almost
        # surely not desired.
        if full_url[-1] == "/" and relative_url[0] == "/":
            full_url += relative_url[1:]
        else:
            full_url += relative_url

        return full_url

    def get(self, relative_url, *args, **kwargs):
        full_url = self.compute_full_url(relative_url=relative_url)
        response = self.http.get(
            full_url, *args, auth=self.auth, verify=self.verify, **kwargs
        )
        return response

    def post(self, relative_url, *args, **kwargs):
        full_url = self.compute_full_url(relative_url=relative_url)
        response = self.http.post(
            full_url, *args, auth=self.auth, verify=self.verify, **kwargs
        )
        return response

    def put(self, relative_url, *args, **kwargs):
        full_url = self.compute_full_url(relative_url=relative_url)
        response = self.http.put(
            full_url, *args, auth=self.auth, verify=self.verify, **kwargs
        )
        return response

    def delete(self, relative_url, *args, **kwargs):
        full_url = self.compute_full_url(relative_url=relative_url)
        response = self.http.delete(
            full_url, *args, auth=self.auth, verify=self.verify, **kwargs
        )
        return response
