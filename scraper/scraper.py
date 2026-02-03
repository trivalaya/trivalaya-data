import time
from web_scraper import parse_lot
from image_downloader import download_image

def scrape_site(
    site_name,
    lot_range,
    sale_id,
    closing_date,
    db_handler,
    download_images=True,
    site_configs=None,
):
    config = site_configs[site_name]

    for lot_number in lot_range:
        data = parse_lot(config, lot_number, sale_id, closing_date, site_name=site_name)

        if not data:
            continue
        data["auction_house"] = site_name
        data["sale_id"] = sale_id
        # ✅ ensure lot_url is present (if parse_lot doesn’t already set it)
        data.setdefault("lot_url", config["base_url"].format(sale_id=sale_id, lot_number=lot_number))

        if download_images:
            img = download_image(
            config,
            lot_number,
            sale_id,
            data.get("image_url"),
            site_name=site_name,
        )

            if img:
                data["image_path"] = img["image_path"]
                data["image_url"] = img["image_url"]
            else:
                data["image_path"] = None
        else:
            data["image_path"] = None

        db_handler.insert_data(data)

        time.sleep(config.get("crawl_delay", 0))
