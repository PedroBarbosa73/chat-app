#!/bin/bash
cd /home/site/wwwroot && gunicorn --config gunicorn.conf.py --timeout 600 --access-logfile '-' --error-logfile '-' --log-level info app:app 