import argparse
import asyncio
import os
import sys
import threading
import time

from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.completion import DynamicCompleter, ThreadedCompleter
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.filters import HasFocus, IsDone
from prompt_toolkit.history import FileHistory
from prompt_toolkit.layout.processors import (
    ConditionalProcessor, HighlightMatchingBracketProcessor, TabsProcessor,
)
from prompt_toolkit.shortcuts import PromptSession, CompleteStyle
from prompt_toolkit.styles import Style

from .completer import MidCompleter
from .context import Context
from .editor.interactive import InteractiveEditor
from .editor.noninteractive import NonInteractiveEditor
from .editor.print_template import PrintTemplateEditor
from .key_bindings import get_key_bindings
from .utils.shell import is_main_cli, switch_to_shell


class CLI:

    default_prompt = '[%h]%_n> '

    def __init__(self, websocket=None, user=None, password=None, command=None, interactive=None,
                 mode=None, print_template=False):
        if command is None or interactive:
            editor = InteractiveEditor()
        elif print_template:
            editor = PrintTemplateEditor()
        else:
            editor = NonInteractiveEditor()

        self.context = Context(self, websocket=websocket, user=user, password=password,
                               editor=editor, mode=mode)
        self.command = command
        self.completer = MidCompleter(self.context)

        self.last_kernel_message = None
        self.loop = None

    def _build_cli(self, history):
        def get_message():
            prompt = self.context.get_prompt(self.default_prompt)
            return [
                ('class:before_prompt', self.context.get_before_prompt()),
                ('class:prompt', prompt),
            ]

        prompt_app = PromptSession(
            message=get_message,
            style=Style.from_dict({
                'before_prompt': 'fg:ansigreen',
            }),
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

    def _show_banner(self):
        self._show_urls()

        print('Type "help" to list available commands.')
        print()

    def _show_urls(self):
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

    def _should_switch_to_shell(self):
        if is_main_cli():
            try:
                with self.context.get_client() as c:
                    return not c.call('system.advanced.config')['consolemenu']
            except Exception:
                pass

        return False

    def _read_kmsg(self):
        with open("/dev/kmsg") as f:
            # Skip existing messages
            os.set_blocking(f.fileno(), False)
            while f.readline():
                pass
            os.set_blocking(f.fileno(), True)

            while True:
                f.readline()
                self.last_kernel_message = time.monotonic()

    def _repaint_cli_after_kernel_messages(self):
        while True:
            if self.last_kernel_message is not None and time.monotonic() - self.last_kernel_message >= 3:
                self.last_kernel_message = None
                self.loop.call_soon_threadsafe(self._repaint_cli)

            time.sleep(1)

    def _repaint_cli(self):
        if is_main_cli():
            self._show_banner()

        run_in_terminal(lambda: None)

    def run(self):
        if self.command is not None:
            self.context.process_input(self.command)
            return

        if self._should_switch_to_shell():
            self._show_urls()
            switch_to_shell()
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

        if is_main_cli():
            print()
            print('Console setup')
            print('_____________')

            self._show_banner()

        try:
            while True:
                try:
                    text = self.prompt_app.prompt()
                except KeyboardInterrupt:
                    continue

                self.context.process_input(text)
        except EOFError:
            os._exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--websocket')
    parser.add_argument('--user')
    parser.add_argument('--password')
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
