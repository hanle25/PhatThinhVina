import math
import random
import traceback
import uuid
from collections import defaultdict

from flask import Blueprint, request, jsonify, make_response

from .models import db, Customers, Storages, Catalogs, Vehicles, VehicleCustomer

bp = Blueprint("api", __name__)

# ---------------------------
# Config
# ---------------------------
TRUCK_SIZES = [1500, 2400, 3500, 4000, 5000, 6000, 7000, 8000, 15000]
MAX_TRUCK_CAPACITY = max(TRUCK_SIZES)
CONTRACT_CAPACITY = 2400
MAX_CUSTOMER_STOPS = 2
MAX_STORAGE_STOPS = 2
MAX_DISTANCE = 15


# ---------------------------
# Geo helpers
# ---------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ, Δλ = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def generate_unique_vehicle_id():
    return f"V{uuid.uuid4().hex[:5].upper()}"


def get_customer_location(customer_id):
    cust = Customers.query.get(customer_id)
    return (cust.CustomerLat, cust.CustomerLong) if cust else (None, None)


def get_customer_name(customer_id):
    cust = Customers.query.get(customer_id)
    return str(cust.CustomerName) if cust else ""


# ---------------------------
# Storage choice optimization
# ---------------------------
def optimize_storage_from_options(storage_options, customer_lat, customer_lng):
    """
    Choose the best storage from multiple options (e.g., "S001/S002") based on distance to customer.
    """
    if not storage_options:
        return None

    # Split storage options if multiple are provided (e.g., "S001/S002")
    storage_ids = storage_options.split('/')
    
    if len(storage_ids) == 1:
        # Single storage option, return as is
        return storage_ids[0]
    
    # Multiple storage options, find the closest one to the customer
    if customer_lat is not None and customer_lng is not None:
        closest_storage = None
        min_distance = float('inf')
        
        for storage_id in storage_ids:
            storage = Storages.query.get(storage_id.strip())
            if storage:
                distance = haversine(customer_lat, customer_lng, storage.StorageLat, storage.StorageLong)
                if distance < min_distance:
                    min_distance = distance
                    closest_storage = storage
        
        if closest_storage:
            print(f"DEBUG: Selected closest storage {closest_storage.StorageName} from options {storage_options} (distance: {min_distance:.2f} km)")
            return closest_storage.StorageID
    
    # Fallback to first option if no location data
    return storage_ids[0].strip()


def optimize_storage_for_group(group_orders, group_customers):
    """
    Optimize storage selection for a group of customers to minimize total route distance.
    """
    # Get all customer locations in the group
    customer_locations = {}
    for customer_id in group_customers:
        lat, lng = get_customer_location(customer_id)
        if lat is not None and lng is not None:
            customer_locations[customer_id] = (lat, lng)
    
    optimized_orders = []
    for order in group_orders:
        optimized_order = order.copy()
        
        # If order has storage options, optimize for the group
        if order.get("StorageID"):
            storage_options = order["StorageID"]
            storage_ids = storage_options.split('/')
            
            if len(storage_ids) > 1:
                # Multiple storage options, find the best one for the group
                best_storage = None
                best_total_distance = float('inf')
                
                for storage_id in storage_ids:
                    storage = Storages.query.get(storage_id.strip())
                    if storage:
                        total_distance = 0
                        for customer_id, (lat, lng) in customer_locations.items():
                            distance = haversine(lat, lng, storage.StorageLat, storage.StorageLong)
                            total_distance += distance
                        
                        if total_distance < best_total_distance:
                            best_total_distance = total_distance
                            best_storage = storage
                
                if best_storage:
                    optimized_order["StorageID"] = best_storage.StorageID
                    print(f"DEBUG: Group-optimized storage for order: {best_storage.StorageName} (total group distance: {best_total_distance:.2f} km)")
        
        optimized_orders.append(optimized_order)
    
    return optimized_orders


# ---------------------------
# Effective-space math
# ---------------------------
def unit_eff(order):
    """
    Per-unit effective space (kg-equivalent).
    Assumes order['weight'] is PER-UNIT weight.
    """
    cat = Catalogs.query.filter_by(CatalogName=order["cataName"]).first()
    se = float(cat.SpaceEquivalent) if cat else 1.0
    num = float(cat.Num) if cat else 0.0
    ue = float(order["weight"]) * se + num
    return ue

def calculate_effective_space(order):
    """
    Line effective space = quantity * per-unit effective space.
    """
    qty = int(order.get("quantity", 1))
    ue = unit_eff(order)
    result = qty * ue
    print(f"DEBUG: calculate_effective_space: qty:{qty}, per_unit_weight:{order.get('weight')}, unit_eff:{ue}, result:{result}")
    return result


