// graph.cpp
#include "graph.h"
#include <queue>
#include <limits>
#include <algorithm>
#define _WIN32_WINNT 0x0601
#include <string.h>  // For strdup
using namespace std;

void RouteGraph::addNode(const Node& node) {
    nodes.push_back(node);
}

void RouteGraph::addEdge(const Edge& edge) {
    edges.push_back(edge);
    adjacency_list[edge.source].push_back(edge);
}

vector<int> RouteGraph::findShortestPath(int start, int end, const string& metric) {
    // Priority queue: (distance, node)
    priority_queue<pair<double, int>, vector<pair<double, int>>, greater<pair<double, int>>> pq;
    
    // Track distances and previous nodes
    map<int, double> distances;
    map<int, int> previous;
    
    // Initialize distances
    for (const auto& node : nodes) {
        distances[node.id] = numeric_limits<double>::infinity();
    }
    distances[start] = 0;
    pq.push({0, start});
    
    while (!pq.empty()) {
        auto current = pq.top();
        double current_dist = current.first;
        int u = current.second;
        pq.pop();
        
        if (u == end) break;
        if (current_dist > distances[u]) continue;
        
        for (const Edge& edge : adjacency_list[u]) {
            double weight = (metric == "cost") ? edge.cost : edge.time;
            double new_dist = current_dist + weight;
            
            if (new_dist < distances[edge.target]) {
                distances[edge.target] = new_dist;
                previous[edge.target] = u;
                pq.push({new_dist, edge.target});
            }
        }
    }
    
    // Reconstruct path
    vector<int> path;
    for (int at = end; at != start; at = previous[at]) {
        path.push_back(at);
        if (previous.find(at) == previous.end()) return {};
    }
    path.push_back(start);
    reverse(path.begin(), path.end());
    return path;
}

vector<int> RouteGraph::findPathWithWaypoints(int start, const vector<int>& waypoints, int end, const string& metric) {
    vector<int> full_path;
    int current = start;
    
    for (int wp : waypoints) {
        vector<int> segment = findShortestPath(current, wp, metric);
        if (segment.empty()) return {};
        
        full_path.insert(full_path.end(), segment.begin(), segment.end() - 1);
        current = wp;
    }
    
    vector<int> last_segment = findShortestPath(current, end, metric);
    if (last_segment.empty()) return {};
    
    full_path.insert(full_path.end(), last_segment.begin(), last_segment.end());
    return full_path;
}