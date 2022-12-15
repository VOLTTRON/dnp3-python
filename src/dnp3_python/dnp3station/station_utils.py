import datetime
import logging
import sys
import time

from pydnp3 import opendnp3, openpal, asiopal, asiodnp3
from .visitors import *
from pydnp3.opendnp3 import GroupVariation, GroupVariationID

from typing import Callable, Union, Dict, Tuple, List, Optional, Type, TypeVar

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)
# _log.setLevel(logging.INFO)

# alias
ICollectionIndexedVal = Union[opendnp3.ICollectionIndexedAnalog,
                              opendnp3.ICollectionIndexedBinary,
                              opendnp3.ICollectionIndexedAnalogOutputStatus,
                              opendnp3.ICollectionIndexedBinaryOutputStatus]
DbPointVal = Union[float, int, bool]
VisitorClass = Union[VisitorIndexedTimeAndInterval,
                     VisitorIndexedAnalog,
                     VisitorIndexedBinary,
                     VisitorIndexedCounter,
                     VisitorIndexedFrozenCounter,
                     VisitorIndexedAnalogOutputStatus,
                     VisitorIndexedBinaryOutputStatus,
                     VisitorIndexedDoubleBitBinary]

MasterCmdType = Union[opendnp3.AnalogOutputDouble64,
                      opendnp3.AnalogOutputFloat32,
                      opendnp3.AnalogOutputInt32,
                      opendnp3.AnalogOutputInt16,
                      opendnp3.ControlRelayOutputBlock]

OutstationCmdType = Union[opendnp3.Analog,
                          opendnp3.AnalogOutputStatus,
                          opendnp3.Binary,
                          opendnp3.BinaryOutputStatus]

MeasurementType = TypeVar("MeasurementType",
                          bound=opendnp3.Measurement)  # inheritance, e.g., opendnp3.Analog,

# TODO: add validating connection logic
# TODO: add validating configuration logic
#  (e.g., check if db at outstation side is configured correctly, i.e., OutstationStackConfig)


class HandlerLogger:
    def __int__(self, logger_name="HandlerLogger"):
        self._log = logging.getLogger(logger_name)
        self.config_logger()

    def get_logger(self):
        return self._log

    def config_logger(self, log_level=logging.INFO):
        self._log.addHandler(stdout_stream)
        self._log.setLevel(log_level)


class AppChannelListener(asiodnp3.IChannelListener):
    """
        Override IChannelListener in this manner to implement application-specific channel behavior.
    """

    def __init__(self):
        super(AppChannelListener, self).__init__()

    def OnStateChange(self, state):
        _log.debug('In AppChannelListener.OnStateChange: state={}'.format(opendnp3.ChannelStateToString(state)))


