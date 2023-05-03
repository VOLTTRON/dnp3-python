import logging
import sys
import argparse
from dnp3_python.dnp3station.master import MyMaster
from time import sleep


stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(f"{__file__}, {__name__}")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)


def input_prompt(display_str=None, prefix="", menu_indicator="") -> str:
    if display_str is None:
        display_str = f"""
======== Your Input Here: ==(Master-{menu_indicator})======
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
"""
    return input(prefix + display_str)


def setup_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:

    # Adding optional argument
    parser.add_argument("--master-ip=", action="store", default="0.0.0.0", type=str,
                        metavar="<IP>",
                        help="master ip, default: 0.0.0.0")
    parser.add_argument("--outstation-ip=", action="store", default="127.0.0.1", type=str,
                        metavar="<IP>",
                        help="outstation ip, default: 127.0.0.1")
    parser.add_argument("--port=", action="store", default=20000, type=int,
                        metavar="<PORT>",
                        help="port, default: 20000")
    parser.add_argument("--master-id=", action="store", default=2, type=int,
                        metavar="<ID>",
                        help="master id, default: 2")
    parser.add_argument("--outstation-id=", action="store", default=1, type=int,
                        metavar="<ID>",
                        help="master id, default: 1")

    return parser


def print_menu():
    welcome_str = """\
==== Master Operation MENU ==================================
<ao> - set analog-output point value (for remote control)
<bo> - set binary-output point value (for remote control)
<dd> - display/polling (outstation) database
<dc> - display configuration
<q>  - quit the program
=================================================================\
"""
    print(welcome_str)

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
    # print(args.__dir__())
    master_application = MyMaster(
        master_ip=d_args.get("master_ip="),
        outstation_ip=d_args.get("outstation_ip="),
        port=d_args.get("port="),
        master_id=d_args.get("master_id="),
        outstation_id=d_args.get("outstation_id="),

        # channel_log_level=opendnp3.levels.ALL_COMMS,
        # master_log_level=opendnp3.levels.ALL_COMMS
        # soe_handler=SOEHandler(soehandler_log_level=logging.DEBUG)
    )
    _log.info("Connection Config", master_application.get_config())
    master_application.start()
    _log.debug('Initialization complete. Master Station in command loop.')

    sleep(3)
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

    count = 0
    while count < 1000:
        # sleep(1)  # Note: hard-coded, master station query every 1 sec.

        count += 1

        print_menu()
        print()
        if master_application.is_connected:
            option = input_prompt(menu_indicator="Main Menu")  # Note: one of ["ai", "ao", "bi", "bo",  "dd", "dc"]
        else:
            option = input_prompt(prefix="!!!!!!!!! WARNING: The Master is NOT connected !!!!!!!!!\n",
                                  menu_indicator="Main Menu")
        while True:
            if option == "ao":
                print("You chose <ao> - set analog-output point value")
                print("Type in <float> and <index>. Separate with space, then hit ENTER. e.g., `1.4321, 1`.")
                print("Type 'q', 'quit', 'exit' to main menu.")
                input_str = input_prompt()
                if input_str in ["q", "quit", "exit"]:
                    break
                try:
                    p_val = float(input_str.split(" ")[0])
                    index = int(input_str.split(" ")[1])
                    master_application.send_direct_point_command(group=40, variation=4, index=index, val_to_set=p_val)
                    result: dict = master_application.get_db_by_group_variation(group=40, variation=4)
                    print("SUCCESS", {"AnalogOutputStatus": list(result.values())[0]})
                    sleep(2)
                except Exception as e:
                    print(f"your input string '{input_str}'")
                    print(e)
            elif option == "bo":
                print("You chose <bo> - set binary-output point value")
                print("Type in <[1/0]> and <index>. Separate with space, then hit ENTER. e.g., `1 0`.")
                input_str = input_prompt()
                if input_str in ["q", "quit", "exit"]:
                    break
                try:
                    p_val_input = input_str.split(" ")[0]
                    if p_val_input not in ["0", "1"]:
                        raise ValueError("binary-output value only takes '0' or '1'.")
                    else:
                        p_val = True if p_val_input == "1" else False
                    index = int(input_str.split(" ")[1])
                    master_application.send_direct_point_command(group=10, variation=2, index=index, val_to_set=p_val)
                    result = master_application.get_db_by_group_variation(group=10, variation=2)
                    print("SUCCESS", {"BinaryOutputStatus": list(result.values())[0]})
                    sleep(2)
                except Exception as e:
                    print(f"your input string '{input_str}'")
                    print(e)
            elif option == "dd":
                print("You chose < dd > - display database")
                master_application.send_scan_all_request()
                sleep(1)
                db_print = master_application.soe_handler.db
                print(db_print)
                sleep(2)
                break
            elif option == "dc":
                print("You chose < dc > - display configuration")
                print(master_application.get_config())
                sleep(3)
                break
            elif option == "q":
                print("Stopping Master")
                _log.debug('Exiting.')
                master_application.shutdown()
                sys.exit(0)
            else:
                print(f"ERROR- your input `{option}` is not one of the following.")
                sleep(1)
                break

    # _log.debug('Exiting.')
    # master_application.shutdown()
    # outstation_application.shutdown()


if __name__ == '__main__':
    main()
