import threading
import time

from truenas_api_client import ClientException


class BeforePrompt:
    def __init__(self, client_factory):
        self.client_factory = client_factory
        self.before_prompt = ""

    def start(self):
        threading.Thread(daemon=True, target=self._run).start()

    def get_before_prompt(self):
        return self.before_prompt

    def _run(self):
        with self.client_factory() as c:
            while True:
                items = []
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
                except ClientException:
                    pass

                if items:
                    self.before_prompt = "\n".join(items) + "\n"
                else:
                    self.before_prompt = ""

                time.sleep(1)
