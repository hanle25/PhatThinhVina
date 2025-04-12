# backend/app.py
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from routes import bp  # Import the blueprint from routes.py
from optimizer import optimize_routes  # Your route optimization logic

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    
    # Register API routes from the blueprint
    app.register_blueprint(bp)
    
    # Example: your /optimize endpoint here...
    @app.route("/optimize", methods=["POST"])
    def optimize():
        # Your current optimize logic, for example:
        from flask import request, jsonify
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON payload received"}), 400
        try:
            result = optimize_routes(data["locations"], data["num_vehicles"], data["depot"])
            return jsonify({"result": result})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
