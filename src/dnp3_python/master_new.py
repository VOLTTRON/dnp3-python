import logging
import sys
import time

from pydnp3 import opendnp3, openpal, asiopal, asiodnp3
# from visitors import *
from .visitors import *
from typing import Callable, Union, Dict, List, Optional, Tuple
from pydnp3.opendnp3 import GroupVariation, GroupVariationID

FILTERS = opendnp3.levels.NORMAL | opendnp3.levels.ALL_COMMS
HOST = "127.0.0.1"  # remote outstation
LOCAL = "0.0.0.0"  # local masterstation
# HOST = "192.168.1.14"
PORT = 20000

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
# _log.addHandler(stdout_stream)
# _log.setLevel(logging.DEBUG)
# _log.setLevel(logging.ERROR)
_log.setLevel(logging.INFO)

from .master_utils import MyLogger, AppChannelListener, SOEHandler
from .master_utils import parsing_gvid_to_gvcls
from .master_utils import collection_callback, command_callback, restart_callback
import datetime

# alias DbPointVal
DbPointVal = Union[float, int, bool, None]
DbStorage = Dict[opendnp3.GroupVariation, Dict[
    int, DbPointVal]]  # e.g., {GroupVariation.Group30Var6: {0: 4.8, 1: 14.1, 2: 27.2, 3: 0.0, 4: 0.0}


