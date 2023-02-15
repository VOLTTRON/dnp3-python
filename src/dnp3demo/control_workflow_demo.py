import logging
import random
import sys

from pydnp3 import opendnp3
from dnp3_python.dnp3station.station_utils import command_callback
from dnp3_python.dnp3station.master_new import MyMasterNew
from dnp3_python.dnp3station.outstation_new import MyOutStationNew

from time import sleep
import datetime

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log = logging.getLogger("control_workflow_demo")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)


def main():
    # cmd_interface_master = MasterCmd()
    master_application = MyMasterNew(
        # channel_log_level=opendnp3.levels.ALL_COMMS,
        # master_log_level=opendnp3.levels.ALL_COMMS
        # soe_handler=SOEHandler(soehandler_log_level=logging.DEBUG)
                                     )
    master_application.start()
    _log.debug('Initialization complete. Master Station in command loop.')
    # cmd_interface_outstation = OutstationCmd()
    outstation_application = MyOutStationNew(
        # channel_log_level=opendnp3.levels.ALL_COMMS,
        # outstation_log_level=opendnp3.levels.ALL_COMMS
    )
    outstation_application.start()
    _log.debug('Initialization complete. OutStation in command loop.')

    count = 0
    while count < 10:
        sleep(2)  # Note: hard-coded, master station query every 1 sec.

        count += 1
        print(datetime.datetime.now(), "============count ", count, )

        # plan: there are 3 AnalogInput Points,
        # outstation will randomly pick from
        # index 0: [4.0, 7.0, 2.0]
        # index 1: [14.0, 17.0, 12.0]
        # index 1: [24.0, 27.0, 22.0]
        # note: for this version of dnp3_python, it needs to inject float type point value, but will parse it into int.

        # master update point value (slower than master query)
        if count % 3 == 1:
            point_values_0 = [4.8, 7.8, 2.8]
            point_values_1 = [14.1, 17.1, 12.1]
            point_values_2 = [24.2, 27.2, 22.2]
            for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
                p_val = random.choice(pts)
                print(f"====== Master send command index {i} with {p_val}")
                master_application.send_direct_operate_command(opendnp3.AnalogOutputDouble64(float(p_val)),
                                                               i,
                                                               command_callback)

        # update binaryInput value as well

        master_application.send_direct_operate_command(
            opendnp3.ControlRelayOutputBlock(opendnp3.ControlCode.LATCH_ON),
            0,
            command_callback)
        master_application.send_direct_operate_command(
            opendnp3.ControlRelayOutputBlock(opendnp3.ControlCode.LATCH_ON),
            2,
            command_callback)
        p_val = random.choice([opendnp3.ControlCode.LATCH_ON, opendnp3.ControlCode.LATCH_OFF])
        master_application.send_direct_operate_command(
            opendnp3.ControlRelayOutputBlock(p_val),
            1,
            command_callback)

        # demo send_direct_operate_command_set
        command_set = opendnp3.CommandSet()
        command_set.Add([
            opendnp3.WithIndex(opendnp3.ControlRelayOutputBlock(opendnp3.ControlCode.LATCH_ON), 3),
            opendnp3.WithIndex(opendnp3.ControlRelayOutputBlock(opendnp3.ControlCode.LATCH_OFF), 4),
            opendnp3.WithIndex(opendnp3.ControlRelayOutputBlock(opendnp3.ControlCode.LATCH_ON), 5)
        ])
        master_application.send_direct_operate_command_set(command_set, command_callback)

        # demo using send_direct_point_command (with consistent parameter than send_direct_operate_command)
        # operate on 4,5,6 (or # operate on 8,9,10)
        if count % 3 == 1:
            point_values_0 = [4.8, 7.8, 2.8]
            point_values_1 = [14.1, 17.1, 12.1]
            point_values_2 = [24.2, 27.2, 22.2]
            for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
                p_val = random.choice(pts)
                print(f"====== Master send command index {i} with {p_val}")
                # master_application.send_direct_operate_command(opendnp3.AnalogOutputDouble64(float(p_val)),
                #                                                i,
                #                                                command_callback)
                # for group40var4 AnalogOutputDouble
                master_application.send_direct_point_command(group=40, variation=4, index=i + 4,
                                                             val_to_set=p_val + 0.0025)  # operate on 4,5,6
                # for group40var2 AnalogOutputInt32
                master_application.send_direct_point_command(group=40, variation=2, index=i + 4 + 4,
                                                             val_to_set=int(p_val))  # operate on 8,9,10
                # for group10var2 BinaryOutput
                master_application.send_direct_point_command(group=10, variation=2, index=i + 4 + 4,
                                                             val_to_set=True)  # operate on 8,9,10

        # master station retrieve value

        # use case 6: retrieve point values specified by single GroupVariationIDs and index.
        # demo float AnalogOutput,
        result = master_application.get_db_by_group_variation(group=40, variation=4)
        print(f"===important log: case6 get_db_by_group_variation ==== {count}", "\n", datetime.datetime.now(),
              result)

        result = master_application.get_db_by_group_variation(group=40, variation=2)
        print(f"===important log: case6b get_db_by_group_variation ==== {count}", "\n", datetime.datetime.now(),
              result)

        result = master_application.get_db_by_group_variation(group=10, variation=2)
        print(f"===important log: case6c get_db_by_group_variation ==== {count}", "\n", datetime.datetime.now(),
              result)

    _log.debug('Exiting.')
    master_application.shutdown()
    outstation_application.shutdown()


if __name__ == '__main__':
    main()
