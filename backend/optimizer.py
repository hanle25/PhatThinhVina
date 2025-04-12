# backend/optimizer.py
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
import math

def compute_euclidean_distance(coord1, coord2):
    """
    Computes the Euclidean distance between two (x, y) points.
    """
    (x1, y1) = coord1
    (x2, y2) = coord2
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def compute_distance_matrix(locations, distance_fn=compute_euclidean_distance):
    """
    Creates a distance matrix (a dict-of-dicts) for the provided list of coordinate pairs.
    """
    size = len(locations)
    matrix = {}
    for i in range(size):
        matrix[i] = {}
        for j in range(size):
            if i == j:
                matrix[i][j] = 0
            else:
                # Multiply the distance by 1000 and cast to int (needed by OR-Tools)
                matrix[i][j] = int(distance_fn(locations[i], locations[j]) * 1000)
    return matrix

def optimize_routes(locations, num_vehicles, depot_index):
    """
    Use OR-Tools to compute an optimized route for the given list of stops.

    Args:
      locations: List of [lat, lng] pairs.
      num_vehicles: Number of vehicles (trucks) available.
      depot_index: Index of the depot (starting/ending location) in the locations list.

    Returns:
      A dictionary containing:
        - message: Confirmation message.
        - total_distance: Total distance of all routes (in same units as distance_fn, if divided by 1000).
        - routes: List of routes for each vehicle.
    """
    # Ensure we have locations
    if not locations:
        raise ValueError("No locations provided.")

    # Compute the distance matrix.
    distance_matrix = compute_distance_matrix(locations)
    
    # Create routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(locations), num_vehicles, depot_index)
    
    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)
    
    # Callback: returns distance between two nodes.
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    
    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Set search parameters.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    
    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        raise Exception("No solution found!")
    
    # Extract routes and compute total distance.
    routes = []
    total_distance = 0
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route = []
        route_distance = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(locations[node_index])
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        # Append depot at end of route.
        route.append(locations[manager.IndexToNode(index)])
        routes.append({
            "vehicle": vehicle_id,
            "route": route,
            "distance": route_distance / 1000.0  # Convert back to original scale
        })
        total_distance += route_distance
    return {
        "message": "Optimization completed successfully",
        "total_distance": total_distance / 1000.0,
        "routes": routes
    }
