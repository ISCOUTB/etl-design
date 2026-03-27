import json
import ssl
import uuid
from http.client import HTTPConnection
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, urlencode, urlparse

import httpx
from opentelemetry.propagate import inject


def inject_otel_headers(headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Inject the current OpenTelemetry context into HTTP headers."""
    carrier = dict(headers or {})
    inject(carrier)
    return carrier


def _is_ssl_error(exc: BaseException) -> bool:
    """Return True when exception chain indicates an SSL transport failure."""
    current: BaseException | None = exc
    depth = 0
    while current is not None and depth < 8:
        if isinstance(current, ssl.SSLError):
            return True

        message = str(current).lower()
        if "_ssl.c:" in message or "ssl" in message:
            return True

        current = current.__cause__ or current.__context__
        depth += 1

    return False


def _build_http_path(url: str, params: Dict[str, Any]) -> str:
    parsed = urlparse(url)
    query_items = list(parse_qsl(parsed.query, keep_blank_values=True))
    for key, value in params.items():
        query_items.append((key, value))

    query = urlencode(query_items, doseq=True)
    path = parsed.path or "/"
    return f"{path}?{query}" if query else path


def _encode_multipart_form_data(
    files: Dict[str, Any],
    data: Dict[str, Any],
    boundary: str,
) -> bytes:
    """Build multipart/form-data body bytes for stdlib HTTP fallback."""
    body = bytearray()
    separator = f"--{boundary}\r\n".encode("utf-8")

    for key, value in data.items():
        body.extend(separator)
        body.extend(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(
                "utf-8"
            )
        )
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    for field_name, file_value in files.items():
        filename = "upload.bin"
        content_type = "application/octet-stream"
        content: bytes

        if isinstance(file_value, tuple):
            if len(file_value) >= 2:
                filename = str(file_value[0])
                raw_content = file_value[1]
            elif len(file_value) == 1:
                raw_content = file_value[0]
            else:
                raw_content = b""

            if len(file_value) >= 3 and file_value[2]:
                content_type = str(file_value[2])
        else:
            raw_content = file_value

        if isinstance(raw_content, bytes):
            content = raw_content
        else:
            content = str(raw_content).encode("utf-8")

        body.extend(separator)
        body.extend(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8")
        )
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(content)
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body)


def post_json_http_with_ssl_fallback(
    *,
    url: str,
    payload: Dict[str, Any],
    timeout_seconds: float,
    logger: Any,
    context: str,
) -> int:
    """POST JSON with httpx and fallback to stdlib HTTPConnection on SSLError.

    Returns the successful HTTP status code.
    Raises RuntimeError on non-2xx responses or transport failures.
    """
    headers = inject_otel_headers({"Content-Type": "application/json"})

    try:
        with httpx.Client(
            timeout=timeout_seconds,
            trust_env=False,
            verify=False,
        ) as client:
            response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.status_code
    except Exception as exc:
        if not _is_ssl_error(exc):
            raise RuntimeError(
                f"{context}: {type(exc).__name__}: {repr(exc)}"
            ) from exc

        logger.warning(
            f"{context}: httpx raised SSLError on plain HTTP. "
            "Retrying with stdlib HTTPConnection. "
            f"Error: {repr(exc)}"
        )

        parsed = urlparse(url)
        if parsed.scheme != "http" or not parsed.hostname:
            raise RuntimeError(
                f"{context}: stdlib fallback only supports absolute HTTP URLs. "
                f"Got: {url}"
            ) from exc

        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        body = json.dumps(payload)
        conn = HTTPConnection(
            host=parsed.hostname,
            port=parsed.port or 80,
            timeout=timeout_seconds,
        )
        try:
            conn.request("POST", path, body=body, headers=headers)
            resp = conn.getresponse()
            if resp.status >= 400:
                text = resp.read(300).decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"{context}: HTTP {resp.status} {resp.reason}. Body: {text}"
                )
            return resp.status
        finally:
            conn.close()


def post_multipart_http(
    *,
    url: str,
    files: Dict[str, Any],
    data: Dict[str, Any],
    params: Dict[str, Any],
    timeout_seconds: float,
    logger: Any,
    context: str,
) -> httpx.Response:
    """POST multipart/form-data with OTel propagation and SSL fallback."""
    headers = inject_otel_headers()

    try:
        with httpx.Client(
            timeout=timeout_seconds,
            trust_env=False,
            verify=False,
        ) as client:
            response = client.post(
                url,
                files=files,
                data=data,
                params=params,
                headers=headers,
            )
        response.raise_for_status()
        return response
    except Exception as exc:
        if not _is_ssl_error(exc):
            raise RuntimeError(
                f"{context}: {type(exc).__name__}: {repr(exc)}"
            ) from exc

        logger.warning(
            f"{context}: httpx raised SSLError on plain HTTP multipart request. "
            "Retrying with stdlib HTTPConnection. "
            f"Error: {repr(exc)}"
        )

        parsed = urlparse(url)
        if parsed.scheme != "http" or not parsed.hostname:
            raise RuntimeError(
                f"{context}: stdlib fallback only supports absolute HTTP URLs. "
                f"Got: {url}"
            ) from exc

        boundary = f"----typechecking-{uuid.uuid4().hex}"
        body = _encode_multipart_form_data(files=files, data=data, boundary=boundary)
        multipart_headers = dict(headers)
        multipart_headers["Content-Type"] = (
            f"multipart/form-data; boundary={boundary}"
        )
        multipart_headers["Content-Length"] = str(len(body))

        path = _build_http_path(url, params)
        conn = HTTPConnection(
            host=parsed.hostname,
            port=parsed.port or 80,
            timeout=timeout_seconds,
        )
        try:
            conn.request("POST", path, body=body, headers=multipart_headers)
            resp = conn.getresponse()
            content = resp.read()

            if resp.status >= 400:
                text = content[:300].decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"{context}: HTTP {resp.status} {resp.reason}. Body: {text}"
                )

            request = httpx.Request("POST", url)
            return httpx.Response(
                status_code=resp.status,
                headers=dict(resp.getheaders()),
                content=content,
                request=request,
            )
        finally:
            conn.close()
