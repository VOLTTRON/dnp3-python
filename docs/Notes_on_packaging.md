# Notes on Packaging

## Background
* The dnp3-python version 0.2.0 is an extension and repackaging of [pydnp3](https://github.com/ChargePoint/pydnp3) version 0.1.0
* The wrapper provides more user-friendly and out-of-the-box examples (under /src/dnp3demo)
* The wrapper enables features to install from [The Python Package Index (Pypi)](https://pypi.org/), 
  while the original package requires installing from the source code.

## Overview
* While, building package from the source code is NOT needed when using the dnp3-python package,
  it is still required for packing for distribution (i.e., building wheel and publishing to pypi.)
* The dependencies to build c++ binding code are cmake and pybind11.
  * CMake >= 2.8.12 is required.
  * a special version of pybind11 is used and located at /deps/pybind11.
* The c++ source code is based on [opendnp3](https://github.com/automatak/dnp3), 
  forked and version-pinned at /deps/dnp3.
  the binding code are located at /src and its sub-folders.
* setup.py describes the packaging configuration. (tested with with python==3.8.13, setuptools==63.4.1)
  * to build and install the package locally, run `python setup.py install`
  * to build wheel, run `python setup.py bdist_wheel [--plat-name=manylinux1_x86_64]`

## Notes on Building native Python + CPP-binding Python Package
#### Intro
* Need to build + package a python project with cpp-binding code.
* Desired result
  * pip install <package_name:dnp3_python>
  * able to import cpp-binding modules, e.g., “from pydnp3 import opendnp3”
  * able to import native python code, e.g., “from dnp3_python.dnp3station import master_new” 
* Note:
  * the package is a wrapper on “pydnp3” project by repackaging its cpp-binding functionality 
    and extended/redesigned API in Python.
  * the package inherited “pydnp3” project’s root module naming, 
    i.e., “pydnp3” for cpp-binding related functionality.
  * the extended method adopted root module naming, “dnp3_python”. 
    (There is a discussion at the end of this memo about the reason for using different root module name.)
#### Ingredients
* Reference: [Package Discovery and Namespace Packages](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html)
* Key configuration in `setup.py`
    ```
    packages=find_namespace_packages(
            where='src',
            include=['dnp3_python*', 'dnp3demo']  # to include sub-packages as well.
        ),
    package_dir={"": "src"},
    ```
* Codebase structure (under /src)
  ```
    ./src
    ├── asiodnp3
    │   ...
    ├── asiopal
    │ 	...
    ├── dnp3demo
    │   ├── data_retrieval_demo.py
    │   ...
    ├── dnp3_python
    │   ├── dnp3station
    │   │   ├── __init__.py
    │   │   ├── master_new.py
    │   │   ├── outstation_new.py
    │   │   ├── outstation_utils.py
    │   │   ├── station_utils.py
    │   │   └── visitors.py
    │   └── __init__.py
    ├── opendnp3
    │  	...
    ├── openpal
    │  	...
    ├── pydnp3asiodnp3.cpp
    ├── pydnp3asiopal.cpp
    ├── pydnp3.cpp
    ├── pydnp3opendnp3.cpp
    └── pydnp3openpal.cpp
    ```

#### Key takeaways
* Using find_namespace_packages to “automatically” find packages 
  (assuming defined sub-modules properly, i.e., with `__init__.py`)
* Using trailing * to include submodules 
  (e.g., dnp3_python* will include dnp3_python and dnp3_python/dnp3station)
* Verifying with artifact structure (e.g., whl structure or tar structure)

#### Discussion:
* dnp3_python is a package mixed with cpp binding binary and native Python source code.
    * the cpp binding path is resolved by using dynamic binary (i.e., *.so file)
    * the name space is called “pydnp3”
* To avoid namespace conflict, use different root namespace for python source code package.
  * e.g., at one point, the pacakge adopted the structure /src/pydnp3/dnp3station, 
    with the attempt to achieve `from pydnp3.dnp3station.master_new import *`. 
    As a result, it will create a “pydnp3/dnp3station” dir at the site-package path.
  * However, under the aforementioned structure, the cpp binding submodules are not resolvable, 
    e.g., not able to achieve “from pydnp3 import opendnp3”. 
    python will find the native “pydnp3/” first and ignore the package path linked to `*.so` file.
  