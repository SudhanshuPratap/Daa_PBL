// graph_bindings.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "graph.h"

namespace py = pybind11;

PYBIND11_MODULE(route_optimizer, m) {
    py::class_<RouteGraph>(m, "RouteGraph")
        .def(py::init<>())
        .def("add_node", &RouteGraph::addNode)
        .def("add_edge", &RouteGraph::addEdge)
        .def("find_shortest_path", &RouteGraph::findShortestPath)
        .def("find_path_with_waypoints", &RouteGraph::findPathWithWaypoints);
}