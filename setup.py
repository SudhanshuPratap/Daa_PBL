from setuptools import setup, Extension
import pybind11

module = Extension(
    'route_optimizer',
    sources=['Graph.cpp', 'graph_binding.cpp'],
    include_dirs=[pybind11.get_include()],
    language='c++',
    extra_compile_args=['-std=c++11'],
)

setup(
    name='route_optimizer',
    version='1.0',
    description='Route optimization module',
    ext_modules=[module],
)