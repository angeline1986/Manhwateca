import unittest
from datetime import datetime, timezone

from manhwateca.mangadex_service.client import MangaDexHTTPError, MangaDexRateLimitError
from manhwateca.mangadex_service.search import MangaDexFeedItem, MangaDexFeedPage
from manhwateca.release_monitor.mangadex_execution import (
    PROVIDER,
    MangaDexExecutionStateRepository,
    process_manga,
)


class FakeReleaseRepository:
    def __init__(self, known_ids=None, fail_on_call=None):
        self.known_ids = set(known_ids or [])
        self.fail_on_call = fail_on_call
        self.calls = []

    def upsert_external_release(self, release, manga_id):
        self.calls.append((release, manga_id))
        if self.fail_on_call and len(self.calls) == self.fail_on_call:
            raise RuntimeError("database unavailable")
        if release.external_release_id in self.known_ids:
            return False
        self.known_ids.add(release.external_release_id)
        return True


class FakeStateRepository:
    def __init__(self, state=None):
        self.state = dict(state or {})
        self.updates = []

    def get_state(self, manga_id, provider=PROVIDER):
        return dict(self.state)

    def mark_success(
        self,
        manga_id,
        provider,
        external_id,
        *,
        checked_at,
        latest_release_published_at,
    ):
        self.updates.append({
            "manga_id": manga_id,
            "provider": provider,
            "external_id": external_id,
            "checked_at": checked_at,
            "latest_release_published_at": latest_release_published_at,
        })
        self.state = {
            "last_checked_at": checked_at,
            "latest_release_published_at": latest_release_published_at,
        }


class FakeMangaRepository:
    def __init__(self, ref=None):
        self.ref = ref
        self.upserts = []

    def get_external_ref(self, manga_id, provider):
        return self.ref

    def upsert_external_ref(self, *args, **kwargs):
        self.upserts.append((args, kwargs))
        return None


class FakeExternalRef:
    metadata = {"other": "kept", "release_monitor": {"last_checked_at": "old"}}
    external_url = "https://mangadex.org/title/manga-uuid"
    external_title = "Existing"


def item(
    release_id,
    chapter="1",
    publish_at="2024-01-02T03:04:05+00:00",
    *,
    volume="1",
    language="pt-br",
):
    return MangaDexFeedItem(
        id=release_id,
        volume=volume,
        chapter=chapter,
        title=f"Chapter {chapter}" if chapter else None,
        translated_language=language,
        publish_at=publish_at,
        readable_at=publish_at,
        created_at=publish_at,
        updated_at=publish_at,
        relationships=[],
        raw_payload={"id": release_id, "attributes": {"publishAt": publish_at}},
    )


def page(items, limit=100, offset=0, total=None):
    return MangaDexFeedPage(
        items=items,
        limit=limit,
        offset=offset,
        total=len(items) if total is None else total,
        raw_payload={"data": []},
    )


