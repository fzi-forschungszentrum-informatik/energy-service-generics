"""
Note: This file is called `test_base_model` to prevent name clashes with
`test_base` in the services folder.

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

from datetime import datetime
from datetime import timezone
import json
from typing import List

from pydantic import BaseModel
from pydantic import RootModel

from esg.models.base import _BaseModel
from esg.models.base import _RootModel


class CustomModelMixinTests:
    """
    Tests for `esg.models.base.CustomModelMixin`.

    As the mixin itself, these tests need to be subclassed to be used.
    """

    def test_model_dump_jsonable(self):
        """
        Test that a message is converted into jsonable format as expected.
        """
        actual_jsonable = self.generic_test_obj.model_dump_jsonable()
        expected_jsonable = self.generic_test_obj_jsonable

        assert actual_jsonable == expected_jsonable

    def test_model_dump_jsonable_matches_dump_json(self):
        """
        Simple consistency test that the output `model_dump_jsonable()` of
        is equivalent to `model_dump_json`.
        This test makes sense as `model_dump_json()` does not use the jsonable
        representation any more.
        """
        expected_jsonable = json.loads(self.generic_test_obj.model_dump_json())
        actual_jsonable = self.generic_test_obj.model_dump_jsonable()

        assert actual_jsonable == expected_jsonable

    def test_model_dump_jsonable_bemcom(self):
        """
        Test that a message is converted into BEMCom format as expected.
        """
        actual_jsonable = self.generic_test_obj.model_dump_jsonable_bemcom()
        expected_jsonable = self.generic_test_obj_jsonable_bemcom

        assert actual_jsonable == expected_jsonable

    def test_model_dump_json_bemcom(self):
        """
        Simple consistency test that `json()` returns the right stuff
        assuming that `jsonable()` is implemented correctly.
        """
        expected_json = json.dumps(
            self.generic_test_obj.model_dump_jsonable_bemcom()
        )
        actual_json = self.generic_test_obj.model_dump_json_bemcom()

        assert actual_json == expected_json

    def test_model_validate_bemcom(self):
        """
        Test that `parse_obj_bemcom` handles timestamp fields as expected.
        """
        expected_obj = self.generic_test_obj

        actual_obj = self.GenericTestModel.model_validate_bemcom(
            self.generic_test_obj_jsonable_bemcom
        )

        assert actual_obj == expected_obj

    def test_model_validate_json_bemcom(self):
        """
        Test that `parse_obj_bemcom` handles timestamp fields as expected.
        """
        expected_obj = self.generic_test_obj

        actual_obj = self.GenericTestModel.model_validate_json_bemcom(
            json.dumps(self.generic_test_obj_jsonable_bemcom)
        )

        assert actual_obj == expected_obj

    # NOTE:
    # -----
    # Since pydantic V2 this may not be significantly faster any more. See:
    # https://docs.pydantic.dev/latest/usage/models/#creating-models-without-validation
    # We hence disable this but leave it here if it may become relevant
    # in future.

    # def test_construct_recursive_for_flat_models(self):
    #     """
    #     Sanity check, verify that `construct_recursive` works on flat
    #     models (i.e. for models which don't need recursion).
    #     """
    #     expected_obj = self.generic_test_obj
    #     actual_obj = self.GenericTestModel.construct_recursive(
    #         **self.generic_test_obj_python_values
    #     )

    #     # Compare jsonable, as jsonable fails if the values have
    #     # not been set correctly.
    #     assert actual_obj.jsonable() == expected_obj.jsonable()

    # def test_construct_recursive_for_list_models(self):
    #     """
    #     Check that child models in lists are instantiated correctly
    #     """

    #     class TestListItemModel(_BaseModel):
    #         value: Json

    #     class TestListModel(_BaseModel):
    #         __root__: List[TestListItemModel]

    #     obj = TestListModel.construct_recursive(
    #         __root__=[{"value": 21.0}, {"value": False}, {"value": "True"}]
    #     )

    #     expected_jsonable = [
    #         {"value": "21.0"},
    #         {"value": "false"},
    #         {"value": '"True"'},
    #     ]

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable

    # def test_construct_recursive_for_json_field_direct_in_list(self):
    #     """
    #     Check that Json fields directly placed in lists are encoded.
    #     Use case is the Datapoint model.
    #     """

    #     class TestListModel(_BaseModel):
    #         value: List[Json]

    #     obj = TestListModel.construct_recursive(
    #         value=[21.0, False, "True"],
    #     )

    #     expected_jsonable = {"value": ["21.0", "false", '"True"']}

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable

    # def test_construct_recursive_for_normal_types_on_root(self):
    #     """
    #     _Value and _Time models are directly defined as a normal (i.e. not
    #     list or dict) type assigned to model root.
    #     """

    #     class TestItemModel(_BaseModel):
    #         __root__: Json

    #     class TestModel(_BaseModel):
    #         items_list: List[TestItemModel]
    #         items_dict: Dict[str, TestItemModel]

    #     obj = TestModel.construct_recursive(
    #         items_list=[21.0, False, "True"],
    #         items_dict={"1": 21.0, "2": False, "3": "True"},
    #     )

    #     expected_jsonable = {
    #         "items_list": ["21.0", "false", '"True"'],
    #         "items_dict": {"1": "21.0", "2": "false", "3": '"True"'},
    #     }

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable

    # def test_construct_recursive_for_nested_list(self):
    #     """
    #     Check that lists that are child models are correctly handled too.
    #     """

    #     class TestListItemModel(_BaseModel):
    #         value: Json

    #     class TestListModel(_BaseModel):
    #         __root__: List[TestListItemModel]

    #     class TestListParentModel(_BaseModel):
    #         test_list: TestListModel

    #     obj = TestListParentModel.construct_recursive(
    #         test_list=[{"value": 21.0}, {"value": False}, {"value": "True"}]
    #     )

    #     expected_jsonable = {
    #         "test_list": [
    #             {"value": "21.0"},
    #             {"value": "false"},
    #             {"value": '"True"'},
    #         ]
    #     }

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable

    # def test_construct_recursive_for_nested_list_of_normal_types(self):
    #     """
    #     Like the test above, but this time for a list with conventional
    #     types as items.

    #     Note: This also tests if `jsonable()` handles this case correctly.
    #     """

    #     class TestListModel(_BaseModel):
    #         __root__: List[str]

    #     class TestListParentModel(_BaseModel):
    #         test_list: TestListModel

    #     obj = TestListParentModel.construct_recursive(
    #         test_list=["21.0", "false", "True"]
    #     )

    #     expected_jsonable = {"test_list": ["21.0", "false", "True"]}

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable

    # def test_construct_recursive_for_nested_dicts(self):
    #     """
    #     Some models (like GeographicPositionDict) are defined directly with a
    #     dict as root type. Check recursive construction works for those too.
    #     """

    #     class TestDictItemModel(_BaseModel):
    #         value: Json

    #     class TestDictModel(_BaseModel):
    #         __root__: Dict[str, TestDictItemModel]

    #     class TestDictParentModel(_BaseModel):
    #         test_dict: TestDictModel

    #     obj = TestDictParentModel.construct_recursive(
    #         test_dict={
    #             "1": {"value": 21.0},
    #             "2": {"value": False},
    #             "3": {"value": "True"},
    #         }
    #     )

    #     expected_jsonable = {
    #         "test_dict": {
    #             "1": {"value": "21.0"},
    #             "2": {"value": "false"},
    #             "3": {"value": '"True"'},
    #         }
    #     }

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable

    # def test_construct_recursive_for_nested_dict_of_normal_types(self):
    #     """
    #     Like the test above, but this time for a list with conventional
    #     types as items.

    #     Note: This also tests if `jsonable()` handles this case correctly.
    #     """

    #     class TestDictModel(_BaseModel):
    #         __root__: Dict[str, str]

    #     class TestDictParentModel(_BaseModel):
    #         test_dict: TestDictModel

    #     obj = TestDictParentModel.construct_recursive(
    #         test_dict={"1": "21.0", "2": "false", "3": "True"}
    #     )

    #     expected_jsonable = {
    #         "test_dict": {"1": "21.0", "2": "false", "3": "True"}
    #     }

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable

    # def test_construct_recursive_for_nested_model(self):
    #     """
    #     Check that child models in lists are instantiated correctly
    #     """

    #     class TestChildModel(_BaseModel):
    #         value: Json

    #     class TestParentModel(_BaseModel):
    #         child: TestChildModel

    #     obj = TestParentModel.construct_recursive(**{"child": {"value": 21.0}})  # NOQA -> line too ling while commented out.

    #     expected_jsonable = {
    #         "child": {"value": "21.0"},
    #     }

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable

    # def test_construct_recursive_for_none_nested_model_(self):
    #     """
    #     Check that child models are handled correctly if they are set to None.
    #     """

    #     class TestChildModel(_BaseModel):
    #         value: Json

    #     class TestParentModel(_BaseModel):
    #         child: TestChildModel

    #     obj = TestParentModel.construct_recursive(**{"child": None})

    #     expected_jsonable = {
    #         "child": None,
    #     }

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable

    # def test_construct_recursive_for_list_field_with_None_value(self):
    #     """
    #     A list item holding a None value (instead of a list) might happen
    #     but has caused errors in construct_recursive.
    #     """

    #     class TestListModel(_BaseModel):
    #         value: List[str]

    #     obj = TestListModel.construct_recursive(
    #         value=None,
    #     )

    #     expected_jsonable = {"value": None}

    #     actual_jsonable = obj.jsonable()

    #     assert actual_jsonable == expected_jsonable


