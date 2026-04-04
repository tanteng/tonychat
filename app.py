import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask

from api.routes import api_bp

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# Ensure uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprint
app.register_blueprint(api_bp)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
