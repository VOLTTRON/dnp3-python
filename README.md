# dnp3-python

## About the DNP3 Protocol

Distributed Network Protocol (DNP or DNP3) has achieved a large-scale acceptance since its introduction in 1993. This
protocol is an immediately deployable solution for monitoring remote sites because it was developed for communication of
critical infrastructure status, allowing for reliable remote control.

GE-Harris Canada (formerly Westronic, Inc.) is generally credited with the seminal work on the protocol. This protocol
is, however, currently implemented by an extensive range of manufacturers in a variety of industrial applications, such
as electric utilities.

DNP3 is composed of three layers of the OSI seven-layer functions model. These layers are application layer, data link
layer, and transport layer. Also, DNP3 can be transmitted over a serial bus connection or over a TCP/IP network.

#### Main DNP3 Capabilities

As an intelligent and robust SCADA protocol, DNP3 gives you many capabilities. Some of them are:

- DNP3 can request and respond with multiple data types in single messages
- Response without request (unsolicited messages)
- It allows multiple masters and peer-to-peer operations
- It supports time synchronization and a standard time format
- It includes only changed data in response messages

For more details about the DNP3 protocol, the `DNP3_Primer.md` article under /docs folder is a good start.

## About the dnp3-python Package

Python bindings for the [opendnp3](https://github.com/automatak/dnp3) library, an open source
implementation of the [DNP3](http://ww.dnp.org) protocol stack written in C++14.

Note:  This is a redesign of [pydnp3](https://github.com/ChargePoint/pydnp3) and work in progress.

**Supported Platforms:** Linux 20.04

## Install

Support Python >= 3.8, using pip

```
$ pip install dnp3-python
```

#### Validate Installation

After installing the package, run the following command to validate the installation.

```
$ dnp3demo
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

> **_NOTE:_**  Use `dnp3demo -h` to see demo options

```
$ dnp3demo -h
usage: dnp3demo [-h] {master,outstation,demo} ...

Dnp3 use case demo

optional arguments:
  -h, --help            show this help message and exit

dnp3demo Sub-command:
  {master,outstation,demo}
    master              run a configurable master interactive program
    outstation          run a configurable outstation interactive program
    demo                run dnp3 demo with default master and outstation
```

For more details about the `dnp3demo` module, please ref to "dnp3demo-module.md" in "/docs".

## For Developers

pydnp3 is a thin wrapper around opendnp3 classes. Documentation for the opendnp3
classes is available at [automatak](https://www.automatak.com/opendnp3/#documentation).

#### Dependencies

To build the library from source, you must have:

* A toolchain with a C++14 compiler
* CMake >= 2.8.12 (https://cmake.org/download/)

This repository includes two repositories as submodules (under `deps/`):

* dnp3 (https://github.com/automatak/dnp3)
* pybind11 (https://github.com/Kisensum/pybind11) - This is a fork containing a minor patch
  required to compile some of the pydnp3 wrapper code. It will be replaced with pybind11 proper
  when the issue is resolved.

Please find more info in the /docs folder about packaging process, e.g., building from the C++ source code,
packaging native Python code with C++ binding code, etc.

