import errno
import re
import socket
import time

from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.completion import Completion

from truenas_api_client import Client, ClientException

from .command.generic_call import GenericCallCommand
from .command.generic_call.update import UpdateCommand
from .command.interface import Command
from .command.override.account import *
from .command.override.api_key import *
from .command.override.interface import *
from .command.query.command import QueryCommand
from .command.tools import ShellCommand
from .command.ui.common import *
from .command.ui.display_mode import ModeCommand
from .command.ui.stacks import StacksCommand
from .display_mode.manager import DisplayModeManager
from .display_mode.mode.csv import CsvDisplayMode
from .display_mode.mode.table import TableDisplayMode
from .utils.shell import is_main_cli, spawn_shell


class Namespace(object):

    parent = None

    def __init__(self, context, name, description=""):
        self.context = context
        self.name = name
        self.aliases = []
        self.description = description
        self.children = list(filter(None, [
            BackCommand(context, self),
            ExitCommand(context, self),
            LsCommand(context, self),
            ManCommand(context, self),
            MenuCommand(context, self),
            QuestionCommand(context, self),
            RootCommand(context, self),
            ShellCommand(context, self) if is_main_cli() else None,
            ModeCommand(context, self),
            StacksCommand(context, self),
        ]))

    def __repr__(self):
        return f"Namespace<{self.name}>"

    def __lt__(self, other):
        return self.name < other.name

    def add_child(self, namespace):
        assert isinstance(namespace, (Command, Namespace))
        self.children.append(namespace)
        namespace.parent = self

    def find(self, path):
        cur = path[0]
        path = path[1:]
        for i in self.children:
            if cur in [i.name] + i.aliases:
                if path:
                    return i.find(path)
                return i
        return None

    def process_input(self, text):
        if not text.strip():
            return

        name, rest = self._shift(text)

        for i in self.children:
            if name in [i.name] + i.aliases:
                if isinstance(i, Namespace):
                    if rest:
                        return i.process_input(rest)
                    return i
                elif isinstance(i, Command):
                    i.process_input(rest)
                    return

        print(f"Namespace {name} not found")

    def get_completions(self, text):
        name, rest = self._shift(text)

        for i in self.children:
            if isinstance(i, Command) and i.builtin:
                continue
            if i.name.startswith(name):
                if rest is not None:
                    if i.name == name:
                        for c in i.get_completions(rest):
                            yield c
                else:
                    yield Completion(i.name, - len(name))

        return []

    def _shift(self, text):
        parsed = re.split(r"\s+", text.lstrip(), maxsplit=1)

        name = parsed[0]

        rest = parsed[1] if len(parsed) > 1 else None

        return name, rest


class Namespaces(object):

    METHOD_OVERRIDE = {
        'account.user.query': AccountQueryCommand,
        'account.user.create': AccountCreateCommand,
        'account.user.update': AccountUpdateCommand,
        'account.user.delete': AccountItemMethodCommand,
        'account.user.shell_choices': ShellChoicesCommand,
        'account.group.query': GroupQueryCommand,
        'account.group.create': GroupCreateCommand,
        'account.group.update': GroupUpdateCommand,
        'account.group.delete': GroupItemMethodCommand,
        'auth.api_key.create': ApiKeyCreateCommand,
        'network.interface.query': InterfaceQueryCommand,
        'network.interface.create': InterfaceCreateCommand,
        'network.interface.update': InterfaceUpdateCommand,
    }

    def __init__(self, context, client):
        self.context = context
        self.root = Namespace(context, None)
        self.build_namespaces(client)

    def build_namespaces(self, client):
        for fullname, method in self.context.methods.items():
            service_name, name = fullname.rsplit('.', 1)
            service = self.context.services[service_name]

            namespace = self.root

            path = service['config']['cli_namespace'].split('.')

            for i, item in enumerate(path):
                tmp = namespace.find([item])
                if not tmp:
                    tmp = Namespace(self.context, item)
                    namespace.add_child(tmp)
                namespace = tmp
                if i == len(path) - 1:
                    namespace.description = service['config']['cli_description']

            method['name'] = fullname

            command = self.METHOD_OVERRIDE.get(f"{service['config']['cli_namespace']}.{name}") or GenericCallCommand
            kwargs = {}

            service_type = service['type']
            if (
                (service_type == 'crud' and name in ['create', 'update', 'delete']) or
                (service_type == 'config' and name == 'update')
            ):
                kwargs['output'] = False

            if command == GenericCallCommand:
                if method['filterable']:
                    command = QueryCommand
                else:
                    command = GenericCallCommand

            if (
                (service_type == 'crud' and name == 'create') or
                (service_type == 'config' and name == 'update')
            ):
                kwargs['splice_kwargs'] = 0
            elif service_type == 'crud' and name == 'update':
                kwargs['splice_kwargs'] = 1
                if command == GenericCallCommand:
                    command = UpdateCommand

            command = command(self.context, namespace, name, method['cli_description'], method['description'],
                              method['examples'].get('cli'), method=method, **kwargs)

            namespace.add_child(command)


