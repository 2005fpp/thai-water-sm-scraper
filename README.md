# 🌱 ThaiWater Soil Moisture Scraper

This project scrapes soil moisture data from [ThaiWater Partners](https://partners.thaiwater.net:3007) for a specific station and date range. The data is saved as a CSV file. 📊

---

## ⚙️ Requirements

Python 3.11+ is recommended.

Install required packages using:

```bash
pip install -r requirements.txt
````

Ensure you have **Chrome browser** installed and the corresponding **ChromeDriver** in `./chromedriver-win64/`. The version of ChromeDriver should match your Chrome browser version. 🖥️

---

## ▶️ How to Run

1. Open `main.py` and configure the following variables:

```python
STATION_ID = "BNKE"          # Replace with the station ID you want to scrape
START_DATE = "2024-07-01"    # Start date in YYYY-MM-DD format
END_DATE = "2024-07-03"      # End date in YYYY-MM-DD format
```

2. Run the script:

```bash
python main.py
```

3. After completion, the script will save a CSV file in the project folder: 💾

```
BNKE_2024-07-01_to_2024-07-03.csv
```

---

## 🔍 How It Works

* Opens the ThaiWater website for the specified station. 🌐
* Sets the start and end dates in the date picker. 📅
* Extracts data from the Highcharts chart using Selenium. 🤖
* Saves the data to a CSV file. 📄

---

## ⚠️ Notes

* Ensure ChromeDriver is compatible with your Chrome browser version. ✅
* If scraping fails or the page layout changes, XPath selectors may need to be updated. 🔧
* The maximum number of data points per series is 24. The script automatically adjusts if more points appear. 📈