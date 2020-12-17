import re

from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.completion import Completion

from middlewared.client import Client

from .command.generic_call import GenericCallCommand
from .command.interface import Command
from .command.query.command import QueryCommand
from .command.ui.common import BackCommand, LsCommand, QuestionCommand
from .command.ui.display_mode import ModeCommand
# from .command.pool import PoolCreateCommand
from .display_mode.manager import DisplayModeManager
from .display_mode.mode.csv import CsvDisplayMode
from .display_mode.mode.table import TableDisplayMode


class Namespace(object):

    parent = None

    def __init__(self, context, name, description=""):
        self.context = context
        self.name = name
        self.description = description
        self.children = [
            BackCommand(context, self),
            LsCommand(context, self),
            QuestionCommand(context, self),
            ModeCommand(context, self),
        ]

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
            if i.name == cur:
                if path:
                    return i.find(path)
                return i
        return None

    def process_input(self, text):
        name, rest = self._shift(text)

        for i in self.children:
            if i.name == name:
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
        # 'pool.create': PoolCreateCommand,
    }

    def __init__(self, context, client):
        self.context = context
        self.root = Namespace(context, None)
        self.build_namespaces(client)

    def build_namespaces(self, client):
        methods = client.call('core.get_methods', None, True)
        services = client.call('core.get_services', True)
        for fullname, method in methods.items():
            service_name, name = fullname.rsplit('.', 1)
            service = services[service_name]

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
            if fullname in self.METHOD_OVERRIDE:
                command = self.METHOD_OVERRIDE[fullname](self.context, namespace, name)
            else:
                kwargs = {}
                service_type = service['type']
                if (
                    (service_type == 'crud' and name in ['create', 'update', 'delete']) or
                    (service_type == 'config' and name == 'update')
                ):
                    kwargs['output'] = False

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

                command = command(self.context, namespace, name, method['cli_description'], method=method, **kwargs)

            namespace.add_child(command)


class Context(object):

    def __init__(self, cli, websocket=None, user=None, password=None):
        self.cli = cli
        self.websocket = websocket
        self.user = user
        self.password = password
        with self.get_client() as c:
            self.namespaces = Namespaces(self, c)
            self.system_info = c.call('system.info')
        self.current_namespace = self.namespaces.root
        self.display_mode_manager = DisplayModeManager({
            "csv": CsvDisplayMode,
            "table": TableDisplayMode,
        }, "table")

    def get_client(self):
        try:
            c = Client(self.websocket)
        except (FileNotFoundError, ConnectionRefusedError):
            exit('middlewared is not running.')

        if self.user and self.password:
            c.call('auth.login', self.user, self.password)
        return c

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
        prompt = prompt.replace('%h', self.system_info['hostname'].split('.', 1)[0])
        return prompt

    def process_input(self, text):
        namespace = self.current_namespace.process_input(text)
        if namespace:
            self.current_namespace = namespace

    def get_completions(self, text, current=None):
        if current is None:
            current = self.current_namespace
        return current.get_completions(text)
