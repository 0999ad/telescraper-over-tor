
#!/usr/bin/env python3
"""
TeleScrape Version 6.2.7

Usage:
  python TeleScrape.py
"""

import os
import time
import requests
import logging
import zipfile
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file, flash
from threading import Thread, Lock
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import boto3
import concurrent.futures
import logging
from logging.handlers import RotatingFileHandler

# Set up logging
log_file_path = "/tmp/telescraper.log"

file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=2)  # 5MB per log file, 2 backups
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(message)s'))

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

# Now, when you log using `logging.info()`, it will output to both console and the file
logging.info("Logging setup complete. Writing to both console and /tmp/telescraper.log.")


app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

# Load environment variables from .env file
load_dotenv()

# AWS S3 Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

DOWNLOADS_DIR = "/tmp/scraper-downloads/"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Set up AWS S3 client if credentials are available
s3_client = None
if S3_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    s3_client = boto3.client('s3',
                             aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
else:
    logging.warning("S3 credentials not found. Skipping S3 upload functionality.")

# Global variables
links_info = {'count': 0, 'filename': ''}
results = []
keywords_searched = []
lock = Lock()
tor_status = {'connected': False, 'ip_address': 'N/A'}
results_filename = ""


def setup_chrome_with_tor():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"  # Use Chromium
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--proxy-server=socks5://localhost:9050")
    chromedriver_path = "/usr/local/bin/chromedriver"  # Path to Chromium ChromeDriver
    chrome_service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    return driver


def verify_tor_connection():
    session = requests.session()
    session.proxies = {'http': 'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'}
    try:
        ip_check_url = 'http://httpbin.org/ip'
        response = session.get(ip_check_url)
        tor_status['ip_address'] = response.json()["origin"]
        tor_status['connected'] = True
        logging.info(f"Connected to TOR. TOR IP Address: {tor_status['ip_address']}")
    except requests.RequestException as e:
        logging.error(f"Tor connection failed: {e}")
        tor_status['connected'] = False


def restart_tor_service():
    try:
        os.system('sudo systemctl restart tor')
        logging.info("TOR service restarted.")
        # Verify that the connection has been re-established
        verify_tor_connection()
    except Exception as e:
        logging.error(f"Failed to restart TOR: {e}")



def get_current_datetime_formatted():
    return time.strftime("%Y-%m-%d-%H%M%S")


def read_keywords_from_file(file_path):
    global keywords_searched
    try:
        logging.info(f"Reading keywords from: {file_path}")
        with open(file_path, 'r') as file:
            keywords_searched = [line.strip() for line in file if line.strip()]
        logging.info(f"Keywords found: {keywords_searched}")
    except FileNotFoundError:
        logging.error(f"Keyword file '{file_path}' not found.")
    return keywords_searched


def create_links_file():
    global links_info
    github_urls = [
        "<CHANNEL LINKS HERE>",
    ]
    all_filtered_links = []
    driver = setup_chrome_with_tor()
    try:
        for github_url in github_urls:
            logging.info(f"Fetching links from {github_url}...")
            driver.get(github_url)
            time.sleep(5)

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            links = soup.find_all("a", href=True)
            filtered_links = [link["href"] for link in links if "https://t.me/" in link["href"]]
            all_filtered_links.extend(filtered_links)
    except Exception as e:
        logging.error(f"Error fetching links from {github_url}: {e}")
    finally:
        driver.quit()

    current_datetime = get_current_datetime_formatted()
    links_filename = f"{current_datetime}-links.txt"
    links_info['count'] = len(all_filtered_links)
    links_info['filename'] = links_filename

    full_path = os.path.join(DOWNLOADS_DIR, links_filename)
    with open(full_path, "w") as file:
        for link in all_filtered_links:
            file.write(f"{link}\n")
    logging.info(f"Found {len(all_filtered_links)} links in total and saved them to '{full_path}'")
    return all_filtered_links


def create_results_file():
    global results_filename
    current_datetime = get_current_datetime_formatted()
    results_filename = f"{current_datetime}-results.txt"

    full_path = os.path.join(DOWNLOADS_DIR, results_filename)
    with open(full_path, "w") as file:
        pass
    logging.info(f"Results file initialized: {full_path}")


def upload_to_s3(file_path):
    if s3_client:
        try:
            s3_client.upload_file(file_path, S3_BUCKET_NAME, os.path.basename(file_path))
            logging.info(f"Uploaded {file_path} to S3 bucket {S3_BUCKET_NAME}.")
        except Exception as e:
            logging.error(f"Failed to upload {file_path} to S3: {e}")
    else:
        logging.info(f"Skipping S3 upload for {file_path} as S3 credentials are not available.")


def scrape_channel(channel_url, keywords, retries=3):
    # Check if TOR is still connected before scraping
    if not tor_status['connected']:
        logging.warning("TOR disconnected. Attempting to restart TOR service.")
        restart_tor_service()

    driver = setup_chrome_with_tor()
    try:
        # Ensure that the /s/ path is appended to the Telegram channel URLs
        if not channel_url.startswith("https://t.me/s/"):
            channel_url = channel_url.replace("https://t.me/", "https://t.me/s/")

        driver.get(channel_url)
        WebDriverWait(driver, 240).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "tgme_widget_message_text"))
        )

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        text_elements = soup.find_all(class_="tgme_widget_message_text")
        for element in text_elements:
            text = element.get_text()
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    start_index = max(text.lower().find(keyword.lower()) - 200, 0)
                    end_index = min(start_index + 200 + len(keyword), len(text))
                    context = text[start_index:end_index]
                    match_message = f"Match found in {channel_url}: ...{context}..."
                    with lock:
                        results.append(match_message)
                        results_file_path = os.path.join(DOWNLOADS_DIR, results_filename)
                        with open(results_file_path, 'a') as file:
                            file.write(f"{match_message}\n*****\n\n")
                    logging.info(match_message)
                    break
    except TimeoutException:
        logging.warning(f"Timed out waiting for page to load: {channel_url}")
        if retries > 0:
            logging.info(f"Retrying... {retries} attempts left.")
            scrape_channel(channel_url, keywords, retries - 1)
        else:
            logging.error(f"Failed to load {channel_url} after multiple attempts.")
    except Exception as e:
        logging.error(f"Error scraping {channel_url}: {e}")
        if retries > 0:
            logging.info(f"Retrying... {retries} attempts left.")
            scrape_channel(channel_url, keywords, retries - 1)
    finally:
        driver.quit()




