from dataclasses import dataclass
from datetime import date

from manhwateca.release_monitor.models import ExternalRelease
from manhwateca.release_monitor.providers import (
    MangaDexReleaseProvider,
    MangaUpdatesReleaseProvider,
)
from manhwateca.release_monitor.repository import normalize_key


@dataclass(frozen=True)
class ProviderReleaseSummary:
    provider: str
    external_series_id: str | None
    releases_count: int
    chapters: list[str]
    dates: list[date]
    languages: list[str]
    releases: list[ExternalRelease]
    error: str | None = None


@dataclass(frozen=True)
class ChapterDateDifference:
    chapter: str
    mangaupdates_dates: list[date]
    mangadex_dates: list[date]


@dataclass(frozen=True)
class WorkProviderComparison:
    manga_id: int
    title: str | None
    mangaupdates: ProviderReleaseSummary
    mangadex: ProviderReleaseSummary
    chapters_in_both: list[str]
    chapters_only_mangaupdates: list[str]
    chapters_only_mangadex: list[str]
    date_differences: list[ChapterDateDifference]

    @property
    def has_errors(self) -> bool:
        return bool(self.mangaupdates.error or self.mangadex.error)


@dataclass(frozen=True)
class ComparableWork:
    manga_id: int
    title: str | None
    mangaupdates_id: str
    mangadex_id: str


class ProviderComparisonService:
    def __init__(
        self,
        *,
        mangaupdates_provider=None,
        mangadex_provider=None,
    ):
        self.mangaupdates_provider = mangaupdates_provider or MangaUpdatesReleaseProvider()
        self.mangadex_provider = mangadex_provider or MangaDexReleaseProvider()

    def compare_work(
        self,
        manga_id,
        title=None,
        *,
        mangaupdates_id=None,
        mangadex_id=None,
        max_pages: int = 100,
        mangadex_options=None,
    ) -> WorkProviderComparison:
        mangaupdates = self._fetch_mangaupdates(mangaupdates_id, max_pages)
        mangadex = self._fetch_mangadex(mangadex_id, mangadex_options or {})
        return compare_provider_releases(
            manga_id,
            title,
            mangaupdates=mangaupdates,
            mangadex=mangadex,
        )

    def _fetch_mangaupdates(self, external_id, max_pages):
        external_id = _text_or_none(external_id)
        if external_id is None:
            return _summary("mangaupdates", None, [], error="Referência MangaUpdates ausente.")
        releases = []
        try:
            for page_number in range(1, max_pages + 1):
                page = self.mangaupdates_provider.fetch_page(page_number)
                releases.extend(
                    release
                    for release in page.releases
                    if release.external_series_id == external_id
                )
                if (
                    not page.has_results_collection
                    or not page.stats.get("releases_received")
                    or not page.has_next_page
                ):
                    break
        except Exception as error:
            return _summary("mangaupdates", external_id, releases, error=_safe_error(error))
        return _summary("mangaupdates", external_id, releases)

    def _fetch_mangadex(self, external_id, options):
        external_id = _text_or_none(external_id)
        if external_id is None:
            return _summary("mangadex", None, [], error="Referência MangaDex ausente.")
        try:
            page = self.mangadex_provider.fetch_manga(external_id, **options)
        except Exception as error:
            return _summary("mangadex", external_id, [], error=_safe_error(error))
        return _summary("mangadex", external_id, page.releases)


def collect_comparable_works(subscriptions, external_ref_repository) -> list[ComparableWork]:
    works = []
    for row in subscriptions:
        manga_id = row.get("manga_id")
        refs = list(external_ref_repository.list_external_refs(manga_id))
        ref_ids = {
            _text_or_none(getattr(ref, "provider", None)): _text_or_none(getattr(ref, "external_id", None))
            for ref in refs
        }
        mangaupdates_id = ref_ids.get("mangaupdates") or _text_or_none(row.get("work_code"))
        mangadex_id = ref_ids.get("mangadex")
        if mangaupdates_id and mangadex_id:
            works.append(ComparableWork(
                manga_id=int(manga_id),
                title=row.get("title"),
                mangaupdates_id=mangaupdates_id,
                mangadex_id=mangadex_id,
            ))
    return works


def compare_provider_releases(
    manga_id,
    title=None,
    *,
    mangaupdates: ProviderReleaseSummary,
    mangadex: ProviderReleaseSummary,
) -> WorkProviderComparison:
    mu_by_chapter = _chapters_by_key(mangaupdates.releases)
    md_by_chapter = _chapters_by_key(mangadex.releases)
    mu_keys = set(mu_by_chapter)
    md_keys = set(md_by_chapter)
    both = sorted(mu_keys & md_keys)
    only_mu = sorted(mu_keys - md_keys)
    only_md = sorted(md_keys - mu_keys)
    return WorkProviderComparison(
        manga_id=int(manga_id),
        title=title,
        mangaupdates=mangaupdates,
        mangadex=mangadex,
        chapters_in_both=[_display_chapter(mu_by_chapter[key], md_by_chapter[key]) for key in both],
        chapters_only_mangaupdates=[_display_chapter(mu_by_chapter[key], []) for key in only_mu],
        chapters_only_mangadex=[_display_chapter([], md_by_chapter[key]) for key in only_md],
        date_differences=[
            ChapterDateDifference(
                chapter=_display_chapter(mu_by_chapter[key], md_by_chapter[key]),
                mangaupdates_dates=_dates(mu_by_chapter[key]),
                mangadex_dates=_dates(md_by_chapter[key]),
            )
            for key in both
            if _dates(mu_by_chapter[key]) != _dates(md_by_chapter[key])
        ],
    )


def _summary(provider, external_series_id, releases, error=None):
    return ProviderReleaseSummary(
        provider=provider,
        external_series_id=external_series_id,
        releases_count=len(releases),
        chapters=sorted({
            release.chapter
            for release in releases
            if _text_or_none(release.chapter)
        }, key=normalize_key),
        dates=sorted({release.release_date for release in releases}),
        languages=sorted({
            release.language
            for release in releases
            if _text_or_none(release.language)
        }, key=normalize_key),
        releases=list(releases),
        error=error,
    )


def _chapters_by_key(releases):
    by_key = {}
    for release in releases:
        chapter = _text_or_none(release.chapter)
        if chapter is None:
            continue
        by_key.setdefault(normalize_key(chapter), []).append(release)
    return by_key


def _display_chapter(mu_releases, md_releases):
    for release in [*mu_releases, *md_releases]:
        chapter = _text_or_none(release.chapter)
        if chapter is not None:
            return chapter
    return ""


def _dates(releases):
    return sorted({release.release_date for release in releases})


def _text_or_none(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_error(error):
    text = str(error).strip()
    return text[:500] if text else "Falha inesperada ao comparar providers."
