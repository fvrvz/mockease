from __future__ import annotations

import re
import uuid


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def unique_slug(base: str) -> str:
    """Generate a unique slug with a short UUID suffix."""
    base_slug = slugify(base)
    suffix = str(uuid.uuid4())[:8]
    return f"{base_slug}-{suffix}"
