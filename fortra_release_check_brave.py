#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time
import csv
import os
import json

# Read URLs from the input file
try:
    with open('fortra_releasenote_urls.txt', 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print("Error: fortra_releasenote_urls.txt not found.")
    exit(1)

# Load previous versions if file exists
previous_versions_file = 'previous_versions.json'
previous_versions = {}
if os.path.exists(previous_versions_file):
    with open(previous_versions_file, 'r') as f:
        previous_versions = json.load(f)

# List to hold the extracted data
data = []

# Set up Selenium WebDriver for Brave in headless mode
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode (no GUI)
options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36')
options.binary_location = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'  # Brave binary path
try:
    driver = webdriver.Chrome(service=Service('/Users/sameera/.chromedrivers/chromedriver'), options=options)
    # https://googlechromelabs.github.io/chrome-for-testing/#stable
except Exception as e:
    print(f"Failed to initialize ChromeDriver: {e}")
    exit(1)

# Function to compare versions
def compare_versions(current, previous):
    if not current or not previous:
        return "Invalid"
    # For numeric versions (e.g., "8.13"), split and compare numerically
    if re.match(r'^[\d.]+$', current) and re.match(r'^[\d.]+$', previous):
        try:
            curr_parts = [int(part) for part in current.split('.')]
            prev_parts = [int(part) for part in previous.split('.')]
            # Pad shorter list with zeros
            max_len = max(len(curr_parts), len(prev_parts))
            curr_parts += [0] * (max_len - len(curr_parts))
            prev_parts += [0] * (max_len - len(prev_parts))
            if curr_parts > prev_parts:
                return "New"
            elif curr_parts == prev_parts:
                return "Same"
            else:
                return "Invalid"  # If current < previous, consider invalid
        except (ValueError, IndexError):
            return "Invalid"
    # For alphanumeric versions (e.g., "R03M63"), compare as strings
    else:
        return "New" if current > previous else "Same" if current == previous else "Invalid"

for url in urls:
    try:
        # Fetch the webpage with Selenium
        driver.get(url)
        time.sleep(5)  # Increased wait for JavaScript to load
        page_source = driver.page_source

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract product name from <h1> or URL
        h1_tag = soup.find('h1')
        if h1_tag:
            product_name = h1_tag.text.strip()
        else:
            # Fallback to URL filename without extension
            parsed_url = urlparse(url)
            product_name = parsed_url.path.split('/')[-1].rsplit('.', 1)[0].replace('forIBMi', ' for IBM i')

        # Initialize version and date
        version = "Not found"
        release_date = "Not found"
        flag = "Invalid"

        # Find version in <h5> under the first <h3> (month/year)
        latest_h3 = soup.find('h3')
        if latest_h3:
            version_h5 = latest_h3.find_next('h5')
            if version_h5:
                version_text = version_h5.text.strip()
                version_match = re.search(r'Version\s*:?\s*([\w\d.]+)', version_text, re.IGNORECASE)
                if version_match:
                    version = version_match.group(1)
                    # Verify version format (must contain at least one digit)
                    if not re.search(r'\d', version):
                        version = "Not found"

                    # Find release date in <p class="release-date">
                    date_p = version_h5.find_next('p', class_='release-date')
                    if date_p:
                        release_date = date_p.text.strip()

        # Fallback: Search page text for version and date patterns
        if version == "Not found" or release_date == "Not found":
            page_text = soup.get_text()
            # Look for version pattern (e.g., "Version R03M63" or "Version 8.13")
            if version == "Not found":
                version_match = re.search(r'Version\s*:?\s*([\w\d.]+[\d][\w\d.]*)', page_text, re.IGNORECASE)
                if version_match and re.search(r'\d', version_match.group(1)):
                    version = version_match.group(1)
                else:
                    # Save page source for debugging
                    with open(f'page_source_{product_name.replace(" ", "_")}.html', 'w', encoding='utf-8') as f:
                        f.write(page_source)

            # Look for date pattern (e.g., "July 1, 2025")
            if release_date == "Not found":
                date_match = re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', page_text, re.IGNORECASE)
                if date_match:
                    release_date = date_match.group(0)

        # Set flag based on comparison with previous version
        previous_version = previous_versions.get(product_name, None)
        if version not in ["Not found", "Error"] and previous_version:
            flag = compare_versions(version, previous_version)
        elif version not in ["Not found", "Error"]:
            flag = "New"  # First time, consider new
        else:
            flag = "Invalid"

        # Add to data list
        data.append({
            'name': product_name,
            'version': version,
            'date': release_date,
            'flag': flag
        })

        # Debugging output
        print(f"Processed {url}: Product={product_name}, Version={version}, Date={release_date}, Flag={flag}")

    except Exception as e:
        # Handle any errors
        parsed_url = urlparse(url)
        product_name = parsed_url.path.split('/')[-1].rsplit('.', 1)[0].replace('forIBMi', ' for IBM i')
        data.append({
            'name': product_name,
            'version': 'Error',
            'date': str(e),
            'flag': 'Error'
        })
        print(f"Error processing {url}: {e}")

# Clean up
driver.quit()

# Update previous versions with current versions
try:
    with open(previous_versions_file, 'w') as f:
        json.dump({item['name']: item['version'] for item in data if item['version'] not in ['Not found', 'Error']}, f, indent=4)
    print(f"Updated previous versions in {previous_versions_file}")
except Exception as e:
    print(f"Error updating previous versions: {e}")

# Write the output to release_status.txt with fixed-width columns
try:
    with open('release_status.txt', 'w') as outfile:
        # Write header with fixed-width columns
        outfile.write(f"{'Product':<50}{'Version':<15}{'Date':<20}{'Flag':<10}\n")
        # Write data with fixed-width columns
        for item in data:
            outfile.write(f"{item['name']:<50}{item['version']:<15}{item['date']:<20}{item['flag']:<10}\n")
    print("Output written to release_status.txt")

    # Open release_status.txt with the default text editor
    os.system("open release_status.txt")

    # Optional: CSV output (uncomment to use instead of txt)
    """
    with open('release_status.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Product', 'Version', 'Date', 'Flag'])  # Header
        for item in data:
            writer.writerow([item['name'], item['version'], item['date'], item['flag']])
    print("Output written to release_status.csv")
    # Open release_status.csv with the default application
    # os.system("open release_status.csv")
    """

except Exception as e:
    print(f"Error writing to output file: {e}")