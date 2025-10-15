# Cloud Run optimized configuration
import multiprocessing

# Server socket
bind = "0.0.0.0:8080"

# Worker processes
# Cloud Run: Use threads instead of workers (single container instance)
workers = 1
threads = 4
worker_class = "sync"

# Timeout
timeout = 300  # 5 minutes for ML inference
graceful_timeout = 30
keepalive = 5

# Memory optimization
max_requests = 1000  # Restart worker after 1000 requests (memory cleanup)
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Application preloading
preload_app = True

# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Visual Product Matcher on Cloud Run")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Shutting down Visual Product Matcher")
