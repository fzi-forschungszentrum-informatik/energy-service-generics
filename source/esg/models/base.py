"""
Provides the _BaseModel class which other models should be derived from.

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

from copy import deepcopy
from datetime import datetime
import json

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pydantic import RootModel

# You need these to enable construct_recursive
# from pydantic._internal import _model_construction
# from pydantic import fields
# ModelMetaclass = _model_construction.ModelMetaclass


class CustomModelMixin:
    """
    The main motivation is to add some convenience methods, especially
    for converting to BEMCom message format.
    """

    def model_dump_jsonable(self):
        """
        Create a dict representation of the model instance that be dumped
        directly with `json.dumps`. This makes use of this fastapi tool:
        https://fastapi.tiangolo.com/tutorial/encoder/#json-compatible-encoder

        Returns:
        --------
        obj_as_jsonable : object
            A Python object that can be converted to JSON.
        """
        obj_as_jsonable = jsonable_encoder(self)

        return obj_as_jsonable

    def model_dump_jsonable_bemcom(self):
        """
        Like `model_dump_jsonable()` but outputs the message in BEMCom format.

        One main difference here is that fields storing time values are
        named `timestamp` instead of `time` and that the values are encoded
        in a Unix Timestamp in milliseconds instead of a string. Furthermore
        value fields are encoded as JSON field in BEMCom messages.

        Returns:
        --------
        obj_as_jsonable : object
            A Python object that can be converted to JSON.
        """
        custom_json_encoders = {
            datetime: lambda dt: round(dt.timestamp() * 1000)
        }
        obj_as_jsonable = jsonable_encoder(
            self.model_dump(), custom_encoder=custom_json_encoders
        )

        # Convert the BEMCom specific fields, even the nested ones.
        def adapt_fields(obj_as_jsonable):
            if isinstance(obj_as_jsonable, list):
                # Catches objects with lists as root field.
                obj_as_jsonable = [adapt_fields(i) for i in obj_as_jsonable]
            elif isinstance(obj_as_jsonable, dict):
                for field_name in list(obj_as_jsonable):

                    if field_name == "time":
                        obj_as_jsonable["timestamp"] = obj_as_jsonable.pop(
                            "time"
                        )
                    elif field_name in ["value", "preferred_value"]:
                        obj_as_jsonable[field_name] = json.dumps(
                            obj_as_jsonable[field_name]
                        )
                    elif field_name == "acceptable_values":
                        all_avs = obj_as_jsonable[field_name]
                        if all_avs is not None:
                            avs_as_json = [json.dumps(v) for v in all_avs]
                            obj_as_jsonable[field_name] = avs_as_json
                    # Handles lists as values, e.g. for schedules and setpoints
                    elif isinstance(obj_as_jsonable[field_name], list):
                        obj_as_jsonable[field_name] = adapt_fields(
                            obj_as_jsonable[field_name]
                        )
                    # Handles dicts as values, e.g. message by datapoint id
                    elif isinstance(obj_as_jsonable[field_name], dict):
                        obj_as_jsonable[field_name] = adapt_fields(
                            obj_as_jsonable[field_name]
                        )
            return obj_as_jsonable

        obj_as_jsonable = adapt_fields(obj_as_jsonable)

        return obj_as_jsonable

    def model_dump_json_bemcom(self):
        """
        Like `model_dump_json()` but outputs the message in BEMCom format.

        Returns:
        --------
        obj_as_json : string
            The object represented as JSON string.
        """
        return json.dumps(self.model_dump_jsonable_bemcom())

    @classmethod
    def model_validate_bemcom(cls, obj):
        """
        Like pydantic's `model_validate` but adapting the BEMCom message.

        This renames the time fields (timestamps are parsed by pydantic).


        Arguments:
        ----------
        obj : dict
            A dictionary carrying the field_name, field_value pairs. See also:
            https://pydantic-docs.helpmanual.io/usage/models/#helper-functions

        Returns:
        --------
        obj : pydantic model object
            The parsed and validated model object.

        Raises:
        -------
        pydantic.error_wrappers.ValidationError:
            If anything goes wrong or the input is not a dict.
        """
        # Prevent side effect, i.e. the operations below would else
        # modify the original object.
        obj = deepcopy(obj)

        # Convert the BEMCom specific fields ...
        def adapt_fields(obj):
            print(obj)
            if isinstance(obj, list):
                # Catches objects with lists as root field.
                obj = [adapt_fields(i) for i in obj]
            elif isinstance(obj, dict):
                for field_name in list(obj):

                    if field_name == "timestamp":
                        obj["time"] = obj.pop("timestamp")
                    elif field_name in ["value", "preferred_value"]:
                        obj[field_name] = json.loads(obj[field_name])
                    elif field_name == "acceptable_values":
                        all_avs = obj[field_name]
                        if all_avs is not None:
                            avs_as_json = [json.loads(v) for v in all_avs]
                            obj[field_name] = avs_as_json
                    # Handles lists as values, e.g. for schedules and setpoints
                    elif isinstance(obj[field_name], list):
                        obj[field_name] = adapt_fields(obj[field_name])
                    # Handles dicts as values, e.g. message by datapoint id
                    elif isinstance(obj[field_name], dict):
                        obj[field_name] = adapt_fields(obj[field_name])
            return obj

        print(obj)
        obj = adapt_fields(obj)
        print(obj)

        return cls.model_validate(obj)

    @classmethod
    def model_validate_json_bemcom(cls, json_string):
        """
        Like pydantic's `model_validate_json` but adapting the BEMCom message.

        This

        Arguments:
        ----------
        json_string : string
            A JSON string carrying the field_name, field_value pairs. See also:
            https://pydantic-docs.helpmanual.io/usage/models/#helper-functions

        Returns:
        --------
        obj : pydantic model object
            The parsed and validated model object.

        Raises:
        -------
        pydantic.error_wrappers.ValidationError:
            If anything goes wrong or the input is not a JSON string.
        """
        jsonable = json.loads(json_string)
        return cls.model_validate_bemcom(jsonable)

    # NOTE:
    # -----
    # Since pydantic V2 this may not be significantly faster any more. See:
    # https://docs.pydantic.dev/latest/usage/models/#creating-models-without-validation
    # We hence disable this but leave it here if it may become relevant
    # in future.

    # @classmethod
    # def construct_recursive(cls, **values):
    #     """
    #     Recursively construct the object from data.

    #     A wrapper around the `construct` method of pydantic that automatically
    #     creates the child models (in contrast to the original `construct`
    #     method which doesn't do that). The intended way in pydantic would be
    #     to use cls.validate which creates all the sub-models but at the price
    #     of running the full validation, which might be rather slow.

    #     ATTENTION:
    #     ----------
    #     Note that all sub-models that should be created must provide a
    #     `construct_recursive` method too.

    #     Arguments:
    #     ----------
    #     values : dict
    #         A dictionary carrying the field_name, field_value pairs.

    #     Returns:
    #     --------
    #     obj : pydantic model object
    #         The UNVALIDATED model object.
    #     """

    #     # Handle fields depending on category (shape in pydantic terminology)
    #     # See the pydantic code for definitions of shape:
    #     # https://github.com/samuelcolvin/pydantic/blob/d7a8272d7e0c151b0bd43df596be02e0d436ebdf/pydantic/fields.py#L322
    #     for name, field in cls.__fields__.items():

    #         if name not in values:
    #             # These hits for fields for which no value was provided.
    #             continue

    #         if field.shape == fields.SHAPE_SINGLETON:
    #             # This is a field which holds a normal value, like a float
    #             # a string or a nested model.
    #             if isinstance(field.type_, ModelMetaclass):
    #                 # This should only be true for nested models.
    #                 child_cls = field.type_
    #                 if "__root__" in child_cls.__fields__:
    #                     # This means that the nested model has a custom
    #                     # root type. We hence give the payload to root of
    #                     # this model and hope that it can cope with it.
    #                     values[name] = child_cls.construct_recursive(
    #                         __root__=values[name]
    #                     )
    #                 else:
    #                     # OK, no custom root type. Hence this should be normal
    #                     # single model. This also means that `values[name]`
    #                     # must be a dict to make sense.
    #                     # However, the child model could also be set to None.
    #                     if values[name] is not None:
    #                         values[name] = child_cls.construct_recursive(
    #                             **values[name]
    #                         )
    #             continue

    #         elif field.shape == fields.SHAPE_LIST and values[name] is not None:
    #             # This is field that holds a list. For such we iterate over
    #             # the items and construct each of those incl. all children.
    #             # But only for non None values (List could be set to None too).
    #             child_objects = []
    #             child_cls = field.type_
    #             if hasattr(child_cls, "construct_recursive"):
    #                 # Only call `construct_recursive` if the children actually
    #                 # have this method. This takes care that we don't try
    #                 # to call `construct_recursive` on normal strings, floats
    #                 # and other conventional types.
    #                 if "__root__" in child_cls.__fields__:
    #                     # Like above, distinguish between models that have
    #                     # custom root and those that have not.
    #                     for list_item in values[name]:
    #                         child_objects.append(
    #                             child_cls.construct_recursive(
    #                                 __root__=list_item
    #                             )
    #                         )
    #                 else:
    #                     for list_item in values[name]:
    #                         child_objects.append(
    #                             child_cls.construct_recursive(**list_item)
    #                         )
    #                 values[name] = child_objects

    #         elif field.shape == fields.SHAPE_DICT and values[name] is not None:
    #             # This field holds a dictionary. Like for list, we iterate
    #             # over all children and construct for each of those.
    #             child_objects = {}
    #             child_cls = field.type_
    #             if hasattr(child_cls, "construct_recursive"):
    #                 if "__root__" in child_cls.__fields__:
    #                     # Like above, distinguish between models that have
    #                     # custom root and those that have not.
    #                     for key, item in values[name].items():
    #                         child_objects[key] = child_cls.construct_recursive(
    #                             __root__=item
    #                         )
    #                 else:
    #                     for key, item in values[name].items():
    #                         child_objects[key] = child_cls.construct_recursive(
    #                             **item
    #                         )
    #                 values[name] = child_objects

    #     obj = cls.construct(**values)
    #     return obj


class _BaseModel(BaseModel, CustomModelMixin):
    """
    This overloads the pydantic.BaseModel with a custom adapted version.
    """

    pass


class _RootModel(RootModel, CustomModelMixin):
    """
    This overloads the pydantic.BaseModel with a custom adapted version.
    """

    pass
