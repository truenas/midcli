# -*- coding=utf-8 -*-
import inspect
import threading
from unittest.mock import Mock

from truenas_api_client import ClientException, JSONRPCClient

from midcli.before_prompt import BeforePrompt


def make_client(**results):
    """Fake API client that answers the calls the prompt status thread makes."""
    client = Mock()
    client.call = Mock(side_effect=lambda method, *args: results[method])
    client._jobs = {}
    client._jobs_lock = threading.Lock()
    return client


def test_no_pending_changes():
    client = make_client(**{"interface.checkin_waiting": None, "interface.has_pending_changes": False})
    before_prompt = BeforePrompt(lambda: client)

    before_prompt.refresh(client)

    assert before_prompt.get_before_prompt() == ""


def test_checkin_waiting():
    client = make_client(**{"interface.checkin_waiting": 42})
    before_prompt = BeforePrompt(lambda: client)

    before_prompt.refresh(client)

    assert "rolled back in 42 seconds" in before_prompt.get_before_prompt()


def test_pending_changes():
    client = make_client(**{"interface.checkin_waiting": None, "interface.has_pending_changes": True})
    before_prompt = BeforePrompt(lambda: client)

    before_prompt.refresh(client)

    assert "network interface commit" in before_prompt.get_before_prompt()


def test_client_error_clears_message():
    client = make_client()
    client.call = Mock(side_effect=ClientException("connection closed"))
    before_prompt = BeforePrompt(lambda: client)
    before_prompt.before_prompt = "stale"

    before_prompt.refresh(client)

    assert before_prompt.get_before_prompt() == ""


def test_job_records_are_discarded_after_every_refresh():
    client = make_client(**{"interface.checkin_waiting": None, "interface.has_pending_changes": False})
    before_prompt = BeforePrompt(lambda: client)

    # Job updates the client hears about while the connection is open pile up here.
    client._jobs[1] = {"id": 1, "state": "SUCCESS", "result": "x" * 1000}
    client._jobs[2] = {"id": 2, "state": "RUNNING"}

    before_prompt.refresh(client)

    assert client._jobs == {}


def test_job_records_are_discarded_even_when_the_call_fails():
    client = make_client()
    client.call = Mock(side_effect=ClientException("connection closed"))
    client._jobs[1] = {"id": 1, "state": "SUCCESS"}
    before_prompt = BeforePrompt(lambda: client)

    before_prompt.refresh(client)

    assert client._jobs == {}


def test_real_client_still_keeps_job_records_where_we_clear_them():
    # We reach into the client library to drop its job records. Make sure the names we rely on
    # are still the ones its job update handler writes to, so a rename there fails here instead
    # of in the prompt thread on a live console.
    source = inspect.getsource(JSONRPCClient._jobs_callback)

    assert "self._jobs_lock" in source
    assert "self._jobs[" in source
