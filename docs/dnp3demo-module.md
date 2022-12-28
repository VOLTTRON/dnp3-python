# dnp3demo Module

This is a documentation about running the `dnp3demo` module shipped with the dnp3-python package.

## Quick-start

After installing the dnp3-python package, the `dnp3demo` module will be accessible from the (virtual) environment /bin
path, and we can run `dnp3demo` just as if it is an executable.

When running `dnp3demo` a typical output is as follows

```
$ dnp3demo
ms(1672178544485) INFO    manager - Starting thread (0)
ms(1672178544486) INFO    server - Listening on: 0.0.0.0:20000
2022-12-27 16:02:24,486 __main__        DEBUG   Initialization complete. OutStation in command loop.
ms(1672178544486) INFO    manager - Starting thread (0)
channel state change: OPENING
ms(1672178544486) INFO    tcpclient - Connecting to: 127.0.0.1
ms(1672178544486) INFO    tcpclient - Connected to: 127.0.0.1
channel state change: OPEN
2022-12-27 16:02:24,486 __main__        DEBUG   Initialization complete. Master Station in command loop.
ms(1672178544486) INFO    server - Accepted connection from: 127.0.0.1
2022-12-27 16:02:26.492432 ============count  1
====== Outstation update index 0 with 5.328052940961683
====== Outstation update index 1 with 17.930440207515584
====== Outstation update index 2 with 24.803467249246957
====== Outstation update index 0 with True
====== Outstation update index 1 with True
====== Outstation update index 2 with False
===important log: case6 get_db_by_group_variation(group=30, variation=6) ==== 1 
 2022-12-27 16:02:26.693757 {GroupVariation.Group30Var6: {0: 5.328052940961683, 1: 17.930440207515584, 2: 24.803467249246957, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}}
===important log: case6b get_db_by_group_variation(group=1, variation=2) ==== 1 
 2022-12-27 16:02:26.894264 {GroupVariation.Group1Var2: {0: True, 1: True, 2: True, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}}
===important log: case6c get_db_by_group_variation(group=30, variation=1) ==== 1 
 2022-12-27 16:02:27.096706 {GroupVariation.Group30Var1: {0: 5, 1: 17, 2: 24, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}}
2022-12-27 16:02:29.098663 ============count  2
===important log: case6 get_db_by_group_variation(group=30, variation=6) ==== 2 
 2022-12-27 16:02:29.299794 {GroupVariation.Group30Var6: {0: 5.328052940961683, 1: 17.930440207515584, 2: 24.803467249246957, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}}
===important log: case6b get_db_by_group_variation(group=1, variation=2) ==== 2 
 2022-12-27 16:02:29.503377 {GroupVariation.Group1Var2: {0: True, 1: True, 2: True, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}}
===important log: case6c get_db_by_group_variation(group=30, variation=1) ==== 2 
 2022-12-27 16:02:29.709358 {GroupVariation.Group30Var1: {0: 5, 1: 17, 2: 24, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}}

....
2022-12-27 16:02:50,610 __main__        DEBUG   Exiting.
channel state change: CLOSED
channel state change: SHUTDOWN
ms(1672178572613) WARN    server - End of file
ms(1672178572613) INFO    manager - Exiting thread (0)
ms(1672178574616) INFO    server - Operation aborted.
ms(1672178578632) INFO    manager - Exiting thread (0)
```

## Get-point demo

The `dnp3demo` module run the “data_retrieval_demo.py” script by default. Or we can use the explicit way by
running `dnp3demo demo --demo-get-point`. In this demo, an outstation update its database values (i.e., data object
values) and have a master poll the outstation database.

The get-point demo consist of the following processes:

- Initialize an outstation instance and start it.
- Initialize a master instance and start it.
- (With proper configuration, connection establish between the master and the outstation.)
- The outstation updates its database point values.
- The master station poll the outstation to retrieve data point values.
- Stop both the master and the outstation.

In each process stage, the affective code snippet and the corresponding output is as follows.

#### Initialization

