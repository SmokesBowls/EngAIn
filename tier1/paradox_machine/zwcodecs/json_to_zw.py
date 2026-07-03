import json
import re
from typing import Any


def convert_to_upper_snake_case(s: Any) -> str:
    s = str(s)
    s_upper = s.upper()
    s_clean = re.sub(r"[^A-Z0-9_\-]+", "_", s_upper)
    s_clean = re.sub(r"__+", "_", s_clean)
    s_clean = s_clean.strip("_")
    return s_clean


def is_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


def format_scalar(value: Any, in_list: bool = False) -> str:
    if isinstance(value, str):
        if in_list and re.fullmatch(r"[A-Z0-9_\-]+", value):
            return value
        return json.dumps(value)

    if isinstance(value, bool):
        return "True" if value else "False"

    if isinstance(value, (int, float)):
        return str(value)

    if value is None:
        return "null"

    return str(value)


def json_to_zw(data: Any, indent_level: int = 0, in_list: bool = False) -> str:
    if indent_level == 0 and isinstance(data, dict):
        blocks = []

        for key, value in data.items():
            key_upper = convert_to_upper_snake_case(key)

            if is_scalar(value):
                blocks.append(f"{key_upper}: {format_scalar(value)}")
            else:
                child_output = json_to_zw(value, indent_level + 1, False)
                blocks.append(f"{key_upper}:\n{child_output}")

        result = "\n\n".join(blocks)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result

    if isinstance(data, dict):
        lines = []
        indent_str = " " * (indent_level * 2)

        for key, value in data.items():
            key_upper = convert_to_upper_snake_case(key)

            if is_scalar(value):
                lines.append(f"{indent_str}{key_upper}: {format_scalar(value)}")
            else:
                lines.append(f"{indent_str}{key_upper}:")
                child_output = json_to_zw(value, indent_level + 1, False)
                lines.append(child_output)

        return "\n".join(lines)

    if isinstance(data, list):
        indent_str = " " * (indent_level * 2)

        if len(data) == 0:
            return indent_str + "- EMPTY"

        lines = []

        for item in data:
            if is_scalar(item):
                formatted_value = format_scalar(item, in_list=True)
                lines.append(f"{indent_str}- {formatted_value}")
            else:
                lines.append(f"{indent_str}-")
                child_output = json_to_zw(item, indent_level + 1, False)
                lines.append(child_output)

        return "\n".join(lines)

    return format_scalar(data, in_list)


def json_file_to_zw_file(input_path: str, output_path: str) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    zw_text = json_to_zw(data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(zw_text)
        f.write("\n")
