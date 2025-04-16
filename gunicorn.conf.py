import os

bind = f"0.0.0.0:{os.getenv('WEBSITES_PORT', '8000')}"
workers = 4
timeout = 600
preload_app = True
worker_class = "sync"
accesslog = "-"
errorlog = "-"
capture_output = True
loglevel = "info" 