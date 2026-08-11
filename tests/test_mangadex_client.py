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


if __name__ == "__main__":
    unittest.main()
