#!/usr/bin/env python3

import subprocess
import json
import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path
from packaging import version  # pip install packaging if needed
import glob  # For finding the binary

# Configuration
DRIVER_DIR = Path.home() / ".chromedrivers"
BROWSER_PATHS = {
    "Chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "Brave": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
}
JSON_URL = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"

def get_browser_version(browser_path):
    """Run browser --version and extract the version string."""
    try:
        result = subprocess.run([browser_path, "--version"], capture_output=True, text=True, check=True)
        # Output like: "Brave Browser 141.1.83.109"
        version_line = result.stdout.strip()
        version = version_line.split()[-1]  # Last word is the version
        return version
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def get_driver_version(driver_path):
    """Run chromedriver --version and extract the version string."""
    try:
        result = subprocess.run([driver_path, "--version"], capture_output=True, text=True, check=True)
        # Output like: "ChromeDriver 141.0.7390.65"
        version_line = result.stdout.strip()
        version = version_line.split()[1]  # Second word is the version
        return version
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def get_architecture():
    """Detect macOS architecture."""
    arch = os.uname().machine
    if arch == "arm64":
        return "mac-arm64"
    elif arch == "x86_64":
        return "mac-x64"
    else:
        raise ValueError(f"Unsupported architecture: {arch}")

def find_matching_driver(major_version):
    """Fetch JSON and find the latest ChromeDriver matching major version."""
    try:
        with urllib.request.urlopen(JSON_URL) as response:
            data = json.loads(response.read().decode())
        
        versions = data.get("versions", [])
        matching_versions = []
        for ver_info in versions:
            if ver_info["version"].startswith(f"{major_version}."):
                downloads = ver_info.get("downloads", {}).get("chromedriver", [])
                platform_downloads = [d for d in downloads if d["platform"] == get_architecture()]
                if platform_downloads:
                    matching_versions.append((ver_info["version"], platform_downloads[0]["url"]))
        
        if not matching_versions:
            return None, None
        
        # Sort by version descending and pick the latest
        matching_versions.sort(key=lambda x: version.parse(x[0]), reverse=True)
        latest_version, url = matching_versions[0]
        return url, latest_version
    except Exception as e:
        print(f"Error fetching versions: {e}", file=sys.stderr)
        return None, None

def download_and_extract(url, driver_dir, major_version):
    """Download ZIP, robustly extract/move chromedriver to root, and make executable."""
    driver_dir.mkdir(parents=True, exist_ok=True)
    zip_path = driver_dir / f"chromedriver_{major_version}.zip"
    
    try:
        print(f"Downloading from {url}...")
        urllib.request.urlretrieve(url, zip_path)
        
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(driver_dir)
        
        final_path = driver_dir / "chromedriver"
        
        # Find chromedriver binary (direct or in subdir)
        candidates = list(driver_dir.rglob("chromedriver"))  # Recursive, but shallow in practice
        if len(candidates) == 0:
            print("Error: chromedriver not found in ZIP.", file=sys.stderr)
            # Debug: List all extracted files
            print("Extracted files:", [p.name for p in driver_dir.rglob("*") if p.is_file()])
            return False
        elif len(candidates) > 1:
            print("Error: Multiple chromedriver files found.", file=sys.stderr)
            return False
        
        chromedriver_found = candidates[0]
        if chromedriver_found != final_path:
            # Move from subdir to root
            print(f"Moving {chromedriver_found} to root...")
            chromedriver_found.rename(final_path)
            # Remove the now-empty parent subdir
            parent_dir = chromedriver_found.parent
            if parent_dir != driver_dir and parent_dir.exists():
                shutil.rmtree(parent_dir)
        
        # Make executable
        os.chmod(final_path, 0o755)
        print(f"ChromeDriver installed to {final_path}")
        return True
    except Exception as e:
        print(f"Download/extract error: {e}", file=sys.stderr)
        return False
    finally:
        if zip_path.exists():
            os.remove(zip_path)
        # Clean up any other potential empty subdirs (e.g., from previous runs)
        for sub in driver_dir.iterdir():
            if sub.is_dir() and sub.name.startswith("chromedriver-"):
                try:
                    shutil.rmtree(sub)
                    print(f"Cleaned up leftover directory: {sub}")
                except OSError:
                    pass  # Ignore if not empty or in use

def main():
    # Find installed browser
    browser = None
    version = None
    for name, path in BROWSER_PATHS.items():
        if os.path.exists(path):
            version = get_browser_version(path)
            if version:
                browser = name
                break
    
    if not version:
        print("No supported browser (Chrome or Brave) found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Detected {browser} version: {version}")
    browser_major = version.split(".")[0]
    
    # Check existing driver
    existing_driver_path = DRIVER_DIR / "chromedriver"
    if existing_driver_path.exists():
        existing_version = get_driver_version(existing_driver_path)
        if existing_version:
            driver_major = existing_version.split(".")[0]
            if driver_major == browser_major:
                print(f"ChromeDriver already up-to-date: {existing_version} (major {driver_major} matches browser {browser_major})")
                # Optional: Full verification
                result = subprocess.run([str(existing_driver_path), "--version"], capture_output=True, text=True)
                print(f"Verification: {result.stdout.strip()}")
                sys.exit(0)  # Skip update
            else:
                print(f"Major version mismatch: Existing {driver_major} vs. needed {browser_major}. Updating...")
        else:
            print("Existing chromedriver invalid (can't get version). Updating...")
    else:
        print("No existing ChromeDriver found. Downloading...")
    
    # Proceed to update
    url, driver_version = find_matching_driver(browser_major)
    if not url:
        print(f"No matching ChromeDriver found for major version {browser_major}.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Downloading latest ChromeDriver {driver_version} for {browser_major}.x...")
    if download_and_extract(url, DRIVER_DIR, browser_major):
        print("Success! Add to PATH or use in Selenium: Service('/Users/sameera/.chromedrivers/chromedriver')")
        # Verify new install
        result = subprocess.run([str(DRIVER_DIR / "chromedriver"), "--version"], capture_output=True, text=True)
        print(f"Verification: {result.stdout.strip()}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()