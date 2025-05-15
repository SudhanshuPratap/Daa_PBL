from setuptools import setup, Extension
import pybind11

module = Extension(
    'route_optimizer',
    sources=['Graph.cpp', 'graph_binding.cpp'],
    include_dirs=[pybind11.get_include()],
    language='c++',
    extra_compile_args=['-std=c++17', '-D_WIN32_WINNT=0x0601'],
    define_macros=[('PYBIND11_STRDUP_MSVC_COMPAT', '1')],
)

setup(
    name='route_optimizer',
    version='1.0',
    description='Route optimization module',
    ext_modules=[module],
)