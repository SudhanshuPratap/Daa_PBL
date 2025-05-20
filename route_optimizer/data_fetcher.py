import requests
import json
import time
from urllib.parse import quote

class RouteDataFetcher:
    def __init__(self):
        self.base_url = "http://router.project-osrm.org/route/v1/driving/"
        self.geocode_url = "https://nominatim.openstreetmap.org/search"
        self.last_request_time = 0
        self.user_agent = "RouteOptimizer/1.0 (contact@yourdomain.com)"
        self.geocode_cache = {}
    
    def geocode_location(self, location_name):
        """Convert location name to coordinates using Nominatim with proper rate limiting"""
        if location_name in self.geocode_cache:
            return self.geocode_cache[location_name]
        
        time_since_last = time.time() - self.last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        
        try:
            headers = {'User-Agent': self.user_agent}
            params = {
                'q': location_name,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = requests.get(self.geocode_url, params=params, headers=headers)
            
            if response.status_code == 429:
                raise Exception("Rate limit exceeded. Please wait and try again.")
            if response.status_code != 200:
                raise Exception(f"Geocoding failed with status {response.status_code}")
            
            data = response.json()
            if not data or not isinstance(data, list):
                raise Exception(f"Location not found: {location_name}")
            
            coords = f"{data[0]['lon']},{data[0]['lat']}"
            self.geocode_cache[location_name] = coords
            self.last_request_time = time.time()
            return coords
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during geocoding: {str(e)}")
    
    def get_route_data(self, origin, destination):
        """Get route data from OSRM API with proper error handling"""
        try:
            # Convert city names to coordinates if needed
            if not all(c.isdigit() or c in ',-.' for c in origin.replace(' ', '')):
                origin = self.geocode_location(origin)
            if not all(c.isdigit() or c in ',-.' for c in destination.replace(' ', '')):
                destination = self.geocode_location(destination)
                
            url = f"{self.base_url}{origin};{destination}?overview=full&geometries=geojson"
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"OSRM API request failed: {response.text}")
                
            return response.json()
            
        except Exception as e:
            raise Exception(f"Failed to get route data: {str(e)}")
    
    def parse_to_graph(self, json_data):
        """Parse OSRM response into graph format with proper error handling"""
        try:
            if not isinstance(json_data, dict):
                raise ValueError("Invalid API response format")
            
            nodes = []
            edges = []
            
            waypoints = json_data.get('waypoints', [])
            for i, waypoint in enumerate(waypoints):
                if not isinstance(waypoint, dict):
                    continue
                location = waypoint.get('location', [0, 0])
                if not isinstance(location, list) or len(location) < 2:
                    continue
                nodes.append({
                    'id': i,
                    'latitude': location[1],
                    'longitude': location[0],
                    'name': waypoint.get('name', f"Waypoint {i}"),
                    'type': 'waypoint'
                })
            
            routes = json_data.get('routes', [])
            if not routes:
                raise ValueError("No route information found")
            
            route = routes[0]
            geometry = route.get('geometry', {})
            
            if geometry.get('type') == 'LineString':
                coordinates = geometry.get('coordinates', [])
                for j, coord in enumerate(coordinates):
                    if not isinstance(coord, list) or len(coord) < 2:
                        continue
                    nodes.append({
                        'id': len(nodes),
                        'longitude': coord[0],
                        'latitude': coord[1],
                        'name': f"Path point {j}",
                        'type': 'path_point'
                    })
            
            if len(nodes) >= 2:
                legs = route.get('legs', [])
                if legs:
                    leg = legs[0]
                    total_duration = leg.get('duration', 0)
                    total_distance = leg.get('distance', 0)
                    segment_count = max(1, len(nodes) - 1)
                    
                    for i in range(len(nodes) - 1):
                        edges.append({
                            'source': nodes[i]['id'],
                            'target': nodes[i+1]['id'],
                            'weight': 1,
                            'time': total_duration / segment_count,
                            'cost': total_distance * 0.01 / segment_count,
                            'distance': total_distance / segment_count
                        })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "total_distance": route.get('distance', 0),
                "total_time": route.get('duration', 0),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "nodes": [],
                "edges": [],
                "total_distance": 0,
                "total_time": 0,
                "status": f"error: {str(e)}"
            }