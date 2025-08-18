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

def is_on_the_way(storage_coord, candidate_coord, main_coord, max_ratio=1.25):
    """
    True if going storage -> candidate -> main is within 25% detour vs storage -> main.
    Uses actual storage coordinates from user-selected storage(s).
    """
    if None in storage_coord or None in candidate_coord or None in main_coord:
        return False
    direct = haversine(*storage_coord, *main_coord)
    if direct <= 0:
        return False
    via = haversine(*storage_coord, *candidate_coord) + haversine(*candidate_coord, *main_coord)
    return via <= direct * max_ratio

def pick_storage_coord_for(customer_space):
    """
    Pick the main batch's storage coordinate based on the actual StorageID(s)
    present in the batch orders (user input after optimization/packing).
    Uses the most frequent StorageID in this batch.
    Returns (lat, lng) or (None, None) if unavailable.
    """
    storage_ids = [o.get("StorageID") for o in customer_space.get("orders", []) if o.get("StorageID")]
    if not storage_ids:
        return (None, None)
    # Most frequent storage id in this batch
    sid = max(storage_ids, key=storage_ids.count)
    s = Storages.query.get(sid)
    return (s.StorageLat, s.StorageLong) if s else (None, None)

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
        
        # Build a global pool of storage transfers to opportunistically co-load onto trucks
        transfers_pool = defaultdict(float)
        if storage_transfers:
            print(f"DEBUG: Processing {len(storage_transfers)} storage transfers")
            for transfer in storage_transfers:
                frm = transfer.get("StorageID")
                to = transfer.get("toStorage")
                if frm and to:
                    transfers_pool[(frm, to)] += calculate_effective_space(transfer)

        customer_spaces.sort(key=lambda x: x["total_effective_space"], reverse=True)
        
        # Debug: Print customer spaces for debugging
        print(f"DEBUG: Total customer spaces: {len(customer_spaces)}")
        for i, cs in enumerate(customer_spaces):
            print(f"DEBUG: Customer space {i}: CustomerID={cs['CustomerID']}, TotalSpace={cs['total_effective_space']}")

        assigned_customers = set()
        vehicle_assignments = []
        contract_vehicles_used = []
        fifteen_ton_truck_used = False

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
            nonlocal fifteen_ton_truck_used  # Flag for single 15-ton truck rule

            all_orders = []
            group_customers = []
            for group_member in group:
                all_orders.extend(group_member["orders"])
                group_customers.append(group_member["CustomerID"])

            optimized_orders = optimize_storage_for_group(all_orders, group_customers)
            pre_chunks = split_orders_by_capacity(optimized_orders, MAX_TRUCK_CAPACITY)
            flat_orders = [o for ch in pre_chunks for o in ch]
            batches = pack_orders_into_trucks(flat_orders, MAX_TRUCK_CAPACITY)

            for batch_orders in batches:
                storage_ids = list({order["StorageID"] for order in batch_orders})[:MAX_STORAGE_STOPS]
                total_effective_space = sum(calculate_effective_space(o) for o in batch_orders)

                # If this batch serves a small number of customers (< 4) but the
                # combined load exceeds 2.4t, try to split into at most two
                # 2.4t contract trucks to optimize delivery cost (use contract first).
                unique_non_transfer_customers = {
                    o.get("CustomerID") for o in batch_orders if o.get("CustomerID") != "TRANSFER"
                }
                num_customers_in_batch = len([cid for cid in unique_non_transfer_customers if cid])
                if (
                    num_customers_in_batch > 0
                    and num_customers_in_batch < 4
                    and total_effective_space > CONTRACT_CAPACITY
                    and len(contract_vehicles_used) < len(contract)
                ):
                    # Prepare orders such that every line can fit into 2.4t, then pack
                    # with a bin packer targeting 2.4t capacity per truck.
                    pre_24_chunks = split_orders_by_capacity(batch_orders, CONTRACT_CAPACITY)
                    flat_24_orders = [o for ch in pre_24_chunks for o in ch]
                    two_packed = pack_orders_into_trucks(flat_24_orders, CONTRACT_CAPACITY)

                    # Only apply this optimization if we can satisfy with <= 2 contract trucks
                    # and we have enough contract vehicles available.
                    if 1 < len(two_packed) <= 2 and (len(contract_vehicles_used) + len(two_packed) <= len(contract)):
                        def batch_mixes_cuchi_brenntag(sub):
                            sub_sids = {o.get("StorageID") for o in sub if o.get("StorageID")}
                            sub_to_sids = {o.get("toStorage") for o in sub if o.get("toStorage")}
                            all_ids = (sub_sids | sub_to_sids)
                            return ("S00002" in all_ids) and ("S00003" in all_ids)

                        # If any sub-batch mixes Cu Chi and Brenntag, schedule it first so
                        # it uses the first contract truck; otherwise order doesn't matter.
                        ordered_subs = sorted(two_packed, key=lambda b: 0 if batch_mixes_cuchi_brenntag(b) else 1)

                        for sub in ordered_subs:
                            temp_group_member = {"CustomerID": next(iter(unique_non_transfer_customers)), "orders": sub}
                            assign_group([temp_group_member])
                        continue

                co_loaded_entries = []  # (from_sid, to_sid, weight) co-loaded onto this vehicle

                # Check if both Cu Chi (S00002) and BRENNTAG (S00003) storages are needed
                must_use_first_contract_truck = "S00002" in storage_ids and "S00003" in storage_ids

                use_contract_truck = len(contract_vehicles_used) < len(contract) and total_effective_space <= CONTRACT_CAPACITY
                # Only use contract truck if load fits within contract capacity
                is_contract = (must_use_first_contract_truck and total_effective_space <= CONTRACT_CAPACITY) or use_contract_truck

                if total_effective_space > MAX_TRUCK_CAPACITY:
                    for sub_batch in pack_orders_into_trucks(batch_orders, MAX_TRUCK_CAPACITY):
                        temp_group_member = {"CustomerID": group_customers[0], "orders": sub_batch}
                        assign_group([temp_group_member])
                    continue

                # Mixed storage restriction (pickups + transfer drop-offs):
                # Only the first contract truck (e.g., V00001) may run a route that touches
                # both Cu Chi (S00002) and Brenntag (S00003), whether as pickups or transfer
                # drop-offs. Others must be split so no single route visits both.
                all_visited_ids = set(storage_ids)
                for o in batch_orders:
                    if o.get("toStorage"):
                        all_visited_ids.add(o.get("toStorage"))
                if ("S00002" in all_visited_ids and "S00003" in all_visited_ids):
                    allow_mixed = is_contract and (len(contract_vehicles_used) == 0)
                    if not allow_mixed:
                        s2_orders = [
                            o for o in batch_orders
                            if o.get("StorageID") == "S00002" or o.get("toStorage") == "S00002"
                        ]
                        s3_orders = [
                            o for o in batch_orders
                            if o.get("StorageID") == "S00003" or o.get("toStorage") == "S00003"
                        ]
                        remainder = [
                            o for o in batch_orders
                            if not (
                                (o.get("StorageID") in {"S00002", "S00003"}) or
                                (o.get("toStorage") in {"S00002", "S00003"})
                            )
                        ]
                        for sub in (s2_orders, s3_orders, remainder):
                            if sub:
                                temp_group_member = {"CustomerID": group_customers[0], "orders": sub}
                                assign_group([temp_group_member])
                        continue

                if is_contract:
                    vtype, vcap = "truck", CONTRACT_CAPACITY
                elif total_effective_space < 100:
                    vtype, vcap = "two-wheeler", 100
                elif total_effective_space <= 1000:
                    vtype, vcap = "van", 1000
                else:
                    suitable_truck = next((s for s in TRUCK_SIZES if total_effective_space <= s), None)

                    if suitable_truck == 15000:
                        if fifteen_ton_truck_used:
                            # If 15-ton truck already used, we need to split this load
                            # The load is too large for smaller trucks, so we'll split it
                            print(f"DEBUG: 15-ton truck already used, splitting load of {total_effective_space}kg")
                            # Split this batch into smaller chunks that can fit in smaller trucks
                            for sub_batch in pack_orders_into_trucks(batch_orders, 8000):  # Use 8-ton truck as max
                                temp_group_member = {"CustomerID": group_customers[0], "orders": sub_batch}
                                assign_group([temp_group_member])
                            continue  # Skip the rest of this batch since we've split it
                        else:
                            # Enforce: 15-ton truck must stop at only ONE customer
                            unique_customers = [
                                cid for cid in {o.get("CustomerID") for o in batch_orders if o.get("CustomerID") != "TRANSFER"}
                                if cid
                            ]
                            if len(unique_customers) > 1:
                                print("DEBUG: 15-ton requires single customer; splitting by customer")
                                for cid in unique_customers:
                                    sub = [o for o in batch_orders if o.get("CustomerID") == cid]
                                    if sub:
                                        assign_group([{"CustomerID": cid, "orders": sub}])
                                continue
                            fifteen_ton_truck_used = True

                    vtype, vcap = "truck", suitable_truck or MAX_TRUCK_CAPACITY

                # If non-contract, remove any TRANSFER orders from this batch and reassign them
                # so that only contract trucks handle relocation products.
                if not is_contract:
                    transfer_only = [o for o in batch_orders if o.get("CustomerID") == "TRANSFER"]
                    if transfer_only:
                        non_transfer_only = [o for o in batch_orders if o.get("CustomerID") != "TRANSFER"]
                        if transfer_only:
                            temp_group_member = {"CustomerID": group_customers[0], "orders": transfer_only}
                            assign_group([temp_group_member])
                        batch_orders = non_transfer_only
                        storage_ids = list({o.get("StorageID") for o in batch_orders if o.get("StorageID")})[:MAX_STORAGE_STOPS]
                        total_effective_space = sum(calculate_effective_space(o) for o in batch_orders)
                        if not batch_orders:
                            continue

                # Attempt to co-load transfers whose pickup or destination storage is already
                # in this batch's normal pickup storages, within remaining capacity. While
                # doing so, enforce the mixed-route restriction: if co-loading would cause
                # this non-first-contract vehicle to visit both Cu Chi and Brenntag, skip it.
                tmp_transfer_pairs = defaultdict(float)
                if is_contract:
                    # 1) Transfers explicitly present in this batch
                    for o in batch_orders:
                        if o["CustomerID"] == "TRANSFER":
                            frm = o.get("StorageID"); to = o.get("toStorage")
                            tmp_transfer_pairs[(frm, to)] += calculate_effective_space(o)

                normal_storage_ids = list({
                    o.get("StorageID") for o in batch_orders
                    if o["CustomerID"] != "TRANSFER" and o.get("StorageID")
                })[:MAX_STORAGE_STOPS]

                # Track storages already implied by this batch before co-loading
                visited_now = set(normal_storage_ids)
                for o in batch_orders:
                    to_sid = o.get("toStorage")
                    if to_sid:
                        visited_now.add(to_sid)

                available_capacity = max(0.0, (vcap or 0) - total_effective_space)

                # 2) First, consider transfers present in this batch (respect mixing rule)
                if is_contract:
                    for (frm, to), wt in list(tmp_transfer_pairs.items()):
                        if not (frm and to):
                            continue
                        if not ((frm in normal_storage_ids) or (to in normal_storage_ids)):
                            continue
                        prospective = set(visited_now) | {frm, to}
                        would_mix = ("S00002" in prospective and "S00003" in prospective)
                        allow_mixed = is_contract and (len(contract_vehicles_used) == 0)
                        if would_mix and not allow_mixed:
                            continue
                        if wt <= available_capacity:
                            co_loaded_entries.append((frm, to, wt))
                            visited_now |= {frm, to}
                            available_capacity -= wt
                            total_effective_space += wt
                            if (frm, to) in transfers_pool:
                                transfers_pool[(frm, to)] = max(0.0, transfers_pool[(frm, to)] - wt)

                # 3) Next, opportunistically co-load from the global pool (respect mixing rule)
                if is_contract:
                    for (frm, to), pool_wt in list(transfers_pool.items()):
                        if pool_wt <= 0:
                            continue
                        if not ((frm in normal_storage_ids) or (to in normal_storage_ids)):
                            continue
                        prospective = set(visited_now) | {frm, to}
                        would_mix = ("S00002" in prospective and "S00003" in prospective)
                        allow_mixed = is_contract and (len(contract_vehicles_used) == 0)
                        if would_mix and not allow_mixed:
                            continue
                        if pool_wt <= available_capacity:
                            co_loaded_entries.append((frm, to, pool_wt))
                            visited_now |= {frm, to}
                            available_capacity -= pool_wt
                            total_effective_space += pool_wt
                            transfers_pool[(frm, to)] = 0.0

                # 4) First contract: absorb at most remaining customer slots, prioritizing
                #    tiny Brenntag-only batches so we don't exceed MAX_CUSTOMER_STOPS.
                if is_contract and (len(contract_vehicles_used) == 0) and available_capacity > 0:
                    storages_we_visit = set(visited_now)
                    # Determine remaining customer slots
                    current_customers = {o.get("CustomerID") for o in batch_orders if o.get("CustomerID") != "TRANSFER"}
                    remaining_slots = max(0, MAX_CUSTOMER_STOPS - len(current_customers))
                    if remaining_slots > 0:
                        candidates = []
                        for idx, other in enumerate(list(unassigned)):
                            if other.get("CustomerID") == "TRANSFER":
                                continue
                            other_sids = {o.get("StorageID") for o in other.get("orders", []) if o.get("StorageID")}
                            if not other_sids:
                                continue
                            if not other_sids.issubset(storages_we_visit):
                                continue
                            wt = other.get("total_effective_space", 0.0)
                            prefer_brenntag = ("S00003" in other_sids) and ("S00003" in storages_we_visit)
                            candidates.append((idx, other, other_sids, wt, prefer_brenntag))

                        # Sort: prefer Brenntag candidates first, then by smallest weight
                        candidates.sort(key=lambda x: (0 if x[4] else 1, x[3]))

                        extras_to_remove = []
                        for idx, other, other_sids, wt, _ in candidates:
                            if remaining_slots <= 0 or available_capacity <= 0:
                                break
                            if wt <= available_capacity:
                                # Attach this batch
                                batch_orders.extend(other["orders"]) 
                                available_capacity -= wt
                                total_effective_space += wt
                                extras_to_remove.append(idx)
                                current_customers.add(other.get("CustomerID"))
                                remaining_slots = max(0, MAX_CUSTOMER_STOPS - len(current_customers))

                        for idx in sorted(extras_to_remove, reverse=True):
                            unassigned.pop(idx)

                veh = allocate_vehicle(is_contract)
                veh.VehicleType = vtype
                veh.VehicleCapacity = vcap
                veh.VehicleCurrentLoad = total_effective_space

                if total_effective_space > vcap:
                    raise ValueError(f"Load {total_effective_space}kg exceeds vehicle capacity {vcap}kg.")

                if is_contract:
                    contract_vehicles_used.append(veh)

                grouped = defaultdict(float)
                for o in batch_orders:
                    grouped[(o["CustomerID"], o.get("StorageID"))] += calculate_effective_space(o)

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

                batch_customer_totals = defaultdict(float)
                for o in batch_orders:
                    if o["CustomerID"] != "TRANSFER":
                        batch_customer_totals[o["CustomerID"]] += calculate_effective_space(o)

                assigned_list = [
                    {"CustomerID": cid, "customerName": get_customer_name(cid), "loadWeight": wt}
                    for cid, wt in batch_customer_totals.items()
                ]

                transfer_pairs = defaultdict(float)
                for o in batch_orders:
                    if o["CustomerID"] == "TRANSFER":
                        frm = o.get("StorageID")
                        to  = o.get("toStorage")
                        transfer_pairs[(frm, to)] += calculate_effective_space(o)

                # Add any co-loaded transfers first so they are shown on this vehicle
                for (frm, to, wt) in co_loaded_entries:
                    s_from = Storages.query.get(frm) if frm else None
                    s_to   = Storages.query.get(to)  if to  else None
                    assigned_list.append({
                        "CustomerID": f"T{random.randint(10000, 99999)}",
                        "customerName": f"Relocate {s_from.StorageName if s_from else str(frm)} → {s_to.StorageName if s_to else str(to)}",
                        "loadWeight": wt
                    })
                    # Remove from remaining transfers so it's not duplicated
                    if (frm, to) in transfer_pairs:
                        transfer_pairs[(frm, to)] = max(0.0, transfer_pairs[(frm, to)] - wt)
                        if transfer_pairs[(frm, to)] == 0:
                            del transfer_pairs[(frm, to)]

                # Remaining transfers (not co-loaded) are listed as separate entries
                for (frm, to), wt in transfer_pairs.items():
                    s_from = Storages.query.get(frm) if frm else None
                    s_to   = Storages.query.get(to)  if to  else None
                    assigned_list.append({
                        "CustomerID": f"T{random.randint(10000, 99999)}",
                        "customerName": f"Relocate {s_from.StorageName if s_from else str(frm)} → {s_to.StorageName if s_to else str(to)}",
                        "loadWeight": wt
                    })

                route = [["start", float(veh.VehicleLat), float(veh.VehicleLong)]]
                storage_data, customer_data = [], []

                normal_storage_ids = list({
                    o.get("StorageID") for o in batch_orders
                    if o["CustomerID"] != "TRANSFER" and o.get("StorageID")
                })[:MAX_STORAGE_STOPS]

                # Deduplicate pickup storages so we don't add the same storage twice
                from_set = {p[0] for p in transfer_pairs.keys() if p[0]} | {frm for (frm, _, _) in co_loaded_entries}
                pickup_storages = set(normal_storage_ids) | set(from_set)
                for sid in pickup_storages:
                    s = Storages.query.get(sid)
                    if s:
                        storage_data.append({"id": sid, "name": s.StorageName})
                        route.append(["storage", sid, s.StorageLat, s.StorageLong])

                to_set = {p[1] for p in transfer_pairs.keys() if p[1]} | {to for (_, to, _) in co_loaded_entries}
                # Collect Phat Thinh (destination) entries to append last
                phat_thinh_drop_entries = []
                for sid in to_set:
                    s = Storages.query.get(sid)
                    if not s:
                        continue
                    storage_data.append({"id": sid, "name": s.StorageName})
                    entry = ["customer", sid, s.StorageLat, s.StorageLong]
                    if (s.StorageName or "").strip().upper() == "PHAT THINH":
                        phat_thinh_drop_entries.append(entry)
                    else:
                        route.append(entry)

                for cid in batch_customer_totals.keys():
                    cust = Customers.query.get(cid)
                    if cust:
                        customer_data.append({"id": cust.CustomerID, "name": cust.CustomerName})
                        route.append(["customer", cust.CustomerID, cust.CustomerLat, cust.CustomerLong])

                # Ensure drop-off to Phat Thinh storage is the last stop
                for entry in phat_thinh_drop_entries:
                    route.append(entry)

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
            main_coord = (main_lat, main_lng)

            # Use the actual storage coord based on this batch's chosen StorageID(s)
            storage_coord = pick_storage_coord_for(main_cust)
            
            print(f"DEBUG: Processing main customer: {main_cust['CustomerID']} with {main_cust['total_effective_space']} space")

            # Pass 1: try on-the-way matches (detour <= 25%)
            on_way_candidates = []
            for i, other in enumerate(unassigned):
                if len(group) >= MAX_CUSTOMER_STOPS:
                    break
                if other["CustomerID"] == "TRANSFER":
                    continue
                other_lat, other_lng = get_customer_location(other["CustomerID"])
                candidate_coord = (other_lat, other_lng)
                if is_on_the_way(storage_coord, candidate_coord, main_coord):
                    potential_total = main_cust["total_effective_space"] + other["total_effective_space"]
                    if potential_total <= MAX_TRUCK_CAPACITY:
                        on_way_candidates.append((i, other))

            if on_way_candidates:
                added_idxs = []
                for match_idx, match_cust in on_way_candidates[:max(0, MAX_CUSTOMER_STOPS - 1)]:
                    group.append(match_cust)
                    added_idxs.append(match_idx)
                    print(f"DEBUG: Added {match_cust['CustomerID']} as on-the-way")
                for idx in sorted(added_idxs, reverse=True):
                    unassigned.pop(idx)
            else:
                # Fallback: original nearest-by-distance
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
                        potential_total = main_cust["total_effective_space"] + other["total_effective_space"]
                        if potential_total <= MAX_TRUCK_CAPACITY:
                            if distance < best_distance:
                                best_distance = distance
                                best_match = (i, other)
                # Storage-aware boost: if no on-the-way chosen, try to add customers
                # whose dominant pickup storage matches the main batch's storage,
                # even if not the absolute nearest, as long as capacity allows.
                if not best_match and len(group) < MAX_CUSTOMER_STOPS:
                    main_sid = None
                    # Determine dominant storage for main batch
                    main_sids = [o.get("StorageID") for o in main_cust["orders"] if o.get("StorageID")]
                    if main_sids:
                        main_sid = max(main_sids, key=main_sids.count)
                    storage_matches = []
                    if main_sid:
                        for i, other in enumerate(unassigned):
                            if len(group) >= MAX_CUSTOMER_STOPS:
                                break
                            other_sids = [o.get("StorageID") for o in other["orders"] if o.get("StorageID")]
                            if not other_sids:
                                continue
                            other_dom = max(other_sids, key=other_sids.count)
                            if other_dom == main_sid:
                                potential_total = main_cust["total_effective_space"] + other["total_effective_space"]
                                if potential_total <= MAX_TRUCK_CAPACITY:
                                    storage_matches.append((i, other))
                    if storage_matches:
                        added_idxs = []
                        for match_idx, match_cust in storage_matches[:max(0, MAX_CUSTOMER_STOPS - len(group))]:
                            group.append(match_cust)
                            added_idxs.append(match_idx)
                            print(f"DEBUG: Added {match_cust['CustomerID']} by same-storage grouping")
                        for idx in sorted(added_idxs, reverse=True):
                            unassigned.pop(idx)
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
        response.headers["Access-Control-Allow-Origin"] = "http://192.168.1.18:3000" #http://192.168.1.18:3000
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