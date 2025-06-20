import logging
from pathlib import Path
from prompt_toolkit import prompt
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import io

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = "https://dataonline.bmkg.go.id"
DATA_DIR = Path("data")
TEMP_DIR = Path("temp")
COOKIE_FILE = Path("cookie.txt")

DATA_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

"""COOKIE"""
def read_cookie():
    if not COOKIE_FILE.exists():
        logging.error("Cookie file not found.")
        return None

    cookies = {}
    with COOKIE_FILE.open("r") as file:
        for line in file:
            if line.strip():
                key, value = line.strip().split("=", 1)
                cookies[key] = value
    return cookies

def save_cookie(cookie):
    with COOKIE_FILE.open("w") as file:
        file.write(cookie)
    logging.info("Cookie saved successfully.")

"""Validation Functions"""
def validate_date_input(date_input):
    if not date_input or len(date_input) != 7 or date_input[2] != '-':
        return False
    return True

"""Functions"""
def menu():
    print("""1. Login\n2. Scrape Data\n3. Exit""")

def login():
    cookie = prompt("Masukkan cookie: ")
    save_cookie(cookie)
    prompt("Cookie saved. Press Enter to continue...")

def scrape_data_extreme_station():
    cookies = read_cookie()
    if not cookies:
        logging.error("No cookies available. Please login first.")
        return

    res = requests.get(f"{BASE_URL}/data-ekstrem", headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }, cookies=cookies)

    if res.status_code != 200:
        logging.error("Failed to retrieve data.")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    csrf_token = soup.find("meta", attrs={"name": "csrf-token"})["content"]
    if not csrf_token:
        logging.error("CSRF token not found.")
        return

    from_input = prompt("Masukkan bulan dan tahun awal (MM-YYYY): ")
    to_input = prompt("Masukkan bulan dan tahun akhir (MM-YYYY): ")

    if not validate_date_input(from_input) or not validate_date_input(to_input):
        logging.error("Invalid date format. Use MM-YYYY.")
        return
    if from_input > to_input:
        logging.error("Start date cannot be greater than end date.")
        return

    range_months = pd.date_range(start=from_input, end=to_input, freq='MS').strftime("%m-%Y").tolist()

    for month in range_months:
        logging.info(f"Processing data for month: {month}")
        form_data = {
            "_token": csrf_token,
            "from": month,
            "to": month,
        }

        res = requests.post(f"{BASE_URL}/proses-data-extrem-station", data=form_data, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Content-Type": "application/x-www-form-urlencoded"
        }, cookies=cookies)

        if res.status_code != 200:
            logging.error(f"Failed to retrieve data for month: {month}")
            continue

        try:
            data = res.json()
        except ValueError:
            logging.error(f"Failed to parse JSON response for month: {month}")
            continue

        temp_file = TEMP_DIR / f"temp_{month}.json"
        temp_file.write_text(json.dumps(data['data']['data'], indent=4))
        logging.info(f"Data for {month} saved to {temp_file}")

    logging.info("Combining data...")
    json_files = [f for f in TEMP_DIR.iterdir() if f.name.startswith("temp_") and f.suffix == ".json"]
    dataframes = []

    for json_file in json_files:
        data = json_file.read_text()
        df = pd.read_json(io.StringIO(data), orient='records')
        dataframes.append(df)
        
        json_file.unlink()

    combined_df = pd.concat(dataframes, ignore_index=True)
    logging.info("Data successfully combined.")

    logging.info("Processing data...")
    for col in combined_df.columns:
        if combined_df[col].dtype == 'object' and combined_df[col].str.contains('<br/>').any():
            split_result = combined_df[col].str.split('<br/>', expand=True)
            combined_df[[col, f"{col}_date"]] = split_result
            combined_df[col] = pd.to_numeric(combined_df[col].str.strip(), errors='coerce')
            combined_df[f"{col}_date"] = pd.to_datetime(combined_df[f"{col}_date"].str.strip(), format='%d %b %Y', errors='coerce')

    output_file = DATA_DIR / f"extreme_data_{from_input}_to_{to_input}.csv"
    combined_df.to_csv(output_file, index=False)
    logging.info(f"Data saved to {output_file}")
    prompt("Data saved. Press Enter to continue...")

"""Main"""
def main():
    while True:
        menu()
        choice = prompt("Pilih menu: ")

        if choice == "1":
            login()
        elif choice == "2":
            scrape_data_extreme_station()
        elif choice == "3":
            logging.info("Exiting...")
            break
        else:
            logging.warning("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Exiting...")