"""
Site configurations for auction house scrapers.
Each config defines URL patterns, XPath selectors, and default values.

USAGE:
    from site_configs import SITE_CONFIGS
    config = SITE_CONFIGS["spink"]
    url = config["base_url"].format(auction_id="21060", lot_number="000868")
"""

SITE_CONFIGS = {
    # =========================================================================
    # EXISTING CONFIGURATIONS
    # =========================================================================
    
    "leu": {
        "name": "leu",
        "base_url": "https://leunumismatik.com/en/lot/{auction_id}/{lot_number}",
        "folder": "leu_{auction_id}",
        "parsers": {
            "title": "//div[@id='ctl36_divLot']/b/text()",
            "description": "//div[@id='ctl36_divLot']/text()",
            "current_bid": "//div[@id='ctl36_divCurrentBid']/text()",
        },
        "image_url_xpath": '//div[@class="col-xs-12 mb-3 lot-description"]//img/@src | //img[contains(@src, "saleuprod.blob.core.windows.net")]/@src',
        "use_lxml": True,
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "No Current Bid",
            "closing_date": "N/A",
        },
    },
    
    "gorny": {
        "name": "gorny",
        "base_url": "https://auktionen.gmcoinart.de/Los/{auction_id}/{lot_number}.0",
        "image_url_pattern": "https://images.auex.de/img/9//{auction_id}/{lot_number:05d}q00.jpg",
        "folder": "gorny_{auction_id}",
        "parsers": {
            "title": "(//div[@class='description']//b)[1]/text() | (//div[@class='description']//strong)[1]/text()",
            "description": "string(//div[@class='description'])",
            "current_bid": '(//table[@class="biddings biddings-top"]//span[@class="bidding" and @data-currency="EUR"]/@data-price)[1]',
        },
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "No Current Bid",
            "closing_date": "N/A",
        },
    },
    
    "nomos": {
        "name": "nomos",
        "base_url": "https://nomosag.com/nomos-{auction_id}/{lot_number}",
        "folder": "nomos_{auction_id}",
        "parsers": {
            "title": "(//p[@class='o-singleLot__description']/b)[1]/text()",
            "description": "string((//p[@class='o-singleLot__description'])[1])",
            "current_bid": "//span[@class='lotCurrentBidInfo']/text()",
        },
        "image_url_xpath": "//img[@id='singleLot-image']/@data-src",
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "0",
        },
        "crawl_delay": 2,
    },
    
    "obolos": {
        "name": "obolos",
        "base_url": "https://nomosag.com/obolos-{auction_id}/{lot_number}",
        "folder": "obolos_{auction_id}",
        "parsers": {
            "title": "(//p[@class='o-singleLot__description']/b)[1]/text()",
            "description": "string((//p[@class='o-singleLot__description'])[1])",
            "current_bid": "//span[@class='lotCurrentBidInfo']/text()",
        },
        "image_url_xpath": "//img[@id='singleLot-image']/@data-src",
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "0",
        },
        "crawl_delay": 2,
    },

    "cng": {
        "name": "cng",
        "base_url": "https://cngcoins.com/Lot.aspx?LOT_ID={lot_number}",
        "image_base_url": "https://cngcoins.com",
        "folder": "cng_{auction_id}",
        "parsers": {
            "title": "//h3[@id='_ctl0_bodyContentPlaceHolder_txtName']/text()",
            "description": "//p[@id='_ctl0_bodyContentPlaceHolder_txtDescription']//text()",
            "current_bid": "//p[@id='_ctl0_bodyContentPlaceHolder_txtPrice']//text()",
        },
        "image_url_xpath": "//img[@id='_ctl0_bodyContentPlaceHolder_imgLot']/@src",
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "0",
        },
        "crawl_delay": 2,
    },

    # =========================================================================
    # NEW CONFIGURATIONS - SPINK & KÜNKER
    # =========================================================================

    "spink": {
        "name": "spink",
        # URL Pattern: https://www.spink.com/lot/21060000868
        # Format: {auction_id}{lot_number} where lot_number is zero-padded to 6 digits
        # Example: auction 21060, lot 868 -> 21060000868
        "base_url": "https://www.spink.com/lot/{auction_id}{lot_number:06d}",
        "folder": "spink_{auction_id}",
        "currency": "GBP",
        "parsers": {
                    # Title - first bold text
                    "title": "//b[1]//text()",
                    # Description - get all text from the container div (will include title, but that's ok)
                    "description": "//span[@class='description']//text()",
                    # Price - just the first £ value (realized price comes before estimate on Spink)
                    "current_bid": "(//text()[contains(., '£')])[1]",
                },
        # Image URL pattern from Cloudfront CDN
        # Example: https://d3ums4016ncdkp.cloudfront.net/auction/main/21060/21060_868_1.jpg
        "image_url_xpath": "//img[contains(@src, 'cloudfront.net')]/@src | //img[contains(@class, 'img-responsive')]/@src",
        "image_url_pattern": "https://d3ums4016ncdkp.cloudfront.net/auction/main/{auction_id}/{auction_id}_{lot_number}_1.jpg",
        "default_values": {
            "title": "No Title",
            "description": "No Description", 
            "current_bid": "0",
            "closing_date": "N/A",
        },
        "crawl_delay": 2,
        # Spink has excellent sceatta coverage - Tony Abramson Collection
        "notes": "Good for: Sceattas, Anglo-Saxon, British hammered coins",
    },

    "kuenker": {
        "name": "kuenker",
        # Künker uses AUEX platform for auctions
        # Lot URL: https://www.kuenker.de/en/archiv/stueck/{lot_id}
        # Or via AUEX: https://auex.de/de/product/{lot_id}
        # The lot_id appears to be a global ID, not auction+lot
        "base_url": "https://www.kuenker.de/en/archiv/stueck/{lot_number}",
        "folder": "kuenker_{auction_id}",
        "currency": "EUR",
        "parsers": {
            # Künker lot pages have structured data
            "title": "//h1[contains(@class, 'product-detail-name')]/text() | //div[contains(@class, 'lot-title')]//text()",
            "description": "string(//div[contains(@class, 'product-detail-description')]) | string(//div[contains(@class, 'lot-description')])",
            "current_bid": "//span[contains(@class, 'product-detail-price')]/text() | //div[contains(@class, 'hammer-price')]//text()",
            "estimate": "//div[contains(text(), 'Estimate') or contains(text(), 'Schätzpreis')]/following-sibling::text()",
        },
        "image_url_xpath": "//img[contains(@src, 'kuenker.s3')]/@src | //img[contains(@class, 'product-detail-image')]/@src",
        # Künker S3 image pattern
        "image_base_url": "https://kuenker.s3.eu-central-1.amazonaws.com",
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "0",
            "closing_date": "N/A",
        },
        "crawl_delay": 2,
        # Künker is strong in German medieval, Celtic, Roman
        "notes": "Good for: Celtic, Roman Imperial, German Medieval, Byzantine",
    },

    # Alternative Künker config for AUEX platform (their live auction system)
    "kuenker_auex": {
        "name": "kuenker_auex", 
        # AUEX lot format: auction_id + lot_number
        "base_url": "https://auex.de/de/product/{auction_id}-{lot_number}",
        "folder": "kuenker_auex_{auction_id}",
        "currency": "EUR",
        "parsers": {
            "title": "//h1[contains(@class, 'title')]/text()",
            "description": "string(//div[contains(@class, 'description')])",
            "current_bid": "//span[contains(@class, 'price')]/text()",
        },
        "image_url_xpath": "//img[contains(@class, 'lot-image')]/@src",
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "0",
        },
        "crawl_delay": 2,
    },
}


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_spink_url(auction_id: int, lot_number: int) -> str:
    """
    Generate Spink lot URL.
    
    Spink URL format: https://www.spink.com/lot/{auction_id}{lot_number:06d}
    
    Examples:
        get_spink_url(21060, 868) -> "https://www.spink.com/lot/21060000868"
        get_spink_url(16019, 53)  -> "https://www.spink.com/lot/16019000053"
    """
    return f"https://www.spink.com/lot/{auction_id}{lot_number:06d}"


