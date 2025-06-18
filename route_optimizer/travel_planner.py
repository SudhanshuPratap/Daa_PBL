import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import time
import json 

# Initialize session state for map_data, route_info, and last_error
if 'map_data' not in st.session_state:
    st.session_state.map_data = None
if 'route_info' not in st.session_state:
    st.session_state.route_info = None
if 'last_error' not in st.session_state:
    st.session_state.last_error = None

class RouteDataFetcher:
    def __init__(self):
        self.base_url = "http://router.project-osrm.org/route/v1/driving/"
        self.geocode_url = "https://nominatim.openstreetmap.org/search"
        self.user_agent = "SmartTravelPlanner/1.0"
        self.last_request = 0

    def geocode(self, location):
        # Rate limiting to avoid hitting API limits
        time_since_last = time.time() - self.last_request
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        
        try:
            response = requests.get(
                self.geocode_url,
                params={'q': location, 'format': 'json', 'limit': 1},
                headers={'User-Agent': self.user_agent}
            )
            self.last_request = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0: # Ensure data is a non-empty list
                    return float(data[0]['lat']), float(data[0]['lon'])
            st.session_state.last_error = f"Geocoding failed: Location not found or invalid response for '{location}'"
            return None
        except requests.exceptions.RequestException as e:
            st.session_state.last_error = f"Network error during geocoding for '{location}': {e}"
            return None
        except json.JSONDecodeError:
            st.session_state.last_error = f"Geocoding API returned invalid JSON for '{location}'"
            return None
        except Exception as e:
            st.session_state.last_error = f"An unexpected error occurred during geocoding for '{location}': {e}"
            return None

    def get_route(self, origin, destination):
        origin_coords = self.geocode(origin)
        dest_coords = self.geocode(destination)
        
        if not origin_coords or not dest_coords:
            # Error message already set by geocode method if coordinates not found
            return None
            
        url = f"{self.base_url}{origin_coords[1]},{origin_coords[0]};{dest_coords[1]},{dest_coords[0]}?overview=full&geometries=geojson" # Added geometries=geojson for clarity
        try:
            response = requests.get(url, headers={'User-Agent': self.user_agent})
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                 st.session_state.last_error = f"OSRM API error 400: Bad request. Often means no route found or invalid coordinates. Response: {response.text}"
                 return None
            elif response.status_code == 429:
                st.session_state.last_error = "OSRM API rate limit exceeded. Please wait a moment and try again."
                return None
            else:
                st.session_state.last_error = f"OSRM API request failed with status {response.status_code}: {response.text}"
                return None
        except requests.exceptions.RequestException as e:
            st.session_state.last_error = f"Network error during route fetching: {e}"
            return None
        except json.JSONDecodeError:
            st.session_state.last_error = "OSRM API returned invalid JSON."
            return None
        except Exception as e:
            st.session_state.last_error = f"An unexpected error occurred during route fetching: {e}"
            return None

# Predefined train routes
TRAIN_ROUTES = {
    ("delhi", "mumbai"): ["Delhi", "Mathura", "Kota", "Ratlam", "Mumbai"],
    ("delhi", "kolkata"): ["Delhi", "Kanpur", "Prayagraj", "Patna", "Asansol", "Kolkata"],
    ("mumbai", "chennai"): ["Mumbai", "Pune", "Solapur", "Guntakal", "Chennai"],
}

def show_map(route_type, locations, names=None):
    if not locations:
        st.session_state.map_data = None # Clear map if no locations
        return
    
    m = folium.Map(location=locations[0], zoom_start=6)
    
    if route_type == "road":
        folium.PolyLine(locations, color="green", weight=5).add_to(m)
    elif route_type == "train":
        folium.PolyLine(locations, color="blue", weight=5).add_to(m)
        if names:
            for coord, name in zip(locations, names):
                folium.Marker(coord, tooltip=name).add_to(m)
    elif route_type == "flight":
        folium.PolyLine(locations, color="red", weight=3, dash_array='5, 10').add_to(m)
        if names:
            folium.Marker(locations[0], tooltip=names[0]).add_to(m)
            folium.Marker(locations[1], tooltip=names[1]).add_to(m)
    
    # Store the Folium map object in session state for persistence
    st.session_state.map_data = m

