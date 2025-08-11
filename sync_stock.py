#!/usr/bin/env python3
"""
WooCommerce Stock Sync V0 - Jednoduchý skript pro synchronizaci skladů
Stáhne XML feed, porovná s WooCommerce exportem, vytvoří CSV pro import změn
"""

import csv
import xml.etree.ElementTree as ET
import requests
from datetime import datetime
from pathlib import Path
import sys

# === KONFIGURACE ===
B2B_FEED_URL = "https://b2bsportswholesale.net/v2/xml/download/format/partner_b2b_full/key/a89c8346b85f143de7acb31923319263/lang/en"
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

# === KROK 1: Stažení B2B feedu ===
def download_feed():
    """Stáhne XML feed z B2B"""
    print("1. Stahuji B2B feed...")
    try:
        response = requests.get(B2B_FEED_URL, timeout=300)
        response.raise_for_status()
        
        # Uložit pro kontrolu
        feed_file = DATA_DIR / f"b2b_feed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        feed_file.write_bytes(response.content)
        print(f"   ✓ Feed stažen: {feed_file.name}")
        
        return response.content
    except Exception as e:
        print(f"   ✗ Chyba při stahování: {e}")
        sys.exit(1)

# === KROK 2: Parsování B2B feedu ===
def parse_b2b_feed(xml_content):
    """Parsuje B2B feed a vrací slovník produktů"""
    print("2. Parsuji B2B feed...")
    products = {}
    
    try:
        root = ET.fromstring(xml_content)
        
        for product in root.findall('.//product'):
            # Parent produkt - SKU
            mpn_elem = product.find('mpn')
            if mpn_elem is not None and mpn_elem.text:
                sku = mpn_elem.text.strip()
                
                # Spočítat celkový sklad ze všech variant
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
                                'stock_status': 'instock' if qty > 0 else 'outofstock'
                            }
                
                # Uložit parent produkt
                products[f"sku_{sku}"] = {
                    'type': 'parent',
                    'sku': sku,
                    'stock': total_stock,
                    'stock_status': 'instock' if total_stock > 0 else 'outofstock'
                }
        
        print(f"   ✓ Načteno {len(products)} produktů/variant")
        return products
        
    except Exception as e:
        print(f"   ✗ Chyba při parsování: {e}")
        sys.exit(1)

# === KROK 3: Načtení WooCommerce exportu ===
def load_woo_export(file_path):
    """Načte export z WooCommerce"""
    print(f"3. Načítám WooCommerce export: {file_path}")
    woo_products = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Parent produkt (má SKU a prázdný post_parent)
                if row.get('sku') and row['sku'].strip() and (not row.get('post_parent') or row['post_parent'] == '' or row['post_parent'] == '0'):
                    key = f"sku_{row['sku'].strip()}"
                    woo_products[key] = {
                        'id': row['ID'],
                        'sku': row['sku'].strip(),
                        'current_stock': int(float(row.get('stock', 0) or 0)),
                        'current_status': row.get('stock_status', 'outofstock'),
                        'type': 'parent'
                    }
                
                # Variation (má EAN a neprázdný post_parent)
                elif row.get('ean') and row['ean'].strip() and row.get('post_parent') and row['post_parent'].strip():
                    # Odstranit .0 z konce EAN pokud tam je
                    ean = row['ean'].strip()
                    if ean.endswith('.0'):
                        ean = ean[:-2]
                    
                    key = f"ean_{ean}"
                    woo_products[key] = {
                        'id': row['ID'],
                        'ean': ean,
                        'current_stock': int(float(row.get('stock', 0) or 0)),
                        'current_status': row.get('stock_status', 'outofstock'),
                        'type': 'variation',
                        'parent_id': row['post_parent']
                    }
        
        print(f"   ✓ Načteno {len(woo_products)} WooCommerce produktů")
        return woo_products
        
    except Exception as e:
        print(f"   ✗ Chyba při načítání WooCommerce exportu: {e}")
        sys.exit(1)

# === KROK 4: Porovnání a detekce změn ===
def detect_changes(b2b_products, woo_products):
    """Porovná data a najde změny"""
    print("4. Porovnávám data a hledám změny...")
    changes = []
    change_log = []
    
    for key, woo_data in woo_products.items():
        if key in b2b_products:
            b2b_data = b2b_products[key]
            
            # Porovnat skladové množství a status
            if (woo_data['current_stock'] != b2b_data['stock'] or 
                woo_data['current_status'] != b2b_data['stock_status']):
                
                change = {
                    'ID': woo_data['id'],
                    'sku': woo_data.get('sku', ''),
                    'ean': woo_data.get('ean', ''),
                    'manage_stock': 'yes',
                    'stock_status': b2b_data['stock_status'],
                    'stock': b2b_data['stock'],  # Používáme 'stock' místo 'stock_quantity'
                    'backorders': 'no'
                }
                changes.append(change)
                
                # Log pro kontrolu
                log_entry = {
                    'id': woo_data['id'],
                    'key': woo_data.get('sku') or woo_data.get('ean'),
                    'old_stock': woo_data['current_stock'],
                    'new_stock': b2b_data['stock'],
                    'old_status': woo_data['current_status'],
                    'new_status': b2b_data['stock_status']
                }
                change_log.append(log_entry)
    
    print(f"   ✓ Nalezeno {len(changes)} změn")
    
    # Uložit log změn
    if change_log:
        log_file = DATA_DIR / f"change_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== LOG ZMĚN ===\n")
            f.write(f"Čas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for entry in change_log:
                f.write(f"ID: {entry['id']}, {entry['key']}: "
                       f"Sklad {entry['old_stock']} → {entry['new_stock']}, "
                       f"Status {entry['old_status']} → {entry['new_status']}\n")
        print(f"   ✓ Log změn uložen: {log_file.name}")
    
    return changes

# === KROK 5: Vytvoření importního CSV ===
def create_import_csv(changes):
    """Vytvoří CSV soubor pro import do WooCommerce"""
    print("5. Vytvářím importní CSV...")
    
    if not changes:
        print("   ℹ Žádné změny k importu")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    import_file = DATA_DIR / f"import_{timestamp}.csv"
    
    with open(import_file, 'w', newline='', encoding='utf-8') as f:
        # Používáme 'stock' místo 'stock_quantity' podle vašeho formátu
        fieldnames = ['ID', 'sku', 'ean', 'manage_stock', 'stock_status', 'stock', 'backorders']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(changes)
    
    print(f"   ✓ Importní soubor vytvořen: {import_file.name}")
    print(f"   ✓ Obsahuje {len(changes)} změn")
    return import_file

# === HLAVNÍ FUNKCE ===
def main():
    print("=== WooCommerce Stock Sync V0 ===")
    print(f"Čas spuštění: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Kontrola WooCommerce exportu
    woo_export_path = input("Zadejte cestu k WooCommerce export CSV: ").strip()
    if not Path(woo_export_path).exists():
        print(f"Soubor {woo_export_path} neexistuje!")
        sys.exit(1)
    
    # Spustit synchronizaci
    xml_content = download_feed()
    b2b_products = parse_b2b_feed(xml_content)
    woo_products = load_woo_export(woo_export_path)
    changes = detect_changes(b2b_products, woo_products)
    import_file = create_import_csv(changes)
    
    print("\n=== HOTOVO ===")
    if import_file:
        print(f"Import soubor: {import_file}")
        print("Nyní můžete importovat tento soubor přes WebToffee Import")
    else:
        print("Skladové stavy jsou aktuální, žádný import není potřeba")

if __name__ == "__main__":
    main()