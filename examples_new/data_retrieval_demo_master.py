import logging
import sys

from datetime import datetime
from pydnp3 import opendnp3
# from master import MyMaster, MyLogger, AppChannelListener, SOEHandler, MasterApplication

# from master_cmd import MasterCmd
# from master_new import MasterCmdNew
from master_new import MyMasterNew

import visitors

from time import sleep

import datetime

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log = logging.getLogger("data_retrieval_demo_master")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)






def main():
    # cmd_interface_master = MasterCmdNew()
    # master_application = MyMasterNew(log_handler=MyLogger(),
    #                                  listener=AppChannelListener(),
    #                                  soe_handler=SOEHandler(),
    #                                  master_application=MasterApplication())
    # master_application = MyMasterNew()
    # _log.debug('Initialization complete. Master Station in command loop.')
    # cmd_interface_outstation = OutstationCmd()
    # _log.debug('Initialization complete. OutStation in command loop.')

    sleep(2)  # TODO: the master and outstation init takes time (i.e., configuration). Hard-coded here
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

    # cmd_interface.startup()
    count = 0
    while count < 4:

        count += 1
        print(datetime.datetime.now(), "============count ", count, )

        # Note: to fit in the server-long-live-client-short-live scenario
        master_application = MyMasterNew()
        _log.debug('Initialization complete. Master Station in command loop.')

        # plan: there are 3 AnalogInput Points,
        # outstation will randomly pick from
        # index 0: [4.0, 7.0, 2.0]
        # index 1: [14.0, 17.0, 12.0]
        # index 1: [24.0, 27.0, 22.0]
        # note: for this version of pydnp3, it needs to inject float type point value, but will parse it into int.
        # TODO: fix/add wrapper to allow taking float value and output as float value.

        # # outstation update point value (slower than master station query)
        # if count % 3 == 1:
        #     point_values_0 = [4.0, 7.0, 2.0]
        #     point_values_1 = [14.0, 17.0, 12.0]
        #     point_values_2 = [24.0, 27.0, 22.0]
        #     for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
        #         p_val = random.choice(pts)
        #         print(f"====== Outstation update index {i} with {p_val}")
        #         cmd_interface_outstation.application.apply_update(opendnp3.Analog(float(p_val)), i)
        #
        # # update binaryInput value as well
        # if count % 3 == 1:
        #     point_values_0 = [True, False]
        #     point_values_1 = [True, False]
        #     point_values_2 = [True, False]
        #     for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
        #         p_val = random.choice(pts)
        #         print(f"====== Outstation update index {i} with {p_val}")
        #         # cmd_interface_outstation.application.apply_update(opendnp3.Binary(p_val), i)
        #         cmd_interface_outstation.application.apply_update(opendnp3.Binary(True), i)

        if count == 1:
            sleep(2.41)  # TODO: since it is aychnous, need this walk-around to assure update
        else:
            sleep(0.41)
        # master station retrieve value

        # for testing purpose, the index no.3 is empty, i.e., it will return 0 always.
        # cmd_interface_master.application.master.ScanRange(gvId=opendnp3.GroupVariationID(30, 1), start=0, stop=3,
        #                                            config=opendnp3.TaskConfig().Default())
        # master_application.master.ScanRange(gvId=opendnp3.GroupVariationID(30, 1), start=0, stop=3,
        #                                                   config=opendnp3.TaskConfig().Default())
        # master_application.master.ScanRange(gvId=opendnp3.GroupVariationID(30, 1), start=0, stop=3,
        #                                     config=opendnp3.TaskConfig().Default())
        #
        # # print(f"===important log _class_index_value ==== {count}",
        # #       cmd_interface_master.application.soe_handler._class_index_value)
        # print(f"===important log _class_index_value ==== {count}",
        #       master_application.soe_handler._class_index_value)

        result = master_application.retrieve_all_obj_by_gvId(gvId=opendnp3.GroupVariationID(30, 1),
                                                             index_start=0,
                                                             index_stop=3,
                                                             config=opendnp3.TaskConfig().Default()
                                                             )

        print(f"===important log _class_index_value ==== {count}",
              result.get(visitors.VisitorIndexedAnalog),
              result.get(visitors.VisitorIndexedBinary),
              )
        sleep(1)
        master_application.shutdown()

    _log.debug('Exiting.')
    # cmd_interface_outstation.do_quit("something")
    # cmd_interface_master.do_quit("something")
    # quit()
    # quit()
    # TODO: shutdown gracefully


if __name__ == '__main__':
    main()
