# -*- coding=utf-8 -*-
import errno
import textwrap
from unittest.mock import Mock

from midcli.editor.yaml.render import render_yaml

CLOUD_SYNC_CREATE_SCHEMA = {
    "accepts": [
        {
            "_attrs_order_": ["bwlimit"],
            "_name_": "cloud_sync_create",
            "properties": {
                "bwlimit": {
                    "_name_": "bwlimit",
                    "_required_": False,
                    "default": [],
                    "items": [
                        {
                            "_attrs_order_": [
                                "time",
                                "bandwidth"
                            ],
                            "_name_": "cloud_sync_bwlimit",
                            "_required_": False,
                            "additionalProperties": False,
                            "default": {},
                            "properties": {
                                "bandwidth": {
                                    "_name_": "bandwidth",
                                    "_required_": True,
                                    "description": "bandwidth",
                                    "type": [
                                        "integer",
                                        "null"
                                    ]
                                },
                                "time": {
                                    "_name_": "time",
                                    "_required_": True,
                                    "description": "time",
                                    "type": "string"
                                }
                            },
                            "description": "cloud_sync_bwlimit",
                            "type": "object"
                        }
                    ],
                    "description": "bwlimit",
                    "type": "array"
                },
            },
            "description": "cloud_sync_create",
            "type": "object",
        },
    ],
}


def test_renders_new():
    assert render_yaml(CLOUD_SYNC_CREATE_SCHEMA, [], []) == textwrap.dedent("""\
        # Object: cloud_sync_create
        cloud_sync_create:
          # Array: bwlimit
          # bwlimit:
            # Object: cloud_sync_bwlimit
            # - # String: time
            #   time:

            #   # Integer | Null: bandwidth
            #   bandwidth:


    """)


def test_renders_existing():
    assert render_yaml(CLOUD_SYNC_CREATE_SCHEMA, [
        {
            "bwlimit": [
                {"time": "09:00", "bandwidth": 512000},
                {"time": "18:00 ", "bandwidth": None},
            ],
        }
    ], [
        Mock(attribute="cloud_sync_create.bwlimit.1.time", errmsg="Incorrect time", errno=errno.EINVAL),
    ]) == textwrap.dedent("""\
        # Object: cloud_sync_create
        cloud_sync_create:
          # Array: bwlimit
          bwlimit:
            # Object: cloud_sync_bwlimit
            - # String: time
              time: 09:00

              # Integer | Null: bandwidth
              bandwidth: 512000

            # Object: cloud_sync_bwlimit
            - # String: time
              # ERROR: Incorrect time
              time: '18:00 '

              # Integer | Null: bandwidth
              bandwidth:


    """)
