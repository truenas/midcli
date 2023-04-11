__all__ = ["format_error", "format_validation_errors"]


def format_error(context, e):
    if e.error == "Pipe 'output' is not open":
        return "Please, specify the output file name using ' > filename.ext'"
    elif context.stacks:
        return e.trace["formatted"]
    elif e.trace:
        if e.trace["class"] == "CallError":
            return "Error: " + e.error.split("] ", 1)[1]
        else:
            return "Error: " + e.trace["repr"]
    else:
        return "Error: " + e.error


def format_validation_errors(e):
    return "\n".join([
        f"* {error.attribute}: {error.errmsg}" if error.attribute else f"* {error.errmsg}"
        for error in e.errors
    ])
