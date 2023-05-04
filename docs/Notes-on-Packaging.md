# Notes on Packaging

## Background

* The dnp3-python version 0.2.0 is an extension and repackaging of [pydnp3](https://github.com/ChargePoint/pydnp3)
  version 0.1.0
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

## Notes on working with recurse-submodules

* In order to build the binary (and the wheel) from the source code, the dnp3-python relies on pin-versioned "dnp3"
  and "pybind11".
* Note that both the aforementioned source code repo need to present locally at the `/deps`.
* Both of them are included in git as submodules. (See [.gitmodules](../.gitmodules)). To include the submodule,
  use `git clone <dnp3-python repo> --recurse-submodules`. The `--recurse-submodules` option makes sure nested
  submodules are cloned. (Note that the submodule "dnp3" include another submodule "asio".)
* If the submodules were not cloned at the beginning, run `git submodule update --init --recursive`.
* To work with submodules, please see the following references:
  * [Submodules - Git](https://git-scm.com/book/en/v2/Git-Tools-Submodules))
  * [Pull latest changes for all git submodules](https://stackoverflow.com/questions/1030169/pull-latest-changes-for-all-git-submodules)
  * [How to create Git submodules in GitHub and GitLab by example](https://www.theserverside.com/blog/Coffee-Talk-Java-News-Stories-and-Opinions/How-to-add-submodules-to-GitHub-repos)
  * [Cleans and resets a git repo and its submodules - gists · GitHub](https://gist.github.com/nicktoumpelis/11214362)
  * [How to checkout old git commit including all submodules recursively?](https://stackoverflow.com/questions/15124430/how-to-checkout-old-git-commit-including-all-submodules-recursively)

## Notes on Building native Python + CPP-binding Python Package

### Intro

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

### Ingredients

*

Reference: [Package Discovery and Namespace Packages](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html)

* Key configuration in `setup.py`

  ```python
  packages=find_namespace_packages(
          where='src',
          include=['dnp3_python*', 'dnp3demo']  # to include sub-packages as well.
      ),
  package_dir={"": "src"},
  ```

* Codebase structure (under /src)
  
  ```bash
  ./src
  ├── asiodnp3
  │   ...
  ├── asiopal
  │   ...
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
  │   ...
  ├── openpal
  │   ...
  ├── pydnp3asiodnp3.cpp
  ├── pydnp3asiopal.cpp
  ├── pydnp3.cpp
  ├── pydnp3opendnp3.cpp
  └── pydnp3openpal.cpp
  ```

### Key takeaways

* Using find_namespace_packages to “automatically” find packages
  (assuming defined sub-modules properly, i.e., with `__init__.py`)

* Using trailing *to include submodules
  (e.g., dnp3_python* will include dnp3_python and dnp3_python/dnp3station)

* Verifying with artifact structure (e.g., whl structure or tar structure)

### Discussion

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

## Example: building binary from C++ source code

* Demo OS: Ubuntu 22.04 -- use [OsBoxes VM](https://www.osboxes.org/ubuntu/) in this demo.
* Virtual Environment Tool (e.g., conda, virtualenv) -- use conda in this demo.
* Python version 3.10.

### prepared the source code (including submodules) for build

```bash
$ git clone <dnp3-python-repo> --recurse-submodules
Cloning into 'dnp3-python'...
remote: Enumerating objects: 1633, done.
remote: Counting objects: 100% (15/15), done.
remote: Compressing objects: 100% (15/15), done.
remote: Total 1633 (delta 2), reused 3 (delta 0), pack-reused 1618
Receiving objects: 100% (1633/1633), 12.09 MiB | 16.00 MiB/s, done.
Resolving deltas: 100% (1275/1275), done.
Submodule 'deps/dnp3' (https://github.com/kefeimo/opendnp3.git) registered for path 'deps/dnp3'
Submodule 'deps/pybind11' (https://github.com/Kisensum/pybind11.git) registered for path 'deps/pybind11'
Cloning into '/home/kefei/project/dnp3-python/deps/dnp3'...
remote: Enumerating objects: 96789, done.        
remote: Counting objects: 100% (2074/2074), done.        
remote: Compressing objects: 100% (834/834), done.        
remote: Total 96789 (delta 1296), reused 1674 (delta 1152), pack-reused 94715        
Receiving objects: 100% (96789/96789), 25.70 MiB | 2.01 MiB/s, done.
Resolving deltas: 100% (68129/68129), done.
Cloning into '/home/kefei/project/dnp3-python/deps/pybind11'...
remote: Enumerating objects: 9840, done.        
remote: Total 9840 (delta 0), reused 0 (delta 0), pack-reused 9840        
Receiving objects: 100% (9840/9840), 3.46 MiB | 1.99 MiB/s, done.
Resolving deltas: 100% (6648/6648), done.
Submodule path 'deps/dnp3': checked out '7d84673d165a4a075590a5f146ed1a4ba35d4e49'
Submodule 'deps/asio' (https://github.com/chriskohlhoff/asio.git) registered for path 'deps/dnp3/deps/asio'
Cloning into '/home/kefei/project/dnp3-python/deps/dnp3/deps/asio'...
remote: Enumerating objects: 62636, done.        
remote: Counting objects: 100% (669/669), done.        
remote: Compressing objects: 100% (269/269), done.        
remote: Total 62636 (delta 462), reused 513 (delta 400), pack-reused 61967        
Receiving objects: 100% (62636/62636), 25.34 MiB | 2.24 MiB/s, done.
Resolving deltas: 100% (45783/45783), done.
Submodule path 'deps/dnp3/deps/asio': checked out '28d9b8d6df708024af5227c551673fdb2519f5bf'
Submodule path 'deps/pybind11': checked out '338d615e12ce41ee021724551841de3cbe0bc1df'
Submodule 'tools/clang' (https://github.com/wjakob/clang-cindex-python3) registered for path 'deps/pybind11/tools/clang'
Cloning into '/home/kefei/project/dnp3-python/deps/pybind11/tools/clang'...
remote: Enumerating objects: 368, done.        
remote: Counting objects: 100% (13/13), done.        
remote: Compressing objects: 100% (10/10), done.        
remote: Total 368 (delta 3), reused 10 (delta 3), pack-reused 355        
Receiving objects: 100% (368/368), 159.34 KiB | 1.20 MiB/s, done.
Resolving deltas: 100% (154/154), done.
Submodule path 'deps/pybind11/tools/clang': checked out '6a00cbc4a9b8e68b71caf7f774b3f9c753ae84d5'
```

#### install build-essential

```bash
$ sudo apt-get update && sudo apt-get install build-essential
Hit:1 http://us.archive.ubuntu.com/ubuntu jammy InRelease
Hit:2 http://security.ubuntu.com/ubuntu jammy-security InRelease
Hit:3 http://us.archive.ubuntu.com/ubuntu jammy-updates InRelease
Hit:4 http://us.archive.ubuntu.com/ubuntu jammy-backports InRelease
Reading package lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
...
```

#### create a conda environment called dnp3-sandbox (Python==3.10)

```bash
$ conda create -n dnp3-sandbox python=3.10
Collecting package metadata (current_repodata.json): done
Solving environment: done

## Package Plan ##

  environment location: /home/kefei/miniconda3/envs/dnp3-sandbox

  added / updated specs:
    - python=3.10


The following NEW packages will be INSTALLED:
...
```

#### activate the virtual environment and install required dependency for build (i.e., cmake)

```bash
$ conda activate dnp3-sandbox
(dnp3-sandbox) $ pip install cmake
Collecting cmake
  Downloading cmake-3.25.0-py2.py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (23.7 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 23.7/23.7 MB 2.1 MB/s eta 0:00:00
Installing collected packages: cmake
Successfully installed cmake-3.25.0
```

#### (at repo root path) run `python setup.py install`

Watch the artifact created at "build/" folder.
e.g., `lib.linux-x86_64-cpython-310/pydnp3.cpython-310-x86_64-linux-gnu.so`

```bash
running install
/home/kefei/miniconda3/envs/dnp3-sandbox/lib/python3.10/site-packages/setuptools/command/install.py:34: SetuptoolsDeprecationWarning: setup.py install is deprecated. Use build and pip and other standards-based tools.
  warnings.warn(
/home/kefei/miniconda3/envs/dnp3-sandbox/lib/python3.10/site-packages/setuptools/command/easy_install.py:144: EasyInstallDeprecationWarning: easy_install command is deprecated. Use build and pip and other standards-based tools.
  warnings.warn(
running bdist_egg
running egg_info
writing src/dnp3_python.egg-info/PKG-INFO
writing dependency_links to src/dnp3_python.egg-info/dependency_links.txt
writing entry points to src/dnp3_python.egg-info/entry_points.txt
writing top-level names to src/dnp3_python.egg-info/top_level.txt
reading manifest file 'src/dnp3_python.egg-info/SOURCES.txt'
adding license file 'LICENSE'
...
Processing dnp3_python-0.2.3b2-py3.10-linux-x86_64.egg
removing '/home/kefei/miniconda3/envs/dnp3-sandbox/lib/python3.10/site-packages/dnp3_python-0.2.3b2-py3.10-linux-x86_64.egg' (and everything under it)
creating /home/kefei/miniconda3/envs/dnp3-sandbox/lib/python3.10/site-packages/dnp3_python-0.2.3b2-py3.10-linux-x86_64.egg
Extracting dnp3_python-0.2.3b2-py3.10-linux-x86_64.egg to /home/kefei/miniconda3/envs/dnp3-sandbox/lib/python3.10/site-packages
dnp3-python 0.2.3b2 is already the active version in easy-install.pth
Installing dnp3demo script to /home/kefei/miniconda3/envs/dnp3-sandbox/bin

Installed /home/kefei/miniconda3/envs/dnp3-sandbox/lib/python3.10/site-packages/dnp3_python-0.2.3b2-py3.10-linux-x86_64.egg
Processing dependencies for dnp3-python==0.2.3b2
Finished processing dependencies for dnp3-python==0.2.3b2
```

(View full log
at [cmake-build-dnp3-python.log](https://gist.github.com/kefeimo/35b7536c235c31ba0abf0da7fa7c4125#file-cmake-build-dnp3-python-log))

#### run `python setup.py bdist_wheel --plat-name=manylinux1_x86_64` to build wheel

Watch the artifact created at "dist/" folder.
e.g., `dnp3_python-0.2.3b2-cp310-cp310-manylinux1_x86_64.whl`

```bash
$ python setup.py bdist_wheel --plat-name=manylinux1_x86_64
running bdist_wheel
running build
running build_py
running build_ext
CMake Deprecation Warning at CMakeLists.txt:1 (cmake_minimum_required):
  Compatibility with CMake < 2.8.12 will be removed from a future version of
  CMake.

  Update the VERSION argument <min> value or use a ...<max> suffix to tell
  CMake that the project does not need compatibility with older versions.
...
adding 'dnp3_python-0.2.3b2.dist-info/METADATA'
adding 'dnp3_python-0.2.3b2.dist-info/WHEEL'
adding 'dnp3_python-0.2.3b2.dist-info/entry_points.txt'
adding 'dnp3_python-0.2.3b2.dist-info/top_level.txt'
adding 'dnp3_python-0.2.3b2.dist-info/RECORD'
removing build/bdist.linux-x86_64/wheel
```

### Building on windows systems
To get started install the following programs:
* Latest Visual Studio (2022 at the time of writing)
    * Desktop development with C++ - Workload
    * Git for Windows - Individual components
* Local python install
    * install python package `wheel` with `py -m pip install wheel`
    
#### Compiling
* Open up powershell from within VS2022 - Tools -> Command Line -> Developer Powershell
* run a `git clone --recurse-submodules https://github.com/VOLTTRON/dnp3-python.git` to obtain the latest version
* `cd dnp3-python`
* `python setup.py install`
* `python setup.py bdist_wheel`
* the `whl` file should now be in the `dist` folder


More information
about [building wheels](https://wheel.readthedocs.io/en/stable/user_guide.html?highlight=bdist_wheel#building-wheels),
[The Story of Wheel](https://wheel.readthedocs.io/en/stable/story.html?highlight=bdist_wheel#the-story-of-wheel),
[manylinux](https://github.com/pypa/manylinux) and `--plat-name`
in [Running setuptools commands](https://setuptools.pypa.io/en/latest/deprecated/commands.html).

## Useful Resource

* [Setup Tools Doc](https://setuptools.pypa.io/en/latest/)
* [wheel Doc](https://wheel.readthedocs.io/en/stable/index.html)
