import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, g, request

from api.routes import api_bp
from infrastructure.logging.request_logger import (
    setup_logger,
    get_logger,
    generate_request_id,
    set_request_id,
    get_request_id,
)

app = Flask(__name__)

# Initialize logger
logger = setup_logger("tonychat")

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# Ensure uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.before_request
def start_timer():
    """Record request start time."""
    g.start_time = time.time()


@app.before_request
def before_request_handler():
    """Generate and set request_id for /api requests."""
    if request.path.startswith("/api"):
        request_id = generate_request_id()
        g.request_id = request_id
        set_request_id(request_id)


@app.after_request
def after_request_handler(response):
    """Add X-Request-ID header and log request completion."""
    if request.path.startswith("/api"):
        request_id = get_request_id()
        if request_id:
            response.headers["X-Request-ID"] = request_id

        # Calculate duration
        duration_ms = 0
        start_time = getattr(g, "start_time", None)
        if start_time:
            duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
    return response


# Register blueprint
app.register_blueprint(api_bp)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