class MangaDexExecutionTests(unittest.TestCase):
    def fixed_now(self):
        return datetime(2024, 2, 3, 4, 5, tzinfo=timezone.utc)

    def test_first_execution_persists_releases_and_updates_state(self):
        calls = []

        def feed_func(manga_id, **kwargs):
            calls.append((manga_id, kwargs))
            return page([
                item("rel-1", chapter="10", language="pt-br"),
                item("rel-2", chapter="9.5", language="en"),
            ])

        releases = FakeReleaseRepository()
        state = FakeStateRepository()

        result = process_manga(
            123,
            "manga-uuid",
            release_repository=releases,
            state_repository=state,
            now_func=self.fixed_now,
            feed_func=feed_func,
        )

        self.assertEqual("success", result.status)
        self.assertEqual(1, result.pages_requested)
        self.assertEqual(2, result.items_received)
        self.assertEqual(2, result.releases_normalized)
        self.assertEqual(2, result.releases_inserted)
        self.assertEqual(0, result.releases_already_known)
        self.assertEqual("end_of_feed", result.stop_reason)
        self.assertEqual("2024-01-02T03:04:05+00:00", result.latest_release_published_at)
        self.assertEqual("2024-02-03T04:05:00+00:00", result.last_checked_at)
        self.assertEqual("manga-uuid", releases.calls[0][0].external_series_id)
        self.assertEqual("pt-br", releases.calls[0][0].language)
        self.assertEqual({"id": "rel-1", "attributes": {"publishAt": "2024-01-02T03:04:05+00:00"}}, releases.calls[0][0].raw_payload)
        self.assertEqual("9.5", releases.calls[1][0].chapter)
        self.assertEqual(123, releases.calls[0][1])
        self.assertEqual([("manga-uuid", {
            "limit": 100,
            "offset": 0,
            "order": "desc",
        })], calls)
        self.assertEqual([{
            "manga_id": 123,
            "provider": "mangadex",
            "external_id": "manga-uuid",
            "checked_at": "2024-02-03T04:05:00+00:00",
            "latest_release_published_at": "2024-01-02T03:04:05+00:00",
        }], state.updates)

    def test_incremental_execution_stops_when_known_publish_at_is_reached(self):
        def feed_func(_manga_id, **_kwargs):
            return page([
                item("new", chapter="11", publish_at="2024-01-03T00:00:00+00:00"),
                item("known", chapter="10", publish_at="2024-01-02T00:00:00+00:00"),
                item("older", chapter="9", publish_at="2024-01-01T00:00:00+00:00"),
            ], total=3)

        releases = FakeReleaseRepository()
        state = FakeStateRepository({
            "latest_release_published_at": "2024-01-02T00:00:00+00:00",
        })

        result = process_manga(
            123,
            "manga-uuid",
            release_repository=releases,
            state_repository=state,
            now_func=self.fixed_now,
            feed_func=feed_func,
        )

        self.assertEqual("success", result.status)
        self.assertEqual("known_release_reached", result.stop_reason)
        self.assertEqual(2, result.items_received)
        self.assertEqual(1, result.releases_normalized)
        self.assertEqual(1, result.releases_ignored)
        self.assertEqual(["new"], [release.external_release_id for release, _ in releases.calls])
        self.assertEqual("2024-01-03T00:00:00+00:00", result.latest_release_published_at)

    def test_no_novelty_updates_checked_at_without_duplicate_persistence(self):
        def feed_func(_manga_id, **_kwargs):
            return page([
                item("known", chapter="10", publish_at="2024-01-02T00:00:00+00:00"),
            ])

        releases = FakeReleaseRepository(known_ids={"known"})
        state = FakeStateRepository({
            "latest_release_published_at": "2024-01-02T00:00:00+00:00",
        })

        result = process_manga(
            123,
            "manga-uuid",
            release_repository=releases,
            state_repository=state,
            now_func=self.fixed_now,
            feed_func=feed_func,
        )

        self.assertEqual("success", result.status)
        self.assertEqual("known_release_reached", result.stop_reason)
        self.assertEqual(0, len(releases.calls))
        self.assertEqual(1, len(state.updates))
        self.assertEqual("2024-01-02T00:00:00+00:00", result.latest_release_published_at)

    def test_known_release_persistence_is_reported_without_duplication(self):
        def feed_func(_manga_id, **_kwargs):
            return page([
                item("already-seen", chapter="11", publish_at="2024-01-03T00:00:00+00:00"),
            ])

        result = process_manga(
            123,
            "manga-uuid",
            release_repository=FakeReleaseRepository(known_ids={"already-seen"}),
            state_repository=FakeStateRepository({
                "latest_release_published_at": "2024-01-02T00:00:00+00:00",
            }),
            now_func=self.fixed_now,
            feed_func=feed_func,
        )

        self.assertEqual("success", result.status)
        self.assertEqual(1, result.releases_normalized)
        self.assertEqual(0, result.releases_inserted)
        self.assertEqual(1, result.releases_already_known)

    def test_invalid_items_are_ignored_but_state_advances_after_success(self):
        def feed_func(_manga_id, **_kwargs):
            return page([
                item("no-chapter", chapter=None),
                item("bad-date", chapter="extra", publish_at="not-a-date"),
            ])

        releases = FakeReleaseRepository()
        result = process_manga(
            123,
            "manga-uuid",
            release_repository=releases,
            state_repository=FakeStateRepository(),
            now_func=self.fixed_now,
            feed_func=feed_func,
        )

        self.assertEqual("success", result.status)
        self.assertEqual(2, result.items_received)
        self.assertEqual(0, result.releases_normalized)
        self.assertEqual(2, result.releases_ignored)
        self.assertEqual([], releases.calls)

    def test_safety_limit_prevents_unbounded_first_execution(self):
        offsets = []

        def feed_func(_manga_id, **kwargs):
            offsets.append(kwargs["offset"])
            return page([item(f"rel-{kwargs['offset']}")], offset=kwargs["offset"], total=500)

        result = process_manga(
            123,
            "manga-uuid",
            max_pages=2,
            release_repository=FakeReleaseRepository(),
            state_repository=FakeStateRepository(),
            now_func=self.fixed_now,
            feed_func=feed_func,
        )

        self.assertEqual("success", result.status)
        self.assertEqual("safety_limit", result.stop_reason)
        self.assertEqual([0, 1], offsets)
        self.assertEqual(2, result.pages_requested)

    def test_feed_errors_do_not_advance_state(self):
        def feed_func(_manga_id, **_kwargs):
            raise MangaDexHTTPError(500, "server error")

        state = FakeStateRepository({
            "latest_release_published_at": "2024-01-02T00:00:00+00:00",
        })
        result = process_manga(
            123,
            "manga-uuid",
            release_repository=FakeReleaseRepository(),
            state_repository=state,
            feed_func=feed_func,
        )

        self.assertEqual("failed", result.status)
        self.assertEqual(1, result.failures)
        self.assertEqual("error", result.stop_reason)
        self.assertEqual([], state.updates)
        self.assertIn("server error", result.error_message)

    def test_persistence_error_does_not_advance_state(self):
        def feed_func(_manga_id, **_kwargs):
            return page([
                item("rel-1", chapter="1", publish_at="2024-01-03T00:00:00+00:00"),
            ])

        state = FakeStateRepository()
        result = process_manga(
            123,
            "manga-uuid",
            release_repository=FakeReleaseRepository(fail_on_call=1),
            state_repository=state,
            feed_func=feed_func,
        )

        self.assertEqual("failed", result.status)
        self.assertEqual("error", result.stop_reason)
        self.assertEqual([], state.updates)
        self.assertIn("database unavailable", result.error_message)

    def test_rate_limit_errors_are_reported_without_local_retry_loop(self):
        def feed_func(_manga_id, **_kwargs):
            raise MangaDexRateLimitError(message="rate limit", retry_after=60)

        result = process_manga(
            123,
            "manga-uuid",
            release_repository=FakeReleaseRepository(),
            state_repository=FakeStateRepository(),
            feed_func=feed_func,
        )

        self.assertEqual("failed", result.status)
        self.assertEqual(1, result.pages_requested)
        self.assertIn("rate limit", result.error_message)

    def test_repository_state_preserves_existing_metadata(self):
        manga_repository = FakeMangaRepository(ref=FakeExternalRef())
        repository = MangaDexExecutionStateRepository(manga_repository)

        repository.mark_success(
            123,
            "mangadex",
            "manga-uuid",
            checked_at="2024-02-03T04:05:00+00:00",
            latest_release_published_at="2024-01-02T00:00:00+00:00",
        )

        args, kwargs = manga_repository.upserts[0]
        self.assertEqual((123, "mangadex", "manga-uuid"), args)
        self.assertEqual("https://mangadex.org/title/manga-uuid", kwargs["external_url"])
        self.assertEqual("Existing", kwargs["external_title"])
        self.assertEqual("kept", kwargs["metadata"]["other"])
        self.assertEqual({
            "last_checked_at": "2024-02-03T04:05:00+00:00",
            "latest_release_published_at": "2024-01-02T00:00:00+00:00",
        }, kwargs["metadata"]["release_monitor"])

    def test_invalid_reference_fails_before_network_or_database(self):
        result = process_manga(
            "",
            "",
            release_repository=FakeReleaseRepository(),
            state_repository=FakeStateRepository(),
        )

        self.assertEqual("failed", result.status)
        self.assertEqual("invalid_reference", result.stop_reason)
        self.assertEqual(0, result.works_consulted)


if __name__ == "__main__":
    unittest.main()
