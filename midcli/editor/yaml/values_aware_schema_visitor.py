# -*- coding=utf-8 -*-
from collections import namedtuple
import logging

from midcli.utils.lang import undefined

from .schema_visitor import SchemaVisitor

logger = logging.getLogger(__name__)

__all__ = ["ValuesAwareSchemaVisitor"]

ScalarResultInspection = namedtuple("ScalarResultInspection", ["commented_out", "value"])
Value = namedtuple("Value", ["schema_path", "object_path", "value"])


class ValuesAwareSchemaVisitor(SchemaVisitor):
    def __init__(self, schema, values):
        super().__init__(schema)
        self.values = values

    def _get_arg_value(self, i):
        return Value(
            schema_path=[self.schema["accepts"][i]["_name_"]],
            object_path=[i],
            value=self.values[i] if i < len(self.values) else undefined,
        )

    def _get_object_child_value(self, value, property_name):
        child_value = undefined
        if isinstance(value.value, dict):
            child_value = value.value.get(property_name, undefined)

        return Value(
            schema_path=value.schema_path + [property_name],
            object_path=value.object_path + [property_name],
            value=child_value,
        )

    def _get_list_values(self, value):
        return [
            Value(
                schema_path=value.schema_path + [f"{i}"],
                object_path=value.object_path + [i],
                value=child_value
            )
            for i, child_value in enumerate(value.value if isinstance(value.value, list) else [])
        ]

    def _inspect_scalar_result(self, item, value):
        if value.value is not undefined:
            commented_out = False
            render_value = value.value
        else:
            if item.get("_required_"):
                commented_out = False
            else:
                commented_out = True

            if "default" in item:
                render_value = item["default"]
            else:
                render_value = None

        return ScalarResultInspection(commented_out, render_value)
