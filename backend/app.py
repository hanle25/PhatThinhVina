from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from .routes import bp
from .models import db

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)
    
    db.init_app(app)
    Migrate(app, db)
    
    app.register_blueprint(bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
