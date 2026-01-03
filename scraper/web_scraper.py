import re
import unicodedata
from lxml.html import fromstring
from http_client import get

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

def parse_lot(config, lot_number, auction_id, closing_date, debug=False):
    url = config["base_url"].format(
        auction_id=auction_id,
        lot_number=lot_number
    )

    html = fromstring(get(url).content)

    data = {"lot_number": lot_number}

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

    if "image_url_xpath" in config:
        imgs = html.xpath(config["image_url_xpath"])
        data["image_url"] = clean_text(imgs[0]) if imgs else None
    elif "image_url_pattern" in config:
        data["image_url"] = config["image_url_pattern"].format(
            auction_id=auction_id,
            lot_number=lot_number
        )

    data["closing_date"] = closing_date or config["default_values"].get(
        "closing_date", "N/A"
    )

    return data
