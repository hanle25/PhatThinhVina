import math
import traceback
import uuid
from flask import Blueprint, request, jsonify, make_response
from .models import db, Customers, Storages, Catalogs, Vehicles, VehicleCustomer
from collections import defaultdict
from sqlalchemy import func

bp = Blueprint('api', __name__)

TRUCK_SIZES = [1500, 2400, 3500, 4000, 5000, 6000, 7000, 8000]
MAX_CUSTOMER_STOPS = 2
MAX_STORAGE_STOPS = 2
MAX_DISTANCE = 25

CONTRACT_CAPACITY = 2400

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

def calculate_effective_space(order):
    catalog = Catalogs.query.filter_by(CatalogName=order["cataName"]).first()
    space_eq = catalog.SpaceEquivalent if catalog else 1
    num_factor = catalog.Num if catalog else 0
    weight = float(order["weight"])
    quantity = int(order.get("quantity", 1))
    return quantity * weight * space_eq + quantity * num_factor

def split_orders_by_capacity(orders, max_capacity):
    chunks = []
    current_chunk = []
    current_load = 0.0

    for order in sorted(orders, key=lambda o: calculate_effective_space(o), reverse=True):
        eff_space = calculate_effective_space(order)
        quantity = int(order.get("quantity", 1))

        if quantity > 1 and eff_space > max_capacity:
            catalog = Catalogs.query.filter_by(CatalogName=order["cataName"]).first()
            space_eq = catalog.SpaceEquivalent if catalog else 1
            num_factor = catalog.Num if catalog else 0
            weight_per_unit = float(order["weight"]) / quantity
            remaining_quantity = quantity

            # calculate per unit effective space
            unit_eff = weight_per_unit * space_eq + num_factor
            if unit_eff > max_capacity:
                raise ValueError(f"Single unit exceeds max capacity: {unit_eff} > {max_capacity}")

            # find max units that fit in one truck
            max_units_fit = int(max_capacity / unit_eff)

            while remaining_quantity > 0:
                fit_quantity = min(remaining_quantity, max_units_fit)
                partial_order = order.copy()
                partial_order["quantity"] = fit_quantity
                partial_order["weight"] = weight_per_unit * fit_quantity
                chunks.append([partial_order])
                remaining_quantity -= fit_quantity

        else:
            if current_load + eff_space <= max_capacity:
                current_chunk.append(order)
                current_load += eff_space
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = [order]
                current_load = eff_space

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def assign_trucks(orders):
    try:
        contract = Vehicles.query.filter_by(VehicleContract=True).order_by(Vehicles.VehicleID).limit(2).all()
        others = Vehicles.query.filter_by(VehicleContract=False).all()
        vehicles = contract + others

        customer_orders = defaultdict(list)
        for order in orders:
            customer_orders[order["CustomerID"]].append(order)

        customer_spaces = []
        for cid, cust_orders in customer_orders.items():
            split_batches = split_orders_by_capacity(cust_orders, 8000)
            for batch in split_batches:
                customer_spaces.append({
                    "CustomerID": cid,
                    "orders": batch,
                    "total_effective_space": sum(calculate_effective_space(o) for o in batch)
                })

        customer_spaces.sort(key=lambda x: x["total_effective_space"], reverse=True)

        assigned_customers = set()
        vehicle_assignments = []
        contract_vehicles_used = []

        def allocate_vehicle(is_contract):
            if is_contract and len(contract_vehicles_used) < len(contract):
                return contract[len(contract_vehicles_used)]
            else:
                veh = Vehicles(
                    VehicleID=generate_unique_vehicle_id(),
                    VehicleType="",
                    VehicleCapacity=0.0,
                    VehicleCurrentLoad=0.0,
                    VehicleLat=10.766590089230672,
                    VehicleLong=106.60678703538484,
                    VehicleContract=False
                )
                db.session.add(veh)
                db.session.flush()
                return veh

        def assign_group(group):
            group_orders = [o for cust in group for o in cust["orders"]]
            storage_ids = list({order["StorageID"] for order in group_orders})[:MAX_STORAGE_STOPS]

            total_effective_space = sum(calculate_effective_space(o) for o in group_orders)
            is_contract = len(contract_vehicles_used) < len(contract) and total_effective_space <= CONTRACT_CAPACITY

            if is_contract:
                vtype, vcap = "truck", CONTRACT_CAPACITY
            elif total_effective_space < 80:
                vtype, vcap = "two-wheeler", 80
            elif total_effective_space <= 800:
                vtype, vcap = "van", 800
            else:
                vtype, vcap = "truck", next((s for s in TRUCK_SIZES if total_effective_space <= s), TRUCK_SIZES[-1])

            veh = allocate_vehicle(is_contract)
            veh.VehicleType = vtype
            veh.VehicleCapacity = vcap
            veh.VehicleCurrentLoad = total_effective_space

            if is_contract:
                contract_vehicles_used.append(veh)

            grouped = defaultdict(float)
            for o in group_orders:
                grouped[(o["CustomerID"], o["StorageID"])] += calculate_effective_space(o)
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
                    "loadWeight": c["total_effective_space"]
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
                "currentLoad": total_effective_space,
                "assignedCustomers": assigned_list,
                "route": route,
                "storages": storage_data,
                "customers": customer_data
            })

        unassigned = customer_spaces.copy()
        while unassigned:
            main_cust = unassigned[0]
            group = [main_cust]
            unassigned = unassigned[1:]
            main_lat, main_lng = get_customer_location(main_cust["CustomerID"])

            new_unassigned = []
            for other in unassigned:
                if len(group) >= MAX_CUSTOMER_STOPS:
                    new_unassigned.append(other)
                    continue
                other_lat, other_lng = get_customer_location(other["CustomerID"])
                if main_lat is None or other_lat is None:
                    new_unassigned.append(other)
                    continue
                if haversine(main_lat, main_lng, other_lat, other_lng) <= MAX_DISTANCE:
                    group.append(other)
                else:
                    new_unassigned.append(other)

            group_total_space = sum(c["total_effective_space"] for c in group)
            if group_total_space > 8000:
                for single_cust in group:
                    assign_group([single_cust])
            else:
                assign_group(group)
                
            unassigned = new_unassigned

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