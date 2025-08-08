#!/usr/bin/env python
# Standalone runner for scraping multiple *place* URLs using util.py

import argparse
import csv
import sys
import time

from selenium.webdriver.common.by import By

from util import (
    initialise_driver,
    extract_place,
    save,
)

def load_urls_from_csv(path):
    urls = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # Expect a column named "url"; allow optional "name"
        for row in reader:
            if not row:
                continue
            url = (row.get("url") or "").strip().strip('"').strip("'")
            if not url:
                continue
            name = (row.get("name") or "").strip()
            urls.append((url, name if name else None))
    # dedupe while preserving order
    seen = set()
    deduped = []
    for url, name in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append((url, name))
    return deduped

def main():
    parser = argparse.ArgumentParser(
        description="Scrape Google Maps Popular Times for a list of place URLs."
    )
    parser.add_argument("--infile", required=True, help="CSV with a 'url' column (optional 'name' column).")
    parser.add_argument("--outfile", default="output.geojson", help="Path to output GeoJSON")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds to sleep between places")
    args = parser.parse_args()

    places = load_urls_from_csv(args.infile)
    if not places:
        print("No URLs found in CSV. Ensure there is a header named 'url'.", file=sys.stderr)
        sys.exit(2)

    features = {}
    driver = None
    failures = 0

    try:
        driver = initialise_driver()
        for idx, (url, name) in enumerate(places, start=1):
            try:
                driver.get(url)

                # If no name provided, try to grab <h1>; if that fails, use a placeholder
                if not name:
                    try:
                        name = driver.find_element(By.CSS_SELECTOR, "h1").text
                    except Exception:
                        name = f"Place {idx}"

                extract_place(driver, features, name, url)
                print(f"[{idx}/{len(places)}] scraped: {name}")
                time.sleep(args.delay)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                failures += 1
                print(f"[{idx}/{len(places)}] ERROR on {url}: {e}", file=sys.stderr)
                # continue to next url

        save(features, args.outfile)
        print(f"Done. Wrote {len(features)} places to {args.outfile}. Failures: {failures}")

    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
