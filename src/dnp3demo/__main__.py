from dnp3demo import data_retrieval_demo, control_workflow_demo, \
    data_retrieval_demo_master, data_retrieval_demo_outstation, \
    control_workflow_demo_master
import argparse


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

    # Read arguments from command line
    args = parser.parse_args()

    # choose among the following scripts to run
    if args.demo_set_point:
        control_workflow_demo.main()
    elif args.run_master_station:
        data_retrieval_demo_master.main(duration=args.duration)
    elif args.run_outstation:
        data_retrieval_demo_outstation.main(duration=args.duration)
    elif args.run_interactive_master:
        control_workflow_demo_master.main()
    else:  # run as default
        data_retrieval_demo.main()


if __name__ == "__main__":
    main()
    print("============")
    print("End of Demo.")
    print("============")
