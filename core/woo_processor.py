"""
WooCommerce data processing module for WooCommerce Stock Sync application.
"""
from pathlib import Path
from typing import Dict, Any, List

from constants import DEFAULT_WOO_EXPORT
from utils.file_utils import load_csv_file
from utils.logger import logger


def load_woo_export(file_path: str = DEFAULT_WOO_EXPORT) -> Dict[str, Dict[str, Any]]:
    """
    Load and process WooCommerce export data.
    
    Args:
        file_path: Path to the WooCommerce export CSV file
        
    Returns:
        Dictionary of products with current stock information
        
    Raises:
        Exception: If file cannot be read or processed
    """
    logger.info(f"Loading WooCommerce export: {file_path}")
    woo_products = {}
    all_skus = set()  # Track all SKUs to ensure we maintain them all
    
    try:
        # Check if file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File {file_path} not found")
            
        # Load CSV data
        rows = load_csv_file(file_path)
        
        for row in rows:
            # Track all SKUs
            if row.get('sku') and row['sku'].strip():
                all_skus.add(row['sku'].strip())
                
            # Parent product (has SKU and empty post_parent)
            if row.get('sku') and row['sku'].strip() and (not row.get('post_parent') or row['post_parent'] == '' or row['post_parent'] == '0'):
                key = f"sku_{row['sku'].strip()}"
                woo_products[key] = {
                    'sku': row['sku'].strip(),
                    'current_stock': int(float(row.get('stock', 0) or 0)),
                    'current_status': row.get('stock_status', 'outofstock'),
                    'type': 'parent'
                }
            
            # Variation (has EAN and non-empty post_parent)
            elif row.get('ean') and row['ean'].strip() and row.get('post_parent') and row['post_parent'].strip():
                # Remove .0 from the end of EAN if present
                ean = row['ean'].strip()
                if ean.endswith('.0'):
                    ean = ean[:-2]
                
                key = f"ean_{ean}"
                woo_products[key] = {
                    'sku': row.get('sku', '').strip(),
                    'ean': ean,
                    'current_stock': int(float(row.get('stock', 0) or 0)),
                    'current_status': row.get('stock_status', 'outofstock'),
                    'type': 'variation',
                    'parent_id': row['post_parent']
                }
        
        logger.info(f"Loaded {len(woo_products)} WooCommerce products")
        logger.info(f"Found {len(all_skus)} unique SKUs")
        
        # Store all SKUs for reference
        woo_products['_all_skus'] = list(all_skus)
        
        return woo_products
        
    except Exception as e:
        logger.error(f"Error loading WooCommerce export: {e}")
        raise


def prepare_import_data(changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepare data for import into WooCommerce.
    
    Args:
        changes: List of product changes
        
    Returns:
        List of dictionaries formatted for WooCommerce import
    """
    import_data = []
    
    for change in changes:
        import_data.append({
            'sku': change.get('sku', ''),
            'ean': change.get('ean', ''),
            'manage_stock': change.get('manage_stock', 'yes'),
            'stock_status': change['stock_status'],
            'stock': change['stock']
        })
    
    return import_data