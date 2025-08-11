"""
B2B Feed processing module for WooCommerce Stock Sync application.
"""
import xml.etree.ElementTree as ET
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from constants import B2B_FEED_URL, DATA_DIR, STATUS_IN_STOCK, STATUS_OUT_OF_STOCK
from utils.logger import logger


def download_feed(url: Optional[str] = None) -> bytes:
    """
    Download XML feed from B2B supplier.
    
    Args:
        url: URL to download from, defaults to B2B_FEED_URL from constants
        
    Returns:
        Raw XML content as bytes
        
    Raises:
        Exception: If download fails
    """
    feed_url = url or B2B_FEED_URL
    if not feed_url:
        raise ValueError("B2B feed URL is not configured. Check your .env file.")
    
    logger.info("Downloading B2B feed...")
    try:
        response = requests.get(feed_url, timeout=300)
        response.raise_for_status()
        
        # Save for reference
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        feed_file = DATA_DIR / f"b2b_feed_{timestamp}.xml"
        feed_file.write_bytes(response.content)
        logger.info(f"Feed downloaded: {feed_file.name}")
        
        return response.content
    except Exception as e:
        logger.error(f"Error downloading feed: {e}")
        raise


def parse_b2b_feed(xml_content: bytes) -> Dict[str, Dict[str, Any]]:
    """
    Parse B2B feed XML and extract product data.
    
    Args:
        xml_content: Raw XML content
        
    Returns:
        Dictionary of products with stock information
        
    Raises:
        Exception: If parsing fails
    """
    logger.info("Parsing B2B feed...")
    products = {}
    
    try:
        root = ET.fromstring(xml_content)
        
        for product in root.findall('.//product'):
            # Parent product - SKU
            mpn_elem = product.find('mpn')
            if mpn_elem is not None and mpn_elem.text:
                sku = mpn_elem.text.strip()
                
                # Calculate total stock from all variants
                total_stock = 0
                stock_elem = product.find('stock')
                
                if stock_elem is not None:
                    for item in stock_elem.findall('item'):
                        qty = int(item.get('quantity', 0))
                        total_stock += qty
                        
                        # Variation - EAN
                        ean = item.get('ean', '').strip()
                        if ean:
                            products[f"ean_{ean}"] = {
                                'type': 'variation',
                                'ean': ean,
                                'stock': qty,
                                'stock_status': STATUS_IN_STOCK if qty > 0 else STATUS_OUT_OF_STOCK
                            }
                
                # Save parent product
                products[f"sku_{sku}"] = {
                    'type': 'parent',
                    'sku': sku,
                    'stock': total_stock,
                    'stock_status': STATUS_IN_STOCK if total_stock > 0 else STATUS_OUT_OF_STOCK
                }
        
        logger.info(f"Parsed {len(products)} products/variants")
        return products
        
    except Exception as e:
        logger.error(f"Error parsing feed: {e}")
        raise


def get_b2b_products(url: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Download and parse B2B feed in one step.
    
    Args:
        url: Optional URL to download from
        
    Returns:
        Dictionary of products with stock information
    """
    xml_content = download_feed(url)
    return parse_b2b_feed(xml_content)