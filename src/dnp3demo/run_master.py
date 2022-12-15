import logging
import random
import sys
import argparse

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


def setup_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:

    # Adding optional argument
    parser.add_argument("-mip", "--master-ip", action="store", default="0.0.0.0", type=str,
                        metavar="x.x.x.x")
    parser.add_argument("-oip", "--outstation-ip", action="store", default="127.0.0.1", type=str,
                        metavar="x.x.x.x")
    parser.add_argument("-p", "--port", action="store", default=20000, type=int,
                        metavar="<PORT>")
    parser.add_argument("-mid", "--master-id", action="store", default=1, type=int,
                        metavar="<ID>")
    parser.add_argument("-oid", "--outstation-id", action="store", default=2, type=int,
                        metavar="<ID>")

    return parser


def main(parser=None, *args, **kwargs):

    if parser is None:
        # Initialize parser
        parser = argparse.ArgumentParser(
            prog="dnp3-master",
            description="Run a dnp3 master",
            # epilog="Thanks for using %(prog)s! :)",
        )
        parser = setup_args(parser)

    # Read arguments from command line
    args = parser.parse_args()

    # dict to store args.Namespace
    d_args = vars(args)
    print(__name__, d_args)

    master_application = MyMasterNew(
        masterstation_ip_str=args.master_ip,
        outstation_ip_str=args.outstation_ip,
        port=args.port,
        masterstation_id_int=args.master_id,
        outstation_id_int=args.outstation_id,

        # channel_log_level=opendnp3.levels.ALL_COMMS,
        # master_log_level=opendnp3.levels.ALL_COMMS
        # soe_handler=SOEHandler(soehandler_log_level=logging.DEBUG)
    )
    master_application.start()
    _log.debug('Initialization complete. Master Station in command loop.')

    sleep(2)
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

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
        # print("===== numOpen", master_application.channel.GetStatistics().channel.numOpen)
        # print("===== numOpenFail", master_application.channel.GetStatistics().channel.numOpenFail)
        # print("===== numClose", master_application.channel.GetStatistics().channel.numClose)

        print(master_application.get_config())
        print(master_application.is_connected)
        print(master_application.channel_statistic)

    _log.debug('Exiting.')
    master_application.shutdown()
    # outstation_application.shutdown()


if __name__ == '__main__':
    main()
