import re
import unicodedata
from pathlib import Path


def normalize_chapter_name(filename, manga_name=None):
    path = Path(filename)
    new_stem = unicodedata.normalize("NFC", path.stem)

    new_stem = re.sub(
        r"(?i)(?:^|[_\s-]+)cap(?:[_\s-]+)(?=\d)", " cap ", new_stem
    )
    new_stem = re.sub(r"_+", " ", new_stem)
    new_stem = re.sub(
        r"\bside\s*stoy\b", "side story", new_stem, flags=re.IGNORECASE
    )
    new_stem = re.sub(
        r"\bside\s+(?=\d)", "side story ", new_stem, flags=re.IGNORECASE
    )
    new_stem = re.sub(
        r"\bside\s*story\b", "side story", new_stem, flags=re.IGNORECASE
    )
    new_stem = re.sub(r"cap[ií]tulo", "cap", new_stem, flags=re.IGNORECASE)
    new_stem = re.sub(r"\bcaps?\b", "cap", new_stem, flags=re.IGNORECASE)
    new_stem = re.sub(
        r"\bcap\s+cap\b", "cap", new_stem, flags=re.IGNORECASE
    )
    new_stem = _normalize_ranges(new_stem)

    if manga_name:
        new_stem = _add_missing_chapter_marker(new_stem, manga_name)
        new_stem = _replace_title(new_stem, manga_name)

    new_stem = re.sub(r"\s+", " ", new_stem).strip()
    new_stem = re.sub(r"\s+([,.;])", r"\1", new_stem)
    new_stem = re.sub(r"[,.;]+$", "", new_stem)
    new_stem = new_stem.rstrip("_- ")
    return f"{new_stem}{path.suffix}"


def _normalize_ranges(stem):
    stem = re.sub(
        r"cap\s*(\d+(?:\.\d+)?)\s*(?:=|_|ao|a|–|—)\s*(\d+(?:\.\d+)?)",
        r"cap \1-\2",
        stem,
        flags=re.IGNORECASE,
    )
    stem = re.sub(
        r"cap\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)",
        r"cap \1-\2",
        stem,
        flags=re.IGNORECASE,
    )
    stem = re.sub(
        r"cap\s*(\d+(?:\.\d+)?)\s*[^\w\s.,_-]+\s*(\d+(?:\.\d+)?)",
        r"cap \1-\2",
        stem,
        flags=re.IGNORECASE,
    )
    stem = re.sub(
        r"cap\s*(\d+(?:\.\d+)?)", r"cap \1", stem, flags=re.IGNORECASE
    )
    stem = re.sub(
        r"\bcap\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)(?=\s|$)",
        r"cap \1-\2",
        stem,
        flags=re.IGNORECASE,
    )
    stem = re.sub(
        r"(\d+(?:\.\d+)?)\s*(?:=|_|\bao\b|\ba\b|–|—)\s*(\d+(?:\.\d+)?)",
        r"\1-\2",
        stem,
        flags=re.IGNORECASE,
    )
    stem = re.sub(
        r"\b(cap|side story)\s+0+(\d)", r"\1 \2", stem, flags=re.IGNORECASE
    )
    stem = re.sub(r"(?<=-)\s*0+(\d)", r"\1", stem)
    stem = re.sub(r"\s*┇\s*", " - ", stem)
    return re.sub(r"\b2segunda\b", "2ª", stem, flags=re.IGNORECASE)


def _add_missing_chapter_marker(stem, manga_name):
    if re.search(
        r"\b(?:cap|side story|sidestory|pr[oó]logo)\b",
        stem,
        flags=re.IGNORECASE,
    ):
        return stem
    title_pattern = re.escape(manga_name)
    if not re.match(rf"^{title_pattern}\s+\d", stem, flags=re.IGNORECASE):
        return stem
    return re.sub(
        rf"^{title_pattern}\s+",
        f"{manga_name} cap ",
        stem,
        count=1,
        flags=re.IGNORECASE,
    )


def _replace_title(stem, manga_name):
    match = re.search(
        r"\b(?:cap\s*\d|side\s*story\b|sidestory\b|pr[oó]logo\b)",
        stem,
        flags=re.IGNORECASE,
    )
    if not match:
        return stem
    content = stem[match.start():]
    if (
        manga_name.casefold().endswith(" side")
        and content.casefold().startswith("side story")
    ):
        content = content[5:]
    return f"{manga_name} {content}"
