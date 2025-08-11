# WooCommerce Stock Sync

Aplikace pro synchronizaci skladových zásob mezi B2B dodavatelem a WooCommerce e-shopem.

## Popis

Tato aplikace automatizuje proces synchronizace skladových zásob mezi B2B dodavatelem a WooCommerce e-shopem. Stahuje XML feed od dodavatele, porovnává ho s exportem produktů z WooCommerce a vytváří CSV soubor pro import aktualizovaných skladových stavů zpět do WooCommerce.

## Struktura projektu

```
.
├── core/                   # Hlavní logika aplikace
│   ├── __init__.py
│   ├── feed_processor.py   # Zpracování B2B XML feedu
│   ├── woo_processor.py    # Zpracování WooCommerce dat
│   └── sync_processor.py   # Synchronizace dat
├── utils/                  # Pomocné funkce
│   ├── __init__.py
│   ├── file_utils.py       # Funkce pro práci se soubory
│   └── logger.py           # Logging
├── .env                    # Konfigurační proměnné (není v git)
├── .gitignore              # Git ignorované soubory
├── constants.py            # Konstanty aplikace
├── main.py                 # Vstupní bod aplikace
└── README.md               # Dokumentace
```

## Instalace

1. Naklonujte repozitář:
   ```
   git clone <url-repozitáře>
   cd match-product-availability
   ```

2. Vytvořte virtuální prostředí a nainstalujte závislosti:
   ```
   python -m venv venv
   source venv/bin/activate  # Na Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Vytvořte soubor `.env` s konfigurací:
   ```
   B2B_FEED_URL="https://example.com/feed.xml"
   DATA_DIR="./data"
   ```

## Použití

### Základní použití

```
python main.py
```

Aplikace použije výchozí soubor `webtoffee_products_all.csv` jako vstupní data z WooCommerce.

### Pokročilé použití

```
python main.py -f cesta/k/souboru.csv
```

Parametry:
- `-f, --file`: Cesta k CSV souboru s exportem z WooCommerce
- `--no-download`: Přeskočit stahování B2B feedu (použít poslední stažený)

## Výstup

Aplikace vytvoří následující výstupy v adresáři `data/`:

1. Stažený XML feed (`b2b_feed_YYYYMMDD_HHMMSS.xml`)
2. Log změn (`change_log_YYYYMMDD_HHMMSS.txt`)
3. CSV soubor pro import (`import_YYYYMMDD_HHMMSS.csv`)

## Požadavky

- Python 3.6+
- requests
- python-dotenv

## Licence

Tento projekt je licencován pod [MIT licencí](LICENSE).