"""
File utility functions for WooCommerce Stock Sync application.
"""
import csv
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict, List, Optional, Any

from constants import DATA_DIR, IMPORT_FIELDNAMES


def load_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of dictionaries representing rows in the CSV
        
    Raises:
        Exception: If file cannot be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}")
        sys.exit(1)


def save_csv_file(data: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
    """
    Save data to a CSV file.
    
    Args:
        data: List of dictionaries to save
        filename: Optional filename, if None a timestamp will be used
        
    Returns:
        Path to the saved file
        
    Raises:
        Exception: If file cannot be written
    """
    if not data:
        return None
        
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"import_{timestamp}.csv"
        
    file_path = DATA_DIR / filename
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=IMPORT_FIELDNAMES)
            writer.writeheader()
            writer.writerows(data)
        return file_path
    except Exception as e:
        print(f"Error writing CSV file {file_path}: {e}")
        sys.exit(1)


def save_log_file(log_data: List[Dict[str, Any]], prefix: str = "change_log") -> Path:
    """
    Save log data to a text file.
    
    Args:
        log_data: List of log entries
        prefix: Prefix for the log filename
        
    Returns:
        Path to the saved log file
        
    Raises:
        Exception: If file cannot be written
    """
    if not log_data:
        return None
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = DATA_DIR / f"{prefix}_{timestamp}.txt"
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== LOG ZMĚN ===\n")
            f.write(f"Čas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for entry in log_data:
                f.write(f"SKU/EAN: {entry['key']}: "
                       f"Sklad {entry['old_stock']} → {entry['new_stock']}, "
                       f"Status {entry['old_status']} → {entry['new_status']}\n")
                       
        return log_file
    except Exception as e:
        print(f"Error writing log file {log_file}: {e}")
        sys.exit(1)