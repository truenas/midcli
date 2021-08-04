# -*- coding=utf-8 -*-
import logging

logger = logging.getLogger(__name__)

__all__ = ["YamlToArgsError", "yaml_to_args"]


class YamlToArgsError(Exception):
    pass


def yaml_to_args(schema, doc):
    if doc is None:
        return []

    if not isinstance(doc, dict):
        raise YamlToArgsError(f"The document you provided is not an object (it is {type(doc)})")

    args = []
    for i, (item, (key, value)) in enumerate(zip(schema["accepts"], doc.items())):
        if item["_name_"] != key:
            raise YamlToArgsError(
                f"Element #{i + 1} should be {item['_name_']!r}, {key!r} given"
            )

        if item.get("type") == "object" and value is None:
            # This happens when user is offered to edit a document like:
            # options:
            #   # Use force
            #   # force: false
            # and they are satisfied with the defaults
            value = {}

        args.append(value)

    return args