class TestBaseModel(CustomModelMixinTests):
    """
    Verify that functionality of the custom `_BaseModel` as well as the
    correct operation of `CustomModelMixin`.

    These tests are certainly partly redundant to the tests of the models
    derived from `_BaseModel`. However, if the tests of this class fail
    you know that any downstream failure is due to errors in `_BaseModel`.
    """

    def setup_method(self, method):
        """
        Provide a simple model suitable for many tests.
        """

        class GenericTestModel(_BaseModel):
            value: float
            float_field: float
            string_field: str
            time: datetime

        self.GenericTestModel = GenericTestModel

        self.generic_test_obj_python_values = {
            "value": 21.1,
            "float_field": 22.2,
            "string_field": "23.3",
            "time": datetime(2022, 2, 22, 2, 53, tzinfo=timezone.utc),
        }

        self.generic_test_obj = GenericTestModel.model_construct(
            **self.generic_test_obj_python_values
        )

        self.generic_test_obj_jsonable = {
            "value": 21.1,
            "float_field": 22.2,
            "string_field": "23.3",
            "time": "2022-02-22T02:53:00Z",
        }

        self.generic_test_obj_jsonable_bemcom = {
            "value": "21.1",
            "float_field": 22.2,
            "string_field": "23.3",
            "timestamp": 1645498380000,
        }


