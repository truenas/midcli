from .call_mixin import CallMixin
from .common_syntax.command import Arg, CommonSyntaxCommand


class PoolCreateCommand(CallMixin, CommonSyntaxCommand):

    args = (
        Arg('name', argtype='string', required=True),
        Arg('disks', argtype='list', required=True),
        Arg('type', argtype='string', required=True, choices=(
            ('raidz1', 'raidz1'),
            ('raidz2', 'raidz2'),
            ('raidz3', 'raidz3'),
            ('mirror', 'mirror'),
            ('stripe', 'stripe'),
        ))
    )

    def run(self, args):
        data = {
            'name': args['name'],
            'topology': {
                'data': [{
                    'disks': args['disks'],
                    'type': args['type'].upper(),
                }],
            },
        }
        self.call('pool.create', data, job=True)
