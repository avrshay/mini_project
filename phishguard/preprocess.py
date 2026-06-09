import re

URL_REGEX = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def extract_urls(text: str) -> list[str]:
    """Pre-processing: extract URL array from raw message text."""
    return URL_REGEX.findall(text)
