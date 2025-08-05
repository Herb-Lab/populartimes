#!/usr/bin/env python

from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from openlocationcode import openlocationcode as olc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import json
import time
import re
import os

options = Options()
options.binary_location = r'C:\Users\maomao\Downloads\chrome-win64\chrome.exe'

# gmaps starts their weeks on sunday
days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

def initialise_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.implicitly_wait(5)
    return driver

def pprint_times(times):
    for i, day in enumerate(days):
        print(day, times[i])

def click(driver, elem):
    try:
        elem.click()
    except:
        driver.execute_script("arguments[0].click();", elem)

def extract_place(driver, features, name, link):
    try:
        approx_ll = re.search(r'(?P<lat>-?\d+\.\d+).+?(?P<lng>-?\d+\.\d+)', link).groupdict()
        lat = float(approx_ll["lat"])
        lng = float(approx_ll["lng"])
    except AttributeError:
        print(f"No approx latlong in URL {link} for {name}")
        return

    # Skip Plus Code entirely
    code = None

    driver.implicitly_wait(0.1)

    # Address
    address = None
    try:
        address = driver.find_element(By.CSS_SELECTOR, "button[data-tooltip='Copy address']").get_attribute("aria-label").split(":")[-1].strip()
    except NoSuchElementException:
        pass

    # Category
    category = None
    try:
        category = driver.find_element(By.CSS_SELECTOR, "button[jsaction='pane.rating.category']").text
    except NoSuchElementException:
        pass

    # Popular Times + Live Info
    live_info = None
    times = None
    try:
        popular = driver.find_element(By.CSS_SELECTOR, "div[aria-label^='Popular times']")
        print("Has popular times")
        times = [[0]*24 for _ in range(7)]  # 7 days x 24 hours

        dow = 0
        hour_prev = 0

        for elem in driver.find_elements(By.CSS_SELECTOR, "div[aria-label*='busy']"):
            bits = elem.get_attribute("aria-label").split()

            if bits[0] == "%":
                dow += 1  # Closed day
            elif bits[0] == "Currently":
                print("Has live info, bits:", bits)
                hour = int(bits[-3]) if bits[-3].isdigit() else hour_prev
                live_info = {
                    "frequency": int(bits[1].rstrip("%")),
                    "hour": hour + 1,
                    "day": days[dow % 7]
                }
                times[dow % 7][hour + 1] = int(bits[-2].rstrip("%"))
            else:
                am_pm = bits[-1]
                hour = int(bits[-2])
                if hour == 12:
                    hour = 0
                if am_pm == "PM.":
                    hour += 12
                if hour < hour_prev:
                    dow += 1
                hour_prev = hour
                times[dow % 7][hour] = int(bits[0].rstrip("%"))

    except NoSuchElementException:
        print("No popular times available")
    except StaleElementReferenceException:
        print("StaleElementReferenceException — retrying...")
        time.sleep(0.1)
        return extract_place(driver, features, name, link)
    except ValueError as e:
        print(f"ValueError during popular times parsing: {e}")

    # Build geojson feature
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lng, lat]
        },
        "properties": {
            "name": name,
            "address": address,
            "category": category,
            "link": link,
            "code": code,
            "live_info": live_info,
            "populartimes": times,
            "scraped_at": datetime.now().isoformat(sep=" ", timespec="seconds")
        }
    }

    features[link] = feature
    driver.implicitly_wait(5)

def refreshPlaces(driver):
    places = []
    scrollCount = 0
    while len(places) < 120 and scrollCount < 10:
        scrollCount += 1
        print("scrolling")
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", driver.find_element(By.CSS_SELECTOR, "div[aria-label^='Results']"))
        time.sleep(1)
        places = driver.find_elements(By.CSS_SELECTOR, "div[aria-label^='Results'] a[aria-label]")
    if not places:
        print("No places")
        raise IndexError
    return places

def extract_page(driver, features):
    try:
        places = refreshPlaces(driver)
    except NoSuchElementException:
        # Single result
        name = driver.find_element(By.CSS_SELECTOR, "h1").text
        print(f"Found {name}")
        link = driver.current_url
        if link in features:
            print(f"Skipping {name}")
        else:
            extract_place(driver, features, name, link)
        return 1

    for place in tqdm(places):
        name = place.get_attribute('aria-label')
        link = place.get_attribute("href")
        if name.startswith("Ad ·"):
            # Don't click on Ads
            continue
        if link in features:
            print(f"Skipping {name}")
            continue
        print(f"Clicking on {name}")
        click(driver, place)
        extract_place(driver, features, name, link)
    return len(places)

def load(features, OUTFILE):
    if os.path.isfile(OUTFILE):
        # Load existing data
        with open(OUTFILE) as f:
            data = json.load(f)
            for feature in data["features"]:
                features[feature["properties"]["link"]] = feature
            print(f"Loaded {len(features)} features")

def save(features, OUTFILE):
    if features:
        geojson = {
            "type": "FeatureCollection",
            "features": list(features.values())
        }

        with open(OUTFILE, "w") as f:
            json.dump(geojson, f)
        print(f"Wrote {len(features)} places")
        
if __name__ == "__main__":
    OUTFILE = "output.json"
    place_url = "https://www.google.com/maps/place/New+York+Public+Library+-+Stephen+A.+Schwarzman+Building/@40.7531823,-73.9822534,1162m/data=!3m2!1e3!4b1!4m6!3m5!1s0x89c2590099a8a8a9:0x3b51df6e509a734c!8m2!3d40.7531823!4d-73.9822534!16s%2Fm%2F03gyv_y?entry=ttu&g_ep=EgoyMDI1MDczMC4wIKXMDSoASAFQAw%3D%3D"

    driver = initialise_driver()
    driver.get(place_url)
    features = {}
    extract_place(driver, features, "New York Public Library - Stephen A. Schwarzman Building", place_url)
    save(features, OUTFILE)
    driver.quit()