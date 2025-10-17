#!/bin/bash
set -e

# Add local bin to PATH
export PATH=/root/.local/bin:$PATH

echo "Starting application..."
gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
