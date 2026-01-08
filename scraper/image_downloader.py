from pathlib import Path
from http_client import get

def download_image(config, lot_number, auction_id, image_url=None):
    """Download auction source image (immutable)."""
    if not image_url and "image_url_pattern" in config:
        image_url = config["image_url_pattern"].format(
            auction_id=auction_id,
            lot_number=lot_number
        )
    if not image_url:
        return None
    
    # Handle relative URLs
    if image_url.startswith('/'):
        base = config.get("image_base_url", "")
        image_url = base + image_url
    
    folder = Path(config["folder"].format(auction_id=auction_id))
    folder.mkdir(parents=True, exist_ok=True)
    source_path = folder / f"Lot_{lot_number:05d}.jpg"
    try:
        response = get(image_url)
        source_path.write_bytes(response.content)
        return {
            "image_path": str(source_path),
            "image_url": image_url
        }
    except Exception as exc:
        print(f"[image] lot {lot_number}: {exc}")
        return None
