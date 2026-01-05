import html
import re

def html_to_text(s: str) -> str:
    """
    Very lightweight HTML -> text:
    - unescape entities
    - replace <br> / </p> / </h*> with newlines
    - strip other tags
    """
    if not s:
        return ""
    s = html.unescape(s)

    # common block/line breaks
    s = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", s)
    s = re.sub(r"(?i)</\s*p\s*>", "\n", s)
    s = re.sub(r"(?i)</\s*h[1-6]\s*>", "\n", s)

    # strip remaining tags
    _TAG_RE = re.compile(r"<[^>]+>")
    s = _TAG_RE.sub("", s)

    # normalize whitespace and remove newlines
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = s.replace("\n", " ")
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s
