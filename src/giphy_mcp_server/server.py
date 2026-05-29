"""
Giphy MCP Server.

Exposes Giphy API endpoints as MCP tools for AI coding agents.
Search for GIFs, get trending GIFs, fetch random GIFs, and more.

Configuration:
  Set GIPHY_API_KEY environment variable to your Giphy API key.
  Get one at https://developers.giphy.com/

Usage:
  giphy-mcp-server
  python -m giphy_mcp_server
"""

import json
import os
import traceback
from functools import wraps

import httpx

from mcp.server import FastMCP

mcp = FastMCP("giphy")

BASE_URL = "https://api.giphy.com/v1/gifs"


def _get_api_key() -> str:
    # In production (Titus), the key is decrypted from root/metatron/encrypted/GIPHY_API_KEY.mtb
    metatron_path = "/metatron/decrypted/GIPHY_API_KEY"
    if os.path.exists(metatron_path):
        with open(metatron_path) as f:
            key = f.read().strip()
        if key:
            return key
    key = os.environ.get("GIPHY_API_KEY")
    if not key:
        raise RuntimeError(
            "GIPHY_API_KEY not set. Set GIPHY_API_KEY env var or store encrypted "
            "secret at root/metatron/encrypted/GIPHY_API_KEY.mtb. "
            "Get a free API key at https://developers.giphy.com/"
        )
    return key


def _json(obj):
    return json.dumps(obj, indent=2, default=str)


def _handle_errors(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            return _json(
                {
                    "error": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc()[-1000:],
                }
            )

    return wrapper


def _format_gif(gif: dict) -> dict:
    images = gif.get("images", {})
    original = images.get("original", {})
    downsized = images.get("downsized", {})
    preview = images.get("preview_gif", {})
    user = gif.get("user")

    return {
        "id": gif.get("id"),
        "title": gif.get("title"),
        "url": gif.get("url"),
        "embed_url": gif.get("embed_url"),
        "rating": gif.get("rating"),
        "images": {
            "original": {
                "url": original.get("url"),
                "width": original.get("width"),
                "height": original.get("height"),
            },
            "downsized": {
                "url": downsized.get("url"),
                "width": downsized.get("width"),
                "height": downsized.get("height"),
            },
            "preview": {
                "url": preview.get("url"),
                "width": preview.get("width"),
                "height": preview.get("height"),
            },
        },
        "source": gif.get("source"),
        "import_datetime": gif.get("import_datetime"),
        "user": {
            "username": user.get("username"),
            "display_name": user.get("display_name"),
            "profile_url": user.get("profile_url"),
        }
        if user
        else None,
    }


async def _giphy_request(endpoint: str, params: dict) -> dict:
    params["api_key"] = _get_api_key()
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
@_handle_errors
async def search_gifs(
    query: str,
    limit: int = 10,
    offset: int = 0,
    rating: str = "g",
    lang: str = "en",
) -> str:
    """Search for GIFs on Giphy.

    Args:
        query: Search query term or phrase (e.g. "funny cats", "thumbs up").
        limit: Max number of results to return (default 10, max 50).
        offset: Results offset for pagination (default 0).
        rating: Content rating filter: "g", "pg", "pg-13", or "r" (default "g").
        lang: Language code (default "en").
    """
    data = await _giphy_request(
        "search",
        {"q": query, "limit": min(limit, 50), "offset": offset, "rating": rating, "lang": lang},
    )
    gifs = [_format_gif(g) for g in data.get("data", [])]
    pagination = data.get("pagination", {})
    return _json(
        {
            "query": query,
            "count": len(gifs),
            "total_count": pagination.get("total_count"),
            "offset": pagination.get("offset"),
            "gifs": gifs,
        }
    )


@mcp.tool()
@_handle_errors
async def get_trending_gifs(
    limit: int = 10,
    offset: int = 0,
    rating: str = "g",
) -> str:
    """Get currently trending GIFs on Giphy.

    Args:
        limit: Max number of results to return (default 10, max 50).
        offset: Results offset for pagination (default 0).
        rating: Content rating filter: "g", "pg", "pg-13", or "r" (default "g").
    """
    data = await _giphy_request(
        "trending",
        {"limit": min(limit, 50), "offset": offset, "rating": rating},
    )
    gifs = [_format_gif(g) for g in data.get("data", [])]
    pagination = data.get("pagination", {})
    return _json(
        {
            "count": len(gifs),
            "total_count": pagination.get("total_count"),
            "offset": pagination.get("offset"),
            "gifs": gifs,
        }
    )


@mcp.tool()
@_handle_errors
async def get_random_gif(
    tag: str | None = None,
    rating: str = "g",
) -> str:
    """Get a random GIF from Giphy, optionally filtered by tag.

    Args:
        tag: Tag to limit random results (e.g. "cats", "happy"). Optional.
        rating: Content rating filter: "g", "pg", "pg-13", or "r" (default "g").
    """
    params: dict = {"rating": rating}
    if tag:
        params["tag"] = tag
    data = await _giphy_request("random", params)
    gif = _format_gif(data.get("data", {}))
    return _json({"gif": gif})


@mcp.tool()
@_handle_errors
async def get_gif_by_id(gif_id: str) -> str:
    """Get a specific GIF by its Giphy ID.

    Args:
        gif_id: The Giphy GIF ID (e.g. "xT9IgzoKnwFNmISR8I").
    """
    data = await _giphy_request(gif_id, {})
    gif = _format_gif(data.get("data", {}))
    return _json({"gif": gif})


@mcp.tool()
@_handle_errors
async def translate(
    term: str,
    rating: str = "g",
) -> str:
    """Translate a word or phrase to the perfect GIF using Giphy's WeirdnesS algorithm.

    This is Giphy's special "translate" endpoint that converts a term
    into the single most relevant GIF. Great for reactions and responses.

    Args:
        term: Term or phrase to translate (e.g. "excited", "oh no").
        rating: Content rating filter: "g", "pg", "pg-13", or "r" (default "g").
    """
    data = await _giphy_request("translate", {"s": term, "rating": rating})
    gif = _format_gif(data.get("data", {}))
    return _json({"term": term, "gif": gif})


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
