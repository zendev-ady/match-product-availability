#!/usr/bin/env python3
"""
WooCommerce Stock Sync - Main entry point

This script synchronizes stock information between a B2B supplier and WooCommerce.
It downloads an XML feed, compares it with WooCommerce export data, and creates
a CSV file for importing updated stock information.
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

from constants import DEFAULT_WOO_EXPORT
from core.feed_processor import get_b2b_products
from core.woo_processor import load_woo_export
from core.sync_processor import sync_stock
from utils.logger import logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="WooCommerce Stock Sync")
    parser.add_argument(
        "-f", "--file",
        default=DEFAULT_WOO_EXPORT,
        help=f"Path to WooCommerce export CSV file (default: {DEFAULT_WOO_EXPORT})"
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip downloading B2B feed (use the most recent downloaded file)"
    )
    return parser.parse_args()


def main():
    """Main function."""
    # Print header
    logger.info("=" * 50)
    logger.info("WooCommerce Stock Sync")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    # Parse command line arguments
    args = parse_arguments()
    
    try:
        # Check if WooCommerce export file exists
        woo_export_path = args.file
        if not Path(woo_export_path).exists():
            logger.error(f"File {woo_export_path} not found!")
            sys.exit(1)
        
        # Step 1 & 2: Download and parse B2B feed
        b2b_products = get_b2b_products()
        
        # Step 3: Load WooCommerce export
        woo_products = load_woo_export(woo_export_path)
        
        # Step 4 & 5: Detect changes and create import file
        import_file = sync_stock(b2b_products, woo_products)
        
        # Print summary
        logger.info("=" * 50)
        logger.info("SUMMARY")
        logger.info("=" * 50)
        if import_file:
            logger.info(f"Import file: {import_file}")
            logger.info("You can now import this file using WebToffee Import")
        else:
            logger.info("Stock levels are up to date, no import needed")
        
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()