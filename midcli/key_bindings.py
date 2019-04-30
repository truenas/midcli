from prompt_toolkit.filters import completion_is_selected
from prompt_toolkit.key_binding import KeyBindings


def get_key_bindings():
    key_bindings = KeyBindings()

    @key_bindings.add('tab')
    def _(event):
        """
        Force autocompletion at cursor.
        """
        b = event.current_buffer
        if b.complete_state:
            b.complete_next()
        else:
            b.start_completion(select_first=True)

    @key_bindings.add('enter', filter=completion_is_selected)
    def _(event):
        b = event.current_buffer
        b.complete_state = None
        b.insert_text(' ')

    return key_bindings
