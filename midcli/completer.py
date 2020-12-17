from prompt_toolkit.completion import Completer


class MidCompleter(Completer):

    def __init__(self, context):
        self.context = context
        super().__init__()

    def get_completions(self, document, complete_event):
        for i in self.context.get_completions(document.text):
            yield i
