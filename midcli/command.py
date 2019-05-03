import pprint

from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.completion import Completion

from .parser import Argument as ParserArgument


class Arg(object):

    def __init__(self, name, argtype=None, null=False, required=False, choices=None):
        assert argtype in ('string', 'list', 'boolean', 'integer'), argtype
        self.name = name
        self.argtype = argtype
        self.choices = choices
        self.null = null
        self.required = required

    def __repr__(self):
        return f'Arg[{self.name}<{self.argtype}>]'

    def clean(self, value):
        if self.argtype == 'boolean':
            if isinstance(value, str) and value.lower() in ('true', 'false', '1', '0'):
                return bool(value)
        elif self.argtype == 'list':
            if isinstance(value, str):
                return value.split(',')
        return value


class Command(object):

    args = []
    hidden = False
    name = None
    parent = None

    def __init__(self, context, namespace, name=None, args=None):
        self.context = context
        self.namespace = namespace
        if name:
            self.name = name
        if args:
            self.args = args

    def __repr__(self):
        return f'Command<{self.name}>'

    def _process_args(self, parsed=None):
        data = {}

        if not parsed:
            return data

        for i in parsed:
            if not isinstance(i, ParserArgument):
                print(f'invalid argument {i}')
                return
            data[i.key] = i.value

        args = {}
        for arg in self.args:
            if arg.name not in data:
                if arg.required:
                    print(f'argument required {arg.name!r}')
                    return
                continue
            v = data.pop(arg.name)
            args[arg.name] = arg.clean(v)

        if data:
            print(f'invalid arguments: {", ".join(data.keys())}')
            return
        return args

    def do_input(self, parsed=None):
        args = self._process_args(parsed)
        self.run(args)

    def run(self, args):
        raise NotImplementedError

    def get_completions(self, text):
        lastarg = text.split(' ')[-1]
        for i in self.args:
            if i.name.startswith(lastarg):
                yield Completion(f'{i.name}=', -len(lastarg), i.name)
            if lastarg == f'{i.name}=':
                for c in i.choices or []:
                    yield Completion(c[0], 0, c[1])


class CallMixin(object):

    output = True
    job_lastdesc = ''

    def __init__(self, *args, **kwargs):
        if 'output' in kwargs:
            self.output = kwargs.pop('output')
        super().__init__(*args, **kwargs)

    def job_callback(self, job):
        desc = job['progress']['description']
        if desc is not None and desc != self.job_lastdesc:
            print(desc)
        self.job_lastdesc = desc

    def call(self, name, *args, job=False):
        try:
            with self.context.get_client() as c:
                rv = c.call(name, *args, job=job, callback=self.job_callback)
        except Exception as e:
            print(e)
        else:
            if self.output:
                pprint.pprint(rv)


class CallCommand(CallMixin, Command):

    def __init__(self, *args, method=None, **kwargs):
        self.method = method
        self.args, self.arg_position = self._schemas_to_args(method['accepts'])
        super().__init__(*args, **kwargs)

    def _schema_to_arg(self, name, schema):
        if 'type' not in schema:
            return
        if 'enum' in schema:
            choices = [(c, c) for c in schema['enum']]
        else:
            choices = None
        argtype = schema['type'][0] if isinstance(schema['type'], list) else schema['type']
        if argtype == 'array':
            argtype = 'list'
        return Arg(
            name=name,
            argtype=argtype,
            null='null' in schema['type'],
            required=schema.get('_required_') is True,
            choices=choices,
        )

    def _schemas_to_args(self, schemas):
        arg_position = {}
        args = []
        for i, schema in enumerate(schemas or []):
            if 'properties' in schema:
                for name, sch in schema['properties'].items():
                    if sch.get('type') == 'object':
                        continue
                    arg = self._schema_to_arg(name, sch)
                    if arg:
                        args.append(arg)
                    arg_position[name] = {'position': i, 'type': 'dict'}
            else:
                name = schema['title']
                arg = self._schema_to_arg(name, schema)
                if arg:
                    args.append(arg)
                arg_position[name] = {'position': i, 'type': 'unique'}
        return args, arg_position

    def do_input(self, parsed=None):
        args = self._process_args(parsed)
        midargs = []
        arg_position = {}
        for name, v in args.items():

            position = self.arg_position[name]
            if position['type'] == 'dict':
                if position['position'] not in arg_position:
                    arg_position[position['position']] = {}
                arg_position[position['position']][name] = v
            else:
                arg_position[position['position']] = v

        for i in sorted(arg_position.items()):
            midargs.append(i[1])

        self.call(self.method['name'], *midargs, job=self.method['job'])


class QueryCommand(CallMixin, Command):

    args = (
        Arg('select', argtype='list'),
    )

    def __init__(self, *args, method=None, **kwargs):
        self.method = method
        super().__init__(*args, **kwargs)

    def run(self, args):
        filters = []
        options = {}
        if 'select' in args:
            options['select'] = args.pop('select')
        self.call(self.method['name'], filters, options)


class BackCommand(Command):
    name = '..'

    def run(self, args):
        parent = self.namespace.parent
        if parent:
            self.context.current_namespace = parent


class ListCommand(Command):
    name = 'list'

    def run(self, args):
        for i in self.namespace.children:
            if i == self:
                continue
            if isinstance(i, Command):
                if i.hidden:
                    continue
            print(i.name)


class QuestionCommand(Command):
    hidden = True
    name = '?'

    def run(self, args):
        for i in self.namespace.children:
            if isinstance(i, self.namespace.__class__):
                continue
            print(i.name)
