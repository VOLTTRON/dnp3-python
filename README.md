# dnp3-python
Python bindings for the [opendnp3](https://github.com/automatak/dnp3) library,  an open source
implementation of the [DNP3](http://ww.dnp.org) protocol stack written in C++14.

Note:  This is a redesign of [pydnp3](https://github.com/ChargePoint/pydnp3) and work in progress.  


**Supported Platforms:** Linux

## Dependencies
To build the library from source, you must have:

* A toolchain with a C++14 compiler
* CMake >= 2.8.12 (https://cmake.org/download/)

This repository includes two repositories as submodules (under `deps/`):

* dnp3 (https://github.com/automatak/dnp3)
* pybind11 (https://github.com/Kisensum/pybind11) - This is a fork containing a minor patch
required to compile some of the pydnp3 wrapper code. It will be replaced with pybind11 proper
when the issue is resolved.

## Install
Support Python >= 3.8, using pip
```
    $ pip install dnp3-python
```
#### Validate Installation
After installing the package, run the following command to validate the installation.
```
    $ python -m dnp3demo
```
Expected output
```
ms(1666217818743) INFO    manager - Starting thread (0)
channel state change: OPENING
ms(1666217818744) INFO    tcpclient - Connecting to: 127.0.0.1
ms(1666217818744) WARN    tcpclient - Error Connecting: Connection refused
2022-10-19 17:16:58,744 dnp3demo.data_retrieval_demo    DEBUG   Initialization complete. Master Station in command loop.
ms(1666217818746) INFO    manager - Starting thread (0)
ms(1666217818746) INFO    server - Listening on: 127.0.0.1:20000
2022-10-19 17:16:58,746 dnp3demo.data_retrieval_demo    DEBUG   Initialization complete. OutStation in command loop.
ms(1666217819745) INFO    tcpclient - Connecting to: 127.0.0.1
ms(1666217819745) INFO    tcpclient - Connected to: 127.0.0.1
channel state change: OPEN
ms(1666217819745) INFO    server - Accepted connection from: 127.0.0.1

...

===important log: case6 get_db_by_group_variation ==== 2 2022-10-19 17:17:01.157129 {GroupVariation.Group30Var6: {0: 5.588852790313346, 1: 17.7138169198775, 2: 22.456219616993142, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}}
===important log: case6b get_db_by_group_variation ==== 2 2022-10-19 17:17:01.157407 {GroupVariation.Group1Var2: {0: True, 1: True, 2: True, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}}
===important log: case6c get_db_by_group_variation ==== 2 2022-10-19 17:17:01.157559 {GroupVariation.Group30Var1: {0: 5, 1: 17, 2: 22, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}}
===important log: case7 get_db_by_group_variation_index ==== 2 2022-10-19 17:17:01.157661 {GroupVariation.Group30Var6: {0: 5.588852790313346}}
===important log: case7b get_db_by_group_variation_index ==== 2 2022-10-19 17:17:01.157878 17.7138169198775
===important log: case7c get_db_by_group_variation_index ==== 2 2022-10-19 17:17:01.157974 0.0

```


## For Developers

pydnp3 is a thin wrapper around most all of the opendnp3 classes. Documentation for the opendnp3
classes is available at [automatak](https://www.automatak.com/opendnp3/#documentation).

Please find more info in the /docs folder about packaging process, e.g., building from the C++ source code, packaging native Python code with C++ binding code, etc.

