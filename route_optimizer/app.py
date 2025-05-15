# app.py
import tkinter as tk
from tkinter import ttk
import json
from data_fetcher import RouteDataFetcher
import route_optimizer  # Our C++ module

class RoutePlannerApp:
    def __init__(self, root):
        self.root = root
        self.fetcher = RouteDataFetcher()
        self.graph = route_optimizer.RouteGraph()
        
        self.setup_ui()
    
    def setup_ui(self):
        # Origin/Destination inputs
        ttk.Label(self.root, text="Origin (long,lat):").grid(row=0, column=0)
        self.origin_entry = ttk.Entry(self.root)
        self.origin_entry.grid(row=0, column=1)
        
        ttk.Label(self.root, text="Destination (long,lat):").grid(row=1, column=0)
        self.dest_entry = ttk.Entry(self.root)
        self.dest_entry.grid(row=1, column=1)
        
        # Optimization criteria
        ttk.Label(self.root, text="Optimize for:").grid(row=2, column=0)
        self.optimize_var = tk.StringVar(value="time")
        ttk.Radiobutton(self.root, text="Time", variable=self.optimize_var, value="time").grid(row=2, column=1)
        ttk.Radiobutton(self.root, text="Cost", variable=self.optimize_var, value="cost").grid(row=2, column=2)
        
        # Waypoints
        ttk.Label(self.root, text="Waypoints (comma separated long,lat):").grid(row=3, column=0)
        self.waypoints_entry = ttk.Entry(self.root)
        self.waypoints_entry.grid(row=3, column=1)
        
        # Calculate button
        ttk.Button(self.root, text="Calculate Route", command=self.calculate_route).grid(row=4, column=0, columnspan=2)
        
        # Results display
        self.results_text = tk.Text(self.root, height=10, width=50)
        self.results_text.grid(row=5, column=0, columnspan=2)
    
    def calculate_route(self):
        origin = self.origin_entry.get()
        destination = self.dest_entry.get()
        waypoints = [wp.strip() for wp in self.waypoints_entry.get().split(",") if wp.strip()]
        
        try:
            # Fetch data
            data = self.fetcher.get_route_data(origin, destination)
            graph_data = self.fetcher.parse_to_graph(data)
            
            # Clear previous graph data
            self.graph = route_optimizer.RouteGraph()
            
            # Build graph in C++
            for node in graph_data["nodes"]:
                self.graph.add_node(route_optimizer.Node(
                    id=node['id'],
                    latitude=node['latitude'],
                    longitude=node['longitude']
                ))
            
            for edge in graph_data["edges"]:
                self.graph.add_edge(route_optimizer.Edge(
                    source=edge['source'],
                    target=edge['target'],
                    weight=edge['weight'],
                    time=edge['time'],
                    cost=edge['cost']
                ))
            
            # Find path
            start_node_id = 0  # First waypoint is start
            end_node_id = 1    # Second waypoint is end
            waypoints_node_ids = [i+2 for i in range(len(waypoints))]  # Subsequent waypoints
            
            if waypoints:
                path = self.graph.find_path_with_waypoints(
                    start_node_id,
                    waypoints_node_ids,
                    end_node_id,
                    self.optimize_var.get()
                )
            else:
                path = self.graph.find_shortest_path(
                    start_node_id,
                    end_node_id,
                    self.optimize_var.get()
                )
            
            # Display results
            self.display_results(path, graph_data)
        
        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Error: {str(e)}")
    
    def display_results(self, path, graph_data):
        # Format and display the path
        self.results_text.delete(1.0, tk.END)
        if not path:
            self.results_text.insert(tk.END, "No path found!")
            return
        
        path_coords = []
        for node_id in path:
            for node in graph_data["nodes"]:
                if node['id'] == node_id:
                    path_coords.append(f"({node['longitude']}, {node['latitude']})")
                    break
        
        self.results_text.insert(tk.END, f"Optimal route:\n")
        self.results_text.insert(tk.END, " → ".join(path_coords))

if __name__ == "__main__":
    root = tk.Tk()
    app = RoutePlannerApp(root)
    root.mainloop()