class SOEHandler(opendnp3.ISOEHandler):
    """
        Override ISOEHandler in this manner to implement application-specific sequence-of-events behavior.

        This is an interface for SequenceOfEvents (SOE) callbacks from the Master stack to the application layer.
    """

    def __init__(self, soehandler_log_level=logging.INFO, *args, **kwargs):
        super(SOEHandler, self).__init__()

        # auxiliary database
        self._gv_index_value_nested_dict: Dict[GroupVariation, Optional[Dict[int, DbPointVal]]] = {}
        self._gv_ts_ind_val_dict: Dict[GroupVariation, Tuple[datetime.datetime, Optional[Dict[int, DbPointVal]]]] = {}
        self._gv_last_poll_dict: Dict[GroupVariation, Optional[datetime.datetime]] = {}

        # logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_logger(log_level=soehandler_log_level)

        # db
        self._db = self.init_db()

    def config_logger(self, log_level=logging.INFO):
        self.logger.addHandler(stdout_stream)
        self.logger.setLevel(log_level)

    def Process(self, info,
                values: ICollectionIndexedVal,
                *args, **kwargs):
        """
            Process measurement data.
            Note: will only evoke when there is response from outstation

        :param info: HeaderInfo
        :param values: A collection of values received from the Outstation (various data types are possible).
        """
        # print("=========Process, info.gv, values", info.gv, values)
        visitor_class_types: dict = {
            opendnp3.ICollectionIndexedBinary: VisitorIndexedBinary,
            opendnp3.ICollectionIndexedDoubleBitBinary: VisitorIndexedDoubleBitBinary,
            opendnp3.ICollectionIndexedCounter: VisitorIndexedCounter,
            opendnp3.ICollectionIndexedFrozenCounter: VisitorIndexedFrozenCounter,
            opendnp3.ICollectionIndexedAnalog: VisitorIndexedAnalog,
            opendnp3.ICollectionIndexedBinaryOutputStatus: VisitorIndexedBinaryOutputStatus,
            opendnp3.ICollectionIndexedAnalogOutputStatus: VisitorIndexedAnalogOutputStatus,
            opendnp3.ICollectionIndexedTimeAndInterval: VisitorIndexedTimeAndInterval
        }
        visitor_class: Union[Callable, VisitorClass] = visitor_class_types[type(values)]
        visitor = visitor_class()  # init
        # hot-fix VisitorXXAnalog do not distinguish float and integer.
        if visitor_class == VisitorIndexedAnalog:
            # Parsing to Int
            if info.gv in [
                # GroupVariation.Group30Var0,
                GroupVariation.Group30Var1,
                GroupVariation.Group30Var2,
                GroupVariation.Group30Var3,
                GroupVariation.Group30Var4,
                # GroupVariation.Group32Var0,
                GroupVariation.Group32Var1,
                GroupVariation.Group32Var2,
                GroupVariation.Group32Var3,
                GroupVariation.Group32Var4
            ]:
                visitor = VisitorIndexedAnalogInt()
        elif visitor_class == VisitorIndexedAnalogOutputStatus:
            if info.gv in [
                # GroupVariation.Group40Var0,
                GroupVariation.Group40Var1,
                GroupVariation.Group40Var2,
                # GroupVariation.Group42Var0,
                GroupVariation.Group42Var1,
                GroupVariation.Group42Var2,
                GroupVariation.Group42Var3,
                GroupVariation.Group42Var4
            ]:
                visitor = VisitorIndexedAnalogOutputStatusInt()
        # Note: mystery method, magic side effect to update visitor.index_and_value
        values.Foreach(visitor)

        # visitor.index_and_value: List[Tuple[int, DbPointVal]]
        for index, value in visitor.index_and_value:
            log_string = 'SOEHandler.Process {0}\theaderIndex={1}\tdata_type={2}\tindex={3}\tvalue={4}'
            self.logger.debug(log_string.format(info.gv, info.headerIndex, type(values).__name__, index, value))
            # print(log_string.format(info.gv, info.headerIndex, type(values).__name__, index, value))

        info_gv: GroupVariation = info.gv
        visitor_ind_val: List[Tuple[int, DbPointVal]] = visitor.index_and_value

        # _log.info("======== SOEHandler.Process")
        # _log.info(f"info_gv {info_gv}")
        # _log.info(f"visitor_ind_val {visitor_ind_val}")
        self._post_process(info_gv=info_gv, visitor_ind_val=visitor_ind_val)

    def _post_process(self, info_gv: GroupVariation, visitor_ind_val: List[Tuple[int, DbPointVal]]):
        """
        SOEHandler post process logic to stage data at MasterStation side
        to improve performance: e.g., consistent output

        info_gv: GroupVariation,
        visitor_ind_val: List[Tuple[int, DbPointVal]]
        """
        # Use dict update method to mitigate delay due to asynchronous communication. (i.e., return None)
        # Also, capture unsolicited updated values.
        if not self._gv_index_value_nested_dict.get(info_gv):
            self._gv_index_value_nested_dict[info_gv] = (dict(visitor_ind_val))
        else:
            self._gv_index_value_nested_dict[info_gv].update(dict(visitor_ind_val))

        # Use another layer of storage to handle timestamp related logic
        self._gv_ts_ind_val_dict[info_gv] = (datetime.datetime.now(),
                                             self._gv_index_value_nested_dict.get(info_gv))
        # Use another layer of storage to handle timestamp related logic
        self._gv_last_poll_dict[info_gv] = datetime.datetime.now()

    def Start(self):
        self.logger.debug('In SOEHandler.Start====')

    def End(self):
        self.logger.debug('In SOEHandler.End')

    @property
    def gv_index_value_nested_dict(self) -> Dict[GroupVariation, Optional[Dict[int, DbPointVal]]]:
        return self._gv_index_value_nested_dict

    @property
    def gv_ts_ind_val_dict(self):
        return self._gv_ts_ind_val_dict

    @property
    def gv_last_poll_dict(self) -> Dict[GroupVariation, Optional[datetime.datetime]]:
        return self._gv_last_poll_dict

    @property
    def db(self) -> dict:
        """micmic DbHandler.db"""
        self._consolidate_db()
        return self._db

    @staticmethod
    def init_db(size=10):
        db = {}
        for number, gv_name in zip([size,
                                    size,
                                    size,
                                    size],
                                   ["Analog", "AnalogOutputStatus",
                                    "Binary", "BinaryOutputStatus"]):
            val_body = dict((n, None) for n in range(number))
            db[gv_name] = val_body

        return db

    def _consolidate_db(self):
        """map group variance to db with 4 keys:
        "Binary", "BinaryOutputStatus", "Analog", "AnalogOutputStatus"
        """
        pass
        # for Analog
        _db = {"Analog": self._gv_index_value_nested_dict.get(GroupVariation.Group30Var6)}
        if _db.get("Analog"):
            self._db.update(_db)
        # for AnalogOutputStatus
        _db = {"AnalogOutputStatus": self._gv_index_value_nested_dict.get(GroupVariation.Group40Var4)}
        if _db.get("AnalogOutputStatus"):
            self._db.update(_db)
        # for Binary
        _db = {"Binary": self._gv_index_value_nested_dict.get(GroupVariation.Group1Var2)}
        if _db.get("Binary"):
            self._db.update(_db)
        # for Binary
        _db = {"BinaryOutputStatus": self._gv_index_value_nested_dict.get(GroupVariation.Group10Var2)}
        if _db.get("BinaryOutputStatus"):
            self._db.update(_db)


