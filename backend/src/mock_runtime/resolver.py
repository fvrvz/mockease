from __future__ import annotations

import re
from typing import Any

from src.models.endpoint import ApiEndpoint


def normalize_path(path: str) -> str:
    path = path.strip()
    if not path.startswith("/"):
        path = "/" + path
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def compile_path_to_regex(pattern: str) -> tuple[re.Pattern, list[str]]:
    norm = normalize_path(pattern)
    param_names: list[str] = []

    def replace_param(match: re.Match) -> str:
        name = match.group(1) or match.group(2)
        param_names.append(name)
        return r"([^/]+)"

    regex_str = re.sub(r"\{([a-zA-Z0-9_]+)\}|:([a-zA-Z0-9_]+)", replace_param, norm)
    regex = re.compile(f"^{regex_str}$")
    return regex, param_names


def match_endpoint(
    method: str,
    path: str,
    endpoints: list[ApiEndpoint],
) -> tuple[ApiEndpoint | None, dict[str, str]]:
    norm_path = normalize_path(path)
    method_upper = method.upper()

    for ep in endpoints:
        if ep.method.value.upper() == method_upper and normalize_path(ep.path) == norm_path:
            return ep, {}

    for ep in endpoints:
        if ep.method.value.upper() == method_upper:
            pattern = normalize_path(ep.path)
            if "{" in pattern or ":" in pattern:
                regex, param_names = compile_path_to_regex(pattern)
                match = regex.match(norm_path)
                if match:
                    extracted = {name: val for name, val in zip(param_names, match.groups())}
                    return ep, extracted

    return None, {}
