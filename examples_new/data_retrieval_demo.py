import logging
import random
import sys

from datetime import datetime
from pydnp3 import opendnp3

from dnp3_python.master_new import MyMasterNew

from dnp3_python.outstation_new import MyOutStationNew

import datetime
from time import sleep

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log = logging.getLogger("data_retrieval_demo")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)


def main():

    master_application = MyMasterNew()
    _log.debug('Initialization complete. Master Station in command loop.')
    outstation_application = MyOutStationNew()
    _log.debug('Initialization complete. OutStation in command loop.')

    # sleep(2)  # TODO: the master and outstation init takes time (i.e., configuration). Hard-coded here
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

    # cmd_interface.startup()

    count = 0
    while count < 2:

        count += 1
        print(datetime.datetime.now(), "============count ", count, )

        # plan: there are 3 AnalogInput Points,
        # outstation will randomly pick from
        # index 0: [4.0, 7.0, 2.0]
        # index 1: [14.0, 17.0, 12.0]
        # index 1: [24.0, 27.0, 22.0]

        # outstation update point value (slower than master station query)
        if count % 3 == 1:
            point_values_0 = [4.8, 7.8, 2.8]
            point_values_1 = [14.1, 17.1, 12.1]
            point_values_2 = [24.2, 27.2, 22.2]
            for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
                p_val = random.choice(pts)
                print(f"====== Outstation update index {i} with {p_val}")
                # cmd_interface_outstation.application.apply_update(opendnp3.Analog(float(p_val)), i)
                outstation_application.apply_update(opendnp3.Analog(value=float(p_val),
                                                                    flags=opendnp3.Flags(24),
                                                                    time=opendnp3.DNPTime(3094)), i)

        # update binaryInput value as well
        if count % 3 == 1:
            point_values_0 = [True, False]
            point_values_1 = [True, False]
            point_values_2 = [True, False]
            for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
                p_val = random.choice(pts)
                print(f"====== Outstation update index {i} with {p_val}")
                # cmd_interface_outstation.application.apply_update(opendnp3.Binary(p_val), i)
                # cmd_interface_outstation.application.apply_update(opendnp3.Binary(True), i)
                outstation_application.apply_update(opendnp3.Binary(True), i)

        # master station retrieve outstation point values
        result = master_application.retrieve_all_obj_by_gvid(gvid=opendnp3.GroupVariationID(30, 6),
                                                             config=opendnp3.TaskConfig().Default()
                                                             )
        print(f"===important log retrieve_all_obj_by_gvid GroupVariationID(30, 6)==== {count}",
              result)
        result = master_application.retrieve_all_obj_by_gvid(gvid=opendnp3.GroupVariationID(1, 2),
                                                             config=opendnp3.TaskConfig().Default()
                                                             )
        print(f"===important log retrieve_all_obj_by_gvid GroupVariationID(1, 2) ==== {count}",
              result)

        result = master_application.retrieve_all_obj_by_gvids()
        print(f"===important log retrieve_all_obj_by_gvids default ==== {count}",
              result)

        sleep(1)  # Note: hard-coded, master station query every 1 sec. Also the sleep needs to be at the end to shutdown

    _log.debug('Exiting.')
    master_application.shutdown()
    outstation_application.shutdown()

    # TODO: shutdown gracefully. (right now outstation/server relies on
    #  "Process finished with exit code 134 (interrupted by signal 6: SIGABRT)")


if __name__ == '__main__':
    main()
