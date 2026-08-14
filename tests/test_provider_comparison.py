import unittest
from datetime import date

from manhwateca.release_monitor.models import ExternalRelease
from manhwateca.release_monitor.provider_comparison import (
    ProviderComparisonService,
    ProviderReleaseSummary,
    compare_provider_releases,
    collect_comparable_works,
)
from manhwateca.release_monitor.providers import ReleaseProviderPage


class FakeMangaUpdatesProvider:
    def __init__(self, pages=None, error=None):
        self.pages = pages or {}
        self.error = error
        self.seen_pages = []

    def fetch_page(self, page):
        self.seen_pages.append(page)
        if self.error:
            raise self.error
        return self.pages[page]


class FakeMangaDexProvider:
    def __init__(self, page=None, error=None):
        self.page = page
        self.error = error
        self.calls = []

    def fetch_manga(self, manga_id, **options):
        self.calls.append((manga_id, options))
        if self.error:
            raise self.error
        return self.page


class NoWriteRepository:
    def upsert_release(self, *_args, **_kwargs):
        raise AssertionError("comparison must not write mangaupdates_releases")

    def upsert_external_release(self, *_args, **_kwargs):
        raise AssertionError("comparison must not write external_releases")

    def mark_viewed(self, *_args, **_kwargs):
        raise AssertionError("comparison must not mark releases viewed")


class FakeExternalRefRepository:
    def __init__(self, refs_by_manga):
        self.refs_by_manga = refs_by_manga
        self.seen = []

    def list_external_refs(self, manga_id):
        self.seen.append(manga_id)
        return list(self.refs_by_manga.get(manga_id, []))


