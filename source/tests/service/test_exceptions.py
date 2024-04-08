"""
Tests for `esg.service.exceptions`

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

from uuid import uuid1

from fastapi import HTTPException
import pytest

from esg.service.exceptions import GenericUnexpectedException
from esg.service.exceptions import RequestInducedException


class TestGenericUnexpectedException:
    """
    Tests for `esg.service.exceptions.GenericUnexpectedException`
    """

    def test_raises_with_code_500(self):
        """
        Verify that the expected HTTPException is raised with the expected
        HTTP status code.
        """
        with pytest.raises(HTTPException) as e:
            raise GenericUnexpectedException()

        assert e.value.status_code == 500

    def test_detail_message_is_provided(self):
        """
        We expect a detail providing generic info that there was an error
        while processing the the request.
        """
        with pytest.raises(HTTPException) as e:
            raise GenericUnexpectedException(status_code=500)

        for expected_word in ["service", "encountered", "error", "request."]:
            assert expected_word in e.value.detail

    def test_detail_message_can_contain_request_ID(self):
        """
        If provided the requestID should be part of the detail message.
        """
        test_uuid = uuid1()
        with pytest.raises(HTTPException) as e:
            raise GenericUnexpectedException(request_ID=test_uuid)

        assert str(test_uuid) in e.value.detail


class TestRequestInducedException:
    """
    Tests for `esg.service.exceptions.RequestInducedException`
    """

    def test_raises_with_code_400(self):
        """
        Verify that the expected HTTPException is raised with the expected
        HTTP status code.
        """
        expected_detail = "The reason for this error is 42."
        with pytest.raises(HTTPException) as e:
            raise RequestInducedException(detail=expected_detail)

        assert e.value.status_code == 400

    def test_provided_detail_is_in_exception(self):
        """
        Verify that the detail argument is forwarded.
        """
        expected_detail = "The reason for this error is 42."
        with pytest.raises(HTTPException) as e:
            raise RequestInducedException(detail=expected_detail)

        assert expected_detail == e.value.detail
