__all__ = ["format_validation_errors"]


def format_validation_errors(e):
    return "\n".join([
        f"* {error.attribute}: {error.errmsg}" if error.attribute else f"* {error.errmsg}"
        for error in e.errors
    ])
