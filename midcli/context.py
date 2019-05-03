from middlewared.client import Client
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.completion import Completion

from .command import CallCommand, Command, BackCommand, ListCommand, QueryCommand
from .commands.pool import PoolCreateCommand
from .parser import Name


class Namespace(object):

    parent = None

    def __init__(self, context, name):
        self.context = context
        self.name = name
        self.children = [BackCommand(context, self), ListCommand(context, self)]

    def __repr__(self):
        return f'Namespace<{self.name}>'

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

    def do_input(self, parsed):
        if not parsed:
            print('namespace not found')
            return
        name = parsed[0]
        if not isinstance(name, Name):
            print(f'invalid namespace {name}')
            return

        parsed = parsed[1:]
        for i in self.children:
            if i.name == name:
                if isinstance(i, Namespace):
                    if parsed:
                        return i.do_input(parsed)
                    return i
                elif isinstance(i, Command):
                    i.do_input(parsed)
                    return
        print(f'namespace {name} not found')

    def get_completions(self, text):
        args = None
        if ' ' in text:
            text, args = text.split(' ', 1)
        for i in self.children:
            if i.name.startswith(text):
                if args is not None:
                    for c in i.get_completions(args):
                        yield c
                else:
                    yield Completion(i.name, - len(text))
        return []


class Namespaces(object):

    BLACKLIST = (
        'auth',
        'auth.twofactor',
        'mdnsbrowser',
        'backup',
        'backup.azure',
        'backup.b2',
        'backup.credential',
        'backup.gcs',
        'backup.s3',
        'reporting',
        'stats',
        'webui.image',
    )
    MAPPING = {
        'acme.dns.authenticator': ['system', 'acme_dns_auth'],
        'activedirectory': ['directoryservice', 'activedirectory'],
        'afp': ['service', 'afp'],
        'alert': ['system', 'alert'],
        'alertclasses': ['system', 'alertclasses'],
        'alertservice': ['system', 'alertservice'],
        'boot': ['system', 'boot'],
        'bootenv': ['system', 'bootenv'],
        'certificate': ['system', 'certificate'],
        'certificateauthority': ['system', 'certifiacteauthority'],
        'cloudsync': ['task', 'cloudsync'],
        'cloudsync.credentials': ['task', 'cloudsync', 'credentials'],
        'cronjob': ['task', 'cronjob'],
        'config': ['system', 'config'],
        'disk': ['storage', 'disk'],
        'device': ['system', 'device'],
        'dns': ['network', 'dns'],
        'dyndns': ['service', 'dyndns'],
        'filesystem': ['storage', 'filesystem'],
        'ftp': ['service', 'ftp'],
        'group': ['account', 'group'],
        'initshutdownscript': ['system', 'initshutdownscript'],
        'interface': ['network', 'interface'],
        'iscsi': ['service', 'iscsi'],
        'iscsi.auth': ['sharing', 'iscsi', 'auth'],
        'iscsi.extent': ['sharing', 'iscsi', 'extent'],
        'iscsi.initiator': ['sharing', 'iscsi', 'initiator'],
        'iscsi.portal': ['sharing', 'iscsi', 'portal'],
        'iscsi.target': ['sharing', 'iscsi', 'target'],
        'iscsi.targetextent': ['sharing', 'iscsi', 'targetextent'],
        'iscsi.global': ['service', 'iscsi'],
        'ipmi': ['network', 'ipmi'],
        'kerberos': ['directoryservice', 'kerberos'],
        'kerberos.keytab': ['directoryservice', 'kerberos', 'keytab'],
        'kerberos.realm': ['directoryservice', 'kerberos', 'realm'],
        'keychaincredential': ['system', 'keychaincredential'],
        'ldap': ['directoryservice', 'ldap'],
        'lldp': ['service', 'lldp'],
        'mail': ['system', 'mail'],
        'multipath': ['storage', 'multipath'],
        'netdata': ['service', 'netdata'],
        'nfs': ['service', 'nfs'],
        'nis': ['directoryservice', 'nis'],
        'pool': ['storage', 'pool'],
        'pool.snapshottask': ['task', 'snapshot'],
        'replication': ['task', 'replication'],
        'rsyncd': ['service', 'rsyncd'],
        'rsyncmod': ['service', 'rsyncmod'],
        'rsynctask': ['task', 'rsync'],
        'route': ['network', 'route'],
        's3': ['service', 's3'],
        'smart': ['service', 'smart'],
        'smart.test': ['task', 'smart'],
        'smb': ['service', 'smb'],
        'snmp': ['service', 'snmp'],
        'ssh': ['service', 'ssh'],
        'support': ['system', 'support'],
        'staticroute': ['network', 'staticroute'],
        'systemdataset': ['system', 'systemdataset'],
        'tftp': ['service', 'tftp'],
        'tunable': ['system', 'tunable'],
        'update': ['system', 'update'],
        'ups': ['service', 'ups'],
        'user': ['account', 'user'],
        'webdav': ['service', 'webdav'],
        'zfs.snapshot': ['storage', 'snapshot'],
    }
    METHOD_OVERRIDE = {
        'pool.create': PoolCreateCommand,
    }

    def __init__(self, context, client):
        self.context = context
        self.root = Namespace(context, None)
        self.build_namespaces(client)

    def build_namespaces(self, client):
        methods = client.call('core.get_methods')
        services = client.call('core.get_services')
        for fullname, method in methods.items():
            service, name = fullname.rsplit('.', 1)

            if service in self.BLACKLIST:
                continue

            namespace = self.root

            if service in self.MAPPING:
                path = self.MAPPING[service]
            else:
                path = service.split('.')

            for i in path:
                tmp = namespace.find([i])
                if not tmp:
                    tmp = Namespace(self.context, i)
                    namespace.add_child(tmp)
                namespace = tmp

            method['name'] = fullname
            if fullname in self.METHOD_OVERRIDE:
                command = self.METHOD_OVERRIDE[fullname](self.context, namespace, name)
            else:
                kwargs = {}
                if service in services:
                    service_type = services[service]['type']
                    if (
                        service_type == 'crud' and name in (
                            'create', 'update', 'delete',
                        )
                    ) or service_type in ('service', 'config') and name == 'update':
                        kwargs['output'] = False
                if method['filterable']:
                    command = QueryCommand
                else:
                    command = CallCommand

                command = command(self.context, namespace, name, method=method, **kwargs)
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

    def get_client(self):
        try:
            c = Client(self.websocket)
        except (FileNotFoundError, ConnectionRefusedError):
            exit('middlewared is not running.')

        if self.user and self.password:
            c.call('auth.login', self.user, self.password)
        return c

    def get_completions(self, text, current=None):
        if current is None:
            current = self.current_namespace
        return current.get_completions(text)

    def get_prompt(self, prompt):
        current = self.current_namespace
        path = []
        while current:
            if current.name:
                path.insert(0, current.name)
            current = current.parent
        namespaces = ' '.join(path)
        prompt = prompt.replace('%n', namespaces)
        prompt = prompt.replace('%h', self.system_info['hostname'].split('.', 1)[0])
        return prompt

    def do_input(self, text):
        namespace = self.current_namespace.do_input(text)
        if namespace:
            self.current_namespace = namespace
