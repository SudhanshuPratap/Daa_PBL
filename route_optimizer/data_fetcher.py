# data_fetcher.py
import requests
import json

class RouteDataFetcher:
    def __init__(self):
        self.base_url = "http://router.project-osrm.org/route/v1/driving/"
    
    def get_route_data(self, origin, destination):
        """Get route data from OSRM API"""
        url = f"{self.base_url}{origin};{destination}?overview=full"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.text}")
        return response.json()
    
    def parse_to_graph(self, json_data):
        """Parse OSRM response into graph format"""
        nodes = []
        edges = []
        
        # Extract waypoints (nodes)
        for i, waypoint in enumerate(json_data['waypoints']):
            nodes.append({
                'id': i,
                'latitude': waypoint['location'][1],
                'longitude': waypoint['location'][0]
            })
        
        # Extract legs (edges)
        for leg in json_data['routes'][0]['legs']:
            edges.append({
                'source': 0,  # Always from start node
                'target': 1,  # Always to end node
                'weight': leg['duration'],
                'time': leg['duration'],
                'cost': leg['distance'] * 0.01  # Example cost calculation
            })
        
        return {"nodes": nodes, "edges": edges}