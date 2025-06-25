import math
import traceback
import uuid
from flask import Blueprint, request, jsonify, make_response
from .models import db, Customers, Storages, Catalogs, Vehicles, VehicleCustomer
from collections import defaultdict
from sqlalchemy import func

bp = Blueprint('api', __name__)

TRUCK_SIZES = [1500, 2400, 3500, 4000, 5000, 6000, 7000, 8000]
MAX_STOPS = 2
MAX_DISTANCE = 25

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ, Δλ = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def generate_unique_vehicle_id():
    return f"V{uuid.uuid4().hex[:5].upper()}"

def get_customer_location(customer_id):
    cust = Customers.query.get(customer_id)
    return (cust.CustomerLat, cust.CustomerLong) if cust else (None, None)

def get_customer_name(customer_id):
    cust = Customers.query.get(customer_id)
    return str(cust.CustomerName) if cust else ""

def assign_trucks(orders):
    try:
        contract = Vehicles.query.filter_by(VehicleContract=True).order_by(Vehicles.VehicleID).all()
        others = Vehicles.query.filter_by(VehicleContract=False).all()
        vehicles = contract + others

        customer_orders = defaultdict(list)
        for order in orders:
            customer_orders[order["CustomerID"]].append(order)

        customer_weights = [
            {
                "CustomerID": cid,
                "orders": cust_orders,
                "total_weight": sum(float(o["weight"]) for o in cust_orders)
            }
            for cid, cust_orders in customer_orders.items()
        ]

        customer_weights.sort(key=lambda x: x["total_weight"], reverse=True)

        assigned_customers = set()
        vehicle_assignments = []
        contract_vehicles_used = []

        def allocate_vehicle(is_contract):
            if is_contract and len(contract_vehicles_used) < len(contract):
                return contract[len(contract_vehicles_used)]
            else:
                veh = Vehicles(
                    VehicleID = generate_unique_vehicle_id(),
                    VehicleType = "", 
                    VehicleCapacity = 0.0,
                    VehicleCurrentLoad = 0.0,
                    VehicleLat = 10.766590089230672,
                    VehicleLong = 106.60678703538484,
                    VehicleContract = False
                )
                db.session.add(veh)
                db.session.flush()
                return veh

        def assign_group(group):
            group_orders = [o for cust in group for o in cust["orders"]]
            storage_ids = list({order["StorageID"] for order in group_orders})

            total_weight = sum(float(o["weight"]) for o in group_orders)
            if total_weight < 80:
                vtype, vcap = "two-wheeler", 80
            elif total_weight <= 800:
                vtype, vcap = "van", 800
            else:
                vtype, vcap = "truck", next((s for s in TRUCK_SIZES if total_weight <= s), TRUCK_SIZES[-1])

            is_contract = len(contract_vehicles_used) < len(contract)
            veh = allocate_vehicle(is_contract)
            veh.VehicleType = vtype
            veh.VehicleCapacity = vcap
            veh.VehicleCurrentLoad = total_weight

            if is_contract:
                contract_vehicles_used.append(veh)

            grouped = defaultdict(float)
            for o in group_orders:
                grouped[(o["CustomerID"], o["StorageID"])] += float(o["weight"])
            for (cid, sid), weight in grouped.items():
                existing = VehicleCustomer.query.filter_by(
                    VehicleID=veh.VehicleID,
                    CustomerID=cid,
                    StorageID=sid
                ).first()
                if existing:
                    existing.LoadWeight += weight
                else:
                    db.session.add(VehicleCustomer(
                        VehicleID=veh.VehicleID,
                        CustomerID=cid,
                        StorageID=sid,
                        LoadWeight=weight
                    ))

            assigned_list = [
                {
                    "CustomerID": c["CustomerID"],
                    "customerName": get_customer_name(c["CustomerID"]),
                    "loadWeight": c["total_weight"]
                }
                for c in group
            ]

            route = [["start", float(veh.VehicleLat), float(veh.VehicleLong)]]
            storage_data = []
            customer_data = []
            for sid in storage_ids:
                s = Storages.query.get(sid)
                if s:
                    storage_data.append({"id": sid, "name": s.StorageName})
                    route.append(["storage", sid, s.StorageLat, s.StorageLong])
            for c in group:
                cust = Customers.query.get(c["CustomerID"])
                if cust:
                    customer_data.append({"id": cust.CustomerID, "name": cust.CustomerName})
                    route.append(["customer", cust.CustomerID, cust.CustomerLat, cust.CustomerLong])

            vehicle_assignments.append({
                "truckId": str(veh.VehicleID),
                "type": vtype,
                "capacity": vcap,
                "currentLoad": total_weight,
                "assignedCustomers": assigned_list,
                "route": route,
                "storages": [
                    {"id": s.StorageID, "name": s.StorageName}
                    for s in Storages.query.filter(Storages.StorageID.in_(storage_ids)).all()
                ],
                "customers": [
                    {"id": c["CustomerID"], "name": get_customer_name(c["CustomerID"])}
                    for c in group
            ]
            })

        unassigned = [c for c in customer_weights if c["CustomerID"] not in assigned_customers]
        while unassigned:
            main_cust = unassigned[0]
            group = [main_cust]
            assigned_customers.add(main_cust["CustomerID"])
            main_lat, main_lng = get_customer_location(main_cust["CustomerID"])

            for other in unassigned[1:]:
                if len(group) >= MAX_STOPS:
                    break
                other_lat, other_lng = get_customer_location(other["CustomerID"])
                if main_lat is None or other_lat is None:
                    continue
                if haversine(main_lat, main_lng, other_lat, other_lng) <= MAX_DISTANCE:
                    group.append(other)
                    assigned_customers.add(other["CustomerID"])

            assign_group(group)
            unassigned = [c for c in customer_weights if c["CustomerID"] not in assigned_customers]

        db.session.commit()
        return vehicle_assignments

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        raise e

@bp.route("/customers", methods=["GET"])
def get_customers():
    return jsonify({"customers": [c.to_dict() for c in Customers.query.all()]}), 200

@bp.route("/storages", methods=["GET"])
def get_storages():
    return jsonify({"storages": [s.to_dict() for s in Storages.query.all()]}), 200

@bp.route("/catalogs", methods=["GET"])
def get_catalogs():
    return jsonify({"catalogs": [c.to_dict() for c in Catalogs.query.all()]}), 200

# @bp.route('/name-maps')
# def get_name_mappings():
#     customer_map = {c.CustomerID: c.CustomerName for c in Customers.query.all()}
#     storage_map = {s.StorageID: s.StorageName for s in Storages.query.all()}
#     return jsonify({
#         "customerNameMap": customer_map,
#         "storageNameMap": storage_map
#     })

@bp.route("/assign_trucks", methods=["POST", "OPTIONS"])
def assign_trucks_endpoint():
    if request.method == "OPTIONS":
        response = make_response('', 200)
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    try:
        orders = request.get_json().get("orders", [])
        assigned = assign_trucks(orders)
        return jsonify({"assigned_vehicles": assigned}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500