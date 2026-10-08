from __future__ import annotations

import random
import re
import string
import time
import uuid
from typing import Any, Mapping

FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Evan", "Fiona", "George", "Hannah", "Ian", "Julia"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Anderson"]
DOMAINS = ["example.com", "test.org", "mockease.dev", "mail.com"]

TEMPLATE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def generate_random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def generate_random_email() -> str:
    first = random.choice(FIRST_NAMES).lower()
    last = random.choice(LAST_NAMES).lower()
    num = random.randint(10, 99)
    domain = random.choice(DOMAINS)
    return f"{first}.{last}{num}@{domain}"


def render_template_value(token: str, context: Mapping[str, Any]) -> Any:
    token = token.strip()
    if token == "uuid":
        return str(uuid.uuid4())
    if token == "timestamp":
        return int(time.time())
    if token == "iso_timestamp":
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if token in ("random.name", "random_name"):
        return generate_random_name()
    if token in ("random.email", "random_email"):
        return generate_random_email()
    if token in ("random.number", "random_number"):
        return random.randint(1, 10000)
    if token in ("random.boolean", "random_boolean"):
        return random.choice([True, False])
    if token in ("random.string", "random_string"):
        return "".join(random.choices(string.ascii_letters + string.digits, k=8))

    parts = token.split(".")
    curr: Any = context
    for p in parts:
        if isinstance(curr, dict) and p in curr:
            curr = curr[p]
        else:
            return f"{{{{{token}}}}}"
    return curr


def render_string(val: str, context: Mapping[str, Any]) -> Any:
    exact_match = re.fullmatch(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}", val)
    if exact_match:
        return render_template_value(exact_match.group(1), context)

    def replacer(match: re.Match) -> str:
        res = render_template_value(match.group(1), context)
        return str(res)

    return TEMPLATE_PATTERN.sub(replacer, val)


def render_template(data: Any, context: Mapping[str, Any]) -> Any:
    if isinstance(data, str):
        return render_string(data, context)
    elif isinstance(data, dict):
        return {k: render_template(v, context) for k, v in data.items()}
    elif isinstance(data, list):
        return [render_template(item, context) for item in data]
    return data
