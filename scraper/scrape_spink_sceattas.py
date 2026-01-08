#!/usr/bin/env python3
"""
scrape_spink_sceattas.py - Targeted scraper for Spink sceatta auctions

This script scrapes the Tony Abramson Collection and other known sceatta sales
from Spink, storing both images and full auction metadata in MySQL.

USAGE:
    python scrape_spink_sceattas.py --auction 21060 --start 1 --end 1000
    python scrape_spink_sceattas.py --auction 21000 --start 1 --end 500
    python scrape_spink_sceattas.py --dry-run  # Test without saving

KNOWN SCEATTA AUCTIONS AT SPINK:
    21060 - Tony Abramson Collection Part III (Collector's Selection)
    21000 - Tony Abramson Collection Part I
    16019 - Lord Stewartby Collection (Anglo-Saxon and Norman)
    9031  - Ancient, English and Foreign Coins
"""

import os
import sys
import time
import random
import hashlib
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import re

# Optional MySQL support
try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False
    print("⚠️  mysql.connector not installed - will save to JSON instead")

import json


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    # Spink URL patterns
    BASE_URL = "https://www.spink.com/lot/{auction_id}{lot_number:06d}"
    IMAGE_CDN = "https://d3ums4016ncdkp.cloudfront.net/auction/main/{auction_id}/{auction_id}_{lot_number}_1.jpg"
    
    # Output directories
    OUTPUT_DIR = Path("trivalaya_data/01_raw/spink")
    
    # Request settings
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    CRAWL_DELAY = (1.5, 3.0)  # Random delay range in seconds
    TIMEOUT = 15
    
    # MySQL (from environment or defaults)
    DB_HOST = os.environ.get("TRIVALAYA_DB_HOST", "localhost")
    DB_USER = os.environ.get("TRIVALAYA_DB_USER", "root")
    DB_PASSWORD = os.environ.get("TRIVALAYA_DB_PASSWORD", "")
    DB_NAME = os.environ.get("TRIVALAYA_DB_NAME", "trivalaya")

    # Keywords that identify sceattas/Anglo-Saxon coins
    SCEATTA_KEYWORDS = [
        "sceatta", "sceat", "anglo-saxon", "northumbria", "styca",
        "primary series", "secondary series", "series a", "series b", 
        "series c", "series d", "series e", "series f", "series g",
        "series h", "series j", "series k", "series l", "series m",
        "series n", "series o", "series p", "series q", "series r",
        "series s", "series t", "series u", "series v", "series w",
        "series x", "woden", "porcupine", "continental", "frisian",
        "merovingian", "thrymsa"
    ]


# =============================================================================
# SCRAPER CLASS
# =============================================================================

