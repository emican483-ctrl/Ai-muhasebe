import os
from flask import Flask, redirect, url_for
from config import Config
from app import models

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    models.init_app(app)

    from app.views import auth, dashboard
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)

    # Ana sayfaya (localhost:5000) girenleri direkt Giriş Sayfasına yolla
    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    @app.route('/health')
    def health_check():
        return {"status": "success", "message": "AI Muhasebe Sistemi, Veritabanı ve Auth Aktif"}, 200

    return app
