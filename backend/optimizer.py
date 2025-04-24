from ortools.constraint_solver import routing_enums_pb2, pywrapcp
import math
from .distance import build_distance_matrix
import os
from dotenv import load_dotenv
load_dotenv()

def compute_euclidean_distance(coord1, coord2):
    """
    Computes the Euclidean distance between two (x,y) points.
    """
    (x1, y1) = coord1
    (x2, y2) = coord2
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def solve_vrp(distance_matrix, num_vehicles, depot_index):
    """
    Solve the vehicle routing problem with the provided distance_matrix using OR-Tools.
    Returns a dictionary with the routes and total duration.
    """
    n = len(distance_matrix)
    manager = pywrapcp.RoutingIndexManager(n, num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        raise Exception("No solution found!")
    
    routes = []
    total_duration = 0
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route = []
        route_duration = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(node_index)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_duration += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        route.append(manager.IndexToNode(index))
        routes.append({
            "vehicle": vehicle_id,
            "route": route,
            "duration": route_duration  # total duration in seconds
        })
        total_duration += route_duration

    return {
        "total_duration": total_duration,
        "routes": routes
    }

def optimize_routes(locations, num_vehicles, depot_index):
    """
    Main function to perform route optimization.
    Args:
      locations: List of strings, each a "lat,lng" for a stop.
      num_vehicles: Number of vehicles (trucks).
      depot_index: Index of the depot location in the locations list.
    
    Returns:
      A dictionary with a message, the input, and optimized routes.
    """
    if not locations:
        raise ValueError("No locations provided.")

    # Build the distance matrix using the Google Distance Matrix API.
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise Exception("Missing GOOGLE_API_KEY in environment")
    
    distance_matrix = build_distance_matrix(locations, google_api_key)
    
    # Solve the VRP using OR-Tools.
    vrp_result = solve_vrp(distance_matrix, num_vehicles, depot_index)
    
    return {
        "message": "Optimization completed successfully",
        "input": {
            "locations": locations,
            "num_vehicles": num_vehicles,
            "depot_index": depot_index
        },
        "optimized_route": vrp_result
    }