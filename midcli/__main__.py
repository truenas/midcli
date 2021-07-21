import argparse
import asyncio
import os
import sys
import threading
import time

from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.application import get_app, run_in_terminal
from prompt_toolkit.completion import DynamicCompleter, ThreadedCompleter
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.filters import HasFocus, IsDone
from prompt_toolkit.history import FileHistory
from prompt_toolkit.layout.processors import (
    ConditionalProcessor, HighlightMatchingBracketProcessor, TabsProcessor,
)
from prompt_toolkit.shortcuts import PromptSession, CompleteStyle

from .completer import MidCompleter
from .context import Context
from .editor.interactive import InteractiveEditor
from .editor.noninteractive import NonInteractiveEditor
from .editor.print_template import PrintTemplateEditor
from .key_bindings import get_key_bindings


class CLI:

    default_prompt = '[%h]%_n> '

    def __init__(self, websocket=None, user=None, password=None, show_urls=False, command=None, interactive=None,
                 mode=None, print_template=False):
        if command is None or interactive:
            editor = InteractiveEditor()
        elif print_template:
            editor = PrintTemplateEditor()
        else:
            editor = NonInteractiveEditor()

        self.context = Context(self, websocket=websocket, user=user, password=password,
                               editor=editor, mode=mode)
        self.show_urls = show_urls
        self.command = command
        self.completer = MidCompleter(self.context)

        self.last_kernel_message = None
        self.loop = None

    def _build_cli(self, history):
        def get_message():
            prompt = self.context.get_prompt(self.default_prompt)
            return [('class:prompt', prompt)]

        prompt_app = PromptSession(
            message=get_message,
            complete_style=CompleteStyle.COLUMN,
            completer=ThreadedCompleter(
                DynamicCompleter(lambda: self.completer)
            ),
            complete_while_typing=True,
            editing_mode=EditingMode.VI,
            enable_system_prompt=True,
            enable_suspend=True,
            history=history,
            input_processors=[
                # Highlight matching brackets while editing.
                ConditionalProcessor(
                    processor=HighlightMatchingBracketProcessor(
                        chars='[](){}',
                    ),
                    filter=HasFocus(DEFAULT_BUFFER) & ~IsDone()),
                # Render \t as 4 spaces instead of "^I"
                TabsProcessor(char1=' ', char2=' ')],
            key_bindings=get_key_bindings(),
            search_ignore_case=True,
        )

        return prompt_app

    def _read_kmsg(self):
        with open("/dev/kmsg") as f:
            while True:
                f.readline()
                self.last_kernel_message = time.monotonic()

    def _repaint_cli_after_kernel_messages(self):
        while True:
            if self.last_kernel_message is not None and time.monotonic() - self.last_kernel_message >= 3:
                self.last_kernel_message = None
                self.loop.call_soon_threadsafe(lambda: run_in_terminal(lambda: None))

            time.sleep(1)

    def run(self):
        if self.command is not None:
            self.context.process_input(self.command)
            return

        history_file = '~/.midcli.hist'
        history = FileHistory(os.path.expanduser(history_file))

        self.prompt_app = self._build_cli(history)
        self.loop = asyncio.get_event_loop()

        is_tty1 = False
        try:
            is_tty1 = os.ttyname(sys.stdout.fileno()) == '/dev/tty1'
        except Exception:
            pass
        if is_tty1:
            threading.Thread(target=self._read_kmsg).start()
            threading.Thread(target=self._repaint_cli_after_kernel_messages).start()

        print()
        print('*' * 60)
        print('Software in ALPHA state, highly experimental.')
        print('No bugs/features being accepted at the moment.')
        print('*' * 60)
        print()

        if self.show_urls:
            with self.context.get_client() as c:
                try:
                    urls = c.call('system.general.get_ui_urls')
                except Exception:
                    pass
                else:
                    print()
                    print('The web user interface is at:')
                    for url in urls:
                        print(url)
                    print()

        try:
            while True:
                try:
                    text = self.prompt_app.prompt()
                except KeyboardInterrupt:
                    continue

                self.context.process_input(text)
        except EOFError:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--websocket')
    parser.add_argument('--user')
    parser.add_argument('--password')
    parser.add_argument('--show-urls', action='store_true')
    parser.add_argument('-c', '--command',
                        help='Single command to execute')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='If -c/--command is specified, execute it in interactive mode')
    parser.add_argument('-m', '--mode',
                        help='Output display mode')
    parser.add_argument('--print-template', action='store_true',
                        help='If -c/--command is specified, print its YAML template instead of executing it')
    args = parser.parse_args()

    cli = CLI(**args.__dict__)
    cli.run()


if __name__ == '__main__':
    main()
