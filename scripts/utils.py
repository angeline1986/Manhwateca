import re
import unicodedata
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


def normalize_name(name: str) -> str:
    return " ".join(name.strip().split())


def clean_manga_name(name: str) -> str:
    name = normalize_name(name)

    name = re.sub(r"^\d+\s*[_\-.]\s*", "", name)
    name = re.sub(r"\s+\d+$", "", name)

    return normalize_name(name)


def normalize_first_letter(text: str) -> str:
    text = text.strip()

    if not text:
        return "#"

    first = text[0].upper()
    first = unicodedata.normalize("NFD", first)
    first = first.encode("ascii", "ignore").decode("utf-8")

    return first.upper() if first else "#"


def is_side_story(filename: str) -> bool:
    filename = filename.lower()

    return any(keyword in filename for keyword in SIDE_STORY_KEYWORDS)


def extract_chapter_numbers(filename: str) -> list[int]:
    name = filename.lower()

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
    name = filename.lower()

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


def scan_chapters(manga_path: Path) -> dict:
    main_caps = 0
    side_caps = 0
    chapter_files = 0
    side_files = 0

    for file in manga_path.iterdir():
        if not file.is_file():
            continue

        if file.suffix.lower() not in CHAPTER_EXTENSIONS:
            continue

        if is_side_story(file.name):
            side_chapter = extract_highest_side_story(file.name)
            if side_chapter > 0:
                side_files += 1
                side_caps = max(side_caps, side_chapter)
        else:
            chapter = extract_highest_chapter(file.name)
            if chapter > 0:
                chapter_files += 1
                main_caps = max(main_caps, chapter)

    return {
        "main_caps": main_caps,
        "side_caps": side_caps,
        "total_caps": main_caps,
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