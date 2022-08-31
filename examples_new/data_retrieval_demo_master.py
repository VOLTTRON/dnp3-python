import logging
import sys

from datetime import datetime
from pydnp3 import opendnp3
# from master import MyMaster, MyLogger, AppChannelListener, SOEHandler, MasterApplication

# from master_cmd import MasterCmd
# from master_new import MasterCmdNew
from dnp3_python.master_new import MyMasterNew

from dnp3_python import visitors

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


    master_application = MyMasterNew()
    _log.debug('Initialization complete. Master Station in command loop.')

    count = 0
    while count < 20:
        sleep(1)  # Note: hard-coded, master station query every 1 sec.

        count += 1
        print(datetime.datetime.now(), "============count ", count, )

        # use case 4: retrieve point values specified by a list of GroupVariationIDs.
        # demo float AnalogInput, BinaryInput,
        result = master_application.retrieve_all_obj_by_gvids(gv_ids=[opendnp3.GroupVariationID(30, 6),
                                                                      opendnp3.GroupVariationID(1, 2)])
        print(f"===important log: case4 retrieve_all_obj_by_gvids default ==== {count}", datetime.datetime.now(),
              result)


    _log.debug('Exiting.')
    master_application.shutdown()
    # cmd_interface_outstation.do_quit("something")
    # cmd_interface_master.do_quit("something")
    # quit()
    # quit()
    # TODO: shutdown gracefully


if __name__ == '__main__':
    main()
