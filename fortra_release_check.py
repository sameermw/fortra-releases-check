#!/usr/bin/env python3
from selenium import webdriver
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time
import csv

# Read URLs from the input file
try:
    with open('fortra_releasenote_urls.txt', 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print("Error: fortra_releasenote_urls.txt not found.")
    exit(1)

# List to hold the extracted data
data = []

# Set up Selenium WebDriver for Safari
driver = webdriver.Safari()

for url in urls:
    try:
        # Fetch the webpage with Selenium
        driver.get(url)
        time.sleep(2)  # Wait for JavaScript to load
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

        # Find version in <h5> under the first <h3> (month/year)
        latest_h3 = soup.find('h3')
        if latest_h3:
            version_h5 = latest_h3.find_next('h5')
            if version_h5:
                version_text = version_h5.text.strip()
                version_match = re.search(r'Version\s+([\d.]+)', version_text, re.IGNORECASE)
                if version_match:
                    version = version_match.group(1)

                    # Find release date in <p class="release-date">
                    date_p = version_h5.find_next('p', class_='release-date')
                    if date_p:
                        release_date = date_p.text.strip()

        # Fallback: Search page text for version and date patterns
        if version == "Not found" or release_date == "Not found":
            page_text = soup.get_text()
            # Look for version pattern (e.g., "Version 8.13")
            version_match = re.search(r'Version\s+([\d.]+)', page_text, re.IGNORECASE)
            if version_match:
                version = version_match.group(1)

            # Look for date pattern (e.g., "July 1, 2025")
            date_match = re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}', page_text, re.IGNORECASE)
            if date_match:
                release_date = date_match.group(0)

        # Add to data list
        data.append({
            'name': product_name,
            'version': version,
            'date': release_date
        })

        # Debugging output
        print(f"Processed {url}: Product={product_name}, Version={version}, Date={release_date}")

    except Exception as e:
        # Handle any errors
        parsed_url = urlparse(url)
        product_name = parsed_url.path.split('/')[-1].rsplit('.', 1)[0].replace('forIBMi', ' for IBM i')
        data.append({
            'name': product_name,
            'version': 'Error',
            'date': str(e)
        })
        print(f"Error processing {url}: {e}")

# Clean up
driver.quit()

# Write the output to release_status.txt with tab-separated format
try:
    with open('release_status.txt', 'w') as outfile:
        # Write header with fixed-width columns
        outfile.write(f"{'Product':<50}{'Version':<15}{'Date':<20}\n")
        # Write data with fixed-width columns
        for item in data:
            outfile.write(f"{item['name']:<50}{item['version']:<15}{item['date']:<20}\n")
    print("Output written to release_status.txt")

    # Optional: CSV output (uncomment to use instead of txt)
    """
    with open('release_status.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Product', 'Version', 'Date'])  # Header
        for item in data:
            writer.writerow([item['name'], item['version'], item['date']])
    print("Output written to release_status.csv")
    """

except Exception as e:
    print(f"Error writing to output file: {e}")