import datetime
import logging
import sys
import time

from pydnp3 import opendnp3, openpal, asiopal, asiodnp3
from .visitors import *
from pydnp3.opendnp3 import GroupVariation, GroupVariationID

from typing import Callable, Union, Dict, Tuple, List, Optional

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

# TODO: add validating connection logic
# TODO: add validating configuration logic
#  (e.g., check if db at outstation side is configured correctly, i.e., OutstationStackConfig)
class MyLogger(openpal.ILogHandler):
    """
        Override ILogHandler in this manner to implement application-specific logging behavior.
    """

    def __init__(self):
        super(MyLogger, self).__init__()

    def Log(self, entry):
        flag = opendnp3.LogFlagToString(entry.filters.GetBitfield())
        filters = entry.filters.GetBitfield()
        location = entry.location.rsplit('/')[-1] if entry.location else ''
        message = entry.message
        _log.debug('LOG\t\t{:<10}\tfilters={:<5}\tlocation={:<25}\tentry={}'.format(flag, filters, location, message))


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
    # TODO: refactor to its own module
    def __init__(self, soehandler_log_level=logging.INFO, *args, **kwargs):
        super(SOEHandler, self).__init__()
        self._gv_index_value_nested_dict: Dict[GroupVariation, Optional[Dict[int, DbPointVal]]] = {}
        self._gv_ts_ind_val_dict: Dict[GroupVariation, Tuple[datetime.datetime, Optional[Dict[int, DbPointVal]]]] = {}
        _log.setLevel(soehandler_log_level)  # TODO: refactor to its own module (right now thi si global)

        self._gv_last_poll_dict: Dict[GroupVariation, Optional[datetime.datetime]] = {}

    def Process(self, info,
                values: ICollectionIndexedVal,
                *args, **kwargs):
        """
            Process measurement data.
            Note: will only evoke when there is response from outstation

        :param info: HeaderInfo
        :param values: A collection of values received from the Outstation (various data types are possible).
        """
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
        # Note: mystery method, magic side effect to update visitor.index_and_value
        values.Foreach(visitor)

        # visitor.index_and_value: List[Tuple[int, DbPointVal]]
        for index, value in visitor.index_and_value:
            log_string = 'SOEHandler.Process {0}\theaderIndex={1}\tdata_type={2}\tindex={3}\tvalue={4}'
            _log.debug(log_string.format(info.gv, info.headerIndex, type(values).__name__, index, value))
            # print(log_string.format(info.gv, info.headerIndex, type(values).__name__, index, value))

        info_gv: GroupVariation = info.gv
        visitor_ind_val: List[Tuple[int, DbPointVal]] = visitor.index_and_value

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
        _log.debug('In SOEHandler.Start====')

    def End(self):
        _log.debug('In SOEHandler.End')

    @property
    def gv_index_value_nested_dict(self) -> Dict[GroupVariation, Optional[Dict[int, DbPointVal]]]:
        return self._gv_index_value_nested_dict

    @property
    def gv_ts_ind_val_dict(self):
        return self._gv_ts_ind_val_dict

    @property
    def gv_last_poll_dict(self) -> Dict[GroupVariation, Optional[datetime.datetime]]:
        return self._gv_last_poll_dict


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
    # if group == 30 and variation == 6:
    #     gv_cls = GroupVariation.Group30Var6
    # elif group == 30 and variation == 1:
    #     gv_cls = GroupVariation.Group30Var1
    # elif group == 1 and variation == 2:
    #     gv_cls = GroupVariation.Group1Var2
    # elif group == 40 and variation == 4:
    #     gv_cls = GroupVariation.Group40Var4
    # elif group == 4 and variation == 1:
    #     gv_cls = GroupVariation.Group40Var1
    # elif group == 10 and variation == 2:
    #     gv_cls = GroupVariation.Group10Var2
    # elif group == 32 and variation == 4:
    #     gv_cls = GroupVariation.Group32Var4
    # elif group == 2 and variation == 2:
    #     gv_cls = GroupVariation.Group2Var2
    # elif group == 42 and variation == 8:
    #     gv_cls = GroupVariation.Group42Var8
    # elif group == 11 and variation == 2:
    #     gv_cls = GroupVariation.Group11Var2

    return gv_cls
