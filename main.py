from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import pyperclip
import time
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ---------------- PARAMETERS ----------------
STATION_ID = "BNKE"
START_DATE = "2021-06-01"
END_DATE = "2024-08-31"
OUTPUT_DIR = f"./results/{STATION_ID}"
os.makedirs(OUTPUT_DIR, exist_ok=True)

columns = ["Time", "Level_10cm", "Level_30cm", "Level_60cm", "Level_100cm"]

series_xpaths = [
    "//*[name()='svg']//*[name()='path' and contains(@class,'highcharts-point highcharts-color-0')]",
    "//*[name()='svg']//*[name()='path' and contains(@class,'highcharts-point highcharts-color-1')]",
    "//*[name()='svg']//*[name()='path' and contains(@class,'highcharts-point highcharts-color-2')]",
    "//*[name()='svg']//*[name()='path' and contains(@class,'highcharts-point highcharts-color-3')]"
]

tooltip_xpaths = [
    "//*[name()='svg']//*[name()='g' and contains(@class,'highcharts-tooltip-header')]//*[name()='text']",
    "//*[name()='svg']//*[name()='g' and contains(@class,'highcharts-tooltip-box highcharts-color-0')]//*[name()='text']",
    "//*[name()='svg']//*[name()='g' and contains(@class,'highcharts-tooltip-box highcharts-color-1')]//*[name()='text']",
    "//*[name()='svg']//*[name()='g' and contains(@class,'highcharts-tooltip-box highcharts-color-2')]//*[name()='text']",
    "//*[name()='svg']//*[name()='g' and contains(@class,'highcharts-tooltip-box highcharts-color-3')]//*[name()='text']"
]

# ---------------- SETUP DRIVER ----------------
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
service = Service("./chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get(f"https://partners.thaiwater.net:3007/soilMoisture/th/chartSoilMoisture/{STATION_ID}/20")

# ---------------- HELPERS ----------------
def safe_find(driver, xpath, retries=3, delay=0.5):
    for _ in range(retries):
        try:
            return driver.find_element(By.XPATH, xpath)
        except StaleElementReferenceException:
            time.sleep(delay)
        except NoSuchElementException:
            return None
    return None

def safe_find_all(driver, xpath):
    try:
        return driver.find_elements(By.XPATH, xpath)
    except:
        return []

def safe_move(driver, elem):
    try:
        ActionChains(driver).move_to_element(elem).perform()
    except:
        pass

def set_date(element, date_value):
    try:
        driver.execute_script("arguments[0].setAttribute('type', 'text');", element)
        pyperclip.copy(date_value)
        element.click()
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.CONTROL + "v")
    except Exception as e:
        print(f"⚠️ Failed to set date {date_value}: {e}")

# ---------------- MAIN FLOW (SAVE DAILY CSV) ----------------
try:
    # Check station
    station_elem = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//table[@class='table table-borderless']/tbody/tr/td[1]"))
    )
    if station_elem.text.strip() != STATION_ID:
        print(f"❌ Station mismatch: {station_elem.text.strip()}")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Date inputs
    start_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "(//input[@name='date'])[1]")))
    end_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "(//input[@name='date'])[2]")))

    # Prepare date range
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d")
    delta = timedelta(days=1)

    # Loop per day
    current_dt = start_dt
    while current_dt <= end_dt:
        date_str = current_dt.strftime("%Y-%m-%d")
        print(f"Processing {date_str}...")

        # Set date
        set_date(end_input, date_str)
        set_date(start_input, date_str)
        time.sleep(1)

        # Wait chart
        try:
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, series_xpaths[0])))
        except TimeoutException:
            print(f"⚠️ Chart not loaded for {date_str}")
            current_dt += delta
            continue

        # Find series with max points
        max_count, max_xpath = 0, None
        for xpath in series_xpaths:
            elems = safe_find_all(driver, xpath)
            if len(elems) > max_count:
                max_count = len(elems)
                max_xpath = xpath

        if max_count == 0 or max_xpath is None:
            print(f"⚠️ No points found for {date_str}")
            current_dt += delta
            continue

        # Hover each point and collect tooltip
        day_data = []
        for i in range(max_count):
            point_elem = safe_find(driver, f"({max_xpath})[{i+1}]")
            if point_elem is None:
                continue
            safe_move(driver, point_elem)

            values = []
            for tip_xpath in tooltip_xpaths:
                tip_elem = safe_find(driver, tip_xpath)
                values.append(tip_elem.text.strip() if tip_elem else "NaN")
            day_data.append(values)

        # ---------------- SAVE DAILY CSV ----------------
        if day_data:
            df_day = pd.DataFrame(day_data, columns=columns)
            df_day = df_day.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            df_day.replace("NaN", np.nan, inplace=True)
            df_day.dropna(how="all", inplace=True)
            csv_path = f"{OUTPUT_DIR}/{STATION_ID}_{date_str}.csv"
            df_day.to_csv(csv_path, index=False)
            print(f"✅ Saved CSV for {date_str}: {csv_path}")
        else:
            print(f"⚠️ No data collected for {date_str}")

        current_dt += delta

finally:
    driver.quit()