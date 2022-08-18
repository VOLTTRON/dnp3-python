import cmd
import logging
import random
import sys

from datetime import datetime
from pydnp3 import opendnp3, openpal
# from master import MyMaster, MyLogger, AppChannelListener, SOEHandler, MasterApplication
# from master import command_callback, restart_callback

from pydnp3 import asiodnp3 as asiodnp3

# from master_cmd import MasterCmd
# from master_new import MasterCmdNew
from master_new import MyMasterNew, MyLogger, AppChannelListener
# from outstation_cmd import OutstationCmd

from outstation_new import MyOutStationNew

import visitors

from time import sleep

import datetime

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log = logging.getLogger("data_retrieval_demo")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)






def main():
    # cmd_interface_master = MasterCmdNew()
    # master_application = MyMasterNew(log_handler=MyLogger(),
    #                                  listener=AppChannelListener(),
    #                                  soe_handler=SOEHandler(),
    #                                  master_application=MasterApplication())
    master_application = MyMasterNew()
    _log.debug('Initialization complete. Master Station in command loop.')
    # cmd_interface_outstation = OutstationCmd()
    outstation_application = MyOutStationNew()
    _log.debug('Initialization complete. OutStation in command loop.')

    sleep(2)  # TODO: the master and outstation init takes time (i.e., configuration). Hard-coded here
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

    # cmd_interface.startup()
    count = 0
    while count < 10:

        count += 1
        print(datetime.datetime.now(), "============count ", count, )

        # plan: there are 3 AnalogInput Points,
        # outstation will randomly pick from
        # index 0: [4.0, 7.0, 2.0]
        # index 1: [14.0, 17.0, 12.0]
        # index 1: [24.0, 27.0, 22.0]
        # note: for this version of pydnp3, it needs to inject float type point value, but will parse it into int.
        # TODO: fix/add wrapper to allow taking float value and output as float value.

        # outstation update point value (slower than master station query)
        if count % 3 == 1:
            point_values_0 = [4.0, 7.0, 2.0]
            point_values_1 = [14.0, 17.0, 12.0]
            point_values_2 = [24.0, 27.0, 22.0]
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

        result = master_application.retrieve_point_vals(gvId=opendnp3.GroupVariationID(30, 1),
                            index_start=0,
                            index_stop=3,
                            config=opendnp3.TaskConfig().Default()
                            )

        print(f"===important log _class_index_value ==== {count}",
              result.get(visitors.VisitorIndexedAnalog),
              result.get(visitors.VisitorIndexedBinary),
              )

        # print(f"===import log _class_index_value_dict ==== {count}",
        #       cmd_interface_master.application.soe_handler._class_index__value_dict)
        # print(f"===import log _class_index_value_dict visitors.VisitorIndexedAnalog ==== {count}",
        #       cmd_interface_master.application.soe_handler._class_index__value_dict.get(visitors.VisitorIndexedAnalog))

        # simple logic: requry the full set of points if get unsolicited result
        # TODO: refactor this logic inside SOEHandler to distinguish unsolicited/solicited update, i.e., use count
        # result = cmd_interface_master.application.soe_handler._class_index__value_dict
        result = master_application.soe_handler._class_index__value_dict
        index_value_s = result.get(visitors.VisitorIndexedAnalog)
        # if index_value_s and (len(index_value_s) < 4 or len(index_value_s) == 10):  # hard coded:
        # if index_value_s and (len(index_value_s) < 4):  # hard coded:
        #     # print("======I am inside")
        #     # cmd_interface_master.application.master.ScanRange(gvId=opendnp3.GroupVariationID(30, 1), start=0, stop=3,
        #     #                                                   config=opendnp3.TaskConfig().Default())
        #     # master_application.master.ScanRange(gvId=opendnp3.GroupVariationID(30, 1), start=0, stop=3,
        #     #                                                   config=opendnp3.TaskConfig().Default())
        #     result = master_application.retrieve_point_vals(gvId=opendnp3.GroupVariationID(30, 1),
        #                                                     index_start=0,
        #                                                     index_stop=3,
        #                                                     config=opendnp3.TaskConfig().Default()
        #                                                     )
        #     sleep(0.01)  # TODO: since it is aychnous, need this walk-around to assure update
        #     # print(f"===import log _class_index_value ==== {count}",
        #     #       cmd_interface_master.application.soe_handler._class_index_value)
        #     # print(f"===import log _class_index_value ==== {count}",
        #     #       master_application.soe_handler._class_index_value)
        #     print(f"===important log _class_index_value ==== {count}",
        #           result.get(visitors.VisitorIndexedAnalog),
        #           result.get(visitors.VisitorIndexedBinary),
        #           )


        # cmd_interface.application.apply_update(opendnp3.Analog(float(value_string)), index)

        # mimic do_o3
        """Send a DirectOperate BinaryOutput (group 12) CommandSet to the Outstation. Command syntax is: o3"""
        # This could also have been in multiple steps, as follows:
        # command_set = opendnp3.CommandSet()
        # command_set.Add([
        #     opendnp3.WithIndex(opendnp3.ControlRelayOutputBlock(opendnp3.ControlCode.LATCH_ON), 0),
        #     opendnp3.WithIndex(opendnp3.ControlRelayOutputBlock(opendnp3.ControlCode.LATCH_OFF), 1),
        #     opendnp3.WithIndex(opendnp3.ControlRelayOutputBlock(opendnp3.ControlCode.LATCH_ON), 2)
        # ])
        # cmd_interface.application.send_direct_operate_command_set(command_set, command_callback)

        # # mimic do_o2
        # # """Send a DirectOperate AnalogOutput (group 41) index 10 value 7 to the Outstation. Command syntax is: o2"""
        # cmd_interface.application.send_direct_operate_command(opendnp3.AnalogOutputInt32(7),
        #                                                       0,
        #                                                       command_callback)

        # mimic do_o2 (kefei's wild guess)
        """Send a DirectOperate AnalogOutput (group 41) index 10 value 7 to the Outstation. Command syntax is: o2"""
        # to_send = random.choice([7.2, 9.5, 287.45])
        # print("to send: ", to_send)
        # cmd_interface.application.send_direct_operate_command(opendnp3.AnalogOutputInt32(int(to_send)),
        #                                                       0,
        #                                                       command_callback)
        # something = cmd_interface.application.send_direct_operate_command(
        #     opendnp3.AnalogOutputFloat32(random.choice([7.2, 9.5, 287.45])),
        #     0,
        #     command_callback)
        # print("=====something========", something)

        # mimic do do_scan_all(self, line):
        #         """Call ScanAllObjects. Command syntax is: scan_all"""
        # cmd_interface.application.master.ScanAllObjects(opendnp3.GroupVariationID(2, 1),  # TODO: investigate the signature, wild guess here.
                                                                                            # TODO: GroupVariationID(30, 1) is a good start for Binary_input(?)
        #                                                 opendnp3.TaskConfig().Default())
        # cmd_interface.application.master.ScanAllObjects(opendnp3.GroupVariationID(1, 2),
        #                                                 opendnp3.TaskConfig().Default())
        # cmd_interface.application.master.ScanAllObjects(opendnp3.GroupVariationID(30, 1),
        #                                                 opendnp3.TaskConfig().Default())
        # result_maybe = cmd_interface.application.master.ScanAllObjects(opendnp3.GroupVariationID(30, 1),
        #                                                 opendnp3.TaskConfig().Default())
        # print("================print something and hope it works =========== (and it doesn't)", result_maybe)

        # cmd_interface.application.fast_scan.Demand()  # not working at the moment
        # cmd_interface.application.slow_scan.Demand()  # not working at the moment

        # mimic def do_scan_range(self, line):
        # """Do an ad-hoc scan of a range of points (group 1, variation 2, indexes 0-3). Command syntax is: scan_range"""
        # self.application.master.ScanRange(opendnp3.GroupVariationID(1, 2), 0, 3, opendnp3.TaskConfig().Default())
        # cmd_interface.application.master.ScanRange(opendnp3.GroupVariationID(30, 1), 0, 3, opendnp3.TaskConfig().Default())  # this is the most promising one so far
        # cmd_interface.application.master.ScanRange(opendnp3.GroupVariationID(10, 2), 0, 3,
        #                                            opendnp3.TaskConfig().Default())  # experiement, for binary output (this is working)
        # cmd_interface.application.master.ScanRange(opendnp3.GroupVariationID(40, 2), 0, 3,
        #                                            opendnp3.TaskConfig().Default())  # experiement, for analog output (this is working)
        # # print(f"count {count}", "if this work, then we are good: ", cmd_interface.application.soe_handler.get_class_index_value())
        # print(f"count {count}", "if this work, then we are good: ",
        #       cmd_interface.application.soe_handler._class_index_value)

        sleep(0.01)  # TODO: since it is aychnous, need this walk-around to assure update
        # cmd_interface.application.master.ScanRange(opendnp3.GroupVariationID(1, 2), 0, 3,
        #                                            opendnp3.TaskConfig().Default())  # this is the most promising one so far
        # print(f"count {count}", "if this work, then we are good: ", cmd_interface.application.soe_handler.get_class_index_value())
        # result_maybe = cmd_interface.application.master.ScanRange(opendnp3.GroupVariationID(30, 1), 0, 3, opendnp3.TaskConfig().Default())
        # print("================print something and hope it works =========== (and it doesn't)", result_maybe)

        # print("================test asiodnp3.IStack().GetStackStatistics()", )
        # asiodnp3.IStack().GetStackStatistics()



        sleep(1)
    _log.debug('Exiting.')
    master_application.shutdown()
    outstation_application.shutdown()
    # cmd_interface_outstation.do_quit("something")
    # cmd_interface_master.do_quit("something")
    # quit()
    # quit()
    # TODO: shutdown gracefully


if __name__ == '__main__':
    main()
