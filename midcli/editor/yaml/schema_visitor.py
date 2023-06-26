# -*- coding=utf-8 -*-
from dataclasses import dataclass, replace
import enum
import logging

logger = logging.getLogger(__name__)

__all__ = ["SchemaVisitor"]


class Parent(enum.Enum):
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class SchemaVisitorContext:
    depth: int
    render_title: bool
    parent: Parent

    def replace(self, **kwargs):
        return replace(self, **kwargs)

    def child(self):
        return self.replace(depth=self.depth + 1)


class SchemaVisitor:
    def __init__(self, schema):
        self.schema = schema

    def _walk_args(self):
        result = []
        for i, item in enumerate(self.schema["accepts"]):
            result.append(self._walk_node(item["_name_"], item, self._get_arg_value(i), SchemaVisitorContext(
                depth=0,
                parent=Parent.OBJECT,
                render_title=True,
            )))

        return result

    def _walk_node(self, name, item, value, context):
        if item.get("type") == "object":
            result = []
            for property_name in item["_attrs_order_"]:
                child = item["properties"][property_name]

                child_value = self._get_object_child_value(value, property_name)

                result.append(self._walk_node(property_name, child, child_value, context.child().replace(
                    parent=Parent.OBJECT,
                    render_title=True,
                )))

            return self._walk_object_node(name, item, value, context, result)
        elif item.get("type") == "array":
            return self._walk_list_node(name, item, value, context)
        else:
            return self._walk_scalar_node(name, item, value, context)

    def _get_arg_value(self, i):
        raise NotImplementedError

    def _get_object_child_value(self, value, property_name):
        raise NotImplementedError

    def _walk_object_node(self, name, item, value, context, result):
        raise NotImplementedError

    def _walk_list_node(self, name, item, value, context):
        raise NotImplementedError

    def _walk_scalar_node(self, name, item, value, context):
        raise NotImplementedError