class Context:
    def __init__(self, cli, url, user, password, timeout, editor, menu, menu_item, mode, stacks):
        self.cli = cli
        self.url = url
        self.user = user
        self.password = password
        self.timeout = timeout
        self.reload()
        with self.get_client() as c:
            self.methods = c.call('core.get_methods', None, 'CLI')
            self.services = c.call('core.get_services', 'CLI')
            self.namespaces = Namespaces(self, c)
        self._current_namespace = self.namespaces.root
        self.display_mode_manager = DisplayModeManager({
            "csv": CsvDisplayMode,
            "table": TableDisplayMode,
        }, mode or "table")
        self.stacks = stacks
        self.editor = editor
        self.menu = menu
        self.menu_item = menu_item

    @property
    def current_namespace(self):
        return self._current_namespace

    @current_namespace.setter
    def current_namespace(self, namespace):
        self._current_namespace = namespace
        self.show_banner()

    def show_banner(self):
        if self._current_namespace == self.namespaces.root:
            print('Type "ls" (followed by Enter) to list available configuration options')
        else:
            names = []
            ns = self._current_namespace
            while True:
                names.insert(0, ns.name)
                if ns.parent == self.namespaces.root:
                    break
                else:
                    ns = ns.parent
            name = ' '.join(names)

            commands = []
            for ns in self._current_namespace.children:
                if isinstance(ns, Command) and not ns.builtin:
                    commands.append(ns.name)

            print(f'Type "ls" (followed by Enter) to list available {name} configuration options')

            if commands:
                command = 'create' if 'create' in commands else commands[0]
                print('Type "man" (followed by Action) to get help on how to use the specific Action.')
                print()
                print('i.e.')
                print(f'\tman {command}')

    def reload(self):
        with self.get_client() as c:
            self.hostname = c.call('system.hostname')

    def get_client(self):
        recoverable_errors = 0
        while True:
            try:
                c = Client(self.url, private_methods=True, call_timeout=self.timeout)

                if self.user and self.password:
                    if not c.call('auth.login', self.user, self.password):
                        raise Exception("Invalid username or password")

                return c
            except Exception as e:
                recoverable_error = False
                if isinstance(e, (FileNotFoundError, ConnectionRefusedError)):
                    error = 'middleware is not running'
                elif isinstance(e, socket.timeout):
                    error = 'middleware is not responding'
                    recoverable_error = True
                elif isinstance(e, ClientException) and e.errno == ClientException.ENOTAUTHENTICATED:
                    error = 'You are not authorized to use TrueNAS CLI'
                elif isinstance(e, ClientException) and e.error == 'Failed connection handshake':
                    error = e.error
                    recoverable_error = True
                else:
                    error = f'Unknown middleware error: {e!r}'

                if recoverable_error and recoverable_errors < 5:
                    recoverable_errors += 1
                    time.sleep(2)
                    continue

                if is_main_cli():
                    print(f'{error}. Press Enter to open shell.')
                    input()
                    spawn_shell()
                else:
                    exit(f'{error}.')

    def get_before_prompt(self):
        items = []

        with self.get_client() as c:
            try:
                if checkin_waiting := c.call('interface.checkin_waiting'):
                    n = int(checkin_waiting)
                    items.append(
                        'Network interface changes have been applied. Please run `network interface checkin`\n'
                        f'if the network is still operational or they will be rolled back in {n} seconds.'
                    )
                elif c.call('interface.has_pending_changes'):
                    items.append(
                        'You have pending network interface changes. Please run `network interface commit`\n'
                        'to apply them.'
                    )
            except ClientException as e:
                if e.errno != errno.EACCES:
                    raise

        if items:
            return '\n'.join(items) + '\n'

        return ''

    def get_prompt(self, prompt):
        current = self.current_namespace
        path = []
        while current:
            if current.name:
                path.insert(0, current.name)
            current = current.parent
        namespaces = ' '.join(path)
        prompt = prompt.replace('%n', namespaces)
        prompt = prompt.replace('%_n', f' {namespaces}' if namespaces else '')
        prompt = prompt.replace('%h', self.hostname.split('.', 1)[0])
        return prompt

    def process_input(self, text):
        namespace = self.current_namespace.process_input(text)
        if namespace:
            self.current_namespace = namespace

    def get_completions(self, text, current=None):
        if current is None:
            current = self.current_namespace
        return current.get_completions(text)
