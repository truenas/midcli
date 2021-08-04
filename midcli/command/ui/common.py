# -*- coding=utf-8 -*-
import logging
import os

from midcli.command.interface import Command

logger = logging.getLogger(__name__)

__all__ = ["BackCommand", "ExitCommand", "LsCommand", "ManCommand", "QuestionCommand", "RootCommand"]


class BackCommand(Command):
    builtin = True
    hidden = True
    name = ".."
    description = "Go one level up"

    def process_input(self, text):
        parent = self.namespace.parent
        if parent:
            self.context.current_namespace = parent


class ExitCommand(Command):
    builtin = True
    hidden = True
    name = "exit"
    aliases = ["quit"]
    description = "Exit CLI"

    def process_input(self, text):
        os._exit(0)


class LsCommand(Command):
    builtin = True
    hidden = True
    name = "ls"
    description = "List available directories and commands"

    def process_input(self, text):
        commands = []
        for i in sorted(self.namespace.children):
            if i == self:
                continue

            if isinstance(i, Command):
                if i.hidden:
                    continue

            commands.append(i)

        print_commands(commands)


class ManCommand(Command):
    builtin = True
    hidden = True
    name = "man"
    description = "Show help and examples for specific command"

    def process_input(self, text):
        path = (text or "").split()
        if not path:
            print("Usage: man <command>")
            return

        command = self.namespace.find(path)
        if not command:
            print(f"Command `{' '.join(path)}` not found")
            return

        if not isinstance(command, Command):
            print(f"`{' '.join(path)}` is not a command")
            return

        print((command.man or f"No documentation found for `{' '.join(path)}`").rstrip())

        if command.examples:
            print('\n' + '\033[1m' + 'Examples' + '\033[0m' + '\n')
            print(''.join(command.examples).strip())


class QuestionCommand(Command):
    builtin = True
    hidden = True
    name = "?"
    aliases = ["help"]
    description = "List available built-in commands"

    def process_input(self, text):
        commands = []
        for i in self.namespace.children:
            if isinstance(i, self.namespace.__class__):
                continue

            if not i.builtin:
                continue

            commands.append(i)

        print_commands(commands)


class RootCommand(Command):
    builtin = True
    hidden = True
    name = "/"
    description = "Go to the root level"

    def process_input(self, text):
        self.context.current_namespace = self.context.namespaces.root


def print_commands(commands):
    if not commands:
        return

    max_name_length = max(len(i.name) for i in commands)

    for i in commands:
        print(i.name + " " * (max_name_length - len(i.name)) + (f" - {i.description}" if i.description else ""))
