"""
Constants for the WooCommerce Stock Sync application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# B2B Feed Configuration
B2B_FEED_URL = os.getenv("B2B_FEED_URL")

# File paths and directories
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(exist_ok=True)

# Default input file
DEFAULT_WOO_EXPORT = "webtoffee_products_all.csv"

# CSV field names for import
IMPORT_FIELDNAMES = ['sku', 'ean', 'manage_stock', 'stock_status', 'stock']

# Stock status constants
STATUS_IN_STOCK = "instock"
STATUS_OUT_OF_STOCK = "outofstock"

# Default stock management settings
DEFAULT_MANAGE_STOCK = "yes"
DEFAULT_BACKORDERS = "no"