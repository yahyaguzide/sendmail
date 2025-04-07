from setuptools import setup, Extension
from Cython.Build import cythonize
from Cython.Compiler import Options

# Set the --embed flag
Options.embed = "main"

ext_modules = [
    Extension("main", ["src/__main__.py"]),
]

setup(name="sendmail", ext_modules=cythonize(ext_modules))
