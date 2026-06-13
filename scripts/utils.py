import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from manhwateca.shared.chapters import (
    CHAPTER_EXTENSIONS,
    SIDE_STORY_KEYWORDS,
    extract_chapter_numbers,
    extract_chapter_range,
    extract_highest_chapter,
    extract_highest_side_story,
    extract_side_story_numbers,
    is_side_story,
    scan_chapters,
)
from manhwateca.shared.duplicates import (
    detect_duplicates_organize,
    normalize_for_duplicate_detection,
)
from manhwateca.shared.media import MEDIA_EXTENSIONS, get_cover_file
from manhwateca.shared.paths import get_required_path_env
from manhwateca.shared.ranges import compact_number_ranges
from manhwateca.shared.sizing import classify_manga_size
from manhwateca.shared.titles import (
    TITLE_ALIASES_FILE,
    clean_manga_name,
    get_canonical_manga_name,
    load_title_aliases,
    normalize_first_letter,
    normalize_name,
)
