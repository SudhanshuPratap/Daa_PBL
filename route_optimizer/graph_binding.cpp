#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "graph.h"

namespace py = pybind11;

PYBIND11_MODULE(route_optimizer, m) {
    py::class_<Node>(m, "Node")
        .def(py::init<int, double, double, std::string>(),
             py::arg("id") = 0,
             py::arg("latitude") = 0.0,
             py::arg("longitude") = 0.0,
             py::arg("name") = "")
        .def_readwrite("id", &Node::id)
        .def_readwrite("latitude", &Node::latitude)
        .def_readwrite("longitude", &Node::longitude)
        .def_readwrite("name", &Node::name);

    py::class_<Edge>(m, "Edge")
        .def(py::init<int, int, double, double>(),
             py::arg("source") = 0,
             py::arg("target") = 0,
             py::arg("weight") = 0.0,
             py::arg("time") = 0.0)
        .def_readwrite("source", &Edge::source)
        .def_readwrite("target", &Edge::target)
        .def_readwrite("weight", &Edge::weight)
        .def_readwrite("time", &Edge::time);

    py::class_<RouteGraph>(m, "RouteGraph")
        .def(py::init<>())
        .def("add_node", &RouteGraph::addNode)
        .def("add_edge", &RouteGraph::addEdge)
        .def("find_shortest_path", &RouteGraph::findShortestPath)
        .def("find_path_with_waypoints", &RouteGraph::findPathWithWaypoints);
}