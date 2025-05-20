import tkinter as tk
from tkinter import ttk
import json
from data_fetcher import RouteDataFetcher
import route_optimizer

class RoutePlannerApp:
    def __init__(self, root):
        self.root = root
        self.fetcher = RouteDataFetcher()
        self.graph = route_optimizer.RouteGraph()
        
        self.setup_ui()
    
    def setup_ui(self):
        ttk.Label(self.root, text="Origin (City):").grid(row=0, column=0)
        self.origin_entry = ttk.Entry(self.root)
        self.origin_entry.grid(row=0, column=1)
        
        ttk.Label(self.root, text="Destination (City):").grid(row=1, column=0)
        self.dest_entry = ttk.Entry(self.root)
        self.dest_entry.grid(row=1, column=1)
        
        ttk.Label(self.root, text="Optimize for:").grid(row=2, column=0)
        self.optimize_var = tk.StringVar(value="time")
        ttk.Radiobutton(self.root, text="Time", variable=self.optimize_var, value="time").grid(row=2, column=1)
        ttk.Radiobutton(self.root, text="Cost", variable=self.optimize_var, value="cost").grid(row=2, column=2)
        
        ttk.Label(self.root, text="Waypoints (comma separated cities):").grid(row=3, column=0)
        self.waypoints_entry = ttk.Entry(self.root)
        self.waypoints_entry.grid(row=3, column=1)
        
        ttk.Button(self.root, text="Calculate Route", command=self.calculate_route).grid(row=4, column=0, columnspan=2)
        
        self.results_text = tk.Text(self.root, height=10, width=50)
        self.results_text.grid(row=5, column=0, columnspan=2)
    
    def calculate_route(self):
    #    def calculate_route(self):
        origin = self.origin_entry.get().strip()
        destination = self.dest_entry.get().strip()
        waypoints = [wp.strip() for wp in self.waypoints_entry.get().split(",") if wp.strip()]
        
        try:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Calculating route...\n")
            self.root.update()  # Force UI update
            
            data = self.fetcher.get_route_data(origin, destination)
            graph_data = self.fetcher.parse_to_graph(data)
            
            if graph_data['status'].startswith('error'):
                raise Exception(graph_data['status'])
            
            self.graph = route_optimizer.RouteGraph()
            
            # Build graph in C++
            for node in graph_data["nodes"]:
                try:
                    self.graph.add_node(route_optimizer.Node(
                        id=node['id'],
                        latitude=node['latitude'],
                        longitude=node['longitude'],
                        name=node.get('name', '')
                    ))
                except Exception as e:
                    raise Exception(f"Failed to add node {node['id']}: {str(e)}")
            
            for edge in graph_data["edges"]:
                try:
                    self.graph.add_edge(route_optimizer.Edge(
                        source=edge['source'],
                        target=edge['target'],
                        weight=edge['weight'],
                        time=edge['time'],
                        cost=edge['cost']
                    ))
                except Exception as e:
                    raise Exception(f"Failed to add edge {edge['source']}->{edge['target']}: {str(e)}")
            
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
            
            # Show success message
            self.results_text.insert(tk.END, f"\n\nTotal distance: {graph_data['total_distance']/1000:.2f} km")
            self.results_text.insert(tk.END, f"\nEstimated time: {graph_data['total_time']/60:.1f} minutes")
        
        except Exception as e:
            self.results_text.delete(1.0, tk.END)
            error_msg = str(e).replace('error: ', '')  # Remove prefix if present
            self.results_text.insert(tk.END, f"Error: {error_msg}")
            # Suggest common solutions for geocoding errors
            if "geocoding" in error_msg.lower():
                self.results_text.insert(tk.END, "\n\nPossible solutions:")
                self.results_text.insert(tk.END, "\n- Check your internet connection")
                self.results_text.insert(tk.END, "\n- Verify the location names are correct")
                self.results_text.insert(tk.END, "\n- Try more specific location names")
    
    def display_results(self, path, graph_data):
        # Format and display the path
        self.results_text.delete(1.0, tk.END)
        if not path:
            self.results_text.insert(tk.END, "No path found!")
            return
        
        path_locations = []
        for node_id in path:
            for node in graph_data["nodes"]:
                if node['id'] == node_id:
                    if 'name' in node:
                        path_locations.append(node['name'])
                    else:
                        path_locations.append(f"({node['longitude']}, {node['latitude']})")
                    break
        
        self.results_text.insert(tk.END, f"Optimal route:\n")
        self.results_text.insert(tk.END, " → ".join(path_locations))

if __name__ == "__main__":
    root = tk.Tk()
    app = RoutePlannerApp(root)
    root.mainloop()