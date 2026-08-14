import unittest
from datetime import date

from manhwateca.mangadex_service.client import MangaDexHTTPError
from manhwateca.mangadex_service.search import parse_manga_feed
from manhwateca.release_monitor.models import ExternalRelease
from manhwateca.release_monitor.providers.mangadex import (
    MangaDexReleaseProvider,
    external_release_from_feed_item,
    normalize_mangadex_feed,
)


class MangaDexReleaseProviderTests(unittest.TestCase):
    def test_transforms_complete_feed_item_to_external_release(self):
        manga_id = "eede42a0-78a1-413d-8cb6-3a03ec365e2b"
        release_id = "91b83f4c-1111-4222-8333-123456789abc"
        item = feed_item(
            release_id,
            chapter="12",
            volume="2",
            title="Side Story",
            translated_language="pt-br",
            publish_at="2026-08-14T10:30:00+00:00",
        )

        release = external_release_from_feed_item(manga_id, item)

        self.assertIsInstance(release, ExternalRelease)
        self.assertEqual(release.provider, "mangadex")
        self.assertEqual(release.external_series_id, manga_id)
        self.assertEqual(release.external_release_id, release_id)
        self.assertEqual(release.chapter, "12")
        self.assertEqual(release.volume, "2")
        self.assertEqual(release.language, "pt-br")
        self.assertEqual(release.title, "Side Story")
        self.assertEqual(release.release_date, date(2026, 8, 14))
        self.assertIs(release.raw_payload, item.raw_payload)

    def test_manga_uuid_and_release_uuid_are_not_confused(self):
        manga_id = "eede42a0-78a1-413d-8cb6-3a03ec365e2b"
        release_id = "91b83f4c-1111-4222-8333-123456789abc"
        release = external_release_from_feed_item(manga_id, feed_item(
            release_id,
            publish_at="2026-08-14T10:30:00Z",
        ))

        self.assertEqual(release.external_series_id, manga_id)
        self.assertEqual(release.external_release_id, release_id)

    def test_preserves_decimal_and_textual_chapters(self):
        decimal = external_release_from_feed_item("manga-id", feed_item(
            "release-decimal",
            chapter="10.5",
            publish_at="2026-08-14T10:30:00Z",
        ))
        textual = external_release_from_feed_item("manga-id", feed_item(
            "release-text",
            chapter="extra",
            publish_at="2026-08-14T10:30:00Z",
        ))

        self.assertEqual(decimal.chapter, "10.5")
        self.assertEqual(textual.chapter, "extra")

    def test_allows_null_volume_and_title(self):
        release = external_release_from_feed_item("manga-id", feed_item(
            "release-id",
            volume=None,
            title=None,
            publish_at="2026-08-14T10:30:00Z",
        ))

        self.assertIsNone(release.volume)
        self.assertIsNone(release.title)

    def test_invalid_when_chapter_is_null(self):
        release = external_release_from_feed_item("manga-id", feed_item(
            "release-id",
            chapter=None,
            publish_at="2026-08-14T10:30:00Z",
        ))

        self.assertIsNone(release)

    def test_invalid_when_publish_at_is_invalid(self):
        release = external_release_from_feed_item("manga-id", feed_item(
            "release-id",
            chapter="1",
            publish_at="not-a-date",
        ))

        self.assertIsNone(release)

    def test_normalizes_multiple_items_and_counts_invalid(self):
        releases, stats = normalize_mangadex_feed("manga-id", [
            feed_item("release-1", chapter="1", publish_at="2026-08-14T10:30:00Z"),
            feed_item("release-invalid", chapter=None, publish_at="2026-08-14T10:30:00Z"),
            feed_item("release-2", chapter="2", publish_at="2026-08-15T10:30:00Z"),
        ])

        self.assertEqual([release.external_release_id for release in releases], [
            "release-1",
            "release-2",
        ])
        self.assertEqual(stats["releases_received"], 3)
        self.assertEqual(stats["releases_parsed"], 2)
        self.assertEqual(stats["releases_with_series_metadata"], 2)
        self.assertEqual(stats["releases_missing_series_metadata"], 0)
        self.assertEqual(stats["releases_invalid"], 1)

    def test_normalizes_empty_feed(self):
        releases, stats = normalize_mangadex_feed("manga-id", [])

        self.assertEqual(releases, [])
        self.assertEqual(stats["releases_received"], 0)
        self.assertEqual(stats["releases_parsed"], 0)

    def test_provider_reuses_iter_manga_feed_contract(self):
        calls = []

        def feed_iter_func(manga_id, **options):
            calls.append((manga_id, options))
            return [feed_item(
                "release-id",
                translated_language="en",
                publish_at="2026-08-14T10:30:00Z",
            )]

        page = MangaDexReleaseProvider(feed_iter_func=feed_iter_func).fetch_manga(
            "manga-id",
            limit=50,
            max_pages=3,
        )

        self.assertEqual(calls, [("manga-id", {"limit": 50, "max_pages": 3})])
        self.assertEqual(page.releases[0].provider, "mangadex")
        self.assertFalse(page.has_next_page)
        self.assertTrue(page.has_results_collection)

    def test_provider_preserves_languages_without_filtering(self):
        page = MangaDexReleaseProvider(feed_iter_func=lambda *_args, **_kwargs: [
            feed_item("release-pt", translated_language="pt-br", publish_at="2026-08-14T10:30:00Z"),
            feed_item("release-en", translated_language="en", publish_at="2026-08-14T10:30:00Z"),
        ]).fetch_manga("manga-id")

        self.assertEqual(
            [release.language for release in page.releases],
            ["pt-br", "en"],
        )

    def test_provider_propagates_mangadex_errors(self):
        def feed_iter_func(*_args, **_kwargs):
            raise MangaDexHTTPError(500)

        with self.assertRaises(MangaDexHTTPError):
            MangaDexReleaseProvider(feed_iter_func=feed_iter_func).fetch_manga("manga-id")

    def test_provider_returns_empty_page_for_empty_feed(self):
        page = MangaDexReleaseProvider(
            feed_iter_func=lambda *_args, **_kwargs: []
        ).fetch_manga("manga-id")

        self.assertEqual(page.releases, [])
        self.assertEqual(page.stats["releases_received"], 0)
        self.assertFalse(page.has_results_collection)


def feed_item(
    release_id,
    *,
    volume="1",
    chapter="1",
    title="Chapter Title",
    translated_language="en",
    publish_at="2026-08-14T10:30:00+00:00",
):
    page = parse_manga_feed({
        "data": [{
            "id": release_id,
            "type": "chapter",
            "attributes": {
                "volume": volume,
                "chapter": chapter,
                "title": title,
                "translatedLanguage": translated_language,
                "publishAt": publish_at,
            },
            "relationships": [{"id": "group-id", "type": "scanlation_group"}],
        }],
        "limit": 1,
        "offset": 0,
        "total": 1,
    })
    return page.items[0]


if __name__ == "__main__":
    unittest.main()
