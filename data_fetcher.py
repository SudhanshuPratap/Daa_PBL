# data_fetcher.py
import requests
import json

class RouteDataFetcher:
    def __init__(self):
        self.base_url = "http://router.project-osrm.org/route/v1/driving/"
    
    def get_route_data(self, origin, destination):
        url = f"{self.base_url}{origin};{destination}?overview=full"
        response = requests.get(url)
        return response.json()
    
    def parse_to_graph(self, json_data):
        # Parse OSRM response into graph format for C++
        nodes = []
        edges = []
        # ... parsing logic
        return {"nodes": nodes, "edges": edges}