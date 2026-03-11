import argparse
import asyncio
import errno
import os
import signal
import sys
import threading
import time
import json

from prompt_toolkit import print_formatted_text as print
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.completion import DynamicCompleter, ThreadedCompleter
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.filters import HasFocus, IsDone
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.layout.processors import (
    ConditionalProcessor, HighlightMatchingBracketProcessor, TabsProcessor,
)
from prompt_toolkit.shortcuts import PromptSession, CompleteStyle
from prompt_toolkit.styles import Style

from .before_prompt import BeforePrompt
from .completer import MidCompleter
from .command.interface import ProcessInputError
from .context import Context
from .editor.interactive import InteractiveEditor
from .editor.noninteractive import NonInteractiveEditor
from .editor.print_template import PrintTemplateEditor
from .key_bindings import get_key_bindings
from .menu.items import get_menu_items, process_menu_item
from .pager import enable_pager
from .utils.shell import is_main_cli, switch_to_shell


class CLI:
    default_prompt = '[%h]%_n> '

    def __init__(self, url=None, user=None, password=None, timeout=None, command=None, interactive=None, menu=False,
                 menu_item=None, mode=None, pager=False, print_template=False, stacks=False, vendor="TrueNAS"):
        if command is None or interactive:
            editor = InteractiveEditor()
        elif print_template:
            editor = PrintTemplateEditor()
        else:
            editor = NonInteractiveEditor()

        if pager:
            enable_pager()

        self.context = Context(self, url=url, user=user, password=password, timeout=timeout,
                               editor=editor, menu=menu, menu_item=menu_item, mode=mode, stacks=stacks, vendor=vendor)

        self.command = command
        self.completer = MidCompleter(self.context)

        self.last_kernel_message = None
        self.loop = None

    def _build_menu(self, menu_items):
        def get_message():
            prompt = '\n'.join([
                f'{i}) {title}'
                for i, (title, _) in enumerate(menu_items, start=1)
            ]) + f'\n\nEnter an option from 1-{len(menu_items)}: '
            return [
                ('class:prompt', prompt),
            ]

        prompt_app = PromptSession(
            message=get_message,
            complete_style=CompleteStyle.COLUMN,
            editing_mode=EditingMode.VI,
            enable_system_prompt=True,
            enable_suspend=True,
        )

        return prompt_app

    def _build_cli(self, history):
        before_prompt = BeforePrompt(self.context.get_client)
        before_prompt.start()

        def get_message():
            prompt = self.context.get_prompt(self.default_prompt)
            return [
                ('class:before_prompt', before_prompt.get_before_prompt()),
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

        if not self.context.menu:
            self.context.show_banner()

    def _show_urls(self):
        with self.context.get_client() as c:
            try:
                urls = c.call('system.general.get_ui_urls')
            except Exception:
                pass
            else:
                print()
                if urls:
                    print('The web user interface is at:')
                    for url in urls:
                        print(url)
                else:
                    print('The web interface could not be accessed.')
                    print('Please check network configuration.')
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

    def _sigusr1_handler(self):
        self.context.reload()
        self.loop.call_soon_threadsafe(self._repaint_cli)

    def run(self):
        if self.command is not None:
            try:
                self.context.process_input(self.command)
            except ProcessInputError as e:
                sys.stderr.write(e.error.rstrip("\n") + "\n")
                sys.exit(1)

            return

        if self._should_switch_to_shell():
            self._show_urls()
            switch_to_shell()
            return

        history_file = os.path.expanduser('~/.midcli.hist')
        try:
            with open(history_file, "a"):
                pass

            history = FileHistory(history_file)
        except Exception as e:
            if e.errno != errno.EPERM:
                print(f'INFO: Unable to open history file: {e} (Using in memory history).')
            history = InMemoryHistory()

        self.loop = asyncio.get_event_loop()

        self.loop.add_signal_handler(signal.SIGUSR1, self._sigusr1_handler)

        is_tty1 = False
        try:
            is_tty1 = os.ttyname(sys.stdout.fileno()) == '/dev/tty1'
        except Exception:
            pass
        if is_tty1:
            # https://www.freedesktop.org/software/systemd/man/systemd.html#SIGRTMIN+21
            # SIGRTMIN+21 - Disables display of status messages on the console, as controlled via
            # systemd.show_status=0 on the kernel command line.
            os.kill(1, signal.SIGRTMIN + 21)

            threading.Thread(daemon=True, target=self._read_kmsg).start()
            threading.Thread(daemon=True, target=self._repaint_cli_after_kernel_messages).start()

        if is_main_cli():
            print()
            print('Console setup')
            print('_____________')

            self._show_banner()

        try:
            menu_items = get_menu_items(self.context)
            menu_app = self._build_menu(menu_items)
            prompt_app = self._build_cli(history)

            while True:
                if self.context.menu_item:
                    process_menu_item(self.context, menu_items, self.context.menu_item)
                    break
                elif self.context.menu:
                    try:
                        text = menu_app.prompt()
                    except KeyboardInterrupt:
                        continue

                    process_menu_item(self.context, menu_items, text)
                else:
                    try:
                        text = prompt_app.prompt()
                    except KeyboardInterrupt:
                        continue

                    try:
                        self.context.process_input(text)
                    except ProcessInputError as e:
                        print(e.error.rstrip("\n") + "\n")
        except EOFError:
            os._exit(0)


def main_console():
    """This is called in console_scripts section of setup.py so that
    we install a binary called "cli_console" so that executing the CLI
    launching the console directly can be done. This is used by local
    users that have set their shell to `/usr/bin/cli_console`."""
    cli = CLI(menu=True)
    cli.run()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url')
    parser.add_argument('--user')
    parser.add_argument('--password')
    parser.add_argument('--timeout', type=int, default=1200,
                        help='Timeout for executing non-job commands (in seconds)')
    parser.add_argument('-c', '--command',
                        help='Execute single command')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='If -c/--command is specified, execute it in interactive mode')
    parser.add_argument('--menu', action='store_true',
                        help='Show shortcut menu')
    parser.add_argument('--menu-item',
                        help='Activate shortcut menu item')
    parser.add_argument('-m', '--mode',
                        help='Output display mode')
    parser.add_argument('--pager', action='store_true',
                        help='Use pager to display commands output')
    parser.add_argument('--print-template', action='store_true',
                        help='If -c/--command is specified, print its YAML template instead of executing it')
    parser.add_argument('--stacks', action='store_true',
                        help='Display errors stack trace')
    args = parser.parse_args()

    vendor = "TrueNAS"
    try:
        with open("/data/.vendor") as f:
            vendor = json.loads(f.read()).get("name", "TrueNAS")
    except Exception:
        pass

    cli = CLI(vendor=vendor, **args.__dict__)
    cli.run()


if __name__ == '__main__':
    main()
