"""
Stock synchronization module for WooCommerce Stock Sync application.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from constants import DEFAULT_MANAGE_STOCK, DEFAULT_BACKORDERS
from utils.file_utils import save_csv_file, save_log_file
from utils.logger import logger


def detect_changes(b2b_products: Dict[str, Dict[str, Any]],
                  woo_products: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Compare B2B and WooCommerce data to detect stock changes.
    
    Args:
        b2b_products: Dictionary of B2B products with stock information
        woo_products: Dictionary of WooCommerce products with current stock information
        
    Returns:
        Tuple containing:
            - List of changes for import
            - List of change log entries
    """
    logger.info("Comparing data and detecting changes...")
    changes = []
    change_log = []
    
    # Get all SKUs from WooCommerce export
    all_skus = woo_products.get('_all_skus', [])
    
    # Create a dictionary to track which SKUs have been processed
    processed_skus = {sku: False for sku in all_skus}
    
    # Process products with changes
    for key, woo_data in woo_products.items():
        # Skip the _all_skus special key
        if key == '_all_skus':
            continue
            
        if key in b2b_products:
            b2b_data = b2b_products[key]
            sku = woo_data.get('sku', '')
            
            # Mark this SKU as processed
            if sku:
                processed_skus[sku] = True
            
            # Compare stock quantity and status
            if (woo_data['current_stock'] != b2b_data['stock'] or
                woo_data['current_status'] != b2b_data['stock_status']):
                
                change = {
                    'sku': sku,
                    'ean': woo_data.get('ean', ''),
                    'manage_stock': DEFAULT_MANAGE_STOCK,
                    'stock_status': b2b_data['stock_status'],
                    'stock': b2b_data['stock']
                }
                changes.append(change)
                
                # Log entry for verification
                log_entry = {
                    'key': sku or woo_data.get('ean'),
                    'old_stock': woo_data['current_stock'],
                    'new_stock': b2b_data['stock'],
                    'old_status': woo_data['current_status'],
                    'new_status': b2b_data['stock_status']
                }
                change_log.append(log_entry)
    
    # Add all unprocessed SKUs to the changes list with their current values
    for sku, processed in processed_skus.items():
        if not processed:
            # Find this SKU in woo_products
            for key, woo_data in woo_products.items():
                if key != '_all_skus' and woo_data.get('sku') == sku:
                    change = {
                        'sku': sku,
                        'ean': woo_data.get('ean', ''),
                        'manage_stock': DEFAULT_MANAGE_STOCK,
                        'stock_status': woo_data.get('current_status', 'outofstock'),
                        'stock': woo_data.get('current_stock', 0)
                    }
                    changes.append(change)
                    break
    
    logger.info(f"Found {len(changes)} changes")
    return changes, change_log


def create_import_file(changes: List[Dict[str, Any]], 
                      log_data: List[Dict[str, Any]]) -> Optional[str]:
    """
    Create import CSV file and log file for detected changes.
    
    Args:
        changes: List of changes for import
        log_data: List of change log entries
        
    Returns:
        Path to the import file if changes were found, None otherwise
    """
    if not changes:
        logger.info("No changes to import")
        return None
    
    # Save import CSV
    import_file = save_csv_file(changes)
    if import_file:
        logger.info(f"Import file created: {import_file.name}")
        logger.info(f"Contains {len(changes)} changes")
    
    # Save log file
    if log_data:
        log_file = save_log_file(log_data)
        if log_file:
            logger.info(f"Change log saved: {log_file.name}")
    
    return import_file


def sync_stock(b2b_products: Dict[str, Dict[str, Any]],
              woo_products: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """
    Synchronize stock between B2B and WooCommerce.
    
    Args:
        b2b_products: Dictionary of B2B products with stock information
        woo_products: Dictionary of WooCommerce products with current stock information
        
    Returns:
        Path to the import file if changes were found, None otherwise
    """
    # Detect changes
    changes, log_data = detect_changes(b2b_products, woo_products)
    
    # Log the number of SKUs being processed
    all_skus = woo_products.get('_all_skus', [])
    logger.info(f"Processing {len(all_skus)} total SKUs")
    logger.info(f"Found {len(changes)} products with changes or to be maintained")
    
    # Create import file
    import_file = create_import_file(changes, log_data)
    
    return import_file