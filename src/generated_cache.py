"""In-memory cache for generated images (data URLs -> short IDs)."""
from __future__ import annotations

import base64
import uuid
from typing import NamedTuple, Optional


class CachedImage(NamedTuple):
    """Stored image data."""

    data: bytes
    media_type: str


# Simple in-memory store; note: not bounded/evicted.
_STORE: dict[str, CachedImage] = {}


def store_data_url(data_url: str) -> str:
    """
    Store a data URL and return a short ID.

    Args:
        data_url: Data URL string (e.g., data:image/jpeg;base64,...)

    Returns:
        Image ID usable in generated image endpoint
    """
    if not data_url.startswith("data:"):
        raise ValueError("Not a data URL")

    if "," not in data_url:
        raise ValueError("Invalid data URL format")

    header, b64_data = data_url.split(",", 1)
    media_type = "application/octet-stream"
    if ";" in header:
        media_type = header.split(";")[0][5:] or media_type
    elif header.startswith("data:"):
        media_type = header[5:] or media_type

    try:
        data_bytes = base64.b64decode(b64_data)
    except Exception as exc:
        raise ValueError(f"Invalid base64 data: {exc}") from exc

    image_id = uuid.uuid4().hex
    _STORE[image_id] = CachedImage(data=data_bytes, media_type=media_type)
    return image_id


def get_image(image_id: str) -> Optional[CachedImage]:
    """Retrieve a cached image by ID."""
    return _STORE.get(image_id)


def store_bytes(data: bytes, media_type: str = "application/octet-stream") -> str:
    """
    Store raw bytes and return a short ID.

    Args:
        data: Binary image data
        media_type: MIME type (e.g., image/jpeg)

    Returns:
        Image ID usable in generated image endpoint
    """
    image_id = uuid.uuid4().hex
    _STORE[image_id] = CachedImage(data=data, media_type=media_type or "application/octet-stream")
    return image_id
