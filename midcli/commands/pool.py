from ..command import Arg, CallMixin, Command


class PoolCreateCommand(Command, CallMixin):

    args = (
        Arg('name', argtype='string', required=True),
        Arg('disks', argtype='list', required=True),
        Arg('type', argtype='string', required=True),
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