def collection_callback(result=None):
    """
    :type result: opendnp3.CommandPointResult
    """
    print("Header: {0} | Index:  {1} | State:  {2} | Status: {3}".format(
        result.headerIndex,
        result.index,
        opendnp3.CommandPointStateToString(result.state),
        opendnp3.CommandStatusToString(result.status)
    ))


def command_callback(result: opendnp3.ICommandTaskResult = None):
    """
    :type result: opendnp3.ICommandTaskResult
    """
    # print("Received command result with summary: {}".format(opendnp3.TaskCompletionToString(result.summary)))
    # result.ForeachItem(collection_callback)
    pass


def restart_callback(result=opendnp3.RestartOperationResult()):
    if result.summary == opendnp3.TaskCompletion.SUCCESS:
        print("Restart success | Restart Time: {}".format(result.restartTime.GetMilliseconds()))
    else:
        print("Restart fail | Failure: {}".format(opendnp3.TaskCompletionToString(result.summary)))


def parsing_gvid_to_gvcls(gvid: GroupVariationID) -> GroupVariation:
    """Mapping gvId to GroupVariation member class

    :param opendnp3.GroupVariationID gvid: group-variance Id

    :return: GroupVariation member class.
    :rtype: opendnp3.GroupVariation

    :example:
    >>> parsing_gvid_to_gvcls(gvid=GroupVariationID(30, 6))
    GroupVariation.Group30Var6
    """
    # print("====gvId GroupVariationID", gvid)
    group: int = gvid.group
    variation: int = gvid.variation
    gv_cls: GroupVariation

    gv_cls = GroupVariationID(30, 6)  # default
    # auto parsing
    try:
        gv_cls = getattr(opendnp3.GroupVariation, f"Group{group}Var{variation}")
        assert gv_cls is not None
    except ValueError as e:
        _log.warning(f"Group{group}Var{variation} is not valid opendnp3.GroupVariation")

    return gv_cls


def parsing_gv_to_mastercmdtype(group: int, variation: int, val_to_set: DbPointVal) -> MasterCmdType:
    pass
    """
    hard-coded parsing, e.g., group40, variation:4 -> opendnp3.AnalogOutputDouble64
    """
    master_cmd: MasterCmdType
    # AnalogOutput
    if group == 40:
        if not type(val_to_set) in [float, int]:
            raise ValueError(f"val_to_set {val_to_set} of MasterCmdType group {group}, variation {variation} invalid.")
        if variation == 1:
            master_cmd = opendnp3.AnalogOutputInt32()
        elif variation == 2:
            master_cmd = opendnp3.AnalogOutputInt16()
        elif variation == 3:
            master_cmd = opendnp3.AnalogOutputFloat32()
        elif variation == 4:
            master_cmd = opendnp3.AnalogOutputDouble64()
        else:
            raise ValueError(f"val_to_set {val_to_set} of MasterCmdType group {group} invalid.")

        master_cmd.value = val_to_set
    # BinaryOutput
    elif group == 10 and variation in [1, 2]:
        master_cmd = opendnp3.ControlRelayOutputBlock()
        if not type(val_to_set) is bool:
            raise ValueError(f"val_to_set {val_to_set} of MasterCmdType group {group}, variation {variation} invalid.")
        if val_to_set is True:
            master_cmd.rawCode = 3
        else:
            master_cmd.rawCode = 4
    else:
        raise ValueError(f"val_to_set {val_to_set} of MasterCmdType group {group} invalid.")

    return master_cmd