def main():
    st.set_page_config(page_title="Travel Planner", layout="centered")
    st.title("🚂 Smart Travel Planner")
    
    fetcher = RouteDataFetcher()
    
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("From", "Delhi").strip()
    with col2:
        destination = st.text_input("To", "Mumbai").strip()
    
    mode = st.radio("Travel Mode", ["Train", "Road", "Flight"], horizontal=True)
    
    if st.button("Plan Journey"):
        # Clear previous map, results, and errors when planning a new journey
        st.session_state.map_data = None 
        st.session_state.route_info = None
        st.session_state.last_error = None

        if not origin or not destination:
            st.error("Please enter both origin and destination")
            return
            
        with st.spinner(f"Finding {mode.lower()} route..."):
            if mode == "Train":
                route = TRAIN_ROUTES.get((origin.lower(), destination.lower())) or \
                        TRAIN_ROUTES.get((destination.lower(), origin.lower()))[::-1]
                if not route:
                    st.session_state.last_error = "No train route found for these cities."
                    return
                
                coords = []
                valid_stops = []
                for stop in route:
                    coord = fetcher.geocode(stop)
                    if coord:
                        coords.append(coord)
                        valid_stops.append(stop)
                    
                if len(coords) >= 2:
                    show_map("train", coords, valid_stops)
                    st.session_state.route_info = f"Train Route: {' → '.join(valid_stops)}"
                else:
                    if st.session_state.last_error is None: 
                        st.session_state.last_error = "Could not map train route (insufficient valid stops or geocoding issues)."
            
            elif mode == "Road":
                route_data = fetcher.get_route(origin, destination)
                # Enhanced checks for route_data and its nested structures
                if (route_data and 
                    'routes' in route_data and 
                    isinstance(route_data['routes'], list) and # Ensure 'routes' is a list
                    len(route_data['routes']) > 0 and        # Ensure 'routes' list is not empty
                    'geometry' in route_data['routes'][0] and
                    'coordinates' in route_data['routes'][0]['geometry'] and
                    isinstance(route_data['routes'][0]['geometry']['coordinates'], list) and # Crucial new check for list type
                    len(route_data['routes'][0]['geometry']['coordinates']) > 0 # Ensure coordinates list is not empty
                   ):
                    
                    coords = [(p[1], p[0]) for p in route_data['routes'][0]['geometry']['coordinates']]
                    distance = route_data['routes'][0]['distance']/1000
                    duration = route_data['routes'][0]['duration']/60
                    
                    show_map("road", coords)
                    st.session_state.route_info = f"Road Route: {origin} → {destination}\nDistance: {distance:.1f} km | Time: {duration:.1f} minutes"
                else:
                    # Only set generic error if no specific API error was captured by get_route
                    if st.session_state.last_error is None: 
                        st.session_state.last_error = "Could not find road route, or OSRM response was malformed/empty for coordinates."
            
            elif mode == "Flight":
                origin_coords = fetcher.geocode(origin)
                dest_coords = fetcher.geocode(destination)
                
                if origin_coords and dest_coords:
                    # Simple straight-line distance and estimated flight time for demo
                    distance = ((dest_coords[0]-origin_coords[0])**2 + 
                               (dest_coords[1]-origin_coords[1])**2)**0.5 * 111.32
                    flight_time = 60 + distance/10 # A very rough estimation
                    
                    show_map("flight", [origin_coords, dest_coords], [origin, destination])
                    st.session_state.route_info = f"Direct Flight: {origin} → {destination}\nDistance: {distance:.1f} km | Flight Time: ~{flight_time:.0f} minutes"
                else:
                    if st.session_state.last_error is None:
                        st.session_state.last_error = "Could not locate airports for flight planning."

    # Display the map if it exists in session state (after all calculations)
    if st.session_state.map_data is not None:
        st_folium(st.session_state.map_data, width=700, height=500)
    
    # Display route information if it exists in session state
    if st.session_state.route_info is not None:
        st.success(st.session_state.route_info)
    
    # Display any error messages
    if st.session_state.last_error is not None:
        st.error(st.session_state.last_error)


if __name__ == "__main__":
    main()