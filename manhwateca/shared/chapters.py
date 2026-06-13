import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from manhwateca.shared.ranges import compact_number_ranges


CHAPTER_EXTENSIONS = {".pdf", ".cbz"}
SIDE_STORY_KEYWORDS = ["side", "side story", "sidestory"]
RANGE_PATTERN = r"(\d+(?:\.\d+)?)(?:\s*(?:-|=|_|ao|a|–|—)\s*(\d+(?:\.\d+)?))?"


def is_side_story(filename: str) -> bool:
    filename = unicodedata.normalize("NFC", filename).lower()
    return any(keyword in filename for keyword in SIDE_STORY_KEYWORDS)


def _extract_numbers(filename: str, marker: str) -> list[int]:
    name = unicodedata.normalize("NFC", filename).lower()

    if marker == "cap":
        name = name.replace("capítulo", "cap").replace("capitulo", "cap")
    else:
        name = name.replace("side story", "side").replace("sidestory", "side")

    matches = re.findall(rf"{marker}\s*{RANGE_PATTERN}", name)
    numbers = []
    for start, end in matches:
        numbers.append(int(float(start)))
        if end:
            numbers.append(int(float(end)))
    return numbers


def extract_chapter_numbers(filename: str) -> list[int]:
    return _extract_numbers(filename, "cap")


def extract_side_story_numbers(filename: str) -> list[int]:
    return _extract_numbers(filename, "side")


def extract_highest_chapter(filename: str) -> int:
    return max(extract_chapter_numbers(filename), default=0)


def extract_highest_side_story(filename: str) -> int:
    return max(extract_side_story_numbers(filename), default=0)


def extract_chapter_range(filename: str, side_story=False) -> set[int]:
    extractor = (
        extract_side_story_numbers
        if side_story
        else extract_chapter_numbers
    )
    numbers = extractor(filename)
    if not numbers:
        return set()
    if len(numbers) == 1:
        return {numbers[0]}

    start, end = numbers[0], numbers[1]
    if end < start:
        start, end = end, start
    return set(range(start, end + 1))


def scan_chapters(manga_path: Path) -> dict:
    main_numbers = set()
    side_numbers = set()
    main_occurrences = defaultdict(list)
    side_occurrences = defaultdict(list)
    chapter_files = 0
    side_files = 0
    unparsed_files = []

    for file in manga_path.iterdir():
        if not file.is_file() or file.suffix.lower() not in CHAPTER_EXTENSIONS:
            continue

        side_story = is_side_story(file.name)
        numbers = extract_chapter_range(file.name, side_story=side_story)
        if not numbers:
            unparsed_files.append(file.name)
            continue

        occurrences = side_occurrences if side_story else main_occurrences
        target = side_numbers if side_story else main_numbers
        target.update(numbers)
        for number in numbers:
            occurrences[number].append(file.name)

        if side_story:
            side_files += 1
        else:
            chapter_files += 1

    main_caps = max(main_numbers, default=0)
    side_caps = max(side_numbers, default=0)
    next_to_read = min(main_numbers, default=0)
    if not next_to_read:
        next_to_read = min(side_numbers, default=0)
    last_read = max(next_to_read - 1, 0)
    missing_main = (
        set(range(1, main_caps + 1)) - main_numbers
        if main_caps
        else set()
    )
    duplicate_main = _duplicates(main_occurrences)
    duplicate_side = _duplicates(side_occurrences)

    issues = []
    if missing_main:
        issues.append("lacunas")
    if duplicate_main or duplicate_side:
        issues.append("sobreposições")
    if unparsed_files:
        issues.append("arquivos não interpretados")
    if not main_numbers and side_numbers:
        issues.append("somente side stories")

    return {
        "main_caps": main_caps,
        "side_caps": side_caps,
        "next_to_read": next_to_read,
        "last_read": last_read,
        "total_caps": main_caps,
        "chapters_found": len(main_numbers),
        "side_stories_found": len(side_numbers),
        "missing_chapters": sorted(missing_main),
        "missing_ranges": compact_number_ranges(missing_main),
        "duplicate_chapters": duplicate_main,
        "duplicate_side_stories": duplicate_side,
        "unparsed_files": sorted(unparsed_files),
        "count_status": "Revisar" if issues else "OK",
        "count_issues": issues,
        "chapter_files": chapter_files,
        "side_files": side_files,
    }


def _duplicates(occurrences):
    return {
        number: files
        for number, files in occurrences.items()
        if len(files) > 1
    }
