#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Start the Gunicorn web server in the background.
# It serves the Flask app (main.py).
gunicorn --bind 0.0.0.0:10000 --workers 1 --threads 2 --timeout 300 main:app &

# Start the RQ worker in the foreground.
# It will listen for jobs on the Redis queue.
# This command must be the last one to keep the service running.
rq worker --url $REDIS_URL