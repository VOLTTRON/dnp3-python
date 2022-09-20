import logging
import random
import sys

from datetime import datetime
from pydnp3 import opendnp3
# from master import command_callback
from dnp3_python.master_utils import command_callback

# from master_cmd import MasterCmd
# from outstation_cmd import OutstationCmd

from dnp3_python.master_new import MyMasterNew

from dnp3_python.outstation_new import MyOutStationNew

# import visitors

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
    master_application = MyMasterNew(channel_log_level=opendnp3.levels.ALL_COMMS,
                                     master_log_level=opendnp3.levels.ALL_COMMS)
    _log.debug('Initialization complete. Master Station in command loop.')
    # cmd_interface_outstation = OutstationCmd()
    outstation_application = MyOutStationNew(channel_log_level=opendnp3.levels.ALL_COMMS,
                                             outstation_log_level=opendnp3.levels.ALL_COMMS)
    _log.debug('Initialization complete. OutStation in command loop.')

    # sleep(2)  # TODO: the master and outstation init takes time (i.e., configuration). Hard-coded here
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

    # cmd_interface.startup()
    count = 0
    while count < 10:
        sleep(1)  # Note: hard-coded, master station query every 1 sec.

        count += 1
        print(datetime.datetime.now(), "============count ", count, )

        # plan: there are 3 AnalogInput Points,
        # outstation will randomly pick from
        # index 0: [4.0, 7.0, 2.0]
        # index 1: [14.0, 17.0, 12.0]
        # index 1: [24.0, 27.0, 22.0]
        # note: for this version of pydnp3, it needs to inject float type point value, but will parse it into int.

        # master update point value (slower than master query)
        if count % 3 == 1:
            point_values_0 = [4.8, 7.8, 2.8]
            point_values_1 = [14.1, 17.1, 12.1]
            point_values_2 = [24.2, 27.2, 22.2]
            for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
                p_val = random.choice(pts)
                print(f"====== Master send command index {i} with {p_val}")
                # cmd_interface_outstation.application.apply_update(opendnp3.Analog(float(p_val)), i)
                # cmd_interface_master.application.send_direct_operate_command(opendnp3.AnalogOutputInt32(int(p_val)),
                #                                                              i,
                #                                                              command_callback)
                master_application.send_select_and_operate_command(opendnp3.AnalogOutputInt32(int(p_val)),
                                                                             i,
                                                                             command_callback)  # TODO: explore difference between send_direct_operate_command and send_select_and_operate_command
                # TODO: redesign the command_callback workflow (command_callback may not be necessary)

        # sleep(0.41)  # TODO: since it is aychnous, need this walk-around to assure update, use callback instead


        # master station retrieve value

        # use case 6: retrieve point values specified by single GroupVariationIDs and index.
        # demo float AnalogInput,
        # result = master_application.retrieve_all_obj_by_gvids(gv_ids=[opendnp3.GroupVariationID(30, 6),
        #                                                               opendnp3.GroupVariationID(1, 2)])
        # result = master_application.retrieve_val_by_gv(gv_id=opendnp3.GroupVariationID(30, 6),)
        result = master_application.get_db_by_group_variation(group=40, variation=4)
        print(f"===important log: case6 get_db_by_group_variation ==== {count}", datetime.datetime.now(),
              result)

        result = master_application.get_db_by_group_variation(group=40, variation=1)
        print(f"===important log: case6b get_db_by_group_variation ==== {count}", datetime.datetime.now(),
              result)

        result = master_application.get_db_by_group_variation(group=30, variation=6)
        print(f"===important log: case6b get_db_by_group_variation ==== {count}", datetime.datetime.now(),
              result)

    _log.debug('Exiting.')
    master_application.shutdown()
    outstation_application.shutdown()


if __name__ == '__main__':
    main()
