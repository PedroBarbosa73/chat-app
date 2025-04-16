#!/bin/bash

# Navigate to app directory
cd /home/site/wwwroot

# Install dependencies if not already installed
pip install -r requirements.txt

# Start Gunicorn
gunicorn --config gunicorn.conf.py --timeout 600 --access-logfile '-' --error-logfile '-' --log-level info app:app 