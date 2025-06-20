# BMKG Cuaca Scraper

A simple web scraper to fetch weather data from the BMKG website.

## Requirements
- Python 3.x
- Packages listed in `requirements.txt`

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python3 scrape.py
```

## How to Get Cookies
1. Open your web browser and go to the BMKG website.
2. Log in to your account.
3. Open the developer tools (usually F12).
4. Go to console and type `document.cookie`.
5. Copy the cookies and paste them into the `cookies.txt` file in the same directory as `scrape.py`.