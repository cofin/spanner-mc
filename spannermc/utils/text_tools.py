import unicodedata
from typing import cast

try:
    import re2 as re  # pyright: ignore
except ImportError:
    import re


__all__ = ["slugify", "camel_case"]


def slugify(value: str, allow_unicode: bool = False, separator: str | None = None) -> str:
    """slugify.

    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.

    Args:
        value (str): the string to slugify
        allow_unicode (bool, optional): allow unicode characters in slug. Defaults to False.
        separator (str, optional): by default a `-` is used to delimit word boundaries.  Set this to configure to something different.

    Returns:
        str: a slugified string of the value parameter
    """
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    if separator is not None:
        return cast("str", re.sub(r"[-\s]+", "-", value)).strip("-_").replace("-", separator)
    return cast("str", re.sub(r"[-\s]+", "-", value).strip("-_"))


def camel_case(string: str) -> str:
    """Convert a string to camel case.

    Args:
        string (str): The string to convert

    Returns:
        str: The string converted to camel case
    """
    return "".join(word if index == 0 else word.capitalize() for index, word in enumerate(string.split("_")))
