# project/tasks.py

import os
from app.scraper import scrape_reviews_from_agoda
from app.sentiment_analysis import run_sentiment_analysis

def scrape_and_analyze(city, star_rating, start_date, end_date):
    """
    A single function that runs both scraping and sentiment analysis.
    This will be executed by the background worker.
    """
    print(f"--- Starting Job for City: {city} ---")
    
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
        input_path = f"output/agoda_{city.lower().replace(' ', '_')}_hotel_reviews.csv"
        output_filename = f"sentiment_{city.lower().replace(' ', '_')}.csv"
        output_path = os.path.join('output', output_filename)

        if os.path.exists(input_path):
            run_sentiment_analysis(input_path, output_path)
            print(f"--- Sentiment analysis for {city} completed successfully. ---")
        else:
            print(f"--- ERROR: Scraped file '{input_path}' not found for analysis. ---")

    except Exception as e:
        print(f"--- ERROR during sentiment analysis for {city}: {e} ---")

    print(f"--- Job for {city} finished. ---")