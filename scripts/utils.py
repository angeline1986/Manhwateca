import json
import re
import unicodedata
import os
from collections import defaultdict
from pathlib import Path


MEDIA_EXTENSIONS = {
    ".pdf",
    ".cbz",
    ".jpg",
    ".jpeg",
    ".png",
}


CHAPTER_EXTENSIONS = {
    ".pdf",
    ".cbz",
}


SIDE_STORY_KEYWORDS = [
    "side",
    "side story",
    "sidestory",
]

TITLE_ALIASES_FILE = Path("config/titles.json")


def get_required_path_env(name: str) -> Path:
    value = os.getenv(name, "").strip()

    if not value:
        raise ValueError(f"{name} não foi definido no .env")

    return Path(value).expanduser()


def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFC", name)
    return " ".join(name.strip().split())


def clean_manga_name(name: str) -> str:
    name = normalize_name(name)

    name = re.sub(r"^\d+\s*[_\-.]\s*", "", name)
    name = re.sub(r"\s+\d+$", "", name)

    return normalize_name(name)


def load_title_aliases(path=TITLE_ALIASES_FILE) -> dict[str, str]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        aliases = json.load(file)

    if not isinstance(aliases, dict):
        raise ValueError(f"Formato inválido em {path}: era esperado um objeto.")

    return {
        normalize_name(source).casefold(): normalize_name(destination)
        for source, destination in aliases.items()
    }


def get_canonical_manga_name(name: str, aliases=None) -> str:
    clean_name = clean_manga_name(name)
    aliases = load_title_aliases() if aliases is None else aliases
    return aliases.get(clean_name.casefold(), clean_name)


def normalize_first_letter(text: str) -> str:
    text = text.strip()

    if not text:
        return "#"

    first = text[0].upper()
    first = unicodedata.normalize("NFD", first)
    first = first.encode("ascii", "ignore").decode("utf-8")

    return first.upper() if first else "#"


def is_side_story(filename: str) -> bool:
    filename = unicodedata.normalize("NFC", filename).lower()

    return any(keyword in filename for keyword in SIDE_STORY_KEYWORDS)


def extract_chapter_numbers(filename: str) -> list[int]:
    name = unicodedata.normalize("NFC", filename).lower()

    name = name.replace("capítulo", "cap")
    name = name.replace("capitulo", "cap")

    pattern = r"cap\s*(\d+(?:\.\d+)?)(?:\s*(?:-|=|_|ao|a|–|—)\s*(\d+(?:\.\d+)?))?"

    matches = re.findall(pattern, name)

    chapters = []

    for start, end in matches:
        chapters.append(int(float(start)))

        if end:
            chapters.append(int(float(end)))

    return chapters


def extract_side_story_numbers(filename: str) -> list[int]:
    name = unicodedata.normalize("NFC", filename).lower()

    name = name.replace("side story", "side")
    name = name.replace("sidestory", "side")

    pattern = r"side\s*(\d+(?:\.\d+)?)(?:\s*(?:-|=|_|ao|a|–|—)\s*(\d+(?:\.\d+)?))?"

    matches = re.findall(pattern, name)

    chapters = []

    for start, end in matches:
        chapters.append(int(float(start)))

        if end:
            chapters.append(int(float(end)))

    return chapters


def extract_highest_chapter(filename: str) -> int:
    chapters = extract_chapter_numbers(filename)

    if not chapters:
        return 0

    return max(chapters)


def extract_highest_side_story(filename: str) -> int:
    chapters = extract_side_story_numbers(filename)

    if not chapters:
        return 0

    return max(chapters)


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


def compact_number_ranges(numbers: set[int]) -> list[str]:
    if not numbers:
        return []

    ordered = sorted(numbers)
    ranges = []
    start = previous = ordered[0]
    for number in ordered[1:]:
        if number == previous + 1:
            previous = number
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = number
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ranges


def scan_chapters(manga_path: Path) -> dict:
    main_numbers = set()
    side_numbers = set()
    main_occurrences = defaultdict(list)
    side_occurrences = defaultdict(list)
    chapter_files = 0
    side_files = 0
    unparsed_files = []

    for file in manga_path.iterdir():
        if not file.is_file():
            continue

        if file.suffix.lower() not in CHAPTER_EXTENSIONS:
            continue

        if is_side_story(file.name):
            numbers = extract_chapter_range(file.name, side_story=True)
            if numbers:
                side_files += 1
                side_numbers.update(numbers)
                for number in numbers:
                    side_occurrences[number].append(file.name)
            else:
                unparsed_files.append(file.name)
        else:
            numbers = extract_chapter_range(file.name)
            if numbers:
                chapter_files += 1
                main_numbers.update(numbers)
                for number in numbers:
                    main_occurrences[number].append(file.name)
            else:
                unparsed_files.append(file.name)

    main_caps = max(main_numbers, default=0)
    side_caps = max(side_numbers, default=0)
    missing_main = (
        set(range(1, main_caps + 1)) - main_numbers
        if main_caps
        else set()
    )
    duplicate_main = {
        number: files
        for number, files in main_occurrences.items()
        if len(files) > 1
    }
    duplicate_side = {
        number: files
        for number, files in side_occurrences.items()
        if len(files) > 1
    }

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


def get_cover_file(manga_path: Path):
    preferred_names = [
        "cover.jpg",
        "cover.jpeg",
        "cover.png",
        "folder.jpg",
        "folder.png",
    ]

    for name in preferred_names:
        file_path = manga_path / name

        if file_path.exists():
            return str(file_path)

    for file in manga_path.iterdir():
        if file.is_file() and file.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            return str(file)

    return None


def normalize_for_duplicate_detection(name):
    name = name.strip()

    articles = ["a ", "o ", "os ", "as ", "the "]
    name_lower = name.lower()

    for article in articles:
        if name_lower.startswith(article):
            name = name[len(article):].strip()
            name_lower = name.lower()
            break

    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")

    name = re.sub(r"\s+", " ", name).strip().lower()

    return name


def detect_duplicates_organize(plan):
    duplicates = []
    name_map = defaultdict(list)

    for item in plan:
        normalized = normalize_for_duplicate_detection(item["name"])
        name_map[normalized].append({
            "original": item["name"],
            "source": str(item["source"]),
            "destination": str(item["destination"]),
            "group": item["group"],
        })

    for normalized, entries in name_map.items():
        if len(entries) > 1:
            duplicates.append({
                "normalized": normalized,
                "entries": entries,
            })

    return duplicates
