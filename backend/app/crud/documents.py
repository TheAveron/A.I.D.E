import re
import unicodedata


def normalize(
    text: str,
    *,
    lowercase=True,
    remove_numbers=True,
    remove_punctuation=True,
    remove_accents=True,
    collapse_whitespace=True,
    join_with="_"
) -> str:
    """
    Enhanced text normalization function.

    Args:
        text (str): Input text.
        lowercase (bool): Convert text to lowercase.
        remove_numbers (bool): Remove numeric digits.
        remove_punctuation (bool): Remove punctuation characters.
        remove_accents (bool): Normalize and strip accents.
        collapse_whitespace (bool): Remove extra spaces/tabs/newlines.
        join_with (str or None): If provided, join words with this string.

    Returns:
        str: Normalized text.
    """

    assert type(text) == str

    if lowercase:
        text = text.lower()

    if remove_accents:
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

    if remove_numbers:
        text = re.sub(r"\d+", "", text)

    if remove_punctuation:
        text = re.sub(r"[^\w\s]", "", text)

    if collapse_whitespace:
        text = re.sub(r"\s+", " ", text).strip()

    words = text.split()

    if join_with is not None:
        return join_with.join(words)
    else:
        return " ".join(words)
