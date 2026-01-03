SITE_CONFIGS = {
    "leu": {
        "name": "leu",  # Added site name
        "base_url": "https://leunumismatik.com/en/lot/{auction_id}/{lot_number}",
        "folder": "leu_{auction_id}",
        "parsers": {
            "title": "//div[@id='ctl36_divLot']/b/text()",  # XPath for the title
            "description": "//div[@id='ctl36_divLot']/text()",  # XPath for the description
            "current_bid": "//div[@id='ctl36_divCurrentBid']/text()",  # XPath for hammer price
        },
        "image_url_xpath": '//div[@class="col-xs-12 mb-3 lot-description"]//img/@src | //img[contains(@src, "saleuprod.blob.core.windows.net")]/@src',
        "use_lxml": True,
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "No Current Bid",
            "closing_date": "23-Oct-2021, 12:00:00",  # Manually set closing date
        },
    },
    "gorny": {
        "base_url": "https://auktionen.gmcoinart.de/Los/{auction_id}/{lot_number}.0",
        "image_url_pattern": "https://images.auex.de/img/9//{auction_id}/{lot_number:05d}q00.jpg",
        "folder": "gorny_{auction_id}",
        "parsers": {
          "title": "//div[@class='description']/strong/text()",  # XPath for title
         "description": "string(//div[@class='description'])",  # Concatenate all text in the description div
         "current_bid": '(//table[@class="biddings biddings-top"]//span[@class="bidding" and @data-currency="EUR"]/@data-price)[1]',
  # XPath for bid price
    },
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "No Current Bid",
            "closing_date": "14-Oct-2019, 12:00:00",
    },
},
        "nomos": {
        "name": "nomos",
        # base_url could be something like https://nomosag.com/auction/{auction_id}
        # or if you need a lot number pattern, adapt it as well:
        "base_url": "https://nomosag.com/nomos-{auction_id}/{lot_number}",
        "image_url_pattern": "https://nomosag.com/images/auctions/{auction_id}/image{lot_number:05d}.jpg",
        # Where you want to download images (if any):
        "folder": "nomos_{auction_id}",

        # This dict defines the main XPaths for fields you want to parse
        "parsers": {
            # Title often appears in a <p class="o-singleLot__description"><b>..text..</b>
            # This sample XPath tries to grab the <b> inside the first description paragraph
            "title": "(//p[@class='o-singleLot__description']/b)[1]/text()",

            # Hammer price example: <span class="currentBid">Hammer Price:</span> <span>Unsold</span>
            # So we look for the <span> after "Hammer Price:" 
            "current_bid": "string(.//div[@class='o-singleLot__priceList bold']//span[contains(text(), 'Hammer Price:')]/following-sibling::span)",

            # Or you might find the same info below in the lot status:
            # <span class="currentBid">Hammer Price:</span><span>Unsold</span>
            # => "string(.//div[@class='o-singleLot__status']//span[contains(text(), 'Hammer Price:')]/following-sibling::span)"

            # Description example: everything in <p class="o-singleLot__description">
            # Sometimes you want all text nodes. We'll just grab the text() from the first such p
            "description": "string((//p[@class='o-singleLot__description'])[1])",

            # Or if you want the "Online bidding closes" date:
            # //span[@class='o-singleLot__hideOnMobile']/strong[1]
            "close_date": "string(.//span[@class='o-singleLot__hideOnMobile']/strong[1])",
        },

        # If you store default or fallback values:
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "No Hammer Price",
            "close_date": "N/A",
        },

        # If your code uses an image_url_xpath or pattern:
        # e.g. <img id="singleLot-image" src="/images/auctions/2/image00001.jpg" alt="Lot 1">
        #"image_url_xpath": "//img[@class='o-singleLot__image']/@src",

        # The site may require a slower crawl or custom logic
        "crawl_delay": 5,
    },

    "cng": {
        "name": "cng",  # Added site name
        "base_url": "https://auctions.cngcoins.com/lots/view/{auction_id}-{lot_id}",
        "folder": "cng_auctions",
        "parsers": {
            "title": "//h1/text()",  # Adjust XPath based on actual HTML
            "description": "//div[contains(@class, 'lot-description')]//text()",
            "current_bid": "//span[contains(@class, 'lot-bid')]/text()",
        },
        "image_url_xpath": "//div[contains(@class, 'lot-image')]//img/@src",
        "default_values": {
            "title": "No Title",
            "description": "No Description",
            "current_bid": "No Current Bid",
            "closing_date": "No Closing Date",  # Default closing date
        },
        "crawl_delay": 4,  # Respect site's crawl delay
    },
}
