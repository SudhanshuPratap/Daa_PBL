// graph.h
#pragma once
#include <vector>
#include <map>
#include <string>
using namespace std;
struct Node {
    int id;
    double latitude;
    double longitude;
};

struct Edge {
    int source;
    int target;
    double weight; // could be time, distance, or cost
    double time;
    double cost;
};

class RouteGraph {
private:
    vector<Node> nodes;
    vector<Edge> edges;
    map<int, vector<Edge>> adjacency_list;
    
public:
    void addNode(const Node& node);
    void addEdge(const Edge& edge);
    
    // Dijkstra's algorithm implementation
    vector<int> findShortestPath(int start, int end, const string& metric="time");
    
    // Algorithm with waypoints
    vector<int> findPathWithWaypoints(int start, const vector<int>& waypoints, int end, const string& metric);
};