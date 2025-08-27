# Fortra Release Notes Scraper

This Python script (`fortra_release_check.py`) scrapes Fortra release note pages to extract product names, versions, release dates, and flags new versions by comparing them against a stored version history (`previous_versions.json`). It generates a fixed-width text output (`release_status.txt`) and optionally a CSV file (`release_status.csv`). The script supports multiple browsers (Brave, Safari, Chrome, Firefox, Edge) and operating systems (macOS, Windows, Linux).

## Features
- Scrapes product names, versions, and release dates from Fortra release note pages listed in `fortra_releasenote_urls.txt`.
- Flags versions as "New", "Same", or "Invalid" based on comparison with `previous_versions.json`.
- Outputs results in a fixed-width `release_status.txt` (automatically opened) or CSV format.
- Supports:
  - **macOS**: Brave (headless), Safari.
  - **Windows/Linux**: Brave, Google Chrome, Firefox (headless), Microsoft Edge (Windows only, headless).

## Prerequisites
- **Python**: Version 3.6 or higher.
- **Dependencies**:
  - `selenium`: For browser automation.
  - `beautifulsoup4`: For HTML parsing.
  - `webdriver-manager` (for Windows/Linux): Automatically downloads browser drivers.
- **Browsers**:
  - **macOS**: Brave Browser or Safari installed.
  - **Windows**: Brave, Google Chrome, Firefox, or Microsoft Edge installed.
  - **Linux**: Brave, Google Chrome, or Firefox installed.
- **Browser Drivers**:
  - macOS Brave: ChromeDriver (manually installed).
  - Windows/Linux: Drivers are managed by `webdriver-manager`.
- **Input File**: `fortra_releasenote_urls.txt` containing URLs of Fortra release note pages (one per line).

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Create and Activate a Virtual Environment
#### macOS/Linux
```bash
python3 -m venv myenv
source myenv/bin/activate
```
#### Windows
```bash
python -m venv myenv
myenv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install selenium beautifulsoup4 webdriver-manager
```

### 4. Prepare Input File
Create a file named `fortra_releasenote_urls.txt` in the project directory with Fortra release note URLs, one per line, e.g.:
```
https://example.com/fortra/product1
https://example.com/fortra/product2
```

