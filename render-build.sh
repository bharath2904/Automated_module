#!/usr/bin/env bash

# Exit on error
set -e 

# 1. Install system dependencies for Playwright
echo "--- Installing System Dependencies ---"
apt-get update && apt-get install -y libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libatspi2.0-0 libxcomposite1 libxcursor1 libxdamage1 libxfixes3 libxi6 libxrandr2 libxtst6 libpango-1.0-0 libcairo2 libasound2

# 2. Install Python dependencies
echo "--- Installing Python Packages ---"
pip install -r requirements.txt

# 3. Install the Playwright browser dependencies
echo "--- Installing Playwright Browsers ---"
playwright install --with-deps chromium

echo "--- Build Complete ---"