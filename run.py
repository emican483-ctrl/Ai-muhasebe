from flask import Flask
from app.views.dashboard import dashboard_bp
from app.views.pricing import pricing_bp
import os

app = Flask(__name__, template_folder='app/templates')
app.secret_key = os.urandom(24)

# Blueprint'leri uygulamaya kaydediyoruz
app.register_blueprint(dashboard_bp)
app.register_blueprint(pricing_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
