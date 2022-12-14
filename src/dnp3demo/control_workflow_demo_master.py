import logging
import random
import sys

from pydnp3 import opendnp3
from dnp3_python.dnp3station.station_utils import command_callback
from dnp3_python.dnp3station.master_new import MyMasterNew
from dnp3_python.dnp3station.outstation_new import MyOutStationNew

from time import sleep
import datetime
import json

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
    # outstation_application = MyOutStationNew(
    #     # channel_log_level=opendnp3.levels.ALL_COMMS,
    #     # outstation_log_level=opendnp3.levels.ALL_COMMS
    # )
    # outstation_application.start()
    # _log.debug('Initialization complete. OutStation in command loop.')

    sleep(2)
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

    # cmd_interface.startup()
    count = 0
    while count < 1000:
        # sleep(1)  # Note: hard-coded, master station query every 1 sec.

        count += 1

        print()
        print("=================================================================")
        print("Set AnalogOutput point")
        print("Type in <value> and <index>. Separate with space, then hit ENTER.")
        print("=================================================================")
        print()
        input_str = input()
        try:
            p_val = float(input_str.split(" ")[0])
            index = int(input_str.split(" ")[1])

            master_application.send_direct_point_command(group=40, variation=4, index=index, val_to_set=p_val)
            # master_application.get_db_by_group_variation(group=30, variation=6)
            # master_application.get_db_by_group_variation(group=40, variation=4)
            # master_application.send_scan_all_request()
            # sleep(3)

        except Exception as e:
            print(f"your input string '{input_str}'")
            print(e)

        master_application.send_scan_all_request()
        sleep(3)

        # db_print = json.dumps(master_application.soe_handler.db, indent=4, sort_keys=True)
        db_print = master_application.soe_handler.db
        # print(f"====== master database: {master_application.soe_handler.gv_index_value_nested_dict}")
        print(f"====== master database: {db_print}")

    _log.debug('Exiting.')
    master_application.shutdown()
    # outstation_application.shutdown()


if __name__ == '__main__':
    main()
