from flask import Blueprint, request, jsonify
from models import Customer, Storage
from optimizer import optimize_routes

bp = Blueprint('api', __name__)

@bp.route("/customers", methods=["GET"])
def get_customers():
    customers = Customer.query.all()
    return jsonify({"customers": [c.to_dict() for c in customers]})

@bp.route("/storages", methods=["GET"])
def get_storages():
    storages = Storage.query.all()
    return jsonify({"storages": [s.to_dict() for s in storages]})

@bp.route("/optimize", methods=["GET"])
def optimize():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload received"}), 400

    locations = data.get("locations")
    num_vehicles = data.get("num_vehicles")
    depot = data.get("depot")

    if locations is None or num_vehicles is None or depot is None:
        return jsonify({"error": "Missing required input values: locations, num_vehicles, depot"}), 400

    try:
        result = optimize_routes(locations, num_vehicles, depot)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