class ProviderComparisonTests(unittest.TestCase):
    def test_compares_shared_and_provider_only_chapters_with_date_difference(self):
        comparison = compare_provider_releases(
            123,
            "Sample",
            mangaupdates=summary("mangaupdates", "mu-1", [
                release("mangaupdates", "mu-1", "28", "2026-08-01"),
                release("mangaupdates", "mu-1", "29", "2026-08-06"),
                release("mangaupdates", "mu-1", "30", "2026-08-10"),
            ]),
            mangadex=summary("mangadex", "md-1", [
                release("mangadex", "md-1", "28", "2026-08-01", language="en"),
                release("mangadex", "md-1", "29", "2026-08-07", language="en"),
                release("mangadex", "md-1", "31", "2026-08-12", language="en"),
            ]),
        )

        self.assertEqual(["28", "29"], comparison.chapters_in_both)
        self.assertEqual(["30"], comparison.chapters_only_mangaupdates)
        self.assertEqual(["31"], comparison.chapters_only_mangadex)
        self.assertEqual(1, len(comparison.date_differences))
        self.assertEqual("29", comparison.date_differences[0].chapter)
        self.assertEqual([date(2026, 8, 6)], comparison.date_differences[0].mangaupdates_dates)
        self.assertEqual([date(2026, 8, 7)], comparison.date_differences[0].mangadex_dates)
        self.assertFalse(comparison.has_errors)

    def test_preserves_mangadex_granularity_for_multiple_languages(self):
        comparison = compare_provider_releases(
            123,
            mangaupdates=summary("mangaupdates", "mu-1", [
                release("mangaupdates", "mu-1", "29", "2026-08-06"),
            ]),
            mangadex=summary("mangadex", "md-1", [
                release("mangadex", "md-1", "29", "2026-08-06", language="en", release_id="md-en"),
                release("mangadex", "md-1", "29", "2026-08-06", language="pt-br", release_id="md-pt"),
            ]),
        )

        self.assertEqual(["29"], comparison.chapters_in_both)
        self.assertEqual(["en", "pt-br"], comparison.mangadex.languages)
        self.assertEqual(2, comparison.mangadex.releases_count)
        self.assertEqual(["md-en", "md-pt"], [
            release.external_release_id for release in comparison.mangadex.releases
        ])

    def test_decimal_textual_and_null_chapters_are_handled_without_new_rules(self):
        comparison = compare_provider_releases(
            123,
            mangaupdates=summary("mangaupdates", "mu-1", [
                release("mangaupdates", "mu-1", "10.5", "2026-08-01"),
                release("mangaupdates", "mu-1", "extra", "2026-08-02"),
                release("mangaupdates", "mu-1", None, "2026-08-03"),
            ]),
            mangadex=summary("mangadex", "md-1", [
                release("mangadex", "md-1", "10.5", "2026-08-01"),
                release("mangadex", "md-1", "side story", "2026-08-04"),
            ]),
        )

        self.assertEqual(["10.5"], comparison.chapters_in_both)
        self.assertEqual(["extra"], comparison.chapters_only_mangaupdates)
        self.assertEqual(["side story"], comparison.chapters_only_mangadex)
        self.assertEqual(3, comparison.mangaupdates.releases_count)
        self.assertNotIn(None, comparison.mangaupdates.chapters)

    def test_provider_without_releases_is_reported_as_empty_not_error(self):
        comparison = compare_provider_releases(
            123,
            mangaupdates=summary("mangaupdates", "mu-1", []),
            mangadex=summary("mangadex", "md-1", [
                release("mangadex", "md-1", "1", "2026-08-01", language="en"),
            ]),
        )

        self.assertEqual(0, comparison.mangaupdates.releases_count)
        self.assertEqual(["1"], comparison.chapters_only_mangadex)
        self.assertFalse(comparison.has_errors)

    def test_service_fetches_both_providers_read_only_and_filters_mangaupdates_series(self):
        mu_provider = FakeMangaUpdatesProvider({
            1: ReleaseProviderPage(
                releases=[
                    release("mangaupdates", "target-mu", "1", "2026-08-01", release_id="mu-target"),
                    release("mangaupdates", "other-mu", "1", "2026-08-01", release_id="mu-other"),
                ],
                stats=stats(2, 2),
                has_results_collection=True,
                has_next_page=False,
            )
        })
        md_provider = FakeMangaDexProvider(ReleaseProviderPage(
            releases=[release("mangadex", "target-md", "1", "2026-08-01", language="pt-br")],
            stats=stats(1, 1),
            has_results_collection=True,
            has_next_page=False,
        ))

        comparison = ProviderComparisonService(
            mangaupdates_provider=mu_provider,
            mangadex_provider=md_provider,
        ).compare_work(
            123,
            "Sample",
            mangaupdates_id="target-mu",
            mangadex_id="target-md",
            mangadex_options={"limit": 50, "max_pages": 2},
        )

        self.assertEqual(["mu-target"], [
            release.external_release_id for release in comparison.mangaupdates.releases
        ])
        self.assertEqual([1], mu_provider.seen_pages)
        self.assertEqual([("target-md", {"limit": 50, "max_pages": 2})], md_provider.calls)
        self.assertEqual(["pt-br"], comparison.mangadex.languages)

    def test_mangaupdates_failure_keeps_mangadex_result(self):
        comparison = ProviderComparisonService(
            mangaupdates_provider=FakeMangaUpdatesProvider(error=RuntimeError("MU down")),
            mangadex_provider=FakeMangaDexProvider(ReleaseProviderPage(
                releases=[release("mangadex", "md-1", "1", "2026-08-01")],
                stats=stats(1, 1),
                has_results_collection=True,
                has_next_page=False,
            )),
        ).compare_work(123, mangaupdates_id="mu-1", mangadex_id="md-1")

        self.assertIn("MU down", comparison.mangaupdates.error)
        self.assertEqual(1, comparison.mangadex.releases_count)
        self.assertTrue(comparison.has_errors)

    def test_mangadex_failure_keeps_mangaupdates_result(self):
        comparison = ProviderComparisonService(
            mangaupdates_provider=FakeMangaUpdatesProvider({
                1: ReleaseProviderPage(
                    releases=[release("mangaupdates", "mu-1", "1", "2026-08-01")],
                    stats=stats(1, 1),
                    has_results_collection=True,
                    has_next_page=False,
                )
            }),
            mangadex_provider=FakeMangaDexProvider(error=RuntimeError("MD down")),
        ).compare_work(123, mangaupdates_id="mu-1", mangadex_id="md-1")

        self.assertEqual(1, comparison.mangaupdates.releases_count)
        self.assertIn("MD down", comparison.mangadex.error)
        self.assertTrue(comparison.has_errors)

    def test_both_failures_are_reported_without_declaring_divergence_an_error(self):
        comparison = ProviderComparisonService(
            mangaupdates_provider=FakeMangaUpdatesProvider(error=RuntimeError("MU down")),
            mangadex_provider=FakeMangaDexProvider(error=RuntimeError("MD down")),
        ).compare_work(123, mangaupdates_id="mu-1", mangadex_id="md-1")

        self.assertIn("MU down", comparison.mangaupdates.error)
        self.assertIn("MD down", comparison.mangadex.error)
        self.assertEqual([], comparison.chapters_in_both)
        self.assertTrue(comparison.has_errors)

    def test_missing_refs_are_explicit_errors_but_no_external_calls_are_made(self):
        mu_provider = FakeMangaUpdatesProvider({})
        md_provider = FakeMangaDexProvider()

        comparison = ProviderComparisonService(
            mangaupdates_provider=mu_provider,
            mangadex_provider=md_provider,
        ).compare_work(123)

        self.assertIn("ausente", comparison.mangaupdates.error)
        self.assertIn("ausente", comparison.mangadex.error)
        self.assertEqual([], mu_provider.seen_pages)
        self.assertEqual([], md_provider.calls)

    def test_collects_only_works_with_both_refs_without_hardcoded_title(self):
        repository = FakeExternalRefRepository({
            1: [ref("mangaupdates", "mu-a"), ref("mangadex", "md-a")],
            2: [ref("mangaupdates", "mu-b")],
            3: [ref("mangadex", "md-c")],
            4: [ref("mangadex", "md-d")],
        })
        subscriptions = [
            {"manga_id": 1, "title": "A", "work_code": "ignored-fallback"},
            {"manga_id": 2, "title": "B", "work_code": "mu-b"},
            {"manga_id": 3, "title": "C", "work_code": None},
            {"manga_id": 4, "title": "D", "work_code": "mu-d"},
        ]

        works = collect_comparable_works(subscriptions, repository)

        self.assertEqual([1, 4], [work.manga_id for work in works])
        self.assertEqual(("mu-a", "md-a"), (works[0].mangaupdates_id, works[0].mangadex_id))
        self.assertEqual(("mu-d", "md-d"), (works[1].mangaupdates_id, works[1].mangadex_id))
        self.assertEqual([1, 2, 3, 4], repository.seen)

    def test_comparison_does_not_use_dashboard_or_write_repository_methods(self):
        repository = NoWriteRepository()
        comparison = compare_provider_releases(
            123,
            mangaupdates=summary("mangaupdates", "mu-1", []),
            mangadex=summary("mangadex", "md-1", []),
        )

        self.assertEqual(0, comparison.mangaupdates.releases_count)
        self.assertFalse(hasattr(repository, "release_summary_called"))


def release(
    provider,
    series_id,
    chapter,
    release_date,
    *,
    language=None,
    release_id=None,
):
    return ExternalRelease(
        provider=provider,
        external_series_id=series_id,
        external_release_id=release_id or f"{provider}-{series_id}-{chapter}-{language}",
        chapter=chapter,
        release_date=date.fromisoformat(release_date),
        language=language,
    )


def ref(provider, external_id):
    return type("Ref", (), {"provider": provider, "external_id": external_id})()


def summary(provider, series_id, releases):
    return ProviderReleaseSummary(
        provider=provider,
        external_series_id=series_id,
        releases_count=len(releases),
        chapters=sorted({
            release.chapter
            for release in releases
            if release.chapter is not None
        }),
        dates=sorted({release.release_date for release in releases}),
        languages=sorted({
            release.language
            for release in releases
            if release.language is not None
        }),
        releases=list(releases),
    )


def stats(received, parsed):
    return {
        "releases_received": received,
        "releases_parsed": parsed,
        "releases_with_series_metadata": parsed,
        "releases_missing_series_metadata": 0,
        "releases_invalid": max(0, received - parsed),
    }


if __name__ == "__main__":
    unittest.main()