def get_spink_image_url(auction_id: int, lot_number: int) -> str:
    """
    Generate Spink image URL from Cloudfront CDN.
    
    Example:
        get_spink_image_url(21060, 868) -> 
        "https://d3ums4016ncdkp.cloudfront.net/auction/main/21060/21060_868_1.jpg"
    """
    return f"https://d3ums4016ncdkp.cloudfront.net/auction/main/{auction_id}/{auction_id}_{lot_number}_1.jpg"


def get_kuenker_archive_url(lot_id: int) -> str:
    """
    Generate Künker archive URL.
    
    Note: Künker uses a global lot_id, not auction+lot format.
    
    Example:
        get_kuenker_archive_url(281856) -> "https://www.kuenker.de/en/archiv/stueck/281856"
    """
    return f"https://www.kuenker.de/en/archiv/stueck/{lot_id}"


# =========================================================================
# SCEATTA-SPECIFIC SEARCH QUERIES
# =========================================================================

SCEATTA_SEARCH_CONFIGS = {
    "spink": {
        "search_url": "https://www.spink.com/archive/index?q=sceatta",
        "department": "coins",
        # Known auctions with sceattas:
        "known_auctions": [
            21060,  # Tony Abramson Collection Part III
            21000,  # Tony Abramson Collection Part I
            16019,  # Lord Stewartby Collection
            9031,   # Ancient, English and Foreign Coins
        ],
    },
    "cng": {
        "search_url": "https://www.cngcoins.com/Search.aspx?SEARCH_TYPE=1&ITEM_DESC=sceatta",
        # CNG has good Anglo-Saxon coverage
    },
    "timeline": {
        # Timeline Auctions - specialist in British hammered
        "search_url": "https://www.timelineauctions.com/search/?q=sceatta",
    },
}


