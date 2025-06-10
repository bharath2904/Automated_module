# project/worker.py

import os
import redis
from rq import Worker, Queue, Connection

# Determine if running on Render
listen = ['default']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        print(f"Worker starting... Listening on: {listen}")
        worker.work()