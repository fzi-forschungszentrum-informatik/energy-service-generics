"""
Custom exceptions for services.

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

from fastapi import HTTPException
from fastapi import status


class GenericUnexpectedException(HTTPException):
    """
    This defines a generic HTTP error (500) that should be returned
    for any unexpected error encountered during processing the request,
    that is a bug in the service.

    This error doesn't contain any additional information as the user
    of the service has no chance to fix it anyways and the responsible
    maintainer can look up the full traceback in the logs.
    """

    def __init__(self, request_ID=None, **kwargs):
        """
        Set `status_code` and `detail` with the desired generic
        information.

        Arguments:
        ----------
        request_id : UUID
            If provided will add the ID to the error detail message.
        kwargs : dict
            Any other keyword arguments that should be forwarded to
            fastapi.HTTPException
        """
        kwargs["status_code"] = status.HTTP_500_INTERNAL_SERVER_ERROR

        base_detail = "The service encountered an error while processing the "
        if request_ID is not None:
            detail = base_detail + "request with ID: %s" % request_ID
        else:
            detail = base_detail + "request."
        kwargs["detail"] = detail

        super().__init__(**kwargs)


class RequestInducedException(HTTPException):
    """
    This defines a HTTP error (400) that should be returned for any
    foreseeable error that might occur during handling the request and
    that is caused by the request arguments (but cannot eliminated with
    reasonable effort during validation). E.g. the user request triggers
    reading data from a file or database which may not always exist but
    if the data exists is only known after the file has been opened or
    the DB has been queried.

    The `detail` field of this exception should always be populated
    with enough information to allow the user of a service to understand
    why the request failed and how to alter the request arguments to
    make it work.

    Note that the `status_code` is set fixed to 400 to distinguish the
    error from other common errors like (403, 404) which have other reasons
    and also from validation errors (422) as the latter returns a different
    data format.
    """

    def __init__(self, detail, **kwargs):
        """
        Overload `status_code`  with the desired generic value and
        validate that a detail is provided.

        This keeps the signature of fastapi.HTTPException and any
        additional arguments are forwarded to it.

        Arguments:
        ----------
        detail : str
            A string explaining the user what went wrong.
        kwargs : dict
            Any other keyword arguments that should be forwarded to
            fastapi.HTTPException

        Raises:
        -------
        ValueError:
            If detail is empty.
        """
        kwargs["status_code"] = status.HTTP_400_BAD_REQUEST

        if not detail:
            raise ValueError(
                "RequestInducedException requires a non empty detail "
                "that explains what went wrong while processing the request."
            )
        kwargs["detail"] = detail

        super().__init__(**kwargs)
