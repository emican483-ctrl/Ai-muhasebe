import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ai_muhasebe_gizli_anahtar_987654')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE = os.path.join(BASE_DIR, 'database.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 
