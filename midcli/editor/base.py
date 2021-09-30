# -*- coding=utf-8 -*-
import logging

logger = logging.getLogger(__name__)

__all__ = ["Editor"]


class Editor:
    def is_available(self):
        """
        Should return `False` if interactive editor is not available.
        """
        return True

    def edit(self, schema, values, errors):
        """
        Offer user to edit YAML arguments for method call defined by `schema`.
        `values` will be inserted instead of defaults and `errors` will be displayed in the comments section.
        """
        raise NotImplementedError

    def on_error(self, title, text):
        """
        Handle error.
        Returns `True` if user wants to retry, else returns `False`
        """
        raise NotImplementedError
