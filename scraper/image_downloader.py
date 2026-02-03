import os
import requests
from pathlib import Path
from urllib.parse import urljoin
from functools import lru_cache
from http_client import get

# ---- 1. Storage Client Caching ----
@lru_cache(maxsize=1)
def _get_spaces_client():
    from spaces_storage import SpacesStorage
    return SpacesStorage()

# ---- 2. Content Sniffing & Mapping ----
_CT_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

# Reverse map for when we detect ext but have bad headers
_EXT_TO_CT = {v: k for k, v in _CT_TO_EXT.items()}

def _sniff_image_ext(data: bytes) -> str | None:
    """Detects image type by looking at the first few 'magic bytes'."""
    if len(data) >= 3 and data[0:3] == b"\xFF\xD8\xFF":
        return ".jpg"
    if len(data) >= 8 and data[0:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if len(data) >= 6 and data[0:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    return None

def _raw_key(site_name: str, sale_id, lot_number: int, ext: str) -> str:
    return f"raw/auctions/{site_name}/{sale_id}/Lot_{lot_number:05d}{ext}"
import os
import gzip
from pathlib import Path

def save_raw_snapshot(config, html_bytes: bytes, sale_id, lot_number: int, site_name: str):
    """Forensic backup: saves the exact HTML bytes seen at scrape time (optionally gzipped)."""
    if not html_bytes:
        return

    mode = os.getenv("TRIVALAYA_SCRAPER_PAGE_STORAGE", "spaces").lower()  # local|spaces|both|off
    if mode == "off":
        return

    write_local = mode in ("local", "both")
    write_spaces = mode in ("spaces", "both")

    # gzip compress (fast, big win)
    try:
        gz = gzip.compress(html_bytes, compresslevel=6)
    except Exception:
        gz = html_bytes  # fallback: store raw if gzip fails

    # Local write (optional)
    local_path = None
    if write_local:
        folder = Path(config["folder"].format(sale_id=sale_id)) / "_pages"
        folder.mkdir(parents=True, exist_ok=True)
        local_path = folder / f"Lot_{lot_number:05d}.html.gz"
        try:
            local_path.write_bytes(gz)
        except Exception as e:
            print(f"[snapshot] Local write failed lot {lot_number}: {e}")

    # Spaces write (preferred)
    if write_spaces:
        try:
            ss = _get_spaces_client()  # reuse cached client
            key = f"raw/pages/{site_name}/{sale_id}/Lot_{lot_number:05d}.html.gz"
            ss.put_bytes(key, gz, content_type="application/gzip")
        except Exception as e:
            print(f"[snapshot] Failed to save HTML for lot {lot_number}: {e}")


def download_image(config, lot_number, sale_id, image_url=None, *, site_name: str = ""):
    """Download auction source image (immutable) with strict validation."""

    # -- A. Resolve URL safely --
    if not image_url and "image_url_pattern" in config:
        image_url = config["image_url_pattern"].format(sale_id=sale_id, lot_number=lot_number)
    
    if not image_url:
        return None

    base = config.get("image_base_url")
    if base:
        image_url = urljoin(base, image_url)

    mode = os.getenv("TRIVALAYA_SCRAPER_IMAGE_STORAGE", "local").lower()
    write_local = mode in ("local", "both")
    write_spaces = mode in ("spaces", "both")

    try:
        # http_client.get raises raise_for_status(), so we wrap in try/except
        resp = get(image_url)
        
        # -- B. Critical: Validate Content --
        img_bytes = getattr(resp, "content", b"") or b""
        
        if len(img_bytes) < 256:
            print(f"[image] lot {lot_number}: File too small ({len(img_bytes)} bytes) - skipping")
            return None

        # Check for HTML masquerading as an image
        head = img_bytes[:64].lstrip().lower()
        if head.startswith(b"<!doctype html") or head.startswith(b"<html"):
            print(f"[image] lot {lot_number}: Downloaded HTML instead of image")
            return None

        # -- C. Determine Extension (Strict) --
        headers = getattr(resp, "headers", {}) or {}
        server_ct = headers.get("Content-Type", "").split(";")[0].strip().lower()
        
        # 1. Trust header if mapped
        ext = _CT_TO_EXT.get(server_ct)
        # 2. If header unknown/generic, sniff bytes
        if not ext:
            ext = _sniff_image_ext(img_bytes)
        
        # 3. STRICT REJECT: If we still don't know, don't save garbage
        if not ext: 
            print(f"[image] lot {lot_number}: Unknown image format (Header: {server_ct}) - refusing to save")
            return None

        # -- D. Determine correct Content-Type for Storage --
        # If server gave us "application/octet-stream" but we found it's a JPEG, fix it.
        final_content_type = server_ct if server_ct in _CT_TO_EXT else _EXT_TO_CT.get(ext, "application/octet-stream")

        # -- E. Write to Storage --
        
        # Local Write
        source_path = None
        if write_local:
            folder = Path(config["folder"].format(sale_id=sale_id))
            folder.mkdir(parents=True, exist_ok=True)
            source_path = folder / f"Lot_{lot_number:05d}{ext}"
            source_path.write_bytes(img_bytes)

        # Spaces Write
        spaces_key = None
        if write_spaces:
            ss = _get_spaces_client() # Cached
            site = site_name or config.get("name", "unknown")
            key = _raw_key(site, sale_id, lot_number, ext)
            spaces_key = ss.put_bytes(key, img_bytes, content_type=final_content_type)

        return {
            "image_path": spaces_key if spaces_key else (str(source_path) if source_path else None),
            "image_url": image_url,
            "image_key": spaces_key,
            "local_path": str(source_path) if source_path else None,
            "content_type": final_content_type
        }

    except requests.HTTPError as e:
        # Handle 404s, 403s cleanly
        code = e.response.status_code if e.response else "Unknown"
        print(f"[image] lot {lot_number}: HTTP {code} for {image_url}")
        return None
        
    except requests.RequestException as e:
        # Handle timeouts, DNS errors
        print(f"[image] lot {lot_number}: Network error: {e}")
        return None
    
    except Exception as exc:
        print(f"[image] lot {lot_number} error: {exc}")
        return None