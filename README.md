# TeleScrape 6.2.7
**Enhanced Telegram Channel Scraper using TOR and a Flask Dashboard for results**

## Legal Disclaimer
This software is designed solely for **educational and research purposes** and should be used with ethical considerations in mind. Users are responsible for ensuring their activities comply with local laws and regulations. The authors of this software bear no responsibility for any misuse or potential damages arising from its use. It's imperative to adhere to the terms of service of any platforms interacted with through this tool.

## Overview

TeleScrape is an advanced tool for extracting content from Telegram channels, emphasizing user privacy through Tor integration and providing real-time insights via a dynamic Flask dashboard. It eschews the need for Telegram's API by utilizing Selenium for web scraping, offering a robust solution for data gathering from public Telegram channels.

## Key Features

- **Enhanced Privacy**: Routes all scraping through the Tor network to protect user anonymity.
- **Keyword-Driven Scraping**: Fetches channel content based on user-defined keywords, focusing on relevant data extraction.
- **Interactive Web Dashboard**: Utilizes Flask to present scraping results dynamically, with real-time updates and insights.
- **Efficient Parallel Processing**: Employs concurrent scraping to expedite data collection from multiple channels simultaneously.
- **User-Friendly Customization**: Designed for easy adaptability to specific requirements, supporting straightforward modifications and extensions.
- **Matched Files Download**: Allows users to download matched result files directly from the dashboard.
- **S3 Integration**: Automatically uploads matched result files to an S3 bucket, with configurable settings via a `.env` file.

## Technical Details

### Prerequisites

- Python 3.x
- Flask
- BeautifulSoup4 - bs4
- Selenium
- Requests
- Flask-SocketIO
- NLTK
- Tor
- Boto3 (for S3 integration)
- Python-Dotenv (for environment variable management)

### Setting Up

1. **Python 3.x Installation**: Verify Python 3.x is installed on your system.
   ```bash
   python3 --version
   sudo apt install -y python3-pip
   ```
2. **Dependencies**: Install the required Python packages using pip.
   ```bash
   pip install flask beautifulsoup4 selenium requests flask_socketio nltk tor boto3 python-dotenv
   ```
3. **Tor Configuration**: Install Tor locally and ensure it's configured to run a SOCKS proxy on `localhost:9050`.
   ```bash
   sudo apt install tor
   sudo systemctl enable tor
   sudo systemctl start tor
   ```
   Edit the Tor configuration file to ensure the SOCKS proxy is running on port `9050`:
   ```bash
   sudo nano /etc/tor/torrc
   ```
   Verify Tor is running a SOCKS proxy:
   ```bash
   curl --socks5 localhost:9050 https://check.torproject.org
   ```
4. **WebDriver Setup**: Ensure the Chrome WebDriver is installed and properly configured in the script's path settings.
   - **Download Chrome WebDriver and browser **:
     ```bash
     curl -O https://storage.googleapis.com/chrome-for-testing-public/129.0.6668.58/linux64/chromedriver-linux64.zip
     ```
   - **Unzip and Install**:
     ```bash
     unzip chromedriver-linux64.zip
     sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
     sudo chmod +x /usr/local/bin/chromedriver
     sudo apt-get update
     sudo apt-get install chromium-browser

     ```
   - **Verify Installation**:
     ```bash
     chromedriver --version
     google-chrome --version
     ```

### Environment Configuration

For S3 integration, create a `.env` file in the project root with the following content:

```bash
S3_BUCKET_NAME=tgscraper-matches
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

### Project Structure

- `TeleScrape.py`: The main script, encapsulating the scraping logic, Flask application, and Tor setup.
- `keywords.txt`: Text file listing the keywords for content scraping.
- `/templates`: Folder containing HTML templates for the Flask-based dashboard.
- `/static`: Folder containing static files like images (e.g., logo).

## Getting Started

1. **Keyword Configuration**: Populate `keywords.txt` with your desired keywords.
2. **Script Execution**: Launch `TeleScrape.py` to start scraping and activate the Flask dashboard.
   ```bash
   python3 TeleScrape.py
   ```
3. **Dashboard Navigation**: Access `http://127.0.0.1:8081/` on your browser to view the scraping progress and results live.

## Dashboard Highlights

- **Real-Time Refresh**: Automatically updates to display the latest scraping data.
- **Keyword Visualization**: Keywords and matches are highlighted within the content for better clarity.
- **File Download**: Download matched result files directly from the dashboard.
- **S3 Integration**: Automatically uploads matched files to an S3 bucket if configured.
- **Adaptive Design**: Ensures a consistent experience across various devices and resolutions.

With download buttons to get matched key word files
![Screenshot 2024-08-29 at 16 20 13](https://github.com/user-attachments/assets/424a39a4-447f-486d-8a98-0282b744f1c2)


## Contributing

Contributions are highly appreciated! If you have improvements or suggestions, please fork this repository, commit your changes, and submit a pull request for review.

## License

This project is distributed under the [MIT License](LICENSE.md), fostering widespread use and contribution by providing a lenient framework for software distribution and modification.

---

This `README.md` file reflects the current state and new features of the project, including the dashboard interface updates, S3 integration, and improved instructions for setup and usage.
