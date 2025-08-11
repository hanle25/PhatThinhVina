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
    db.init_app(app)
    Migrate(app, db)
    with app.app_context():
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            app.logger.warning(f"DB ping failed on startup: {e}")

    # IMPORTANT: import blueprint AFTER app/db are ready
    from .routes import bp
    app.register_blueprint(bp)

    # Always clear sessions at end of context/request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
