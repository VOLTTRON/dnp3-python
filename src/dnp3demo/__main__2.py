import sys

from dnp3demo import data_retrieval_demo, control_workflow_demo, \
    data_retrieval_demo_master, data_retrieval_demo_outstation, \
    control_workflow_demo_master
import argparse

from dnp3demo import run_master


def main():

    # Initialize parser
    parser = argparse.ArgumentParser(
        prog="dnp3demo",
        description="Basic dnp3 use case demo",
        # epilog="Thanks for using %(prog)s! :)",
    )

    # Adding optional argument
    parser.add_argument("-d", "--duration", action="store",
                        help="Configure demo duration (in seconds.)",
                        type=int,
                        default=60,
                        metavar="sec")

    # use exclusive group, choose among scripts to run,
    # by default run --demo-get-point

    group = parser.add_mutually_exclusive_group(required=False)
    group.description = "some description"
    group.add_argument("-rm", "--run-master-station", action="store_true",
                       help="Run a standalone master station.", )
    group.add_argument("-ro", "--run-outstation", action="store_true",
                       help="Run a standalone master station.")
    group.add_argument("-dg", "--demo-get-point", action="store_true",
                       help="Demo get point workflow.")
    group.add_argument("-ds", "--demo-set-point", action="store_true",
                       help="Demo set point workflow.")
    group.add_argument("-rim", "--run-interactive-master", action="store_true",
                       help="Run an interactive master station. (For set point demo)")

    # subcommand
    # Note: by using `dest="command"`, we create namespace, such that args.command
    # to access subcommand
    subparsers = parser.add_subparsers(title="Run Station Sub-command",
                                       help='run-station sub-command help',
                                       dest="command")
    parser_master = subparsers.add_parser('master', help='run an interactive master')
    # parser_master = subparsers
    parser_master = run_master.setup_args(parser_master)
    # hacky: added subcommands
    # parser_master.add_argument("")

    args = parser.parse_args()
    # args_master = parser_master.parse_args()
    print(f"1st d_args args, {vars(args)}")
    # print(f"1st d_args args_master, {vars(args_master)}")

    # parser.set_defaults(func=run_master.main, which="master")
    # run_master.main()
    cmd = args.command
    if cmd == "master":
        run_master.main(parser=parser)
        pass
    # print(f"===========cmd {cmd}")


if __name__ == "__main__":
    main()
    print("============")
    print("End of Demo.")
    print("============")
