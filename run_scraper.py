# project/run_scraper.py

import os
from app.scraper import scrape_reviews_from_agoda
from app.sentiment_analysis import run_sentiment_analysis
from datetime import datetime

# --- CONFIGURATION ---
# Change these values before running!
CITY_TO_SCRAPE = "Paris"  # <-- The city you want to scrape
STAR_RATING = 5          # <-- 5 for 5-star, 4 for 4-star, etc. 0 for all.
START_DATE = ""          # <-- Optional: "DD-MM-YYYY", e.g., "01-01-2023"
END_DATE = ""            # <-- Optional: "DD-MM-YYYY", e.g., "31-03-2023"
# ---------------------

def scrape_and_analyze(city, star_rating, start_date, end_date):
    """
    A single function that runs both scraping and sentiment analysis.
    """
    print(f"--- Starting Job for City: {city}, Stars: {star_rating} ---")
    city_slug = city.lower().replace(" ", "_")
    
    # 1. Run the scraper
    try:
        scrape_reviews_from_agoda(
            city=city,
            star_rating=star_rating,
            start_date=start_date,
            end_date=end_date
        )
        print(f"--- Scraping for {city} completed successfully. ---")
    except Exception as e:
        print(f"--- ERROR during scraping for {city}: {e} ---")
        return # Stop if scraping fails

    # 2. Run the sentiment analysis
    try:
        input_path = f"output/agoda_{city_slug}_hotel_reviews.csv"
        output_filename = f"sentiment_{city_slug}.csv"
        output_path = os.path.join('output', output_filename)

        if os.path.exists(input_path):
            run_sentiment_analysis(input_path, output_path)
            print(f"--- Sentiment analysis for {city} completed successfully. ---")
            print(f"--- Your output file is '{output_filename}' ---")
        else:
            print(f"--- ERROR: Scraped file '{input_path}' not found for analysis. ---")

    except Exception as e:
        print(f"--- ERROR during sentiment analysis for {city}: {e} ---")

    print(f"--- Job for {city} finished. ---")


if __name__ == '__main__':
    print("Starting the scraper directly...")
    scrape_and_analyze(CITY_TO_SCRAPE, STAR_RATING, START_DATE, END_DATE)
    print("Script finished.")