# -*- coding=utf-8 -*-
import logging

logger = logging.getLogger(__name__)

__all__ = ["object_to_yaml_arg", "property_to_yaml_arg"]


def object_to_yaml_arg(schema, object):
    result = {}
    for k, v in object.items():
        property = schema["properties"].get(k)
        if property is None:
            continue

        result[k] = property_to_yaml_arg(property, v)

    return result


def property_to_yaml_arg(property, value):
    if isinstance(value, dict) and "integer" in (property.get("type") or []):  # both "integer" and ["integer", "null"]
        return value["id"]

    return value
