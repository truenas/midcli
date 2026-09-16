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
                self.refresh(c)
                time.sleep(1)

    def refresh(self, c):
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

        discard_job_records(c)


def discard_job_records(c):
    """
    The API client subscribes every connection to job updates the first time it is used and
    keeps the last update of every job it hears about. That includes jobs started by other
    clients and the periodic jobs middleware runs on its own. Nothing ever removes them, so a
    connection that stays open for days grows without limit.

    The connection used here only asks whether network changes are pending and never reads
    these records, so throw them away after every check.
    """
    with c._jobs_lock:
        c._jobs.clear()
