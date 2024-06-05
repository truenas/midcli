# -*- coding=utf-8 -*-
import pytest

from truenas_api_client import Client

from midcli.utils.test import command_test


@pytest.fixture
def delete_test_user():
    with Client() as c:
        u = c.call("user.query", [["username", "=", "test"]])
        if u:
            c.call("user.delete", u[0]["id"])


@pytest.fixture
def create_test_user():
    with Client() as c:
        g = c.call("group.query", [["group", "=", "users"]], {"get": True})
        c.call("user.create", {
            "username": "test",
            "full_name": "test",
            "group": g["id"],
            "password_disabled": True,
        })
        return c.call("user.query", [["username", "=", "test"]], {"get": True})["uid"]


test_account_user_query = lambda: command_test(
    "account user query * WHERE uid == 0",
    regex="uid,username.+\n0,root"
)

test_account_user_create_1 = lambda: command_test(
    "account user create group=nonexistentgroup",
    regex="Validation errors:\n"
          ".*"
          "\* user_create.group: Group 'nonexistentgroup' does not exist",
)
test_account_user_create_2 = lambda: command_test(
    "account user create group=users",
    regex="Validation errors:\n"
          ".*"
          "\* user_create.username: attribute required",
)
test_account_user_create_3 = lambda delete_test_user: command_test(
    "account user create username=test full_name=test group=users password_disabled=true",
    text="",
)
test_account_user_create_4 = lambda delete_test_user: command_test(
    "account user create username=test full_name=test group=users groups=[\"www-data\"] password_disabled=true",
    text="",
)

test_account_user_update_1 = lambda delete_test_user, create_test_user: command_test(
    f"account user update {create_test_user} full_name=test",
    text="",
)
test_account_user_update_2 = lambda delete_test_user, create_test_user: command_test(
    "account user update test group=users",
    text="",
)
test_account_user_update_3 = lambda delete_test_user, create_test_user: command_test(
    f"account user update {create_test_user}",
    extra_args=["--print-template"],
    regex=".*\n"
          f"uid_or_username: {create_test_user}\n"
          ".*"
          "  \# full_name: test",
)
test_account_user_update_4 = lambda delete_test_user, create_test_user: command_test(
    f"account user update test",
    extra_args=["--print-template"],
    regex=".*\n"
          f"uid_or_username: test\n"
          ".*"
          "  \# full_name: test",
)
test_account_user_update_5 = lambda delete_test_user, create_test_user: command_test(
    f"account user update test",
    input={
        "uid_or_username": "test",
        "user_update": {"full_name": "Test"},
    },
    regex="",
)

test_account_user_delete_1 = lambda delete_test_user, create_test_user: command_test(
    f"account user delete {create_test_user}",
    text="",
)
test_account_user_delete_2 = lambda delete_test_user, create_test_user: command_test(
    "account user delete test",
    text="",
)
