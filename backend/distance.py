# backend/distance_fetcher.py
import os
import requests

def build_distance_matrix(locations, google_api_key):
    """
    Given a list of locations (as strings: "lat,long") and a Google API key,
    returns a 2D list (matrix) of travel durations in seconds.
    """
    origins = "|".join(locations)
    destinations = "|".join(locations)
    
    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?origins={origins}"
        f"&destinations={destinations}"
        f"&key={google_api_key}"
        "&units=metric"
    )
    response = requests.get(url)
    data = response.json()

    n = len(locations)
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    
    for i, row in enumerate(data['rows']):
        for j, element in enumerate(row['elements']):
            if element['status'] == 'OK':
                # Using travel duration (seconds) as cost; you could also use distance in meters.
                matrix[i][j] = element['duration']['value']
            else:
                matrix[i][j] = 999999  # a large number for unavailable routes
    return matrix