We can use the `MyOutStationNew()` and `MyMasterNew()` construction methods to instantiate an outstation and and an
master instance. Note the station instances are configurable if different configuration setup is desired. However, in
this demo, the default configuration is implemented and cannot be changed from the command line interface.

```
# init an outstation using default configuration, e.g., port=20000. Then start.
outstation_application = MyOutStationNew()
outstation_application.start()
_log.debug('Initialization complete. OutStation in command loop.')

# init a master using default configuration, e.g., port=20000. Then start.
master_application = MyMasterNew()
master_application.start()
_log.debug('Initialization complete. Master Station in command loop.')
```

```
# Expected output when a master is connected to an outstation

ms(1672179135240) INFO    manager - Starting thread (0)
ms(1672179135241) INFO    server - Listening on: 0.0.0.0:20000
2022-12-27 16:12:15,241 dnp3demo.data_retrieval_demo    DEBUG   Initialization complete. OutStation in command loop.
ms(1672179135241) INFO    manager - Starting thread (0)
channel state change: OPENING
ms(1672179135241) INFO    tcpclient - Connecting to: 127.0.0.1
ms(1672179135241) INFO    tcpclient - Connected to: 127.0.0.1
channel state change: OPEN
2022-12-27 16:12:15,241 dnp3demo.data_retrieval_demo    DEBUG   Initialization complete. Master Station in command loop.
ms(1672179135241) INFO    server - Accepted connection from: 127.0.0.1
```

#### Outstation update database

An outstation application instance can update its database value
using `outstation_application.apply_update(measurement: OutstationCmdType, index: int)`

```
for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
		p_val = random.choice(pts)
		print(f"====== Outstation update index {i} with {p_val}")
		outstation_application.apply_update(opendnp3.Analog(value=float(p_val)), i)
```

```
2022-12-27 16:12:17.244255 ============count  1
====== Outstation update index 0 with 7.857376294282144
====== Outstation update index 1 with 17.10942437272606
====== Outstation update index 2 with 22.71609594500621
```

#### Master poll outstation

A master application instance can poll the outstation database
using `get_db_by_group_variation(group: int, variation: int)`. It returns a dict-like database structure.

```
result = master_application.get_db_by_group_variation(group=30, variation=6)
print(f"===important log: case6 get_db_by_group_variation(group=30, variation=6) ==== {count}", "\n",
      datetime.datetime.now(),
      result)
result = master_application.get_db_by_group_variation(group=1, variation=2)
print(f"===important log: case6b get_db_by_group_variation(group=1, variation=2) ==== {count}", "\n",
      datetime.datetime.now(),
      result)
result = master_application.get_db_by_group_variation(group=30, variation=1)
print(f"===important log: case6c get_db_by_group_variation(group=30, variation=1) ==== {count}", "\n",
      datetime.datetime.now(),
      result)
```

```
===important log: case6 get_db_by_group_variation(group=30, variation=6) ==== 1 
 2022-12-27 16:12:17.446272 {GroupVariation.Group30Var6: {0: 7.857376294282144, 1: 17.10942437272606, 2: 22.71609594500621, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}}
===important log: case6b get_db_by_group_variation(group=1, variation=2) ==== 1 
 2022-12-27 16:12:17.649596 {GroupVariation.Group1Var2: {0: True, 1: True, 2: True, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}}
===important log: case6c get_db_by_group_variation(group=30, variation=1) ==== 1 
 2022-12-27 16:12:17.850156 {GroupVariation.Group30Var1: {0: 7, 1: 17, 2: 22, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}}
```

