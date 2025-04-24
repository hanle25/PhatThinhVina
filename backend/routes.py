# backend/routes.py
from flask import Blueprint, request, jsonify
from .models import Customers, Storages
from .optimizer import optimize_routes

bp = Blueprint('api', __name__)

@bp.route("/optimize", methods=["POST"])
def optimize():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload received"}), 400
    
    # Expecting payload:
    # {
    #   "locations": ["lat,lng", "lat,lng", ...],
    #   "num_vehicles": <number>,
    #   "depot_index": <index>
    # }
    
    locations = data.get("locations")
    num_vehicles = data.get("num_vehicles")
    depot_index = data.get("depot_index")
    
    if locations is None or num_vehicles is None or depot_index is None:
        return jsonify({"error": "Missing required input: locations, num_vehicles, depot_index"}), 400
    
    try:
        result = optimize_routes(locations, num_vehicles, depot_index)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/customers", methods=["GET"])
def get_customers():
    customers = Customers.query.all()
    return jsonify({"customers": [c.to_dict() for c in customers]})

@bp.route("/storages", methods=["GET"])
def get_storages():
    storages = Storages.query.all()
    return jsonify({"storages": [s.to_dict() for s in storages]})
