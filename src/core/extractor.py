"""
Metadata extraction engine using yt-dlp.
Supports single videos, shorts, playlists, channels, and batch URL lists.
"""

import re
import shutil
from typing import Any, Callable, Dict, List, Optional
import yt_dlp

from src.config import config


def get_base_ydl_opts(custom_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Base options for yt-dlp with Node.js and challenge solver enabled."""
    opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "skip_download": True,
    }

    # Enable Node.js for signature / n-token challenge solving if node exists
    if shutil.which("node"):
        opts["js_runtimes"] = {"node": {}}
        opts["remote_components"] = ["ejs:github"]

    # Cookies handling
    browser = config.get("browser_cookies", "none")
    if browser and browser != "none":
        opts["cookiesfrombrowser"] = (browser,)

    custom_cookies = config.get("custom_cookies_path", "")
    if custom_cookies:
        opts["cookiefile"] = custom_cookies

    if custom_opts:
        opts.update(custom_opts)

    return opts


def parse_video_formats(info: Dict[str, Any]) -> List[str]:
    """Parse unique available video resolutions sorted from highest to lowest."""
    formats = info.get("formats", [])
    res_set = set()

    for f in formats:
        # Check video height
        h = f.get("height")
        vcodec = f.get("vcodec")
        if h and vcodec and vcodec != "none":
            if h >= 2160:
                res_set.add("2160p (4K)")
            elif h >= 1440:
                res_set.add("1440p (2K)")
            elif h >= 1080:
                res_set.add("1080p (Full HD)")
            elif h >= 720:
                res_set.add("720p (HD)")
            elif h >= 480:
                res_set.add("480p (SD)")
            elif h >= 360:
                res_set.add("360p")
            elif h >= 240:
                res_set.add("240p")

    order = [
        "2160p (4K)",
        "1440p (2K)",
        "1080p (Full HD)",
        "720p (HD)",
        "480p (SD)",
        "360p",
        "240p"
    ]
    available = [r for r in order if r in res_set]
    if not available:
        available = ["Best Available"]
    else:
        available.insert(0, "Best Available")
    return available


def extract_single_info(url: str) -> Dict[str, Any]:
    """Extract full information and formats for a single video."""
    opts = get_base_ydl_opts({
        "extract_flat": False,
        "noplaylist": True,
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("Could not fetch video information. Please check the URL.")

        # If it somehow returned a playlist, grab first entry
        if "entries" in info:
            entries = list(info["entries"])
            if entries:
                info = entries[0]
            else:
                raise ValueError("No video entry found at URL.")

        resolutions = parse_video_formats(info)

        # Subtitles available
        subtitles = list(info.get("subtitles", {}).keys())
        auto_subtitles = list(info.get("automatic_captions", {}).keys())

        return {
            "id": info.get("id"),
            "title": info.get("title", "Unknown Title"),
            "uploader": info.get("uploader") or info.get("channel") or "Unknown Channel",
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail") or (info.get("thumbnails")[-1]["url"] if info.get("thumbnails") else ""),
            "view_count": info.get("view_count", 0),
            "resolutions": resolutions,
            "has_subtitles": len(subtitles) > 0 or len(auto_subtitles) > 0,
            "subtitles_list": subtitles + [f"{s} (auto)" for s in auto_subtitles[:5]],
            "webpage_url": info.get("webpage_url") or url,
            "filesize_approx": info.get("filesize_approx") or info.get("filesize") or 0,
            "is_live": info.get("is_live", False),
        }


def extract_playlist_or_channel(
    url: str,
    max_items: Optional[int] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Extracts high-level playlist or channel metadata and entries list quickly
    using flat extraction.
    """
    custom_opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "skip_download": True,
    }
    if max_items and max_items > 0:
        custom_opts["playlist_items"] = f"1:{max_items}"

    opts = get_base_ydl_opts(custom_opts)

    if progress_callback:
        progress_callback("Connecting to YouTube and parsing metadata...")

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("Could not extract playlist or channel information.")

        entries_raw = info.get("entries", [])
        entries = []
        idx = 1

        for e in entries_raw:
            if not e:
                continue
            video_id = e.get("id")
            title = e.get("title", f"Video {idx}")
            video_url = e.get("url") or (f"https://www.youtube.com/watch?v={video_id}" if video_id else None)
            if not video_url:
                continue

            thumb = e.get("thumbnail") or (e.get("thumbnails")[-1]["url"] if e.get("thumbnails") else "")

            entries.append({
                "index": idx,
                "id": video_id,
                "title": title,
                "url": video_url,
                "duration": e.get("duration") or 0,
                "uploader": e.get("uploader") or info.get("uploader") or info.get("channel") or "",
                "thumbnail": thumb,
                "selected": True,  # Default selected for download
            })
            idx += 1

        is_channel = "/@" in url or "/channel/" in url or "/c/" in url or "/user/" in url
        title = info.get("title") or ("Channel Videos" if is_channel else "YouTube Playlist")
        uploader = info.get("uploader") or info.get("channel") or ""

        return {
            "type": "channel" if is_channel else "playlist",
            "title": title,
            "uploader": uploader,
            "url": url,
            "total_items": len(entries),
            "entries": entries,
        }


def extract_multiple_urls(urls: List[str]) -> List[Dict[str, Any]]:
    """Takes a list of individual URLs and returns standardized video entries."""
    results = []
    opts = get_base_ydl_opts({
        "extract_flat": True,
        "skip_download": True,
    })

    with yt_dlp.YoutubeDL(opts) as ydl:
        for idx, u in enumerate(urls, 1):
            u_clean = u.strip()
            if not u_clean:
                continue
            try:
                info = ydl.extract_info(u_clean, download=False)
                if not info:
                    continue
                # If it's a playlist entry, unfold
                if "entries" in info:
                    for sub_idx, item in enumerate(info["entries"], 1):
                        if not item:
                            continue
                        vid = item.get("id")
                        results.append({
                            "index": len(results) + 1,
                            "id": vid,
                            "title": item.get("title", f"Item {len(results)+1}"),
                            "url": item.get("url") or f"https://www.youtube.com/watch?v={vid}",
                            "duration": item.get("duration") or 0,
                            "uploader": item.get("uploader") or "",
                            "thumbnail": item.get("thumbnail") or "",
                            "selected": True
                        })
                else:
                    vid = info.get("id")
                    results.append({
                        "index": len(results) + 1,
                        "id": vid,
                        "title": info.get("title", f"Video {len(results)+1}"),
                        "url": info.get("webpage_url") or u_clean,
                        "duration": info.get("duration") or 0,
                        "uploader": info.get("uploader") or "",
                        "thumbnail": info.get("thumbnail") or "",
                        "selected": True
                    })
            except Exception as ex:
                print(f"Error parsing URL {u_clean}: {ex}")
                # Still add placeholder entry so user sees it
                results.append({
                    "index": len(results) + 1,
                    "id": "",
                    "title": u_clean,
                    "url": u_clean,
                    "duration": 0,
                    "uploader": "Unknown",
                    "thumbnail": "",
                    "selected": True
                })

    return results