# =========================================================================
# AUCTION HOUSE METADATA (for reference)
# =========================================================================

AUCTION_HOUSE_INFO = {
    "spink": {
        "full_name": "Spink & Son",
        "location": "London, UK",
        "founded": 1666,
        "specialties": ["British coins", "Anglo-Saxon", "Medals", "Banknotes"],
        "buyer_premium": 0.20,  # 20%
        "currency": "GBP",
    },
    "kuenker": {
        "full_name": "Fritz Rudolf Künker GmbH & Co. KG",
        "location": "Osnabrück, Germany",
        "founded": 1971,
        "specialties": ["German coins", "Roman", "Celtic", "Medieval"],
        "buyer_premium": 0.25,  # 25% (margin scheme)
        "currency": "EUR",
    },
    "cng": {
        "full_name": "Classical Numismatic Group",
        "location": "Lancaster, PA, USA",
        "founded": 1975,
        "specialties": ["Greek", "Roman", "Byzantine", "Celtic"],
        "buyer_premium": 0.20,
        "currency": "USD",
    },
    "nomos": {
        "full_name": "Nomos AG",
        "location": "Zurich, Switzerland",
        "founded": 2008,
        "specialties": ["Greek", "Roman", "Celtic"],
        "buyer_premium": 0.20,
        "currency": "CHF",
    },
    "leu": {
        "full_name": "Leu Numismatik AG",
        "location": "Zurich, Switzerland", 
        "founded": 1936,
        "specialties": ["Greek", "Roman", "World coins"],
        "buyer_premium": 0.20,
        "currency": "CHF",
    },
    "gorny": {
        "full_name": "Gorny & Mosch",
        "location": "Munich, Germany",
        "founded": 1974,
        "specialties": ["Greek", "Roman", "Byzantine"],
        "buyer_premium": 0.25,
        "currency": "EUR",
    },
}