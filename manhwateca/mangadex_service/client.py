import json
import random
import socket
import time
import urllib.error
import urllib.request
from urllib.parse import urlencode


API_BASE = "https://api.mangadex.org"
USER_AGENT = "Manhwateca/1.0"


class MangaDexError(Exception):
    """Base error for MangaDex HTTP client failures."""


class MangaDexHTTPError(MangaDexError):
    def __init__(self, status_code, message=None, url=None):
        self.status_code = status_code
        self.url = url
        text = message or f"MangaDex HTTP {status_code}"
        super().__init__(text)


class MangaDexRateLimitError(MangaDexHTTPError):
    def __init__(self, status_code=429, message=None, url=None, retry_after=None):
        self.retry_after = retry_after
        super().__init__(
            status_code,
            message or "Limite de requisições do MangaDex atingido.",
            url=url,
        )


class MangaDexPayloadError(MangaDexError):
    pass


def request_json(
    path,
    params=None,
    *,
    base_url=API_BASE,
    timeout=30,
    retries=2,
    base_delay=3.0,
    urlopen_func=None,
    sleep_func=None,
):
    urlopen_func = urlopen_func or urllib.request.urlopen
    sleep_func = sleep_func or time.sleep
    url = _build_url(base_url, path, params)
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    for attempt in range(retries + 1):
        try:
            with urlopen_func(request, timeout=timeout) as response:
                return _load_json(response)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                retry_after = _retry_after(error)
                if attempt < retries:
                    sleep_func(_retry_delay(attempt, retry_after, base_delay))
                    continue
                raise MangaDexRateLimitError(
                    url=error.url,
                    retry_after=retry_after,
                ) from error
            if 500 <= error.code < 600 and attempt < retries:
                sleep_func(_retry_delay(attempt, None, base_delay))
                continue
            raise MangaDexHTTPError(
                error.code,
                f"MangaDex HTTP {error.code}",
                url=error.url,
            ) from error
        except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
            if attempt < retries:
                sleep_func(_retry_delay(attempt, None, base_delay))
                continue
            raise MangaDexError(f"Falha ao consultar MangaDex: {error}") from error


def _build_url(base_url, path, params=None):
    url = f"{str(base_url).rstrip('/')}/{str(path).lstrip('/')}"
    if params:
        url = f"{url}?{urlencode(params, doseq=True)}"
    return url


def _load_json(response):
    try:
        payload = json.load(response)
    except json.JSONDecodeError as error:
        raise MangaDexPayloadError("Resposta MangaDex não é JSON válido.") from error
    if not isinstance(payload, (dict, list)):
        raise MangaDexPayloadError("Resposta MangaDex possui estrutura inválida.")
    return payload


def _retry_after(error):
    value = error.headers.get("Retry-After") if error.headers else None
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _retry_delay(attempt, retry_after, base_delay):
    if retry_after is not None:
        return retry_after
    return base_delay * (2 ** attempt) + random.uniform(0, 1)