@app.route('/restart-scrape', methods=['POST'])
def restart_scrape():
    # Ensure the latest keywords are loaded before starting the scrape
    load_keywords()
    # Start a new thread for scraping to not block the main thread
    Thread(target=start_scraping).start()
    # Redirect back to the dashboard
    return redirect(url_for('dashboard'))


@app.route('/update-keywords', methods=['POST'])
def update_keywords():
    new_keywords = request.form['new_keywords']
    new_keyword_list = new_keywords.split(',')
    global keywords_searched
    keywords_searched = new_keyword_list
    with open('keywords.txt', 'w') as file:
        for keyword in new_keyword_list:
            file.write(f"{keyword}\n")
    logging.info("Keywords updated.")
    return redirect(url_for('dashboard'))


def load_keywords():
    keywords_file = 'keywords.txt'
    logging.info(f"Loading keywords from: {keywords_file}")
    read_keywords_from_file(keywords_file)
    logging.info(f"Keywords in use: {keywords_searched}")


def clear_downloads_dir():
    try:
        # List all files in the directory
        for file_name in os.listdir(DOWNLOADS_DIR):
            file_path = os.path.join(DOWNLOADS_DIR, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logging.info(f"Deleted old file: {file_path}")
    except Exception as e:
        logging.error(f"Error while clearing downloads directory: {e}")


def start_scraping():
    global results, links_info, results_filename
    with lock:
        results.clear()  # Clear previous results
        links_info = {'count': 0, 'filename': ''}  # Reset links info

    logging.info("Clearing old links and results files...")
    clear_downloads_dir()  # Clear old files before starting new scrape

    logging.info("Starting new scrape with current keywords.")
    keywords = keywords_searched
    links = create_links_file()  # Create new links file
    create_results_file()  # Create a new results file

    # Start scraping channels
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scrape_channel, link, keywords) for link in links]
        concurrent.futures.wait(futures)

    # Upload results file to S3 (if enabled)
    results_file_path = os.path.join(DOWNLOADS_DIR, results_filename)
    upload_to_s3(results_file_path)


@app.route('/download/<filename>')
def download_file(filename):
    """Download a file from the scraper-downloads directory."""
    try:
        return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        flash(f"File {filename} not found.")
        return redirect(url_for('dashboard'))


@app.route('/download_matched_files')
def download_matched_files():
    """Create a zip file of all matched files and allow download."""
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for file_name in os.listdir(DOWNLOADS_DIR):
            file_path = os.path.join(DOWNLOADS_DIR, file_name)
            zf.write(file_path, file_name)

    memory_file.seek(0)

    return send_file(memory_file, attachment_filename='matched_files.zip', as_attachment=True)


@app.route('/')
def dashboard():
    keywords_str = ' | '.join(keywords_searched)
    with lock:
        local_results = list(results)
    files = os.listdir(DOWNLOADS_DIR)
    return render_template('dashboard.html',
                           results=local_results,
                           links_info=links_info,
                           keywords=keywords_str,
                           tor_connected=tor_status['connected'],
                           tor_ip=tor_status['ip_address'],
                           results_filename=results_filename,
                           warning_message="Warning: The information displayed is live and could contain offensive or malicious language.",
                           files=files)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['Cache-Control'] = 'no-store'
    return response


def run_flask_app():
    app.run(debug=True, host='0.0.0.0', port=8081, use_reloader=False)


def main():
    logging.info("Current working directory: " + os.getcwd())
    load_keywords()

    start_time = time.time()
    verify_tor_connection()
    if not keywords_searched:
        logging.error("No keywords found in the file. Exiting.")
        return

    links = create_links_file()
    if not links:
        logging.error("No links were found. Exiting.")
        return

    create_results_file()
    start_scraping()

    end_time = time.time()
    total_time = end_time - start_time
    logging.info(
        f"Scraping and keyword search completed in {total_time:.2f} seconds. Please visit the dashboard for results.")

    # Keep the script running until manually terminated, allowing Flask dashboard to remain accessible
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Manual interruption received, exiting.")


if __name__ == "__main__":
    flask_thread = Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    main()
