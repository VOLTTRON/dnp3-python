import logging
import sys
import argparse

from pydnp3 import opendnp3
from dnp3_python.dnp3station.outstation_new import MyOutStationNew

from time import sleep

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log = logging.getLogger("control_workflow_demo")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)


def input_prompt(display_str=None) -> str:
    if display_str is None:
        display_str = """
======== Your Input Here: ==(outstation)======
"""
    return input(display_str)


def setup_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:

    # Adding optional argument
    # parser.add_argument("-mip", "--master-ip", action="store", default="0.0.0.0", type=str,
    #                     metavar="<IP>")
    parser.add_argument("--outstation-ip=", action="store", default="0.0.0.0", type=str,
                        metavar="<IP>",
                        help="outstation ip, default: 0.0.0.0")
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
==== Outstation Operation MENU ==================================
<ai> - update analog-input point value (for local reading)
<ao> - update analog-output point value (for local control)
<bi> - update binary-input point value (for local reading)
<bo> - update binary-output point value (for local control)
<dd> - display database
<dc> - display configuration
=================================================================\
"""
    print(welcome_str)

def main(parser=None, *args, **kwargs):

    if parser is None:
        # Initialize parser
        parser = argparse.ArgumentParser(
            prog="dnp3-outstation",
            description="Run a dnp3 outstation",
            # epilog="Thanks for using %(prog)s! :)",
        )
        parser = setup_args(parser)

    # Read arguments from command line
    args = parser.parse_args()

    # dict to store args.Namespace
    d_args = vars(args)
    print(__name__, d_args)

    outstation_application = MyOutStationNew(
        # masterstation_ip_str=args.master_ip,
        outstation_ip=d_args.get("outstation_ip="),
        port=d_args.get("port="),
        master_id=d_args.get("master_id="),
        outstation_id=d_args.get("outstation_id="),

        # channel_log_level=opendnp3.levels.ALL_COMMS,
        # master_log_level=opendnp3.levels.ALL_COMMS
        # soe_handler=SOEHandler(soehandler_log_level=logging.DEBUG)
    )
    _log.info("Connection Config", outstation_application.get_config())
    outstation_application.start()
    _log.debug('Initialization complete. Outstation in command loop.')

    sleep(3)
    # Note: if without sleep(2) there will be a glitch when first send_select_and_operate_command
    #  (i.e., all the values are zero, [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0)]))
    #  since it would not update immediately

    count = 0
    while count < 1000:
        # sleep(1)  # Note: hard-coded, master station query every 1 sec.

        count += 1
        # print(f"=========== Count {count}")

        if outstation_application.is_connected:
            # print("Communication Config", master_application.get_config())
            print_menu()
        else:
            print("Connection error.")
            print("Connection Config", outstation_application.get_config())
            print("Start retry...")
            sleep(2)
            continue

        option = input_prompt()  # Note: one of ["ai", "ao", "bi", "bo",  "dd", "dc"]
        while True:
            if option == "ai":
                print("You chose <ai> - update analog-input point value (for local reading)")
                print("Type in <float> and <index>. Separate with space, then hit ENTER.")
                print("Type 'q', 'quit', 'exit' to main menu.")
                input_str = input_prompt()
                if input_str in ["q", "quit", "exit"]:
                    break
                try:
                    p_val = float(input_str.split(" ")[0])
                    index = int(input_str.split(" ")[1])
                    outstation_application.apply_update(opendnp3.Analog(value=p_val), index)
                    result = {"Analog": outstation_application.db_handler.db.get("Analog")}
                    print(result)
                    sleep(2)
                except Exception as e:
                    print(f"your input string '{input_str}'")
                    print(e)
            elif option == "ao":
                print("You chose <ao> - update analog-output point value (for local control)")
                print("Type in <float> and <index>. Separate with space, then hit ENTER.")
                print("Type 'q', 'quit', 'exit' to main menu.")
                input_str = input_prompt()
                if input_str in ["q", "quit", "exit"]:
                    break
                try:
                    p_val = float(input_str.split(" ")[0])
                    index = int(input_str.split(" ")[1])
                    outstation_application.apply_update(opendnp3.AnalogOutputStatus(value=p_val), index)
                    result = {"AnalogOutputStatus": outstation_application.db_handler.db.get("AnalogOutputStatus")}
                    print(result)
                    sleep(2)
                except Exception as e:
                    print(f"your input string '{input_str}'")
                    print(e)
            elif option == "bi":
                print("You chose <bi> - update binary-input point value (for local reading)")
                print("Type in <[1/0]> and <index>. Separate with space, then hit ENTER.")
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
                    outstation_application.apply_update(opendnp3.Binary(value=p_val), index)
                    result = {"Binary": outstation_application.db_handler.db.get("Binary")}
                    print(result)
                    sleep(2)
                except Exception as e:
                    print(f"your input string '{input_str}'")
                    print(e)
            elif option == "bo":
                print("You chose <bo> - update binary-output point value (for local control)")
                print("Type in <[1/0]> and <index>. Separate with space, then hit ENTER.")
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
                    outstation_application.apply_update(opendnp3.BinaryOutputStatus(value=p_val), index)
                    result = {"BinaryOutputStatus": outstation_application.db_handler.db.get("BinaryOutputStatus")}
                    print(result)
                    sleep(2)
                except Exception as e:
                    print(f"your input string '{input_str}'")
                    print(e)
            elif option == "dd":
                print("You chose < dd > - display database")
                db_print = outstation_application.db_handler.db
                print(db_print)
                sleep(2)
                break
            elif option == "dc":
                print("You chose < dc> - display configuration")
                print(outstation_application.get_config())
                sleep(3)
                break
            else:
                print(f"ERROR- your input `{option}` is not one of the following.")
                sleep(1)
                break

    _log.debug('Exiting.')
    outstation_application.shutdown()
    # outstation_application.shutdown()


if __name__ == '__main__':
    main()