Observe that the polling result is consistent with the outstation updating values from the last stage. From
the [data object specification](https://www.vtscada.com/help/Content/D_Tags/Dev_DNPObjTypes.htm), Group30Variation60 is
the GroupVariation-ID for AnalogInput(Float64) and Group1Variation2 is for BinaryInput. Note that Group30Variation1 is
for AnalogInput(Int32), thus the values are round to integers.

Note: there are other database polling methods available, for
example `get_db_by_group_variation_index(group: int, variation: int, index: int)`

#### Stop the application

Use `.stop()` method for both master application and outstation application to stop the application and release the
threads.

```
_log.debug('Exiting.')
master_application.shutdown()
outstation_application.shutdown()
```

```
# output
2022-12-27 16:12:41,348 dnp3demo.data_retrieval_demo    DEBUG   Exiting.
channel state change: CLOSED
ms(1672179163352) WARN    server - End of file
channel state change: SHUTDOWN
ms(1672179163352) INFO    manager - Exiting thread (0)
ms(1672179165356) INFO    server - Operation aborted.
ms(1672179169369) INFO    manager - Exiting thread (0)
```

## set-point demo

We can run this demo by using `dnp3demo demo --demo-set-point`. Compared to the get-point demo, the master station will
send control command to the outstation and then poll the outstation database to check the states.

The set-point demo consist of the following processes:

- Initialize station instances (i.e., master and outstation) and start them.
- The master send control command to the outstation.
- The master station poll the outstation to retrieve data point values.
- Stop both the master and the outstation.

We will not go into details into each process stage since they very similar to the get-point demo—except for the
master-send-control stage. Check the `send_direct_operate_command` method for more details about the public interface.

## Run an interactive configurable standalone outstation

The `dnp3demo` module also provides a command line interface to run an interactive outstation program that is
configurable. Using `dnp3demo outstation -h` command to see configuration options

```
$ dnp3demo outstation -h
usage: dnp3demo outstation [-h] [--outstation-ip= <IP>] [--port= <PORT>] [--master-id= <ID>] [--outstation-id= <ID>]

run a configurable outstation interactive program

optional arguments:
  -h, --help            show this help message and exit
  --outstation-ip= <IP>
                        outstation ip, default: 0.0.0.0
  --port= <PORT>        port, default: 20000
  --master-id= <ID>     master id, default: 2
  --outstation-id= <ID>
                        master id, default: 1
```

To start an outstation instance with default configuration, run `dnp3demo outstation`

```
$ dnp3demo outstation
dnp3demo.run_outstation {'command': 'outstation', 'outstation_ip=': '0.0.0.0', 'port=': 20000, 'master_id=': 2, 'outstation_id=': 1}
ms(1672194004907) INFO    manager - Starting thread (0)
2022-12-27 20:20:04,907 control_workflow_demo   INFO    Connection Config
2022-12-27 20:20:04,907 control_workflow_demo   INFO    Connection Config
2022-12-27 20:20:04,907 control_workflow_demo   INFO    Connection Config
ms(1672194004908) INFO    server - Listening on: 0.0.0.0:20000
2022-12-27 20:20:04,908 control_workflow_demo   DEBUG   Initialization complete. Outstation in command loop.
2022-12-27 20:20:04,908 control_workflow_demo   DEBUG   Initialization complete. Outstation in command loop.
2022-12-27 20:20:04,908 control_workflow_demo   DEBUG   Initialization complete. Outstation in command loop.
Connection error.
Connection Config {'outstation_ip_str': '0.0.0.0', 'port': 20000, 'masterstation_id_int': 2, 'outstation_id_int': 1}
Start retry...
Connection error.
Connection Config {'outstation_ip_str': '0.0.0.0', 'port': 20000, 'masterstation_id_int': 2, 'outstation_id_int': 1}
Start retry...
```

<aside>
💡 Note: if there is no connection established the application will keep on retrying. One such connection error might be caused by only outstation has started but no master.

</aside>

We need to start a master to establish valid connection. From another terminal, run `dnp3demo master` to start a default
master instance and wait to see the following messages at the original (outstation) terminal.

```
ms(1672194379180) INFO    server - Accepted connection from: 127.0.0.1
==== Outstation Operation MENU ==================================
<ai> - update analog-input point value (for local reading)
<ao> - update analog-output point value (for local control)
<bi> - update binary-input point value (for local reading)
<bo> - update binary-output point value (for local control)
<dd> - display database
<dc> - display configuration
=================================================================

======== Your Input Here: ==(outstation)======
```

#### <dd> - display database

Run “dd” command at the main menu to display the database. Note: for a fresh-started outstation database all the data
point values are empty (init value).

```
======== Your Input Here: ==(outstation)======
dd
You chose < dd > - display database
{'Analog': {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}, 'AnalogOutputStatus': {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}, 'Binary': {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}, 'BinaryOutputStatus': {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}}
```

#### <dc> - display configuration

Run “dc” command to display the configuration

```
======== Your Input Here: ==(outstation)======
dc
You chose < dc> - display configuration
{'outstation_ip_str': '0.0.0.0', 'port': 20000, 'masterstation_id_int': 2, 'outstation_id_int': 1}
```

Note: for this version, the configuration is only available when first start the program (i.e., when
running `dnp3demo outstation`.) If we would like to use different configuration, for example, set port to “21000”, then
we should cease the program (ctrl+c) and run `dnp3demo outstation --port=21000`

#### ai - update analog-input point value (for local reading)

The “ai” option (stands for analog-input) is a wrapper on the `apply_update` method and provides a command line
interface for users to interact with outstation application instance.

In the following demo, we update the index0 to value=0.1234, and index1 to value=1.2345. The prompt will verify with the
database point value within the group in interests .

```
======== Your Input Here: ==(outstation)======
ai
You chose <ai> - update analog-input point value (for local reading)
Type in <float> and <index>. Separate with space, then hit ENTER.
Type 'q', 'quit', 'exit' to main menu.

======== Your Input Here: ==(outstation)======
0.1234 0
{'Analog': {0: 0.1234, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}}
You chose <ai> - set analog-input point value
Type in <float> and <index>. Separate with space, then hit ENTER.
Type 'q', 'quit', 'exit' to main menu.

======== Your Input Here: ==(outstation)======
1.2345 1
{'Analog': {0: 0.1234, 1: 1.2345, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}}
You chose <ai> - set analog-input point value
Type in <float> and <index>. Separate with space, then hit ENTER.
Type 'q', 'quit', 'exit' to main menu.
```

To return to the main menu, use “q” (or “quit” or “exit”.) Then we can verify with the `<dd> - display database`
command.

```
======== Your Input Here: ==(outstation)======
q
==== Outstation Operation MENU ==================================
<ai> - update analog-input point value (for local reading)
<ao> - update analog-output point value (for local control)
<bi> - update binary-input point value (for local reading)
<bo> - update binary-output point value (for local control)
<dd> - display database
<dc> - display configuration
=================================================================

======== Your Input Here: ==(outstation)======
dd
You chose < dd > - display database
{'Analog': {0: 0.1234, 1: 1.2345, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}, 'AnalogOutputStatus': {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}, 'Binary': {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}, 'BinaryOutputStatus': {0: None, 1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None}}
==== Outstation Operation MENU ==================================
<ai> - update analog-input point value (for local reading)
<ao> - update analog-output point value (for local control)
<bi> - update binary-input point value (for local reading)
<bo> - update binary-output point value (for local control)
<dd> - display database
<dc> - display configuration
=================================================================
```

#### "ao" "bi" and "bo" commands

The "ao" "bi" and "bo" commands are very similar to the "ai" command, and we will not go into the details for this demo.

## Run an interactive configurable standalone master

To start a standalone master program with default configuration we use `dnp3demo master`.  (As a reminder, we need to
start an outstation to establish a valid connection to continue the following demo.)

```
==== Master Operation MENU ==================================
<ao> - set analog-output point value (for remote control)
<bo> - set binary-output point value (for remote control)
<dd> - display/polling (outstation) database
<dc> - display configuration
=================================================================

======== Your Input Here: ==(master)======
```

The master’s interface feels similar to the one of the outstation, which is expected since master is the counterpart of
outstation.

```
======== Your Input Here: ==(master)======
You chose < dd > - display database
{'Analog': {0: 0.1234, 1: 1.2345, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}, 'AnalogOutputStatus': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}, 'Binary': {0: False, 1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}, 'BinaryOutputStatus': {0: False, 1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}}
==== Master Operation MENU ==================================
<ao> - set analog-output point value (for remote control)
<bo> - set binary-output point value (for remote control)
<dd> - display/polling (outstation) database
<dc> - display configuration
=================================================================
```

```
======== Your Input Here: ==(master)======
dc
You chose < dc > - display configuration
{'masterstation_ip_str': '0.0.0.0', 'outstation_ip_str': '127.0.0.1', 'port': 20000, 'masterstation_id_int': 2, 'outstation_id_int': 1}
```

While the result might look the same, the “dd” command from master and outstation have the following differences:

- Since the database state is stored at the outstation side, it is instantly available to the outstation application,
  while the master needs to poll the outstation to retrieve the point values. (e.g., using `get_db_by_group_variation`
  or `get_db_by_group_variation_index` method.)
- The master’s dd command require interaction with an outstation, while the outstation’s dd does not require a master.

### "ao" - set analog-output point value (for remote control)

The “ao” command from the master side mimics the control workflow that a master send set analog-output value command to
the outstation.

```
======== Your Input Here: ==(master)======
100.123 1
SUCCESS {'AnalogOutputStatus': {0: 0.0, 1: 100.123, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}}
You chose <ao> - set analog-output point value
Type in <float> and <index>. Separate with space, then hit ENTER.
Type 'q', 'quit', 'exit' to main menu.

======== Your Input Here: ==(master)======
200.456 2
SUCCESS {'AnalogOutputStatus': {0: 0.0, 1: 100.123, 2: 200.456, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}}
You chose <ao> - set analog-output point value
Type in <float> and <index>. Separate with space, then hit ENTER.
Type 'q', 'quit', 'exit' to main menu.
```

Note the “ao” command from master and outstation have the following differences:

- The master’s ao command implement the remote-control application, while the outstation’s ao command implement
  local-control application.
- Underneath the hood, the master application evoke the `send_direct_operate_command` method rather than `apply_update`
  method by the outstation.
- Recall that, since the database state is stored at the outstation side, the master’s ao command require interaction
  with an outstation, while the outstation’s ao doesn’t require a master.

```
======== Your Input Here: ==(master)======
q
==== Master Operation MENU ==================================
<ao> - set analog-output point value (for remote control)
<bo> - set binary-output point value (for remote control)
<dd> - display/polling (outstation) database
<dc> - display configuration
=================================================================

======== Your Input Here: ==(master)======
dd
You chose < dd > - display database
{'Analog': {0: 0.1234, 1: 1.2345, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}, 'AnalogOutputStatus': {0: 0.0, 1: 100.123, 2: 200.456, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0}, 'Binary': {0: False, 1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}, 'BinaryOutputStatus': {0: False, 1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}}
==== Master Operation MENU ==================================
```

#### "bo" command but no "ai" or "bi" for master

The `<bo> - set binary-output point value (for remote control)` command is very similar to the "ao" command, except that
“bo” is
to control the BinaryOutput points.

Note that there is no “ai” or “bi” commands on the master side, since from the DNP3 (or SCADA) logics on the
Output-typed points can be controlled remotely and set by a master.

## Summary

In this document, we walk through the `dnp3demo` module shipped with the dnp3-python package.

- Introduced the `dnp3demo -h` command and explained the helper menu.
- There are three sub-commands available: demo, master, and outstation.
- The “demo” subcommand run a paired outstation and master with the option to demo data-retrieval workflow and control
  workflow when specifying the `--demo-get-point` and `--demo-set-point` options respectively.
- The “master” and “outstation” subcommands provide interface to run an interactive standalone master and outstation
  respectively. The standalone station instance is configurable through the command line interface. We can use `-h`
  syntax to see more details.
- We demonstrate the options when running a master and an outstation programming for features including `<dd> - display
  database`, `<dc> - display configuration`, `<ai> - update analog-input point value (for local reading)`,
  and `<ao> - set
  analog-output point value (for remote control)`.
- Note that while some commands from either master or outstation side share the same name or produce identical results,
  the underlying logic, implementation details or the application scenario are different.
