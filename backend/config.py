"""
Configuration settings for NLytics
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Flask settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('FLASK_ENV', 'development') == 'development'

# File upload settings
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
UPLOAD_FOLDER = BASE_DIR / 'data' / 'uploads'
PROCESSED_FOLDER = BASE_DIR / 'data' / 'processed'

# API settings
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Model settings
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# Session settings
SESSION_TIMEOUT = 3600  # 1 hour

# Processing limits
MAX_ROWS = 1_000_000
MAX_COLUMNS = 500
EXECUTION_TIMEOUT = 300  # 5 minutes