def split_orders_by_capacity(orders, max_capacity):
    """
    Split orders into batches so each batch <= max_capacity (kg-eq).
    Uses per-unit effective space and splits ONLY by quantity.
    Keeps order['weight'] as PER-UNIT (never divides/multiplies it).
    """
    chunks = []
    current_chunk, current_load = [], 0.0

    # Pack biggest lines first
    for o in sorted(orders, key=calculate_effective_space, reverse=True):
        qty = int(o.get("quantity", 1))
        ue = unit_eff(o)            # per-unit eff
        total = qty * ue            # line eff

        if qty > 1 and total > max_capacity:
            # how many units of THIS item fit in one truck?
            max_units_fit = int(max_capacity // ue)
            if max_units_fit <= 0:
                raise ValueError(f"Single unit exceeds capacity: {ue} > {max_capacity}")

            remaining = qty
            while remaining > 0:
                take = min(remaining, max_units_fit)
                part = o.copy()
                part["quantity"] = take
                # IMPORTANT: keep weight as PER-UNIT; do NOT scale it
                # part["weight"] stays the same as original per-unit
                partial_total = take * ue
                print(f"DEBUG: Split part -> {part.get('cataName')} qty:{take} unit_eff:{ue} total_eff:{partial_total}")
                chunks.append([part])   # one batch for this slice
                remaining -= take

        else:
            if total > max_capacity:
                raise ValueError(
                    f"Order for customer {o.get('CustomerID')} exceeds truck capacity: "
                    f"{total} > {max_capacity}. Please split the order into smaller quantities."
                )

            if current_load + total <= max_capacity:
                current_chunk.append(o)
                current_load += total
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk, current_load = [o], total

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def pack_orders_into_trucks(orders, max_capacity):
    """
    First-Fit Decreasing bin packing that guarantees each batch total <= max_capacity.
    Assumes each individual order's effective space <= max_capacity (caller must ensure).
    """
    sorted_orders = sorted(orders, key=lambda o: calculate_effective_space(o), reverse=True)
    batches = []
    batch_loads = []

    for order in sorted_orders:
        eff_space = calculate_effective_space(order)
        if eff_space > max_capacity:
            raise ValueError(
                f"Order for customer {order.get('CustomerID')} exceeds truck capacity: "
                f"{eff_space} > {max_capacity}. Please split the order into smaller quantities."
            )
        placed = False
        for i in range(len(batches)):
            if batch_loads[i] + eff_space <= max_capacity:
                batches[i].append(order)
                batch_loads[i] += eff_space
                placed = True
                break
        if not placed:
            batches.append([order])
            batch_loads.append(eff_space)

    return batches

# ---------------------------
# Core assignment
# ---------------------------
def assign_trucks(orders):
    try:
        contract = Vehicles.query.filter_by(VehicleContract=True).order_by(Vehicles.VehicleID).limit(2).all()
        others = Vehicles.query.filter_by(VehicleContract=False).all()
        vehicles = contract + others

        # Separate customer orders from storage transfers
        customer_orders = defaultdict(list)
        storage_transfers = []
        
        for order in orders:
            if order["CustomerID"] == "TRANSFER":
                storage_transfers.append(order)
            else:
                customer_orders[order["CustomerID"]].append(order)

        customer_spaces = []
        for cid, cust_orders in customer_orders.items():
            # Get customer location for storage optimization
            customer_lat, customer_lng = get_customer_location(cid)
            
            # Optimize storage selection for each order
            optimized_orders = []
            for order in cust_orders:
                optimized_order = order.copy()
                
                # For regular orders, optimize storage selection
                if optimized_order.get("StorageID"):
                    optimized_storage = optimize_storage_from_options(optimized_order["StorageID"], customer_lat, customer_lng)
                    if optimized_storage:
                        optimized_order["StorageID"] = optimized_storage
                
                optimized_orders.append(optimized_order)
            
            # Pre-split large-quantity lines, then bin-pack to guarantee batches <= capacity
            print(f"DEBUG: Processing customer {cid} with {len(optimized_orders)} orders")
            for i, order in enumerate(optimized_orders):
                eff_space = calculate_effective_space(order)
                print(f"DEBUG: Order {i}: {order.get('cataName')} - qty:{order.get('quantity', 1)} - eff_space:{eff_space}")
            
            pre_chunks = split_orders_by_capacity(optimized_orders, MAX_TRUCK_CAPACITY)
            print(f"DEBUG: After splitting: {len(pre_chunks)} chunks")
            for i, chunk in enumerate(pre_chunks):
                chunk_total = sum(calculate_effective_space(o) for o in chunk)
                print(f"DEBUG: Chunk {i}: {len(chunk)} orders, total: {chunk_total}")
            
            flattened = [o for ch in pre_chunks for o in ch]
            print(f"DEBUG: Flattened: {len(flattened)} orders")
            for i, order in enumerate(flattened):
                eff_space = calculate_effective_space(order)
                print(f"DEBUG: Flattened order {i}: eff_space:{eff_space}")
            
            bin_packed_batches = pack_orders_into_trucks(flattened, MAX_TRUCK_CAPACITY)
            for batch in bin_packed_batches:
                batch_total = sum(calculate_effective_space(o) for o in batch)
                customer_spaces.append({
                    "CustomerID": cid,
                    "orders": batch,
                    "total_effective_space": batch_total
                })
        
        # Process storage transfers separately
        if storage_transfers:
            print(f"DEBUG: Processing {len(storage_transfers)} storage transfers")
            for transfer in storage_transfers:
                customer_spaces.append({
                    "CustomerID": "TRANSFER",
                    "orders": [transfer],
                    "total_effective_space": calculate_effective_space(transfer)
                })

        customer_spaces.sort(key=lambda x: x["total_effective_space"], reverse=True)
        
        # Debug: Print customer spaces for debugging
        print(f"DEBUG: Total customer spaces: {len(customer_spaces)}")
        for i, cs in enumerate(customer_spaces):
            print(f"DEBUG: Customer space {i}: CustomerID={cs['CustomerID']}, TotalSpace={cs['total_effective_space']}")

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
            # Combine all orders from the group
            all_orders = []
            group_customers = []
            for group_member in group:
                all_orders.extend(group_member["orders"])
                group_customers.append(group_member["CustomerID"])
            
            # Optimize storage selection for the entire group
            optimized_orders = optimize_storage_for_group(all_orders, group_customers)
            
            # Split then bin-pack to ensure batches never exceed capacity
            pre_chunks = split_orders_by_capacity(optimized_orders, MAX_TRUCK_CAPACITY)
            flat_orders = [o for ch in pre_chunks for o in ch]
            batches = pack_orders_into_trucks(flat_orders, MAX_TRUCK_CAPACITY)
            
            for batch_orders in batches:
                storage_ids = list({order["StorageID"] for order in batch_orders})[:MAX_STORAGE_STOPS]

                total_effective_space = sum(calculate_effective_space(o) for o in batch_orders)
                is_contract = len(contract_vehicles_used) < len(contract) and total_effective_space <= CONTRACT_CAPACITY

                # Since batches are bin-packed, they should never exceed capacity
                if total_effective_space > MAX_TRUCK_CAPACITY:
                    print(f"DEBUG: ASSERTION - bin-packed batch over capacity: {total_effective_space}")
                    # As a last resort, pack this batch alone again
                    for sub_batch in pack_orders_into_trucks(batch_orders, MAX_TRUCK_CAPACITY):
                        # Re-enqueue each sub_batch by recursively handling via assign_group logic
                        # Build a temporary group of one with these orders
                        temp_group_member = {"CustomerID": group_customers[0], "orders": sub_batch}
                        assign_group([temp_group_member])
                    continue

                # Normal vehicle assignment for batches that fit within capacity
                if is_contract:
                    vtype, vcap = "truck", CONTRACT_CAPACITY
                elif total_effective_space < 80:
                    vtype, vcap = "two-wheeler", 80
                elif total_effective_space <= 800:
                    vtype, vcap = "van", 800
                else:
                    # Find the smallest truck that can handle this load
                    suitable_truck = next((s for s in TRUCK_SIZES if total_effective_space <= s), None)
                    if suitable_truck:
                        vtype, vcap = "truck", suitable_truck
                    else:
                        vtype, vcap = "truck", MAX_TRUCK_CAPACITY

                veh = allocate_vehicle(is_contract)
                veh.VehicleType = vtype
                veh.VehicleCapacity = vcap
                veh.VehicleCurrentLoad = total_effective_space
                
                # Safety check: ensure load doesn't exceed capacity
                if total_effective_space > vcap:
                    raise ValueError(f"Load {total_effective_space}kg exceeds vehicle capacity {vcap}kg. This should not happen.")

                if is_contract:
                    contract_vehicles_used.append(veh)

                # Aggregate weights by (customer, storage) within this batch
                grouped = defaultdict(float)
                for o in batch_orders:
                    grouped[(o["CustomerID"], o.get("StorageID"))] += calculate_effective_space(o)

                # Write VehicleCustomer (skip transfers entirely)
                for (cid, sid), weight in grouped.items():
                    if cid == "TRANSFER":
                        continue
                    existing = VehicleCustomer.query.filter_by(
                        VehicleID=veh.VehicleID, CustomerID=cid, StorageID=sid
                    ).first()
                    if existing:
                        existing.LoadWeight += weight
                    else:
                        db.session.add(VehicleCustomer(
                            VehicleID=veh.VehicleID, CustomerID=cid, StorageID=sid, LoadWeight=weight
                        ))

                # ---- Build payloads
                # Customers (non-transfer)
                batch_customer_totals = defaultdict(float)
                for o in batch_orders:
                    if o["CustomerID"] != "TRANSFER":
                        batch_customer_totals[o["CustomerID"]] += calculate_effective_space(o)

                assigned_list = [
                    {"CustomerID": cid, "customerName": get_customer_name(cid), "loadWeight": wt}
                    for cid, wt in batch_customer_totals.items()
                ]

                # Transfers: aggregate by (From -> To)
                transfer_pairs = defaultdict(float)  # (from_sid, to_sid) -> eff load
                for o in batch_orders:
                    if o["CustomerID"] == "TRANSFER":
                        # For storage transfers, we need to handle the route properly
                        # The transfer should pick up from source storage and deliver to destination storage
                        # Frontend sends: StorageID (source) and toStorage (destination)
                        # UI: First dropdown = destination, Second dropdown = source
                        frm = o.get("StorageID")  # Source storage (where to pick up FROM)
                        to  = o.get("toStorage")  # Destination storage (where to deliver TO)
                        transfer_pairs[(frm, to)] += calculate_effective_space(o)

                # Add transfers as pseudo-customers with clear label
                for (frm, to), wt in transfer_pairs.items():
                    s_from = Storages.query.get(frm) if frm else None
                    s_to   = Storages.query.get(to)  if to  else None
                    assigned_list.append({
                        "CustomerID": f"T{random.randint(10000, 99999)}",
                        "customerName": f"Relocate {s_from.StorageName if s_from else frm} → {s_to.StorageName if s_to else to}",
                        "loadWeight": wt
                    })

                # ---- Route
                route = [["start", float(veh.VehicleLat), float(veh.VehicleLong)]]
                storage_data, customer_data = [], []

                # Only normal (non-transfer) storages for legacy stops
                normal_storage_ids = list({
                    o.get("StorageID") for o in batch_orders
                    if o["CustomerID"] != "TRANSFER" and o.get("StorageID")
                })[:MAX_STORAGE_STOPS]

                # 1) Pickups for transfers (From) - truck picks up products
                from_set = {p[0] for p in transfer_pairs.keys() if p[0]}
                for sid in from_set:
                    s = Storages.query.get(sid)
                    if s:
                        storage_data.append({"id": sid, "name": s.StorageName})
                        route.append(["storage", sid, s.StorageLat, s.StorageLong])

                # 2) Drops for transfers (To) - deliver to destination storage
                to_set = {p[1] for p in transfer_pairs.keys() if p[1]}
                for sid in to_set:
                    s = Storages.query.get(sid)
                    if s:
                        storage_data.append({"id": sid, "name": s.StorageName})
                        route.append(["customer", sid, s.StorageLat, s.StorageLong])

                # 3) Any storages from normal orders
                for sid in normal_storage_ids:
                    s = Storages.query.get(sid)
                    if s:
                        storage_data.append({"id": sid, "name": s.StorageName})
                        route.append(["storage", sid, s.StorageLat, s.StorageLong])

                # 4) Customers (non-transfer)
                for cid in batch_customer_totals.keys():
                    cust = Customers.query.get(cid)
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
            
            print(f"DEBUG: Processing main customer: {main_cust['CustomerID']} with {main_cust['total_effective_space']} space")
            
            # Try to find a nearby customer to group with
            best_match = None
            best_distance = float('inf')
            
            for i, other in enumerate(unassigned):
                if len(group) >= MAX_CUSTOMER_STOPS:
                    break
                    
                other_lat, other_lng = get_customer_location(other["CustomerID"])
                if main_lat is None or other_lat is None:
                    continue
                    
                distance = haversine(main_lat, main_lng, other_lat, other_lng)
                print(f"DEBUG: Distance from {main_cust['CustomerID']} to {other['CustomerID']}: {distance} km")
                
                if distance <= MAX_DISTANCE:
                    # Check if adding this customer would exceed truck capacity
                    potential_total = main_cust["total_effective_space"] + other["total_effective_space"]
                    if potential_total <= MAX_TRUCK_CAPACITY:  # Use max truck capacity for grouping check
                        if distance < best_distance:
                            best_distance = distance
                            best_match = (i, other)
            
            # Add the best match to the group if found
            if best_match:
                match_idx, match_cust = best_match
                group.append(match_cust)
                unassigned.pop(match_idx)
                print(f"DEBUG: Added {match_cust['CustomerID']} to group (distance: {best_distance} km)")
            
            # Process the group
            if len(group) > 1:
                print(f"DEBUG: Final group size: {len(group)}, customers: {[g['CustomerID'] for g in group]}")
            else:
                print(f"DEBUG: Single customer group: {group[0]['CustomerID']}")
            
            assign_group(group)

        db.session.commit()
        return vehicle_assignments

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        raise e


# ---------------------------
# Routes
# ---------------------------
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