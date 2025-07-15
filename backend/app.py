from flask import Flask, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from bs4 import BeautifulSoup
import os
import json
import datetime
import time
import glob

app = Flask(__name__)
CORS(app)  # Allow requests from frontend

EDGE_DRIVER_PATH = os.path.join(os.path.dirname(__file__), 'msedgedriver.exe')

def safe_int(text):
    text = text.replace(',', '').strip()
    return int(text) if text.isdigit() else 0

def scrape_mohfw_data_selenium():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Edge(executable_path=EDGE_DRIVER_PATH, options=options)
    url = 'https://covid19dashboard.mohfw.gov.in/'
    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    table = soup.find('table', class_='table')
    data = []
    if not table:
        print("Could not find the data table!")
        return data

    rows = table.find_all('tr')[1:-1]
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 6:
            continue
        state = cols[1].get_text(strip=True).replace('***', '').strip()
        active = safe_int(cols[2].get_text(strip=True))
        recovered = safe_int(cols[3].get_text(strip=True))
        deaths = safe_int(cols[4].get_text(strip=True))
        confirmed = active + recovered + deaths
        data.append({
            'state': state,
            'active': active,
            'recovered': recovered,
            'deaths': deaths,
            'confirmed': confirmed
        })
    return data

def get_data_filename():
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    return os.path.join(os.path.dirname(__file__), f'covid_data_{today_str}.json')

def cleanup_old_data():
    for file in glob.glob(os.path.join(os.path.dirname(__file__), 'covid_data_*.json')):
        os.remove(file)

def get_or_load_covid_data():
    data_file = get_data_filename()
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    else:
        cleanup_old_data()
        data = scrape_mohfw_data_selenium()
        with open(data_file, 'w') as f:
            json.dump(data, f)
        return data

@app.route("/api/covid")
def api_covid():
    data = get_or_load_covid_data()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
