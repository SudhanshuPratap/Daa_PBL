#pragma once
#include <vector>
#include <map>
#include <string>
using namespace std;

struct Node {
    int id;
    double latitude;
    double longitude;
    string name;
    
    Node(int id = 0, double lat = 0.0, double lon = 0.0, string name = "")
        : id(id), latitude(lat), longitude(lon), name(name) {}
};

struct Edge {
    int source;
    int target;
    double weight;
    double time;
    double cost;
    
    // Add constructor
    Edge(int src = 0, int tgt = 0, double w = 0.0, double t = 0.0, double c = 0.0)
        : source(src), target(tgt), weight(w), time(t), cost(c) {}
};

class RouteGraph {
    private:
    vector<Node> nodes;
    vector<Edge> edges;
    map<int, vector<Edge>> adjacency_list;
    
public:
    void addNode(const Node& node);
    void addEdge(const Edge& edge);
    
    vector<int> findShortestPath(int start, int end, const string& metric="time");
    
    vector<int> findPathWithWaypoints(int start, const vector<int>& waypoints, int end, const string& metric);
};