# -*- coding=utf-8 -*-
import errno
import logging

from truenas_api_client import ClientException, ValidationErrors

from midcli.command.common_syntax.argument import EnumArgument
from midcli.command.generic_call import GenericCallCommand
from midcli.command.generic_call.update import UpdateCommand
from midcli.command.query.command import QueryCommand
from midcli.utils.lang import undefined

from .utils import remove_fields, rows_processor

logger = logging.getLogger(__name__)

__all__ = ["AccountQueryCommand", "AccountCreateCommand", "AccountUpdateCommand", "AccountItemMethodCommand",
           "GroupQueryCommand", "GroupCreateCommand", "GroupUpdateCommand", "GroupItemMethodCommand",
           "ShellChoicesCommand"]

remove_id = remove_fields("id")


def get_groups(context):
    with context.get_client() as c:
        return [g["group"] for g in c.call("group.query", [], {"select": ["group"], "order_by": ["group"]})]


@rows_processor
def patch_users(context, users):
    with context.get_client() as c:
        groups = {
            group["id"]: group["group"]
            for group in c.call("group.query", [], {"select": ["id", "group"]})
        }

    for user in users:
        user["group"].pop("id")
        user["group"] = {k[len("bsdgrp_"):]: v for k, v in user["group"].items()}

        user["groups"] = [groups[id] for id in user["groups"]]


class AccountQueryCommand(QueryCommand):
    output_processors = [remove_id, patch_users]


class AccountCommandMixin:
    def _process_key(self, key):
        with self.context.get_client() as c:
            if isinstance(key, str):
                filter = [["username", "=", key]]
            else:
                filter = [["uid", "=", key]]

            try:
                return c.call(
                    "user.query",
                    filter,
                    {"get": True},
                )["id"]
            except ClientException:
                raise ValidationErrors([(
                    f'{self.method["accepts"][0]["_name_"]}',
                    f"User {key!r} does not exist",
                    errno.ENOENT,
                )])

    def _process_value(self, value):
        with self.context.get_client() as c:
            if "group" in value:
                try:
                    value["group"] = self._get_group(c, value["group"])
                except ClientException:
                    raise ValidationErrors([(
                        f'{self.method["accepts"][0]["_name_"]}.group',
                        f"Group {value['group']!r} does not exist",
                        errno.ENOENT,
                    )])

            if "groups" in value:
                for i, group in enumerate(value["groups"]):
                    try:
                        value["groups"][i] = self._get_group(c, group)
                    except ClientException:
                        raise ValidationErrors([(
                            f'{self.method["accepts"][0]["_name_"]}.groups.{i}',
                            f"Group {group!r} does not exist",
                            errno.ENOENT,
                        )])

    def _get_group(self, c, key):
        if isinstance(key, str):
            filter = [["group", "=", key]]
        else:
            filter = [["gid", "=", key]]

        return c.call(
            "group.query",
            filter,
            {"get": True},
        )["id"]

    def _create_argument(self, item):
        if item["_name_"] == "group":
            return EnumArgument("group", False, item.get("default", undefined), enum=lambda: get_groups(self.context))

        return super()._create_argument(item)


class AccountCreateCommand(AccountCommandMixin, GenericCallCommand):
    def _process_method(self, method):
        method["accepts"][0]["properties"]["group"]["type"] = ["integer", "string"]
        return method

    def _process_call_args(self, values):
        if values:
            self._process_value(values[0])
        return values


class AccountUpdateCommand(AccountCommandMixin, UpdateCommand):
    def _process_method(self, method):
        method["accepts"][0]["_name_"] = "uid_or_username"
        method["accepts"][0]["type"] = ["integer", "string"]
        method["accepts"][1]["properties"]["group"]["type"] = ["integer", "string"]
        return method

    def _process_call_args(self, values):
        values = list(values)
        if values:
            values[0] = self._process_key(values[0])
            if len(values) > 1:
                self._process_value(values[1])
        return values

    def _get_instance_call_arg(self, pk):
        return self._process_key(pk)


class AccountItemMethodCommand(AccountCommandMixin, GenericCallCommand):
    def _process_method(self, method):
        method["accepts"][0]["type"] = ["integer", "string"]
        return method

    def _process_call_args(self, values):
        values = list(values)
        if values:
            values[0] = self._process_key(values[0])
        return values


@rows_processor
def patch_groups(context, groups):
    with context.get_client() as c:
        users = {
            user["id"]: user["username"]
            for user in c.call("user.query", [], {"select": ["id", "username"]})
        }

    for i, group in enumerate(groups):
        groups[i] = group = {
            k: group[k]
            for k in ["gid", "name"] + [k for k in group.keys() if k not in ["gid", "group", "name"]]
            if k in group
        }

        group["users"] = [users[id] for id in group["users"]]


class GroupQueryCommand(QueryCommand):
    output_processors = [remove_id, patch_groups]


class GroupCommandMixin:
    def _process_key(self, key):
        with self.context.get_client() as c:
            if isinstance(key, str):
                filter = [["group", "=", key]]
            else:
                filter = [["gid", "=", key]]

            try:
                return c.call(
                    "group.query",
                    filter,
                    {"get": True},
                )["id"]
            except ClientException:
                raise ValidationErrors([(
                    f'{self.method["accepts"][0]["_name_"]}',
                    f"Group {key!r} does not exist",
                    errno.ENOENT,
                )])

    def _process_value(self, value):
        with self.context.get_client() as c:
            if "users" in value:
                for i, user in enumerate(value["users"]):
                    try:
                        value["users"][i] = self._get_user(c, user)
                    except ClientException:
                        raise ValidationErrors([(
                            f'{self.method["accepts"][0]["_name_"]}.users.{i}',
                            f"User {user!r} does not exist",
                            errno.ENOENT,
                        )])

    def _get_user(self, c, key):
        if isinstance(key, str):
            filter = [["username", "=", key]]
        else:
            filter = [["uid", "=", key]]

        return c.call(
            "user.query",
            filter,
            {"get": True},
        )["id"]


class GroupCreateCommand(GroupCommandMixin, GenericCallCommand):
    def _process_call_args(self, values):
        if values:
            self._process_value(values[0])
        return values


class GroupUpdateCommand(GroupCommandMixin, UpdateCommand):
    def _process_method(self, method):
        method["accepts"][0]["_name_"] = "gid_or_name"
        method["accepts"][0]["type"] = ["integer", "string"]
        return method

    def _process_call_args(self, values):
        values = list(values)
        if values:
            values[0] = self._process_key(values[0])
            if len(values) > 1:
                self._process_value(values[1])
        return values

    def _get_instance_call_arg(self, pk):
        return self._process_key(pk)


class GroupItemMethodCommand(GroupCommandMixin, GenericCallCommand):
    def _process_method(self, method):
        method["accepts"][0]["type"] = ["integer", "string"]
        return method

    def _process_call_args(self, values):
        values = list(values)
        if values:
            values[0] = self._process_key(values[0])
        return values


class ShellChoicesCommand(GroupCommandMixin, GenericCallCommand):
    def _process_method(self, method):
        method["accepts"][0]["items"] = [{"type": "integer"}, {"type": "string"}]
        return method

    def _process_call_args(self, values):
        values = list(values)
        if values:
            values[0] = [self._process_key(v) for v in values[0]]
        return values
