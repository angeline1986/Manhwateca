import io
import socket
import unittest
import urllib.error
from email.message import Message

from manhwateca.mangadex_service.client import (
    MangaDexError,
    MangaDexHTTPError,
    MangaDexPayloadError,
    MangaDexRateLimitError,
    request_json,
)
from manhwateca.mangadex_service.search import (
    parse_manga_search,
    search_manga,
)


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return io.BytesIO(self.body.encode("utf-8"))

    def __exit__(self, *_args):
        return False


class FakeTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []
        self.timeouts = []

    def __call__(self, request, timeout=30):
        self.requests.append(request)
        self.timeouts.append(timeout)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return FakeResponse(response)


class MangaDexClientTests(unittest.TestCase):
    def test_request_json_returns_payload_and_sends_headers(self):
        transport = FakeTransport('{"result": "ok"}')
        payload = request_json(
            "/manga",
            {"title": "Alpha", "includedTags[]": ["a", "b"]},
            base_url="https://example.test",
            timeout=12,
            urlopen_func=transport,
        )
        request = transport.requests[0]
        self.assertEqual(payload, {"result": "ok"})
        self.assertEqual(transport.timeouts, [12])
        self.assertIn("/manga?", request.full_url)
        self.assertIn("title=Alpha", request.full_url)
        self.assertEqual(request.get_header("Accept"), "application/json")
        self.assertEqual(request.get_header("User-agent"), "Manhwateca/1.0")

    def test_404_raises_http_error_without_retry(self):
        transport = FakeTransport(http_error(404))
        with self.assertRaises(MangaDexHTTPError) as context:
            request_json("/missing", urlopen_func=transport, retries=2)
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(len(transport.requests), 1)

    def test_500_retries_then_raises_http_error(self):
        sleeps = []
        transport = FakeTransport(http_error(500), http_error(500))
        with self.assertRaises(MangaDexHTTPError) as context:
            request_json(
                "/server-error",
                urlopen_func=transport,
                retries=1,
                sleep_func=sleeps.append,
            )
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(len(transport.requests), 2)
        self.assertEqual(len(sleeps), 1)

    def test_429_retries_with_retry_after_then_raises_rate_limit(self):
        sleeps = []
        transport = FakeTransport(
            http_error(429, retry_after="2.5"),
            http_error(429, retry_after="7"),
        )
        with self.assertRaises(MangaDexRateLimitError) as context:
            request_json(
                "/limited",
                urlopen_func=transport,
                retries=1,
                sleep_func=sleeps.append,
            )
        self.assertEqual(sleeps, [2.5])
        self.assertEqual(context.exception.status_code, 429)
        self.assertEqual(context.exception.retry_after, 7.0)

    def test_network_timeout_retries_then_raises_mangadex_error(self):
        sleeps = []
        transport = FakeTransport(socket.timeout("timed out"), socket.timeout("again"))
        with self.assertRaises(MangaDexError):
            request_json(
                "/slow",
                urlopen_func=transport,
                retries=1,
                sleep_func=sleeps.append,
            )
        self.assertEqual(len(transport.requests), 2)
        self.assertEqual(len(sleeps), 1)

    def test_invalid_json_raises_payload_error(self):
        transport = FakeTransport("not-json")
        with self.assertRaises(MangaDexPayloadError):
            request_json("/bad-json", urlopen_func=transport, retries=0)

    def test_empty_payload_shape_raises_payload_error(self):
        transport = FakeTransport("null")
        with self.assertRaises(MangaDexPayloadError):
            request_json("/empty", urlopen_func=transport, retries=0)

    def test_list_payload_is_allowed_for_http_infrastructure(self):
        transport = FakeTransport('[{"id": "1"}]')
        payload = request_json("/list", urlopen_func=transport)
        self.assertEqual(payload, [{"id": "1"}])

    def test_search_manga_requests_candidates_by_title(self):
        calls = []

        def request_func(path, params, **_options):
            calls.append((path, params))
            return manga_search_payload([
                manga_item(
                    "eede42a0-78a1-413d-8cb6-3a03ec365e2b",
                    title={"en": "Accidental Baby"},
                    alt_titles=[{"ko": "우연한 아기"}],
                    original_language="ko",
                    status="ongoing",
                    year=2024,
                    links={"mu": "39054810010"},
                    relationships=[{"id": "cover-1", "type": "cover_art"}],
                )
            ])

        candidates = search_manga(
            "Accidental Baby",
            limit=5,
            offset=10,
            request_func=request_func,
        )

        self.assertEqual(calls, [("/manga", {
            "title": "Accidental Baby",
            "limit": 5,
            "offset": 10,
        })])
        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            candidates[0].id,
            "eede42a0-78a1-413d-8cb6-3a03ec365e2b",
        )
        self.assertEqual(candidates[0].title, "Accidental Baby")
        self.assertEqual(candidates[0].alt_titles, [{"ko": "우연한 아기"}])
        self.assertEqual(candidates[0].original_language, "ko")
        self.assertEqual(candidates[0].status, "ongoing")
        self.assertEqual(candidates[0].year, 2024)
        self.assertEqual(candidates[0].links, {"mu": "39054810010"})
        self.assertEqual(candidates[0].relationships[0]["type"], "cover_art")

    def test_search_manga_returns_empty_for_blank_title_without_request(self):
        calls = []
        self.assertEqual(search_manga("  ", request_func=calls.append), [])
        self.assertEqual(calls, [])

    def test_parse_manga_search_accepts_no_results(self):
        self.assertEqual(parse_manga_search(manga_search_payload([])), [])

    def test_parse_manga_search_preserves_multiple_results(self):
        candidates = parse_manga_search(manga_search_payload([
            manga_item("uuid-1", title={"en": "Alpha"}),
            manga_item("uuid-2", title={"en": "Alpha Side Story"}),
        ]))

        self.assertEqual([candidate.id for candidate in candidates], ["uuid-1", "uuid-2"])

    def test_parse_manga_search_uses_non_english_title_when_needed(self):
        candidates = parse_manga_search(manga_search_payload([
            manga_item("uuid-1", title={"ko-ro": "Dressed to Kill"}),
        ]))

        self.assertEqual(candidates[0].title, "Dressed to Kill")
        self.assertEqual(candidates[0].titles, {"ko-ro": "Dressed to Kill"})

    def test_parse_manga_search_can_fallback_to_alt_title(self):
        candidates = parse_manga_search(manga_search_payload([
            manga_item("uuid-1", title={}, alt_titles=[{"en": "Fallback"}]),
        ]))

        self.assertEqual(candidates[0].title, "Fallback")

    def test_parse_manga_search_handles_partial_attributes(self):
        candidates = parse_manga_search({"data": [{
            "id": "uuid-1",
            "attributes": {"links": None, "altTitles": None},
        }]})

        self.assertIsNone(candidates[0].title)
        self.assertEqual(candidates[0].links, {})
        self.assertEqual(candidates[0].alt_titles, [])
        self.assertEqual(candidates[0].relationships, [])

    def test_parse_manga_search_rejects_invalid_data_shape(self):
        with self.assertRaises(MangaDexPayloadError):
            parse_manga_search({"data": {}})


def http_error(status, retry_after=None):
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(
        "https://example.test",
        status,
        "error",
        headers,
        io.BytesIO(b""),
    )


def manga_search_payload(items):
    return {"result": "ok", "response": "collection", "data": items}


def manga_item(
    manga_id,
    *,
    title=None,
    alt_titles=None,
    original_language=None,
    status=None,
    year=None,
    links=None,
    relationships=None,
):
    attributes = {
        "title": title if title is not None else {},
        "altTitles": alt_titles if alt_titles is not None else [],
        "originalLanguage": original_language,
        "status": status,
        "year": year,
        "links": links if links is not None else {},
    }
    return {
        "id": manga_id,
        "type": "manga",
        "attributes": attributes,
        "relationships": relationships if relationships is not None else [],
    }


if __name__ == "__main__":
    unittest.main()