class SpinkSceattaScraper:
    def __init__(self, dry_run: bool = False, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update(Config.HEADERS)
        self.db_conn = None
        
        if not dry_run:
            Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            self._init_db()
    
    def _init_db(self):
        """Initialize MySQL connection if available."""
        if not HAS_MYSQL or not Config.DB_PASSWORD:
            print("ℹ️  Running without MySQL - saving to JSON files")
            return
        
        try:
            self.db_conn = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            print(f"✅ Connected to MySQL: {Config.DB_NAME}")
        except Exception as e:
            print(f"⚠️  MySQL connection failed: {e}")
            self.db_conn = None
    
    def _log(self, msg: str):
        """Print if verbose mode enabled."""
        if self.verbose:
            print(msg)
    
    def _delay(self):
        """Polite crawl delay."""
        time.sleep(random.uniform(*Config.CRAWL_DELAY))
    
    def get_lot_url(self, auction_id: int, lot_number: int) -> str:
        """Generate Spink lot URL."""
        return Config.BASE_URL.format(auction_id=auction_id, lot_number=lot_number)
    
    def get_image_url(self, auction_id: int, lot_number: int) -> str:
        """Generate Spink image CDN URL."""
        return Config.IMAGE_CDN.format(auction_id=auction_id, lot_number=lot_number)
    
    def fetch_lot(self, auction_id: int, lot_number: int) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse a single lot page.
        
        Returns dict with:
            - title, description, price_realized, estimate
            - image_url, lot_url
            - is_sceatta (bool)
            - raw_html (for debugging)
        """
        url = self.get_lot_url(auction_id, lot_number)
        
        try:
            response = self.session.get(url, timeout=Config.TIMEOUT)
            
            if response.status_code == 404:
                return None  # Lot doesn't exist
            
            response.raise_for_status()
            
        except requests.RequestException as e:
            self._log(f"  ❌ Request failed: {e}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse lot data
        data = {
            "auction_id": auction_id,
            "lot_number": lot_number,
            "lot_url": url,
            "auction_house": "spink",
            "currency": "GBP",
            "scraped_at": datetime.now().isoformat(),
        }
        
        # Title - usually in bold within description
        title_elem = soup.find('b')
        if title_elem:
            data["title"] = title_elem.get_text(strip=True)
        else:
            # Fallback: first significant text
            for p in soup.find_all(['p', 'div']):
                text = p.get_text(strip=True)
                if len(text) > 20 and 'cookie' not in text.lower():
                    data["title"] = text[:200]
                    break
        
        # Full description
        desc_parts = []
        for elem in soup.find_all(['p', 'div']):
            text = elem.get_text(strip=True)
            if text and len(text) > 10 and 'cookie' not in text.lower():
                desc_parts.append(text)
        data["description"] = " | ".join(desc_parts[:5])
        
        # Price realized
        price_text = response.text
        price_match = re.search(r'Sold for[^\d]*£?([\d,]+)', price_text)
        if price_match:
            data["price_realized"] = price_match.group(1).replace(',', '')
        
        # Starting price / Estimate
        estimate_match = re.search(r'Starting price[^\d]*£?([\d,]+)', price_text)
        if estimate_match:
            data["estimate"] = estimate_match.group(1).replace(',', '')
        
        # Image URL
        img_elem = soup.find('img', src=re.compile(r'cloudfront\.net'))
        if img_elem:
            data["image_url"] = img_elem['src']
        else:
            # Construct from pattern
            data["image_url"] = self.get_image_url(auction_id, lot_number)
        
        # Check if this is a sceatta
        full_text = f"{data.get('title', '')} {data.get('description', '')}".lower()
        data["is_sceatta"] = any(kw in full_text for kw in Config.SCEATTA_KEYWORDS)
        
        # Extract weight if present (important for sceattas)
        weight_match = re.search(r'(\d+\.?\d*)\s*g(?:rams?)?', full_text)
        if weight_match:
            data["weight_g"] = float(weight_match.group(1))
        
        # Extract reference numbers (Spink, North, etc.)
        refs = []
        for pattern in [r'S\.?\s*(\d+)', r'North\s*(\d+)', r'N\.?\s*(\d+)']:
            matches = re.findall(pattern, data.get('description', ''), re.IGNORECASE)
            refs.extend(matches)
        if refs:
            data["references"] = ", ".join(refs[:5])
        
        return data
    
    def download_image(self, image_url: str, save_dir: Path, filename: str) -> Optional[str]:
        """Download image and return local path."""
        if self.dry_run:
            return f"[DRY RUN] Would save to {save_dir / filename}"
        
        try:
            response = self.session.get(image_url, timeout=Config.TIMEOUT)
            response.raise_for_status()
            
            save_path = save_dir / filename
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return str(save_path)
            
        except Exception as e:
            self._log(f"  ⚠️  Image download failed: {e}")
            return None
    
    def save_to_db(self, data: Dict[str, Any], image_path: Optional[str]):
        """Save lot data to MySQL."""
        if not self.db_conn or self.dry_run:
            return
        
        try:
            cursor = self.db_conn.cursor()
            
            query = """
                INSERT INTO auction_data 
                (lot_number, title, description, current_bid, image_url, image_path, 
                 closing_date, auction_house, sale_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                description = VALUES(description),
                current_bid = VALUES(current_bid)
            """
            
            values = (
                data["lot_number"],
                data.get("title", "")[:500],
                data.get("description", "")[:2000],
                data.get("price_realized", data.get("estimate", "0")),
                data.get("image_url", ""),
                image_path or "",
                data.get("scraped_at", ""),
                "spink",
                str(data["auction_id"]),
            )
            
            cursor.execute(query, values)
            self.db_conn.commit()
            cursor.close()
            
        except Exception as e:
            self._log(f"  ⚠️  DB save failed: {e}")
    
    def save_to_json(self, data: Dict[str, Any], save_dir: Path):
        """Save lot data to JSON file."""
        if self.dry_run:
            return
        
        filename = f"spink_{data['auction_id']}_{data['lot_number']:06d}.json"
        save_path = save_dir / filename
        
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def scrape_auction(self, auction_id: int, start_lot: int = 1, end_lot: int = 1000,
                       sceattas_only: bool = False):
        """
        Scrape a range of lots from a Spink auction.
        
        Args:
            auction_id: Spink auction number (e.g., 21060)
            start_lot: First lot number to scrape
            end_lot: Last lot number to scrape
            sceattas_only: If True, only save lots containing sceatta keywords
        """
        print(f"\n{'='*60}")
        print(f"🔍 Scraping Spink Auction {auction_id}")
        print(f"   Lots {start_lot} - {end_lot}")
        print(f"   Sceattas only: {sceattas_only}")
        print(f"   Dry run: {self.dry_run}")
        print(f"{'='*60}\n")
        
        # Create output directory
        save_dir = Config.OUTPUT_DIR / f"spink_{auction_id}"
        if not self.dry_run:
            save_dir.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "total": 0,
            "success": 0,
            "sceattas": 0,
            "failed": 0,
            "not_found": 0,
        }
        
        consecutive_404 = 0
        
        for lot_num in range(start_lot, end_lot + 1):
            stats["total"] += 1
            
            self._log(f"  📄 Lot {lot_num}...", )
            
            # Fetch lot data
            data = self.fetch_lot(auction_id, lot_num)
            
            if data is None:
                stats["not_found"] += 1
                consecutive_404 += 1
                self._log(f" not found")
                
                # Stop if many consecutive 404s (likely end of auction)
                if consecutive_404 > 20:
                    self._log(f"\n⚠️  20 consecutive 404s - stopping")
                    break
                    
                continue
            
            consecutive_404 = 0
            
            # Check sceatta filter
            if sceattas_only and not data.get("is_sceatta", False):
                self._log(f" skipped (not sceatta)")
                continue
            
            # Download image
            image_filename = f"spink_{auction_id}_{lot_num:06d}.jpg"
            image_path = self.download_image(
                data.get("image_url", ""),
                save_dir,
                image_filename
            )
            data["image_path"] = image_path
            
            # Save to DB and JSON
            self.save_to_db(data, image_path)
            self.save_to_json(data, save_dir)
            
            stats["success"] += 1
            if data.get("is_sceatta"):
                stats["sceattas"] += 1
            
            sceatta_flag = "🪙" if data.get("is_sceatta") else ""
            price = data.get("price_realized", "?")
            self._log(f" ✅ {data.get('title', 'Unknown')[:40]}... £{price} {sceatta_flag}")
            
            # Polite delay
            self._delay()
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 SCRAPE COMPLETE")
        print(f"   Total attempted: {stats['total']}")
        print(f"   Successful: {stats['success']}")
        print(f"   Sceattas found: {stats['sceattas']}")
        print(f"   Not found: {stats['not_found']}")
        print(f"   Failed: {stats['failed']}")
        print(f"{'='*60}\n")
        
        return stats


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Scrape Spink auctions for sceatta coins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
KNOWN SCEATTA AUCTIONS:
  21060  Tony Abramson Collection Part III
  21000  Tony Abramson Collection Part I  
  16019  Lord Stewartby Collection
  9031   Ancient, English and Foreign Coins

EXAMPLES:
  python scrape_spink_sceattas.py --auction 21060 --start 800 --end 900
  python scrape_spink_sceattas.py --auction 21000 --sceattas-only
  python scrape_spink_sceattas.py --dry-run --auction 21060 --start 1 --end 10
        """
    )
    
    parser.add_argument("--auction", type=int, required=True,
                        help="Spink auction ID (e.g., 21060)")
    parser.add_argument("--start", type=int, default=1,
                        help="Starting lot number (default: 1)")
    parser.add_argument("--end", type=int, default=1000,
                        help="Ending lot number (default: 1000)")
    parser.add_argument("--sceattas-only", action="store_true",
                        help="Only save lots containing sceatta keywords")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't save anything, just show what would be scraped")
    parser.add_argument("--quiet", action="store_true",
                        help="Minimal output")
    
    args = parser.parse_args()
    
    scraper = SpinkSceattaScraper(
        dry_run=args.dry_run,
        verbose=not args.quiet
    )
    
    scraper.scrape_auction(
        auction_id=args.auction,
        start_lot=args.start,
        end_lot=args.end,
        sceattas_only=args.sceattas_only
    )


if __name__ == "__main__":
    main()