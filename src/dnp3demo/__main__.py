from dnp3demo import data_retrieval_demo, control_workflow_demo
from dnp3demo import run_master, run_outstation
import argparse
import argcomplete


def main():
    # Initialize parser
    parser = argparse.ArgumentParser(
        prog="dnp3demo",
        description="Dnp3 use case demo",
        # epilog="Thanks for using %(prog)s! :)",
    )

    # subcommand
    # Note: by using `dest="command"`, we create namespace, such that args.command
    # to access subcommand
    subparsers = parser.add_subparsers(title="dnp3demo Sub-command",
                                       # help='run-station sub-command help',
                                       dest="command")
    parser_master = subparsers.add_parser('master', help='run a configurable master interactive program',
                                          description='run a configurable master interactive program'
                                          )
    # parser_master = subparsers
    parser_master = run_master.setup_args(parser_master)

    parser_outstation = subparsers.add_parser('outstation', help='run a configurable outstation interactive program',
                                              description='run a configurable outstation interactive program')
    parser_outstation = run_outstation.setup_args(parser_outstation)

    # demo-subcommand (default)
    parser_demo = subparsers.add_parser('demo', help='run dnp3 demo with default master and outstation', )
    subparser_group = parser_demo.add_mutually_exclusive_group(required=True)
    subparser_group.add_argument("--demo-get-point", action="store_true",
                                 help="Demo get point workflow. (default)")
    subparser_group.add_argument("--demo-set-point", action="store_true",
                                 help="Demo set point workflow.")
    # auto-complete
    argcomplete.autocomplete(parser)

    # read args
    args = parser.parse_args()

    cmd = args.command
    if cmd == "master":
        run_master.main(parser=parser)
    elif cmd == "outstation":
        run_outstation.main(parser=parser)
    elif cmd == "demo":
        if args.demo_set_point:
            control_workflow_demo.main()
        else:
            data_retrieval_demo.main()
    elif cmd is None:  # default behavior
        data_retrieval_demo.main()


if __name__ == "__main__":
    main()
    print("============")
    print("End of Demo.")
    print("============")
