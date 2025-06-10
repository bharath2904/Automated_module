# from flask import Flask, render_template, request, redirect, url_for, send_from_directory
# import os
# from datetime import datetime
# from app.scraper import scrape_reviews_from_agoda
# from app.sentiment_analysis import run_sentiment_analysis

# app = Flask(__name__)
# OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/start-scraping', methods=['POST'])
# def start_scraping():
#     city = request.form['city']
#     star_rating = int(request.form['star_rating'])
    
#     # Get date parameters from form (they might be empty)
#     start_date = request.form.get('start_date', '')
#     end_date = request.form.get('end_date', '')
    
#     # Convert date strings to DD-MM-YYYY format if they exist
#     formatted_start_date = None
#     formatted_end_date = None
    
#     if start_date:
#         try:
#             # Convert from YYYY-MM-DD (HTML date input) to DD-MM-YYYY
#             dt = datetime.strptime(start_date, "%Y-%m-%d")
#             formatted_start_date = dt.strftime("%d-%m-%Y")
#         except ValueError:
#             print("⚠️ Invalid start date format, ignoring date filter")
    
#     if end_date:
#         try:
#             # Convert from YYYY-MM-DD (HTML date input) to DD-MM-YYYY
#             dt = datetime.strptime(end_date, "%Y-%m-%d")
#             formatted_end_date = dt.strftime("%d-%m-%Y")
#         except ValueError:
#             print("⚠️ Invalid end date format, ignoring date filter")
    
#     # Call the scraper with date parameters
#     scrape_reviews_from_agoda(
#         city=city,
#         star_rating=star_rating,
#         start_date=formatted_start_date,
#         end_date=formatted_end_date
#     )
    
#     return redirect(url_for('analysis_page', city=city.lower().replace(" ", "_")))

# @app.route('/analysis/<city>')
# def analysis_page(city):
#     return render_template('analysis.html', city=city)

# @app.route('/start-analysis/<city>', methods=['POST'])
# def start_analysis(city):
#     input_path = f"output/agoda_{city}_hotel_reviews.csv"
#     output_filename = f"sentiment_{city}.csv"
#     output_path = os.path.join(OUTPUT_FOLDER, output_filename)
#     run_sentiment_analysis(input_path, output_path)
#     return render_template('download.html', filename=output_filename)

# @app.route('/download/<filename>')
# def download_file(filename):
#     return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

# if __name__ == '__main__':
#     try:
#         print("Starting Flask server...")
#         app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
#     except Exception as e:
#         print(f"Error starting server: {e}")
# project/main.py (Updated Version)

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from datetime import datetime
from redis import Redis
from rq import Queue
from tasks import scrape_and_analyze

app = Flask(__name__)
OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')

# Setup Redis and RQ
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = Redis.from_url(redis_url)
q = Queue(connection=redis_conn)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-scraping', methods=['POST'])
def start_scraping():
    city = request.form['city']
    star_rating = int(request.form['star_rating'])
    
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    
    formatted_start_date = None
    if start_date:
        dt = datetime.strptime(start_date, "%Y-%m-%d")
        formatted_start_date = dt.strftime("%d-%m-%Y")
    
    formatted_end_date = None
    if end_date:
        dt = datetime.strptime(end_date, "%Y-%m-%d")
        formatted_end_date = dt.strftime("%d-%m-%Y")
    
    # --- THIS IS THE KEY CHANGE ---
    # Instead of calling the function directly, we add it to the queue.
    # The job will be run by our background worker.
    q.enqueue(
        scrape_and_analyze,
        city,
        star_rating,
        formatted_start_date,
        formatted_end_date,
        job_timeout=1800  # Allow job to run for 30 minutes
    )
    
    # Redirect to a new "job started" page
    return redirect(url_for('job_started_page', city=city.lower().replace(" ", "_")))

@app.route('/job-started/<city>')
def job_started_page(city):
    # This page confirms the job started and provides the eventual download link.
    # The user might have to wait a while for the file to be ready.
    output_filename = f"sentiment_{city}.csv"
    return render_template('analysis.html', city=city, filename=output_filename)


@app.route('/download/<filename>')
def download_file(filename):
    # Make sure the 'output' directory exists before trying to send from it
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

# Add a health check endpoint for Render
@app.route('/healthz')
def healthz():
    return "OK", 200

# Remove the __main__ block, as gunicorn will run the app
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)