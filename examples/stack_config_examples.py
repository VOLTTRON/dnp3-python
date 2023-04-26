import logging
import random
import sys

from pydnp3 import opendnp3

from dnp3_python.dnp3station.master import MyMaster
from dnp3_python.dnp3station.outstation import MyOutStation

import datetime
from time import sleep

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
# _log = logging.getLogger("data_retrieval_demo")
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)


def main():

    # db-sizes configuration examples, more on "opendnp3.DatabaseSizes"
    # example 1: use AllType
    db_sizes = opendnp3.DatabaseSizes.AllTypes(count=10)
    print(f"========== db_sizes.numDoubleBinary {db_sizes.numDoubleBinary}")

    db_sizes = opendnp3.DatabaseSizes(numBinary=15,
                                      numBinaryOutputStatus=15,
                                      numAnalog=15,
                                      numAnalogOutputStatus=10,
                                      numDoubleBinary=0,
                                      numCounter=0,
                                      numFrozenCounter=0,
                                      numTimeAndInterval=0)
    print(f"========== db_sizes.numDoubleBinary {db_sizes.numDoubleBinary}")

    # Tips: use __dir__() to inspect available attributes
    print(f"========== db_sizes.__dir__() {db_sizes.__dir__()}")

    # Event buffer config example, more on opendnp3.EventBufferConfig, opendnp3.EventType
    # example 1: use AllType
    event_buffer_config = opendnp3.EventBufferConfig().AllTypes(15)
    print(f"========= event_buffer_config.TotalEvents {event_buffer_config.TotalEvents()}")
    print(f"========= event_buffer_config.GetMaxEventsForType(opendnp3.EventType.Binary) "
          f"{event_buffer_config.GetMaxEventsForType(opendnp3.EventType.Binary)}")
    # example 2: specify individual event type
    event_buffer_config = opendnp3.EventBufferConfig(maxBinaryEvents=5, maxAnalogEvents=5,
                                                     maxBinaryOutputStatusEvents=5, maxAnalogOutputStatusEvents=5,
                                                     maxCounterEvents=0, maxFrozenCounterEvents=0,
                                                     maxDoubleBinaryEvents=0, maxSecurityStatisticEvents=0)
    print(f"========= event_buffer_config.TotalEvents {event_buffer_config.TotalEvents()}")
    print(f"========= event_buffer_config.GetMaxEventsForType(opendnp3.EventType.Binary) "
          f"{event_buffer_config.GetMaxEventsForType(opendnp3.EventType.Binary)}")

    ####################
    # init an outstation using default configuration, e.g., port=20000. Then start.
    outstation_application = MyOutStation(db_sizes=db_sizes, event_buffer_config=event_buffer_config)
    outstation_application.start()
    _log.debug('Initialization complete. OutStation in command loop.')

    # init a master using default configuration, e.g., port=20000. Then start.
    master_application = MyMaster()
    master_application.start()
    _log.debug('Initialization complete. Master Station in command loop.')

    def poll_demo():
        count = 0
        while count < 10:
            sleep(2)  # Note: hard-coded, master station query every 1 sec.

            count += 1
            print(datetime.datetime.now(), "============count ", count, )

            # plan: there are 3 AnalogInput Points,
            # outstation will randomly pick from
            # index 0: [4.0, 7.0, 2.0]
            # index 1: [14.0, 17.0, 12.0]
            # index 1: [24.0, 27.0, 22.0]

            # outstation update point value (slower than master station query)
            if count % 2 == 1:
                point_values_0 = [4.8, 7.8, 2.8]
                point_values_1 = [14.1, 17.1, 12.1]
                point_values_2 = [24.2, 27.2, 22.2]
                point_values_0 = [val + random.random() for val in point_values_0]
                point_values_1 = [val + random.random() for val in point_values_1]
                point_values_2 = [val + random.random() for val in point_values_2]
                for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
                    p_val = random.choice(pts)
                    print(f"====== Outstation update index {i} with {p_val}")
                    outstation_application.apply_update(opendnp3.Analog(value=float(p_val)), i)

            if count % 2 == 1:
                point_values_0 = [True, False]
                point_values_1 = [True, False]
                point_values_2 = [True, False]
                for i, pts in enumerate([point_values_0, point_values_1, point_values_2]):
                    p_val = random.choice(pts)
                    print(f"====== Outstation update index {i} with {p_val}")
                    outstation_application.apply_update(opendnp3.Binary(True), i)

            # master station retrieve outstation point values

            result = master_application.get_db_by_group_variation(group=30, variation=6)
            print(f"===important log: case6 get_db_by_group_variation(group=30, variation=6) ==== {count}", "\n",
                  datetime.datetime.now(),
                  result)
            result = master_application.get_db_by_group_variation(group=1, variation=2)
            print(f"===important log: case6b get_db_by_group_variation(group=1, variation=2) ==== {count}", "\n",
                  datetime.datetime.now(),
                  result)
            result = master_application.get_db_by_group_variation(group=30, variation=1)
            print(f"===important log: case6c get_db_by_group_variation(group=30, variation=1) ==== {count}", "\n",
                  datetime.datetime.now(),
                  result)

    poll_demo()
    _log.debug('Exiting.')
    master_application.shutdown()
    outstation_application.shutdown()


if __name__ == '__main__':
    main()
