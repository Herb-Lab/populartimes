# populartimes

Python + Selenium scraper to extract Google Maps places and popular times

## Folder Structure

```text
populartimes/
├── LICENSE
├── README.md
├── requirements.txt
├── util.py
├── scraper.py
├── example_urls.csv         # Example input file (CSV with place URLs)
├── example_output.geojson   # Example output file (GeoJSON)
└── .env                     # Enviornment path file for chrome path config
```

## Setup

1. **Install Google Chrome** (or Chromium). If Chrome is not in the default location, create a `.env` file in the project root and add the following line (adjust the path as needed):

 ```properties
 CHROME_PATH="C:\\Path\\To\\chrome.exe"
 ```

2. *(Recommended)* Create and activate a virtual environment:

 ```powershell
 python -m venv .venv
 .venv\Scripts\Activate.ps1
 ```

3. Install dependencies:

 ```powershell
 pip install -r requirements.txt
 ```

## How to Scrape

Prepare a CSV file (see `example_urls.csv`) with at least a `url` column:

```csv
url,name
"https://www.google.com/maps/place/Boston+Logan+International+Airport/...",Boston Logan International Airport
...
```

Run the scraper:

```powershell
python scraper.py --infile example_urls.csv --outfile places.geojson
```

Options:

- `--infile`   Input CSV file with URLs (required)
- `--outfile`  Output GeoJSON file (default: `output.geojson`)
- `--delay`    Seconds to wait between requests (default: 0.5)

The output will be a GeoJSON file with all scraped places and their popular times (see `example_output.geojson`).

---