# alias
# OutstationCmdType = Union[opendnp3.Analog, opendnp3.Binary, opendnp3.AnalogOutputStatus,
#                           opendnp3.BinaryOutputStatus]  # based on asiodnp3.UpdateBuilder.Update(**args)
# MasterCmdType = Union[opendnp3.AnalogOutputDouble64,
#                       opendnp3.AnalogOutputFloat32,
#                       opendnp3.AnalogOutputInt32,
#                       opendnp3.AnalogOutputInt16,
#                       opendnp3.ControlRelayOutputBlock]


def master_to_outstation_command_parser(master_cmd: MasterCmdType) -> OutstationCmdType:
    """
    Used to parse send command to update command, e.g., opendnp3.AnalogOutputDouble64 -> AnalogOutputStatus
    """
    # return None
    if type(master_cmd) in [opendnp3.AnalogOutputDouble64,
                            opendnp3.AnalogOutputFloat32,
                            opendnp3.AnalogOutputInt32,
                            opendnp3.AnalogOutputInt16]:
        return opendnp3.AnalogOutputStatus(value=master_cmd.value)
    elif type(master_cmd) is opendnp3.ControlRelayOutputBlock:
        # Note: ControlRelayOutputBlock requires to use hard-coded rawCode to retrieve value at this version.
        bi_value: bool
        if master_cmd.rawCode == 3:
            bi_value = True
        elif master_cmd.rawCode == 4:
            bi_value = False
        else:
            raise ValueError(
                f"master_cmd.rawCode {master_cmd.rawCode} is not a valid rawCode. (3: On/True, 4:Off/False.")
        return opendnp3.BinaryOutputStatus(value=bi_value)
    else:
        raise ValueError(f"master_cmd {master_cmd} with type {type(master_cmd)} is not a valid command.")


class DBHandler:
    """
        Work as an auxiliary database for outstation (Mimic SOEHAndler for master-station)
    """

    def __init__(self, stack_config=asiodnp3.OutstationStackConfig(opendnp3.DatabaseSizes.AllTypes(10)),
                 dbhandler_log_level=logging.INFO, *args, **kwargs):

        self.stack_config = stack_config
        self._db: dict = self.config_db(stack_config)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_logger(log_level=dbhandler_log_level)

    def config_logger(self, log_level=logging.INFO):
        self.logger.addHandler(stdout_stream)
        self.logger.setLevel(log_level)

    @staticmethod
    def config_db(stack_config):
        db = {}
        for number, gv_name in zip([stack_config.dbConfig.sizes.numBinary,
                                    stack_config.dbConfig.sizes.numBinaryOutputStatus,
                                    stack_config.dbConfig.sizes.numAnalog,
                                    stack_config.dbConfig.sizes.numAnalogOutputStatus],
                                   ["Analog", "AnalogOutputStatus",
                                    "Binary", "BinaryOutputStatus"]):
            val_body = dict((n, None) for n in range(number))
            db[gv_name] = val_body

        return db

    @property
    def db(self) -> dict:
        return self._db

    def process(self, command, index):
        pass
        # _log.info(f"command {command}")
        # _log.info(f"index {index}")
        update_body: dict = {index: command.value}
        if self.db.get(command.__class__.__name__):
            self.db[command.__class__.__name__].update(update_body)
        else:
            self.db[command.__class__.__name__] = update_body
        # _log.info(f"========= self.db {self.db}")


class MyLogger(openpal.ILogHandler):
    """
        Override ILogHandler in this manner to implement application-specific logging behavior.
    """

    def __init__(self):
        super(MyLogger, self).__init__()

    def Log(self, entry):
        filters = entry.filters.GetBitfield()
        location = entry.location.rsplit('/')[-1] if entry.location else ''
        message = entry.message
        _log.debug('Log\tfilters={}\tlocation={}\tentry={}'.format(filters, location, message))