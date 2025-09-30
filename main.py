from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pyperclip
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

STATION_ID = "BNKE"
START_DATE = "2021-06-01"
END_DATE = "2024-08-31"

chrome_options = Options()
chrome_options.add_argument("--start-maximized")
service = Service("./chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(f"https://partners.thaiwater.net:3007/soilMoisture/th/chartSoilMoisture/{STATION_ID}/20")

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

try:
    station = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//table[@class='table table-borderless']/tbody/tr/td[1]"))
    )
    station_text = station.text.strip()
    print("Found station:", station_text)
    if station_text == STATION_ID:
        print("✅ Station matches!")
    else:
        print(f"❌ Station mismatch. Expected {STATION_ID}, but got {station_text}")

except TimeoutException:
    print("❌ Timeout: Station element not found within 10s")
except NoSuchElementException:
    print("❌ No such element found in the page")
except Exception as e:
    print("⚠️ Unexpected error:", e)
    
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

start_date = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, "(//input[@name='date'])[1]"))
)
end_date = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, "(//input[@name='date'])[2]"))
)

def set_date_by_paste(element, date_value):
    driver.execute_script("arguments[0].setAttribute('type', 'text');", element)
    pyperclip.copy(date_value)
    element.click()
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.CONTROL + "v")
    
def get_chart_tooltips_helper(driver, series_xpaths, tooltip_xpaths, start_date_input, end_date_input, START_DATE, END_DATE):
    # Set the date range
    time.sleep(1)
    set_date_by_paste(end_date_input, END_DATE)
    set_date_by_paste(start_date_input, START_DATE)
    
    # Wait for chart points to appear
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, series_xpaths[0]))
        )
        print("✅ Chart points loaded!")
    except TimeoutException:
        print("❌ Timeout: Chart points did not load within 10s")
        return []
    
    max_count = -1
    max_xpath = None

    for attempt in range(5):
        for xpath in series_xpaths:
            elements = driver.find_elements(By.XPATH, xpath)
            count = len(elements)
            if count > max_count:
                max_count = count
                max_xpath = xpath

        print(f"Attempt {attempt+1}: XPath with most points: {max_xpath} ({max_count} points)")

        if max_count <= 24:
            break
        else:
            print("⚠️ Detected more than 24 points, retrying...")
            time.sleep(1)
            max_count = -1
            max_xpath = None
    
    values_all_points = []
    elements = driver.find_elements(By.XPATH, max_xpath)  # get all points of the max series
    for point in elements:  # loop directly over them
        ActionChains(driver).move_to_element(point).perform()
        
        values = []
        for tooltip_xpath in tooltip_xpaths:
            try:
                elem = driver.find_element(By.XPATH, tooltip_xpath)
                values.append(elem.text.strip())
            except NoSuchElementException:
                values.append("NaN")
        values_all_points.append(values)
    
    return values_all_points

def get_chart_tooltips(driver, series_xpaths, tooltip_xpaths, start_date_input, end_date_input, start_date_str, end_date_str):
    all_values = []

    # Convert string dates to datetime objects
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    delta = timedelta(days=1)

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"Processing date: {date_str}")
        
        # Call your helper function for this date
        values_by_date = get_chart_tooltips_helper(
            driver,
            series_xpaths,
            tooltip_xpaths,
            start_date_input,
            end_date_input,
            START_DATE=date_str,
            END_DATE=date_str
        )
        all_values.append(values_by_date)
        current_date += delta

    return all_values

all_tooltip_values = get_chart_tooltips(
    driver,
    series_xpaths,
    tooltip_xpaths,
    start_date_input=start_date,
    end_date_input=end_date,
    start_date_str=START_DATE,
    end_date_str=END_DATE
)

flat_values = [row for day in all_tooltip_values for row in day]
df = pd.DataFrame(flat_values, columns=columns)
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df.replace("NaN", np.nan, inplace=True)
df.dropna(how="all", inplace=True)
df.to_csv(f"./results/{STATION_ID}_{START_DATE}_to_{END_DATE}.csv", index=False)

driver.quit()