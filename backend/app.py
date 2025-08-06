from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from .routes import bp
from .models import db
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    # CORS(app, supports_credentials=True, origins=[
    #     "http://192.168.1.18:3000",
    #     "http://localhost:3000",
    #     "http://127.0.0.1:3000"
    # ])
    CORS(app, supports_credentials=True)
    app.config.from_object(Config)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,        # critical: test connections before use
        "pool_size": 12,              # persistent connections per app process
        "max_overflow": 24,           # allow bursts
        "pool_timeout": 30,           # seconds to wait for a connection
        "pool_recycle": 1800,         # recycle connections older than 30 minutes
        "connect_args": {"sslmode": "require"},
    }
    db.init_app(app)
    Migrate(app, db)
    app.register_blueprint(bp)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
