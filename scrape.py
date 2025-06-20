import os
from prompt_toolkit import prompt
import requests
from bs4 import BeautifulSoup
import pandas as pd
import keyboard

os.makedirs("data", exist_ok=True)

BASE_URL = "https://dataonline.bmkg.go.id"

# read cookie from cookie.txt
def read_cookie():
    cookie_file = "cookie.txt"
    if not os.path.exists(cookie_file):
        print("Cookie file not found.")
        return None

    with open(cookie_file, "r") as file:
        cookies = {}
        for line in file:
            if line.strip():
                key, value = line.strip().split("=", 1)
                cookies[key] = value
    return cookies


def menu():
    print("""1. Login\n2. Scrape Data\n3. Exit""")
    
def login():
    cookie = prompt("Masukkan cookie: ")
    
    # insert that text to cookie.txt
    with open("cookie.txt", "w") as file:
        file.write(cookie)
        
    prompt("Cookie saved. Press Enter to continue...")
    
def data_extreme_station():
    cookies = read_cookie()
    if not cookies:
        print("No cookies available. Please login first.")
        return
    
    res = requests.get(f"{BASE_URL}/data-ekstrem", headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }, cookies=cookies)

    
    if res.status_code != 200:  
        print("Failed to retrieve data.")
        return
    
    soup = BeautifulSoup(res.text, "html.parser")
    
    csrf_token = soup.find("meta", attrs={"name": "csrf-token"})["content"]
    if not csrf_token:
        print("CSRF token not found.")
        return
    
    from_input = prompt("Masukkan bulan dan tahun awal (MM/YYYY): ")
    to_input = prompt("Masukkan bulan dan tahun akhir (MM/YYYY): ")
    
    form_data = {
        "_token": csrf_token,
        # format MM/YYYY
        "from": from_input,
        "to":  to_input,
    }
    
    res = requests.post(f"{BASE_URL}/proses-data-extrem-station", data=form_data, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Content-Type": "application/x-www-form-urlencoded"
    }, cookies=cookies)
    
    if res.status_code != 200:
        print("Failed to retrieve data.")
        return
    
    # validate if is json
    try:
        data = res.json()
    except ValueError:
        print("Failed to parse JSON response.")        
    
    # save as csv
    df = pd.DataFrame(data['data']['data'])
    
    """
        pada setiap kolom itu bentuknya seperti ini:
        102.6<br/>20 Jul 2023
        
        maka kita perlu memisahkan nilai dan tanggalnya
        menjadi dua kolom terpisah yaitu 'nilai' dan 'tanggal'
        
        contoh:
        kolom rainfall = 102.6
        kolom rainfall_date = 20-07-2023
    """
    
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].str.contains('<br/>').any():
            print(f"Processing column: {col}")
            # split the column by '<br/>', ensuring two columns are always created
            split_result = df[col].str.split('<br/>', expand=True)
            if split_result.shape[1] < 2:
                split_result[1] = None  # Fill missing second column with None
            df[[col, f"{col}_date"]] = split_result
            # remove whitespace and convert to numeric
            df[col] = pd.to_numeric(df[col].str.strip(), errors='coerce')
            # convert date to datetime format
            df[f"{col}_date"] = pd.to_datetime(df[f"{col}_date"].str.strip(), format='%d %b %Y', errors='coerce')
            
    
    df.to_csv("data/data_extreme_station.csv", index=False)
    prompt("Data saved to data/data_extreme_station.csv. Press Enter to continue...")

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    menu()
    print("Tekan tombol angka untuk memilih opsi (1, 2, 3):")

    keyboard.add_hotkey("1", login)
    keyboard.add_hotkey("2", data_extreme_station)
    keyboard.add_hotkey("3", lambda: print("Exiting...") or exit())

    print("Tekan 'q' untuk keluar.")
    keyboard.wait("q")  # Tunggu hingga tombol 'q' ditekan untuk keluar
            
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