### 5. Browser-Specific Setup
#### macOS: Brave
1. **Install Brave Browser**:
   - Download and install Brave from [brave.com](https://brave.com).
   - Default path: `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser`.
2. **Install ChromeDriver**:
   - Download ChromeDriver matching your Brave version (e.g., 139.0.7258.138) from [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/).
   - Extract and place it at `~/.chromedrivers/chromedriver` (create the directory if needed):
     ```bash
     mkdir -p ~/.chromedrivers
     mv ~/Downloads/chromedriver-mac-arm64/chromedriver ~/.chromedrivers/
     chmod +x ~/.chromedrivers/chromedriver
     ```
   - Verify:
     ```bash
     ~/.chromedrivers/chromedriver --version
     ```

#### macOS: Safari
1. **Enable SafariDriver**:
   - Open Safari, go to **Preferences > Advanced**, and enable the Develop menu.
   - In the Develop menu, enable **Allow Remote Automation**.
   - Run:
     ```bash
     /usr/bin/safaridriver --enable
     ```
2. No additional driver download is needed (SafariDriver is built-in).

#### Windows/Linux: Brave, Chrome, Firefox, Edge
1. **Install Browsers**:
   - **Brave**: Download from [brave.com](https://brave.com).
     - Windows default: `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`.
     - Linux default: `/usr/bin/brave-browser`.
   - **Google Chrome**: Download from [google.com/chrome](https://www.google.com/chrome).
     - Windows default: `C:\Program Files\Google\Chrome\Application\chrome.exe`.
     - Linux default: `/usr/bin/google-chrome`.
   - **Firefox**: Download from [mozilla.org](https://www.mozilla.org/firefox).
     - Windows default: `C:\Program Files\Mozilla Firefox\firefox.exe`.
     - Linux default: `/usr/bin/firefox`.
   - **Edge (Windows only)**: Pre-installed or download from [microsoft.com/edge](https://www.microsoft.com/edge).
     - Default: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`.
2. **Browser Drivers**: The script uses `webdriver-manager` to automatically download the appropriate driver (ChromeDriver for Brave/Chrome, GeckoDriver for Firefox, EdgeDriver for Edge). Ensure internet access during the first run.

### 6. Configure the Script
- Open `fortra_release_check.py` and uncomment the desired browser/OS configuration block (lines 28–54).
  - Example for Windows Brave:
    ```python
    # --- Windows: Brave (headless) ---
    from webdriver_manager.chrome import ChromeDriverManager
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.binary_location = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    ```
- Adjust `options.binary_location` if your browser is installed in a non-standard location.

## Running the Script
1. **Activate Virtual Environment**:
   ```bash
   source myenv/bin/activate  # macOS/Linux
   myenv\Scripts\activate     # Windows
   ```
2. **Run the Script**:
   ```bash
   python fortra_release_check.py
   ```
3. **Output**:
   - `release_status.txt`: Fixed-width text file with columns: Product, Version, Date, Flag.
     - Automatically opens with the default text editor (macOS: TextEdit, Windows: Notepad, Linux: varies).
     - Example:
       ```
       Product                                           Version         Date                Flag        
       Sequel                                            R11M19          June 10, 2024       New         
       Esend                                             R03M63          August 15, 2023     New         
       Sequel Data Warehouse Server                      8.3.05          November 25, 2024   New         
       Multi-Factor Authentication for Insite            1.6.12          Not found           New         
       Robot Schedule for Insite                         1.15.11         June 2020           New         
       ```
   - `previous_versions.json`: Updated with current versions for future comparisons.
   - Optional CSV output: Uncomment lines 103–108 in the script to generate `release_status.csv`.

## Troubleshooting
1. **Incorrect Versions** (e.g., "to", "s", "of"):
   - Check `page_source_<product>.html` files generated for failing products.
   - Verify URLs in `fortra_releasenote_urls.txt`.
   - Increase `time.sleep(5)` to `time.sleep(10)` (line 47) if JavaScript isn’t loading fully.
2. **Flag Issues**:
   - Inspect `previous_versions.json` for incorrect stored versions.
   - Share the file and output for affected products.
3. **Browser/Driver Errors**:
   - **macOS Brave**: Ensure ChromeDriver matches Brave version (`~/.chromedrivers/chromedriver --version`).
   - **Safari**: Verify remote automation is enabled.
   - **Windows/Linux**: Ensure `webdriver-manager` downloads the correct driver (internet required).
   - Check browser binary paths in the script.
4. **Alignment Issues**:
   - Adjust column widths in lines 95–98 (e.g., `{'Version':<20}`).
   - Use CSV output by uncommenting lines 103–108.
5. **Page Load Issues**:
   - Increase wait time (line 47) or add explicit waits:
     ```python
     from selenium.webdriver.support.ui import WebDriverWait
     WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
     ```

## Notes
- **Version Comparison**: Numeric versions (e.g., "8.3.05") are compared numerically; alphanumeric versions (e.g., "R03M63") use string comparison.
- **CSV Output**: Uncomment lines 103–108 for CSV output, which is Excel-compatible.
- **Debugging**: Page source is saved for products with failed version extraction (`page_source_<product>.html`).
- **Browser Paths**: Adjust `binary_location` in the script if browsers are installed in non-standard locations.

## Example `previous_versions.json`
To test flagging, create `previous_versions.json`:
```json
{
    "Sequel Data Warehouse Server": "8.3.04",
    "Multi-Factor Authentication for Insite": "1.6.11",
    "Robot Schedule for Insite": "1.15.10"
}
```

## Contributing
- Report issues or suggest improvements via GitHub Issues.
- Ensure URLs in `fortra_releasenote_urls.txt` are valid Fortra release note pages.

## License
MIT License (or specify your preferred license).
