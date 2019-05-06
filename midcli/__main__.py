import argparse
import os

from prompt_toolkit import print_formatted_text as print
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
from .key_bindings import get_key_bindings
from .parser import parse


class CLI(object):

    default_prompt = '%h[%n]> '

    def __init__(self, websocket=None, user=None, password=None, show_urls=False):
        self.context = Context(self, websocket=websocket, user=user, password=password)
        self.show_urls = show_urls
        self.completer = MidCompleter(self.context)

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

    def run(self):
        history_file = '~/.midcli.hist'
        history = FileHistory(os.path.expanduser(history_file))

        self.prompt_app = self._build_cli(history)

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
                parsed = parse(text)
                if parsed:
                    self.context.do_input(parsed)
        except EOFError:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--websocket')
    parser.add_argument('--user')
    parser.add_argument('--password')
    parser.add_argument('--show-urls', action='store_true')
    args = parser.parse_args()

    cli = CLI(**args.__dict__)
    cli.run()


if __name__ == '__main__':
    main()
