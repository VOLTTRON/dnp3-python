import sys

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

    # borrow children program arg parser
    from dnp3demo import run_master
    # parser = run_master.arg_config()

    # p = argparse.ArgumentParser()
    s = parser.add_subparsers()
    ss = s.add_parser('script', parents=[parser], add_help=False)

    print(f"====parser, {vars(parser.parse_args())}")
    # print(f"====s, {vars(s.parse_args())}")
    print(f"====ss, {vars(ss.parse_args())}")

    # Adding optional argument
    parser.add_argument("-d", "--duration", action="store",
                        help="Configure demo duration (in seconds.)",
                        type=int,
                        default=60,
                        metavar="sec")

    args = parser.parse_args()
    print(f"1st d_args, {vars(args)}")

    from dnp3demo import run_master
    run_master.main(sys.argv)


if __name__ == "__main__":
    main()
    print("============")
    print("End of Demo.")
    print("============")
