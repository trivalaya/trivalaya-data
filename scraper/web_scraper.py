import re
import unicodedata
from lxml.html import fromstring
from http_client import get
from image_downloader import save_raw_snapshot

ZERO_WIDTH_RE = re.compile(r'[\u200B-\u200D\uFEFF]+')
WS_RE = re.compile(r'\s+')

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = ZERO_WIDTH_RE.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    text = WS_RE.sub(" ", text)
    return text.strip()

def normalize_number(value: str) -> str:
    if not value:
        return value
    value = value.replace(",", ".")
    try:
        num = float(value)
        return str(int(num)) if num.is_integer() else f"{num:g}"
    except ValueError:
        return value

def clean_url(url: str) -> str:
    """
    Fixes protocol-relative URLs.
    Smartly removes cache busters while preserving authentication tokens.
    """
    if not url:
        return None
    
    url = clean_text(url)
    
    # Fix protocol-relative URLs (e.g., //media... -> https://media...)
    if url.startswith("//"):
        url = "https:" + url
        
    # Smart Query String Handling
    if "?" in url:
        base, query = url.split("?", 1)
        
        # HEURISTIC:
        # If query contains '=', it's likely functional (SAS tokens, IDs) -> KEEP IT
        # If query has NO '=', it's likely a timestamp/cache-buster -> STRIP IT
        if "=" not in query:
            url = base
        # Else: keep the url as-is with parameters
            
    return url

def parse_lot(config, lot_number, sale_id, closing_date, debug=False, site_name: str | None = None):
    url = config["base_url"].format(
        sale_id=sale_id,
        lot_number=lot_number
    )

    # Fetch HTML (http_client.get uses requests.Session + raise_for_status())
    response = get(url)

    # ✅ Forensic snapshot: save raw bytes BEFORE parsing
    # Uses passed site_name if provided, else falls back to config["name"] or "unknown"
    try:
        effective_site = site_name or config.get("name", "unknown")
        save_raw_snapshot(
            config=config,
            html_bytes=response.content,
            sale_id=sale_id,
            lot_number=lot_number,
            site_name=effective_site,
        )
    except Exception as e:
        # Never fail scrape because snapshot failed
        if debug:
            print(f"[snapshot] lot {lot_number}: {e}")

    # Parse HTML
    html = fromstring(response.content)

    data = {"lot_number": lot_number}
    data["lot_url"] = url

    # 1. Parse Text Fields
    for field, xpath in config["parsers"].items():
        nodes = html.xpath(xpath)
        if nodes:
            raw = "".join(
                n if isinstance(n, str) else n.text_content()
                for n in nodes
            )
            value = clean_text(raw)
        else:
            value = config["default_values"].get(field, "N/A")

        if field == "current_bid":
            value = normalize_number(value)

        data[field] = value

    # 2. Parse Image URL
    raw_image_url = None
    if "image_url_xpath" in config:
        imgs = html.xpath(config["image_url_xpath"])
        if imgs:
            raw_image_url = imgs[0] if isinstance(imgs[0], str) else imgs[0].text_content()

    elif "image_url_pattern" in config:
        raw_image_url = config["image_url_pattern"].format(
            sale_id=sale_id,
            lot_number=lot_number
        )

    # 3. Clean the Image URL
    data["image_url"] = clean_url(raw_image_url)

    data["closing_date"] = closing_date or config["default_values"].get(
        "closing_date", "N/A"
    )

    return data
