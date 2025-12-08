import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'boxplot_tool_2025_secure_key'
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or 'outputs'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 5 * 1024 * 1024)
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'xml', 'txt'}