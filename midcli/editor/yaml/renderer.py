# -*- coding=utf-8 -*-
import logging
import textwrap

from yaml import SafeDumper
import yaml

from midcli.utils.lang import undefined

from .schema_visitor import Parent
from .values_aware_schema_visitor import Value, ValuesAwareSchemaVisitor

logger = logging.getLogger(__name__)

__all__ = ["YamlRenderer"]

SafeDumper.add_representer(
    type(None),
    lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:null", "")
)


class YamlRenderer(ValuesAwareSchemaVisitor):
    def __init__(self, schema, values, errors):
        super().__init__(schema, values)

        self.errors = errors

        self.terminal_width = 80
        self.indent_width = 2

    def render(self):
        result = self._walk_args()

        if self.errors:
            result.insert(0, textwrap.indent(
                "".join(textwrap.wrap(
                    "".join(self._render_errors(self.errors)), self.terminal_width - 2, replace_whitespace=False,
                )),
                "# ",
            ) + "\n\n")

        return "".join(result)

    def _walk_object_node(self, name, item, value, context, result):
        field_errors = self._field_errors(value)

        rendered = [self._comment(context.depth, item, field_errors)]
        result = sum([[s, "\n"] for s in result], [])
        if context.parent == Parent.OBJECT:
            rendered.append(
                " " * context.depth * self.indent_width +
                self._nonscalar_prefix(value, context) +
                f"{item['_name_']}:\n"
            )
        else:
            lines = result[0].split("\n")

            line = lines[0]

            width = context.depth * self.indent_width

            content = line[width + self.indent_width:]

            lines[0] = line[:width] + "- " + content

            result[0] = "\n".join(lines)

        rendered.extend(result)

        if item.get("additionalProperties") and value.value != undefined:
            rendered.extend(textwrap.indent(yaml.safe_dump(value.value), " " * (context.depth + 1) * self.indent_width))

        return "".join(rendered)

    def _walk_list_node(self, name, item, value, context):
        field_errors = self._field_errors(value)

        list_values = self._get_list_values(value)
        schema_items = item.get("items", [])
        uncommented_empty_list = value.value != undefined and not list_values and not schema_items
        rendered = [
            self._comment(context.depth, item, field_errors),
            (
                " " * context.depth * self.indent_width +
                self._nonscalar_prefix(value, context) +
                f"{item['_name_']}:{' []' if uncommented_empty_list else ''}\n"
            ),
        ]
        if list_values:
            for i, node_value in enumerate(list_values):
                rendered.append(
                    self._walk_node(None, item["items"][0], node_value, context.child().replace(
                        render_title=i == 0,
                        parent=Parent.ARRAY,
                    ))
                )
        elif schema_items:
            # Render examples
            for schema in schema_items:
                lines = []
                for line in self._walk_node(None, schema, Value([], [], undefined), context.child().child().replace(
                    parent=Parent.ARRAY,
                )).split("\n"):
                    # Comment out rendered example
                    if line:
                        width = (context.depth + 1) * self.indent_width

                        content = line[width + self.indent_width:]
                        if not content.startswith("# "):
                            insertion = "# "
                        else:
                            insertion = ""

                        line = line[:width] + insertion + content

                    lines.append(line)

                rendered.append("\n".join(lines))

        return "".join(rendered)

    def _walk_scalar_node(self, name, item, value, context):
        inspection = self._inspect_scalar_result(item, value)

        field_errors = self._field_errors(value)

        if context.parent == Parent.OBJECT:
            dump = yaml.safe_dump({item["_name_"]: inspection.value})
        else:
            dump = yaml.safe_dump([inspection.value])

        rendered = [
            self._comment(context.depth, item, field_errors, context.render_title),
            textwrap.indent(
                dump,
                f"{' ' * context.depth * self.indent_width}{'# ' if inspection.commented_out else ''}",
            ),
        ]

        return "".join(rendered)

    def _comment(self, depth, item, errors, render_title=True):
        prefix = " " * depth * self.indent_width + "# "

        if isinstance(item.get("type"), list):
            type_title = " | ".join([t.title() for t in item["type"]])
        else:
            type_title = item.get("type", "Parameter").title()

        if item.get("description"):
            description = item["description"].rstrip()
            title = f"{type_title}: {description}\n"
        else:
            title = f"{type_title}\n"

        comment_text = "".join(([title] if render_title else []) + self._render_errors(errors))

        return textwrap.indent(
            "".join(textwrap.wrap(comment_text, self.terminal_width - len(prefix), replace_whitespace=False,
                                  drop_whitespace=False)),
            prefix,
        )

    def _render_errors(self, errors):
        return [f"ERROR: {error.errmsg}\n" for error in errors]

    def _field_errors(self, value):
        field_errors = []
        other_errors = []
        for error in self.errors:
            if error.attribute == ".".join(value.schema_path):
                field_errors.append(error)
            else:
                other_errors.append(error)
        self.errors = other_errors

        return field_errors

    def _nonscalar_prefix(self, value, context):
        if value.value == undefined and context.depth > 0:
            return "# "
        else:
            return ""
