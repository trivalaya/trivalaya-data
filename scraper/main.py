import argparse
from database_handler import DatabaseHandler
from scraper import scrape_site
from site_configs import SITE_CONFIGS

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("site")
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    parser.add_argument("auction_id", type=int)
    parser.add_argument("closing_date")
    parser.add_argument("--download-images", action="store_true")

    args = parser.parse_args()

    db = DatabaseHandler(
        host="127.0.0.1",
        user="auction_user",
        password="Veritas@2024",
        database="auction_data",
    )

    scrape_site(
        site_name=args.site,
        lot_range=range(args.start, args.end + 1),
        auction_id=args.auction_id,
        closing_date=args.closing_date,
        db_handler=db,
        download_images=args.download_images,
        site_configs=SITE_CONFIGS,
    )

if __name__ == "__main__":
    main()
