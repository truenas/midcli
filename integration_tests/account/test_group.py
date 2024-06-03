# -*- coding=utf-8 -*-
import pytest

from truenas_api_client import Client

from midcli.utils.test import command_test


@pytest.fixture
def delete_test_group():
    with Client() as c:
        g = c.call("group.query", [["group", "=", "test"]])
        if g:
            c.call("group.delete", g[0]["id"])


@pytest.fixture
def create_test_group():
    with Client() as c:
        c.call("group.create", {
            "name": "test",
        })
        return c.call("group.query", [["group", "=", "test"]], {"get": True})["gid"]


test_account_group_query_1 = lambda: command_test(
    "account group query * WHERE gid == 0",
    regex="gid,name.+\n0,root"
)
test_account_group_query_2 = lambda: command_test(
    "account group query gid",
    regex="gid\n"
)
test_account_group_query_3 = lambda: command_test(
    "account group query unknown_field",
    regex="None of the specified fields"
)

test_group_create_1 = lambda: command_test(
    "account group create users=[\"nonexistentuser\"]",
    regex="Validation errors:\n"
          ".*"
          "\* group_create.users.0: User 'nonexistentuser' does not exist",
)
test_group_create_2 = lambda: command_test(
    "account group create users=[\"root\"]",
    regex="Validation errors:\n"
          ".*"
          "\* group_create.name: attribute required",
)
test_group_create_3 = lambda delete_test_group: command_test(
    "account group create name=test users=[\"root\"]",
    text="",
)
test_group_create_4 = lambda delete_test_group: command_test(
    "account group create name=test users=[0]",
    text="",
)

test_account_group_update_1 = lambda delete_test_group, create_test_group: command_test(
    f"account group update {create_test_group} sudo=true",
    text="",
)
test_account_group_update_2 = lambda delete_test_group, create_test_group: command_test(
    "account group update test sudo=true",
    text="",
)
test_account_group_update_3 = lambda delete_test_group, create_test_group: command_test(
    f"account group update {create_test_group}",
    extra_args=["--print-template"],
    regex=".*\n"
          f"gid_or_name: {create_test_group}\n"
          ".*"
          "  \# name: test",
)
test_account_group_update_4 = lambda delete_test_group, create_test_group: command_test(
    f"account group update test",
    extra_args=["--print-template"],
    regex=".*\n"
          f"gid_or_name: test\n"
          ".*"
          "  \# name: test",
)

test_account_group_delete_1 = lambda delete_test_group, create_test_group: command_test(
    f"account group delete {create_test_group}",
    text="",
)
test_account_group_delete_2 = lambda delete_test_group, create_test_group: command_test(
    "account group delete test",
    text="",
)
