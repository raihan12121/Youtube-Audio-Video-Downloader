"""
Thumbnail caching and asynchronous image loader for smooth GUI rendering.
"""

import hashlib
import io
import threading
from pathlib import Path
from typing import Callable, Dict, Optional
import requests
from PIL import Image, ImageDraw
import customtkinter as ctk


CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache" / "thumbnails"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ThumbnailCache:
    """Manages downloading, disk caching, and CTkImage generation."""

    def __init__(self):
        self._memory_cache: Dict[str, Image.Image] = {}
        self._lock = threading.Lock()
        self._placeholder: Optional[Image.Image] = None

    def get_placeholder(self, width: int = 120, height: int = 68) -> Image.Image:
        """Generates a stylish dark placeholder image."""
        key = f"placeholder_{width}x{height}"
        if key in self._memory_cache:
            return self._memory_cache[key]

        img = Image.new("RGBA", (width, height), color=(30, 30, 40, 255))
        draw = ImageDraw.Draw(img)

        # Draw a subtle play icon in center
        cx, cy = width // 2, height // 2
        r = min(width, height) // 4
        poly = [
            (cx - r // 2, cy - r),
            (cx - r // 2, cy + r),
            (cx + r, cy)
        ]
        draw.polygon(poly, fill=(120, 120, 140, 255))

        self._memory_cache[key] = img
        return img

    def get_ctk_image(
        self,
        url: Optional[str],
        size: tuple = (120, 68),
        on_loaded: Optional[Callable[[ctk.CTkImage], None]] = None
    ) -> ctk.CTkImage:
        """
        Returns a CTkImage for the URL. If not cached, returns a placeholder
        and asynchronously downloads the image, calling on_loaded when ready.
        """
        if not url:
            ph = self.get_placeholder(size[0], size[1])
            return ctk.CTkImage(light_image=ph, dark_image=ph, size=size)

        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
        cache_path = CACHE_DIR / f"{url_hash}.jpg"

        with self._lock:
            if url_hash in self._memory_cache:
                pil_img = self._memory_cache[url_hash]
                return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)

        # Check disk cache
        if cache_path.exists():
            try:
                pil_img = Image.open(cache_path).convert("RGB")
                pil_img.thumbnail((size[0] * 2, size[1] * 2), Image.Resampling.LANCZOS)
                with self._lock:
                    self._memory_cache[url_hash] = pil_img
                return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            except Exception:
                pass

        # Need to fetch asynchronously
        placeholder = self.get_placeholder(size[0], size[1])
        ctk_ph = ctk.CTkImage(light_image=placeholder, dark_image=placeholder, size=size)

        if on_loaded:
            threading.Thread(
                target=self._fetch_worker,
                args=(url, url_hash, cache_path, size, on_loaded),
                daemon=True
            ).start()

        return ctk_ph

    def _fetch_worker(
        self,
        url: str,
        url_hash: str,
        cache_path: Path,
        size: tuple,
        on_loaded: Callable[[ctk.CTkImage], None]
    ):
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                raw_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                # Save to disk
                raw_img.save(cache_path, format="JPEG", quality=85)
                # Resize
                raw_img.thumbnail((size[0] * 2, size[1] * 2), Image.Resampling.LANCZOS)
                with self._lock:
                    self._memory_cache[url_hash] = raw_img

                ctk_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=size)
                on_loaded(ctk_img)
        except Exception:
            pass


thumbnail_cache = ThumbnailCache()
