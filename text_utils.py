"""Utility functions for text processing."""

import re


def trim_text(text: str) -> str:
    """Trim text to be between 500 and 1000 characters.

    If the text is longer than 1000 characters, it is cut off at the
    last complete sentence not exceeding 1000 characters. A complete
    sentence ends with '.', '?', or '!'. If the text is shorter than
    500 characters, it is returned unchanged.
    """
    length = len(text)
    if length <= 1000:
        if length < 500:
            return text
        # ensure text ends with a full sentence
        last_punct = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
        if last_punct != -1 and last_punct != length - 1:
            return text[: last_punct + 1]
        return text

    # text > 1000: cut without breaking a sentence
    truncated = text[:1000]
    last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
    if last_punct != -1:
        truncated = truncated[: last_punct + 1]
    return truncated