class MyMasterNew:
    """
        Interface for all master application callback info except for measurement values. (TODO: where is and how to get measurement values then?)

        DNP3 spec section 5.1.6.1:
            The Application Layer provides the following services for the DNP3 User Layer in a master:
                - Formats requests directed to one or more outstations.
                - Notifies the DNP3 User Layer when new data or information arrives from an outstation.

        DNP spec section 5.1.6.3:
            The Application Layer requires specific services from the layers beneath it.
                - Partitioning of fragments into smaller portions for transport reliability.
                - Knowledge of which device(s) were the source of received messages.
                - Transmission of messages to specific devices or to all devices.
                - Message integrity (i.e., error-free reception and transmission of messages).
                - Knowledge of the time when messages arrive.
                - Either precise times of transmission or the ability to set time values
                  into outgoing messages.
    """

    def __init__(self,
                 masterstation_ip_str: str = "0.0.0.0",
                 outstation_ip_str: str = "127.0.0.1",
                 port: int = 20000,
                 masterstation_id_int: int = 2,
                 outstation_id_int: int = 1,
                 concurrencyHint: int = 1,
                 log_handler=asiodnp3.ConsoleLogger().Create(),
                 listener=asiodnp3.PrintingChannelListener().Create(),
                 # soe_handler=asiodnp3.PrintingSOEHandler().Create(),
                 soe_handler=SOEHandler(),
                 master_application=asiodnp3.DefaultMasterApplication().Create(),
                 channel_log_level=opendnp3.levels.NORMAL,
                 master_log_level=7,  # wild guess, 7: warning, 15 (opendnp3.levels.NORMAL): info
                 num_polling_retry: int = 2,
                 delay_polling_retry: float = 0.2,  # in seconds
                 stale_if_longer_than: float = 2,  # in seconds

                 stack_config=None,
                 *args, **kwargs):
        """
        TODO: docstring here
        """
        # TODO: refactor to apply factory pattern, allow further config

        self.log_handler = log_handler
        self.listener = listener
        self.soe_handler: SOEHandler = soe_handler
        self.master_application = master_application

        self.num_polling_retry = num_polling_retry
        self.delay_polling_retry = delay_polling_retry  # in seconds
        self.stale_if_longer_than = stale_if_longer_than  # in seconds

        _log.debug('Configuring the DNP3 stack.')
        self.stack_config = stack_config
        if not self.stack_config:
            self.stack_config = asiodnp3.MasterStackConfig()
            self.stack_config.master.responseTimeout = openpal.TimeDuration().Seconds(2)
            self.stack_config.link.RemoteAddr = outstation_id_int  # meaning for outstation, use 1 to follow simulator's default
            self.stack_config.link.LocalAddr = masterstation_id_int  # meaning for master station, use 2 to follow simulator's default

        # init steps: DNP3Manager(manager) -> TCPClient(channel) -> Master(master)
        # init DNP3Manager(manager)
        _log.debug('Creating a DNP3Manager.')
        self.manager = asiodnp3.DNP3Manager(concurrencyHint, self.log_handler)

        # init TCPClient(channel)
        _log.debug('Creating the DNP3 channel, a TCP client.')
        self.retry = asiopal.ChannelRetry().Default()
        level = opendnp3.levels.NORMAL | opendnp3.levels.ALL_COMMS  # TODO: check why this seems not working
        self.channel = self.manager.AddTCPClient(id="tcpclient",
                                                 levels=level,
                                                 retry=self.retry,
                                                 host=outstation_ip_str,
                                                 local=masterstation_ip_str,
                                                 port=port,
                                                 listener=self.listener)

        # init Master(master)
        _log.debug('Adding the master to the channel.')
        self.master = self.channel.AddMaster(id="master",
                                             SOEHandler=self.soe_handler,
                                             # SOEHandler=asiodnp3.PrintingSOEHandler().Create(),
                                             application=self.master_application,
                                             config=self.stack_config)

        _log.debug('Configuring some scans (periodic reads).')
        # Set up a "slow scan", an infrequent integrity poll that requests events and static data for all classes.
        self.slow_scan = self.master.AddClassScan(opendnp3.ClassField().AllClasses(),  # TODO: add interface entrypoint
                                                  openpal.TimeDuration().Minutes(30),
                                                  opendnp3.TaskConfig().Default())
        # Set up a "fast scan", a relatively-frequent exception poll that requests events and class 1 static data.
        self.fast_scan = self.master.AddClassScan(opendnp3.ClassField(opendnp3.ClassField.CLASS_1),
                                                  openpal.TimeDuration().Minutes(1),
                                                  opendnp3.TaskConfig().Default())

        # Configure log level for channel(server) and master
        # note: one of the following
        #   ALL = -1
        #   ALL_APP_COMMS = 129024
        #   ALL_COMMS = 130720
        #   NORMAL = 15  # INFO, WARN
        #   NOTHING = 0
        # TODO: Rewrite opendnp3.levels note: wild guess, 7: warning, 15 (opendnp3.levels.NORMAL): info
        _log.debug('Configuring log level')  # TODO: provide more info. Right now this log is not very useful
        self.channel_log_level: opendnp3.levels = channel_log_level
        self.master_log_level: opendnp3.levels = master_log_level

        self.channel.SetLogFilters(openpal.LogFilters(self.channel_log_level))
        self.master.SetLogFilters(openpal.LogFilters(self.master_log_level))
        # self.channel.SetLogFilters(openpal.LogFilters(opendnp3.levels.ALL_COMMS))
        # self.master.SetLogFilters(openpal.LogFilters(opendnp3.levels.ALL_COMMS))

        _log.debug('Enabling the master. At this point, traffic will start to flow between the Master and Outstations.')
        self.master.Enable()

        # TODO: the master and outstation init takes time (i.e., configuration). Hard-coded here
        # time.sleep(3)  # TODO: justify the neccessity

        # TODO: add tcp/ip connection validation process, e.g., using socket. Python - Test the TCP port connectivity

    def send_direct_operate_command(self,
                                    command: Union[opendnp3.ControlRelayOutputBlock,
                                                   opendnp3.AnalogOutputInt16,
                                                   opendnp3.AnalogOutputInt32,
                                                   opendnp3.AnalogOutputFloat32,
                                                   opendnp3.AnalogOutputDouble64],
                                    index: int,
                                    callback: Callable[[opendnp3.ICommandTaskResult], None],
                                    config: opendnp3.TaskConfig = opendnp3.TaskConfig().Default()):
        """
            Direct operate a single command

        :param command: command to operate
        :param index: index of the command
        :param callback: callback that will be invoked upon completion or failure.
        :param config: optional configuration that controls normal callbacks and allows the user to be specified for SA
        """
        self.master.DirectOperate(command, index, callback, config)  # real signature unknown; restored from __doc__

    def send_direct_operate_command_set(self, command_set, callback=asiodnp3.PrintingCommandCallback.Get(),
                                        config=opendnp3.TaskConfig().Default()):
        """
            Direct operate a set of commands

        :param command_set: set of command headers
        :param callback: callback that will be invoked upon completion or failure
        :param config: optional configuration that controls normal callbacks and allows the user to be specified for SA
        """
        self.master.DirectOperate(command_set, callback, config)

    def send_select_and_operate_command(self, command, index, callback=asiodnp3.PrintingCommandCallback.Get(),
                                        config=opendnp3.TaskConfig().Default()):  # TODO: compare to send_direct_operate_command, what's the difference
        """
            Select and operate a single command

        :param command: command to operate
        :param index: index of the command
        :param callback: callback that will be invoked upon completion or failure
        :param config: optional configuration that controls normal callbacks and allows the user to be specified for SA
        """
        self.master.SelectAndOperate(command, index, callback, config)

    def send_select_and_operate_command_set(self, command_set, callback=asiodnp3.PrintingCommandCallback.Get(),
                                            config=opendnp3.TaskConfig().Default()):  # TODO: compare to send_direct_operate_command_set, what's the difference
        """
            Select and operate a set of commands

        :param command_set: set of command headers
        :param callback: callback that will be invoked upon completion or failure
        :param config: optional configuration that controls normal callbacks and allows the user to be specified for SA
        """
        self.master.SelectAndOperate(command_set, callback, config)

    def retrieve_all_obj_by_gvid(self, gv_id: opendnp3.GroupVariationID,
                                 config=opendnp3.TaskConfig().Default()
                                 ) -> Dict[opendnp3.GroupVariation, Dict[int, DbPointVal]]:
        """
        Deprecated. (Use retrieve_val_by_gv instead)
        Retrieve point value (from an outstation databse) based on gvId (Group Variation ID).

        Common gvId: ref: dnp3 Namespace Reference: https://docs.stepfunc.io/dnp3/0.9.0/dotnet/namespacednp3.html
        TODO: rewrite opendnp3.GroupVariationID to add docstring
        for static state
            GroupVariationID(30, 6): Analog input - double-precision, floating-point with flag
            GroupVariationID(30, 1): Analog input - 32-bit with flag
            GroupVariationID(1, 2): Binary input - with flags

            GroupVariationID(40, 4): Analog Output Status - Double-precision floating point with flags
            GroupVariationID(40, 1): Analog Output Status - 32-bit with flags
            GroupVariationID(10, 2): Binary Output - With flags
        for event
            GroupVariationID(32, 4): Analog Input Event - 16-bit with time
            GroupVariationID(2, 2): Binary Input Event - With absolute time
            GroupVariationID(42, 8): Analog Output Event - Double-preicions floating point with time
            GroupVariationID(11, 2): Binary Output Event - With time

        :param opendnp3.GroupVariationID gv_id: group-variance Id
        :param opendnp3.TaskConfig config: Task configuration. Default: opendnp3.TaskConfig().Default()

        :return: retrieved point values stored in a nested dict.
        :rtype: Dict[opendnp3.GroupVariation, Dict[int, DbPointVal]]

        :example:
        >>> # prerequisite: outstation db properly configured and updated, master_application properly initialized
        >>> master_application.retrieve_all_obj_by_gvid(gv_id=opendnp3.GroupVariationID(30, 6))
        GroupVariation.Group30Var6: {0: 4.8, 1: 12.1, 2: 24.2, 3: 0.0}}
        """
        # self.master.ScanRange(gvId=opendnp3.GroupVariationID(30, 1), start=0, stop=3,
        #                 config=opendnp3.TaskConfig().Default())
        # self.master.ScanRange(gvId=gvId, start=index_start, stop=index_stop,
        #                       config=config)

        # self.master.ScanAllObjects(gvId=gvid,
        #                            config=config)
        # gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gvid)
        # db_val = {gv_cls: self.soe_handler.gv_index_value_nested_dict.get(gv_cls)}

        # TODO: refactor hard-coded retry and sleep, allow config
        # TODO: "prettify" the following while loop workflow. e.g., helper function + recurrent function
        self.master.ScanAllObjects(gvId=gv_id,
                                   config=config)
        gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
        gv_db_val = self.soe_handler.gv_index_value_nested_dict.get(gv_cls)

        # retry logic to improve performance
        retry_max = self.num_polling_retry
        n_retry = 0
        sleep_delay = self.delay_polling_retry
        while gv_db_val is None and n_retry < retry_max:
            self.master.ScanAllObjects(gvId=gv_id,
                                       config=config)
            # gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
            time.sleep(sleep_delay)
            gv_db_val = self.soe_handler.gv_index_value_nested_dict.get(gv_cls)
            n_retry += 1
            # print("=======n_retry, gv_db_val, gv_cls", n_retry, gv_db_val, gv_cls)
            # print("=======self.soe_handler", self.soe_handler)
            # print("=======self.soe_handler.gv_index_value_nested_dict id", self.soe_handler.gv_index_value_nested_dict,
            #       id(self.soe_handler.gv_index_value_nested_dict))

            if n_retry >= retry_max:
                _log.warning("==Retry numbers hit retry limit {}==".format(retry_max))

        return {gv_cls: gv_db_val}

    def retrieve_all_obj_by_gvids(self,
                                  gv_ids: Optional[List[opendnp3.GroupVariationID]] = None,
                                  config=opendnp3.TaskConfig().Default()
                                  ) -> Dict[opendnp3.GroupVariation, Dict[int, DbPointVal]]:
        """
        Deprecated. (encorage the user to use retrieve_val_by_gv instead)

        Retrieve point value (from an outstation databse) based on gvId (Group Variation ID).

        Common gvId: ref: dnp3 Namespace Reference: https://docs.stepfunc.io/dnp3/0.9.0/dotnet/namespacednp3.html
        TODO: rewrite opendnp3.GroupVariationID to add docstring
        for static state
            GroupVariationID(30, 6): Analog input - double-precision, floating-point with flag
            GroupVariationID(30, 1): Analog input - 32-bit with flag
            GroupVariationID(1, 2): Binary input - with flags

            GroupVariationID(40, 4): Analog Output Status - Double-precision floating point with flags
            GroupVariationID(40, 1): Analog Output Status - 32-bit with flags
            GroupVariationID(10, 2): Binary Output - With flags
        for event
            GroupVariationID(32, 4): Analog Input Event - 16-bit with time
            GroupVariationID(2, 2): Binary Input Event - With absolute time
            GroupVariationID(42, 8): Analog Output Event - Double-preicions floating point with time
            GroupVariationID(11, 2): Binary Output Event - With time

        :param opendnp3.GroupVariationID gv_ids: list of group-variance Id
        :param opendnp3.TaskConfig config: Task configuration. Default: opendnp3.TaskConfig().Default()

        :return: retrieved point values stored in a nested dict.
        :rtype: Dict[opendnp3.GroupVariation, Dict[int, DbPointVal]]

        :example:
        >>> # prerequisite: outstation db properly configured and updated, master_application properly initialized
        >>> master_application.retrieve_all_obj_by_gvids()  # using default
        GroupVariation.Group30Var6: {0: 4.8, 1: 12.1, 2: 24.2, 3: 0.0}}
        """

        gv_ids: Optional[List[opendnp3.GroupVariationID]]
        if gv_ids is None:  # using default
            # GroupVariationID(30, 6): Analog input - double-precision, floating-point with flag
            # GroupVariationID(1, 2): Binary input - with flags
            # GroupVariationID(40, 4): Analog Output Status - Double-precision floating point with flags
            # GroupVariationID(10, 2): Binary Output - With flags

            # GroupVariationID(32, 4): Analog Input Event - 16-bit with time
            # GroupVariationID(2, 2): Binary Input Event - With absolute time
            # GroupVariationID(42, 8): Analog Output Event - Double-preicions floating point with time
            # GroupVariationID(11, 2): Binary Output Event - With time
            gv_ids = [GroupVariationID(30, 6),
                      GroupVariationID(1, 2),
                      GroupVariationID(40, 4),
                      GroupVariationID(10, 2),
                      # GroupVariationID(32, 4),
                      # GroupVariationID(2, 2),
                      # GroupVariationID(42, 8),
                      # GroupVariationID(11, 2),
                      ]
        filtered_db: Dict[opendnp3.GroupVariation, Dict[int, DbPointVal]] = {}
        for gv_id in gv_ids:
            self.retrieve_all_obj_by_gvid(gv_id=gv_id, config=config)
            gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
            filtered_db.update({gv_cls: self.soe_handler.gv_index_value_nested_dict.get(gv_cls)})
        return filtered_db

    def _retrieve_all_obj_by_gvids_w_ts(self,
                                        gv_ids: Optional[List[opendnp3.GroupVariationID]] = None,
                                        config=opendnp3.TaskConfig().Default()
                                        ):
        """Retrieve point value (from an outstation databse) based on gvId (Group Variation ID).

        :param opendnp3.GroupVariationID gv_ids: list of group-variance Id
        :param opendnp3.TaskConfig config: Task configuration. Default: opendnp3.TaskConfig().Default()

        :return: retrieved point values stored in a nested dict.
        :rtype: Dict[opendnp3.GroupVariation, Dict[int, DbPointVal]]

        """
        gv_ids: Optional[List[opendnp3.GroupVariationID]]
        if gv_ids is None:  # using default
            gv_ids = [GroupVariationID(30, 6),
                      GroupVariationID(1, 2),
                      GroupVariationID(40, 4),
                      GroupVariationID(10, 2),
                      # GroupVariationID(32, 4),
                      # GroupVariationID(2, 2),
                      # GroupVariationID(42, 8),
                      # GroupVariationID(11, 2),
                      ]
        filtered_db_w_ts = {}
        for gv_id in gv_ids:
            # self.retrieve_all_obj_by_gvid(gv_id=gv_id, config=config)
            self.retrieve_val_by_gv(gv_id=gv_id)
            gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
            # filtered_db_w_ts.update({gv_cls: self.soe_handler.gv_ts_ind_val_dict.get(gv_cls)})
            filtered_db_w_ts.update({gv_cls: (self.soe_handler.gv_last_poll_dict.get(gv_cls),
                                              self.soe_handler.gv_index_value_nested_dict.get(gv_cls))})

        return filtered_db_w_ts

    def retrieve_all_obj_by_gvis(self,
                                 gv_id: opendnp3.GroupVariationID = None,
                                 index=None
                                 ) -> DbPointVal:
        """
        Retrive value based group-variation id and index
        """

        gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
        val: DbPointVal = self.soe_handler.gv_index_value_nested_dict.get(gv_cls).get(index)
        return val

    def retrieve_val_by_gv(self, gv_id: opendnp3.GroupVariationID) -> DbStorage:
        """Retrieve point value based on group-variation id, e.g., GroupVariationID(30, 6)

        Return ret_val: "ValStorage"

        EXAMPLE:
        >>> # prerequisite: outstation db properly configured and updated, master_application properly initialized
        >>> master_application.retrieve_val_by_gv(gv_id=opendnp3.GroupVariationID(30, 6))
        ({GroupVariation.Group30Var6: {0: 7.8, 1: 14.1, 2: 22.2, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0}}, datetime.datetime(2022, 9, 8, 22, 3, 50, 591742), 'init')
        """

        # alias
        ValStorage = Union[None, Tuple[datetime.datetime, Dict[int, DbPointVal]]]
        gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
        val_storage: ValStorage = self.soe_handler.gv_ts_ind_val_dict.get(gv_cls)
        val_storage = self.soe_handler.gv_last_poll_dict.get(gv_cls), self.soe_handler.gv_index_value_nested_dict.get(
            gv_cls)
        ret_val: {opendnp3.GroupVariation: Dict[int, DbPointVal]}

        ts = self.soe_handler.gv_last_poll_dict.get(gv_cls)
        stale_if_longer_than = self.stale_if_longer_than
        if ts and (datetime.datetime.now() - ts).total_seconds() < stale_if_longer_than:
            # Note: there is caching logic to prevent overuse self.master.ScanAllObjects.
            # The stale checking logic is to prevent extensive caching
            val_body = self.soe_handler.gv_index_value_nested_dict.get(gv_cls)
            ret_val = {gv_cls: val_body}
            _log.debug(f"Retrieve {ret_val} at {datetime.datetime.now()} using caching")
        else:
            ret_val = self._get_updated_val_storage(gv_id)
            _log.debug(f"Retrieve {ret_val} at {datetime.datetime.now()}")

        return ret_val

    def _get_updated_val_storage(self, gv_id: opendnp3.GroupVariationID) -> DbStorage:
        """
        Wrap on self.master.ScanAllObjects with retry logic
        """

        gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)

        # Start from fresh--Set val_storage to None
        self.soe_handler.gv_index_value_nested_dict[gv_cls] = None
        self.soe_handler.gv_ts_ind_val_dict[gv_cls] = None
        self.soe_handler.gv_last_poll_dict[gv_cls] = None
        # perform scan
        config = opendnp3.TaskConfig().Default()
        # TODO: refactor hard-coded retry and sleep, allow config
        # TODO: "prettify" the following while loop workflow. e.g., helper function + recurrent function
        self.master.ScanAllObjects(gvId=gv_id,
                                   config=config)
        # gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
        # # update stale logic to improve performance
        # self.soe_handler.update_stale_db()
        gv_db_val = self.soe_handler.gv_index_value_nested_dict.get(gv_cls)

        # retry logic to improve performance
        retry_max = self.num_polling_retry
        n_retry = 0
        sleep_delay = self.delay_polling_retry  # in seconds
        while gv_db_val is None and n_retry < retry_max:
            self.master.ScanAllObjects(gvId=gv_id,
                                       config=config)
            # gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
            time.sleep(sleep_delay)
            gv_db_val = self.soe_handler.gv_index_value_nested_dict.get(gv_cls)
            if gv_db_val is None:
                _log.debug(f"No value returned when polling {gv_cls}. "
                           f"Starting retry No. {n_retry + 1} (of {retry_max}) after {sleep_delay} sec.")
            n_retry += 1
            # print("=======n_retry, gv_db_val, gv_cls", n_retry, gv_db_val, gv_cls)
            # print("=======self.soe_handler", self.soe_handler)
            # print("=======self.soe_handler.gv_index_value_nested_dict id", self.soe_handler.gv_index_value_nested_dict,
            #       id(self.soe_handler.gv_index_value_nested_dict))
            # print("======gv_db_val", gv_db_val)

            if n_retry >= retry_max:
                _log.warning("==Retry numbers hit retry limit {}, when polling {}==".format(retry_max, gv_cls))
                info_gv: GroupVariation = gv_cls
                # Note: this is method is penetrating (it should belong to SOEHandler instead)
                # but SOEHandler is blind to retry logic
                self.soe_handler.gv_ts_ind_val_dict[info_gv] = (datetime.datetime.now(),
                                                                self.soe_handler.gv_ts_ind_val_dict.get(info_gv))
                self.soe_handler.gv_last_poll_dict[info_gv] = datetime.datetime.now()
                # self.soe_handler[info_gv]

        return {gv_cls: gv_db_val}

    def get_db_by_group_variation(self, group: int, variation: int) -> DbStorage:
        """Retrieve point value (from an outstation databse) based on Group-Variation pair.

        Common gvId: ref: dnp3 Namespace Reference: https://docs.stepfunc.io/dnp3/0.9.0/dotnet/namespacednp3.html

        for static state
            GroupVariationID(30, 6): Analog input - double-precision, floating-point with flag
            GroupVariationID(30, 1): Analog input - 32-bit with flag
            GroupVariationID(1, 2): Binary input - with flags

            GroupVariationID(40, 4): Analog Output Status - Double-precision floating point with flags
            GroupVariationID(40, 1): Analog Output Status - 32-bit with flags
            GroupVariationID(10, 2): Binary Output - With flags
        for event
            GroupVariationID(32, 4): Analog Input Event - 16-bit with time
            GroupVariationID(2, 2): Binary Input Event - With absolute time
            GroupVariationID(42, 8): Analog Output Event - Double-preicions floating point with time
            GroupVariationID(11, 2): Binary Output Event - With time

        :param group: group Id
        :param variation: variation Id

        :return: retrieved point values stored in a nested dict.
        :rtype: Dict[opendnp3.GroupVariation, Dict[int, DbPointVal]]

        :example:
        >>> # prerequisite: outstation db properly configured and updated, master_application properly initialized
        >>> master_application.get_db_by_group_variation(group=6, variation=30)
        GroupVariation.Group30Var6: {0: 4.8, 1: 12.1, 2: 24.2, 3: 0.0}}
        """

        gv_id = opendnp3.GroupVariationID(group, variation)
        return self.retrieve_val_by_gv(gv_id=gv_id)

    def get_db_by_group_variation_index(self, group: int, variation: int, index: int) -> DbStorage:
        """Retrieve point value based on group-variation id, e.g., GroupVariationID(30, 6), and index

         Return ret_val: DbStorage (return_meta=True, default), DbPointVal(return_meta=False)
        
         EXAMPLE:
         >>> # prerequisite: outstation db properly configured and updated, master_application properly initialized
         >>> master_application.get_db_by_group_variation_index(group=6, variation=30, index=0)
         ({GroupVariation.Group30Var6: {0: 7.8, 1: 14.1, 2: 22.2, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0}}, datetime.datetime(2022, 9, 8, 22, 3, 50, 591742), 'init')

        """

        gv_id = opendnp3.GroupVariationID(group, variation)
        gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)

        ts = self.soe_handler.gv_last_poll_dict.get(gv_cls)
        stale_if_longer_than = self.stale_if_longer_than
        if ts and (datetime.datetime.now() - ts).total_seconds() < stale_if_longer_than:  # Use aggressive caching
            vals: Dict[int, DbPointVal] = self.soe_handler.gv_index_value_nested_dict.get(gv_cls)
        else:  # Use normal routine
            vals: Dict[int, DbPointVal] = self.get_db_by_group_variation(group, variation).get(gv_cls)

        if vals:
            return {gv_cls: {index: vals.get(index)}}
        else:
            return {gv_cls: {index: None}}

    def get_val_by_group_variation_index(self, group: int, variation: int, index: int) -> DbPointVal:
        val_w_meta = self.get_db_by_group_variation_index(group, variation, index)
        gv_id = opendnp3.GroupVariationID(group, variation)
        gv_cls: opendnp3.GroupVariation = parsing_gvid_to_gvcls(gv_id)
        if val_w_meta.get(gv_cls):
            return val_w_meta.get(gv_cls).get(index)
        else:
            return None

    def shutdown(self):
        # print("=======before master del self.__dict", self.__dict__)
        time.sleep(2)  # Note: hard-coded sleep to avoid hanging process
        del self.slow_scan
        del self.fast_scan
        del self.master
        del self.channel
        del self.manager
