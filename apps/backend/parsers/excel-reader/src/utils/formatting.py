import re
import unicodedata


def _normalize_fill_spaces(fill_spaces: str) -> str:
    if fill_spaces == "":
        return ""

    normalized = unicodedata.normalize("NFKD", str(fill_spaces))
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-zA-Z0-9_]", "", normalized).lower()

    if not normalized:
        return "_"

    return normalized


def standardize_string(value: str, fill_spaces: str = "_") -> str:
    """Normalize a string into a PostgreSQL-safe identifier.

    Rules:
    - lowercase
    - remove accents/diacritics
    - replace spaces with ``fill_spaces``
    - remove special characters (allow only a-z, 0-9, _)
    - prefix with ``_`` if it starts with a digit
    """

    text = unicodedata.normalize("NFKD", str(value).strip().lower())
    text = text.encode("ascii", "ignore").decode("ascii")

    spaces_replacement = _normalize_fill_spaces(fill_spaces)
    text = re.sub(r"\s+", spaces_replacement, text)
    text = re.sub(r"[^a-z0-9_]", "", text)

    text = re.sub(r"_+", "_", text).strip("_")

    if not text:
        return "unnamed"

    if text[0].isdigit():
        return f"_{text}"

    return text