class TestRootModel(CustomModelMixinTests):
    """
    Verify that functionality of the custom `_RootModel`. Note, this doesn't
    tests
    """

    @classmethod
    def setup_class(cls):
        """
        Define model used for all tests here.
        """

        class TestListItemModel(BaseModel):
            value: float

        cls.TestListItemModel = TestListItemModel

        class TestListModel(RootModel):
            root: List[TestListItemModel]

        cls.TestListModel = TestListModel

        cls.test_obj = [{"value": 21.0}, {"value": 22.5}]

    def setup_method(self, method):
        """
        Provide a simple model suitable for many tests.
        """

        class ListItemModel(_BaseModel):
            value: float
            float_field: float
            string_field: str
            time: datetime

        class GenericTestModel(_RootModel):
            root: List[ListItemModel]

        self.GenericTestModel = GenericTestModel

        self.generic_test_obj_python_values = [
            {
                "value": 21.1,
                "float_field": 22.2,
                "string_field": "23.3",
                "time": datetime(2022, 2, 22, 2, 53, tzinfo=timezone.utc),
            },
            {
                "value": 21.1,
                "float_field": 22.2,
                "string_field": "23.3",
                "time": datetime(2022, 2, 22, 2, 53, tzinfo=timezone.utc),
            },
            {
                "value": 21.1,
                "float_field": 22.2,
                "string_field": "23.3",
                "time": datetime(2022, 2, 22, 2, 53, tzinfo=timezone.utc),
            },
        ]

        self.generic_test_obj = GenericTestModel.model_validate(
            self.generic_test_obj_python_values
        )

        self.generic_test_obj_jsonable = [
            {
                "value": 21.1,
                "float_field": 22.2,
                "string_field": "23.3",
                "time": "2022-02-22T02:53:00Z",
            },
            {
                "value": 21.1,
                "float_field": 22.2,
                "string_field": "23.3",
                "time": "2022-02-22T02:53:00Z",
            },
            {
                "value": 21.1,
                "float_field": 22.2,
                "string_field": "23.3",
                "time": "2022-02-22T02:53:00Z",
            },
        ]

        self.generic_test_obj_jsonable_bemcom = [
            {
                "value": "21.1",
                "float_field": 22.2,
                "string_field": "23.3",
                "timestamp": 1645498380000,
            },
            {
                "value": "21.1",
                "float_field": 22.2,
                "string_field": "23.3",
                "timestamp": 1645498380000,
            },
            {
                "value": "21.1",
                "float_field": 22.2,
                "string_field": "23.3",
                "timestamp": 1645498380000,
            },
        ]
