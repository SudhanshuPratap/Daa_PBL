import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import route_optimizer
import time
from urllib.parse import quote

class RouteDataFetcher:
    def __init__(self):
        self.base_url = "http://router.project-osrm.org/route/v1/driving/"
        self.geocode_url = "https://nominatim.openstreetmap.org/search"
        self.last_request_time = 0
        self.user_agent = "RouteOptimizer/1.0"
        self.geocode_cache = {}
    
    def geocode_location(self, location_name):
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
            
            coords = (float(data[0]['lat']), float(data[0]['lon']))
            self.geocode_cache[location_name] = coords
            self.last_request_time = time.time()
            return coords
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during geocoding: {str(e)}")
    
    def get_route_data(self, origin, destination):
        try:
            origin_coords = self.geocode_location(origin)
            destination_coords = self.geocode_location(destination)
                
            url = f"{self.base_url}{origin_coords[1]},{origin_coords[0]};{destination_coords[1]},{destination_coords[0]}?overview=full&geometries=geojson"
            headers = {'User-Agent': self.user_agent}
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"OSRM API request failed: {response.text}")
                
            return response.json()
            
        except Exception as e:
            raise Exception(f"Failed to get route data: {str(e)}")
    
    def parse_to_graph(self, json_data):
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

# Train route data
train_routes = {
    ("delhi", "mumbai"): ["Delhi", "Mathura", "Kota", "Ratlam", "Mumbai"],
    ("delhi", "kolkata"): ["Delhi", "Kanpur", "Prayagraj", "Patna", "Asansol", "Kolkata"],
    ("mumbai", "chennai"): ["Mumbai", "Pune", "Solapur", "Guntakal", "Chennai"],
    ("delhi", "hyderabad"): ["Delhi", "Agra", "Jhansi", "Nagpur", "Secunderabad", "Hyderabad"],
    ("mumbai", "kolkata"): ["Mumbai", "Nasik", "Jabalpur", "Bilaspur", "Raipur", "Kolkata"],
    ("chennai", "kolkata"): ["Chennai", "Vijayawada", "Visakhapatnam", "Bhubaneswar", "Kolkata"],
    ("delhi", "chennai"): ["Delhi", "Agra", "Jhansi", "Nagpur", "Warangal", "Chennai"],
    ("hyderabad", "mumbai"): ["Hyderabad", "Gulbarga", "Solapur", "Pune", "Mumbai"],
}

def main():
    st.set_page_config(page_title="Smart Travel Planner", layout="wide")
    st.title("Smart Travel Planner")
    
    fetcher = RouteDataFetcher()
    
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("Enter Origin", "Delhi")
        destination = st.text_input("Enter Destination", "Mumbai")
        waypoints = st.text_input("Waypoints (comma separated)", "")
    
    with col2:
        mode = st.selectbox("Select Mode of Transportation", ["Train", "Road", "Flight"])
        optimize_time = st.checkbox("Optimize for shortest time", True)
    
    if st.button("Plan Route"):
        if not origin or not destination:
            st.error("Please enter both origin and destination")
        else:
            try:
                waypoint_list = [wp.strip() for wp in waypoints.split(",") if wp.strip()]
                
                if mode == "Train":
                    route = train_routes.get((origin.lower(), destination.lower()))
                    if not route:
                        route = train_routes.get((destination.lower(), origin.lower()))
                        if route:
                            route = route[::-1]
                    if not route:
                        raise ValueError("Train route not found for this path.")
                    
                    coords = [fetcher.geocode_location(stop) for stop in route]
                    folium_map = folium.Map(location=coords[0], zoom_start=5)
                    folium.PolyLine(coords, color="blue", weight=5).add_to(folium_map)
                    for loc, coord in zip(route, coords):
                        folium.Marker(coord, tooltip=loc).add_to(folium_map)
                    st_folium(folium_map, width=900, height=600)
                    
                    st.success(f"Train route: {' → '.join(route)}")
                
                elif mode == "Road":
                    data = fetcher.get_route_data(origin, destination)
                    graph_data = fetcher.parse_to_graph(data)
                    
                    if graph_data['status'].startswith('error'):
                        raise Exception(graph_data['status'])
                    
                    graph = route_optimizer.RouteGraph()
                    
                    for node in graph_data["nodes"]:
                        graph.add_node(route_optimizer.Node(
                            id=node['id'],
                            latitude=node['latitude'],
                            longitude=node['longitude'],
                            name=node.get('name', '')
                        ))
                    
                    for edge in graph_data["edges"]:
                        graph.add_edge(route_optimizer.Edge(
                            source=edge['source'],
                            target=edge['target'],
                            weight=edge['weight'],
                            time=edge['time']
                        ))
                    
                    path = graph.find_shortest_path(0, 1)
                    
                    path_locations = []
                    for node_id in path:
                        for node in graph_data["nodes"]:
                            if node['id'] == node_id:
                                path_locations.append(node.get('name', f"Point {node_id}"))
                                break
                    
                    coords = []
                    for node_id in path:
                        for node in graph_data["nodes"]:
                            if node['id'] == node_id:
                                coords.append((node['latitude'], node['longitude']))
                                break
                    
                    folium_map = folium.Map(location=coords[0], zoom_start=6)
                    folium.PolyLine(coords, color="green", weight=5).add_to(folium_map)
                    st_folium(folium_map, width=900, height=600)
                    
                    st.success(f"Optimal road route: {' → '.join(path_locations)}")
                    st.info(f"Total distance: {graph_data['total_distance']/1000:.2f} km | Estimated time: {graph_data['total_time']/60:.1f} minutes")
                
                elif mode == "Flight":
                    start_coords = fetcher.geocode_location(origin)
                    end_coords = fetcher.geocode_location(destination)
                    
                    folium_map = folium.Map(location=start_coords, zoom_start=5)
                    folium.PolyLine([start_coords, end_coords], color="red", weight=3, dash_array='5, 10').add_to(folium_map)
                    folium.Marker(start_coords, tooltip=origin).add_to(folium_map)
                    folium.Marker(end_coords, tooltip=destination).add_to(folium_map)
                    st_folium(folium_map, width=900, height=600)
                    
                    # Simple flight time estimation (1 hour + 1 minute per 10km)
                    distance = ((end_coords[0]-start_coords[0])**2 + (end_coords[1]-start_coords[1])**2)**0.5 * 111.32  # approx km
                    flight_time = 60 + distance / 10  # minutes
                    st.success(f"Direct flight from {origin} to {destination}")
                    st.info(f"Estimated flight distance: {distance:.1f} km | Flight time: ~{flight_time:.0f} minutes")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
                if "geocoding" in str(e).lower():
                    st.warning("Possible solutions:")
                    st.warning("- Check your internet connection")
                    st.warning("- Verify the location names are correct")
                    st.warning("- Try more specific location names")

if __name__ == "__main__":
    main()