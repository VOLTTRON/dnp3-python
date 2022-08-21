import datetime
import logging
import sys
import time

from pydnp3 import opendnp3, openpal, asiopal, asiodnp3
from .visitors import *
from pydnp3.opendnp3 import GroupVariation, GroupVariationID

from typing import Callable, Union

FILTERS = opendnp3.levels.NORMAL | opendnp3.levels.ALL_COMMS
HOST = "127.0.0.1"
LOCAL = "0.0.0.0"
# HOST = "192.168.1.14"
PORT = 20000

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)
_log.setLevel(logging.DEBUG)


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

    def __init__(self):
        super(SOEHandler, self).__init__()
        self._class_index_value = None
        self._class_index__value_dict = {}
        self._class_index_value_nested_dict = {}
        self._gv_index_value_nested_dict = {}

    def get_class_index_value(self):
        return self._class_index_value

    def Process(self, info,
                values: Union[opendnp3.ICollectionIndexedAnalog,
                              opendnp3.ICollectionIndexedBinary,
                              opendnp3.ICollectionIndexedAnalogOutputStatus,
                              opendnp3.ICollectionIndexedBinaryOutputStatus],
                *args, **kwargs):
        """
            Process measurement data.

        :param info: HeaderInfo
        :param values: A collection of values received from the Outstation (various data types are possible).
        """
        visitor_class_types = {
            opendnp3.ICollectionIndexedBinary: VisitorIndexedBinary,
            opendnp3.ICollectionIndexedDoubleBitBinary: VisitorIndexedDoubleBitBinary,
            opendnp3.ICollectionIndexedCounter: VisitorIndexedCounter,
            opendnp3.ICollectionIndexedFrozenCounter: VisitorIndexedFrozenCounter,
            opendnp3.ICollectionIndexedAnalog: VisitorIndexedAnalog,
            opendnp3.ICollectionIndexedBinaryOutputStatus: VisitorIndexedBinaryOutputStatus,
            opendnp3.ICollectionIndexedAnalogOutputStatus: VisitorIndexedAnalogOutputStatus,
            opendnp3.ICollectionIndexedTimeAndInterval: VisitorIndexedTimeAndInterval
        }
        visitor_class = visitor_class_types[type(values)]
        visitor = visitor_class()
        values.Foreach(
            visitor)  # mystery method, magic side effect. Seems to init visitor_class based on values (though not pythonic way)

        # print("================= values type", type(values))
        # print("=====values.count", values.Count())

        for index, value in visitor.index_and_value:
            # print("=================this seems important")
            log_string = 'SOEHandler.Process {0}\theaderIndex={1}\tdata_type={2}\tindex={3}\tvalue={4}'
            _log.debug(log_string.format(info.gv, info.headerIndex, type(values).__name__, index, value))

        # TODO: it seems the visitor is not very efficient

        # self._class_index_value = (visitor_class, visitor.index_and_value)
        # self._class_index__value_dict[visitor_class] = visitor.index_and_value
        # # update nested dict
        # if not self._class_index_value_nested_dict.get(visitor_class):
        #     self._class_index_value_nested_dict[visitor_class] = dict(visitor.index_and_value)
        # else:
        #     self._class_index_value_nested_dict[visitor_class].update(dict(visitor.index_and_value))
        # # print("=============== self._class_index_value_nested_dict", self._class_index_value_nested_dict)

        if not self._gv_index_value_nested_dict.get(info.gv):
            # self._gv_index_value_nested_dict[info.gv] = dict(visitor.index_and_value)
            self.gv_index_value_nested_dict[info.gv] = dict(visitor.index_and_value)
        else:
            # self._gv_index_value_nested_dict[info.gv].update(dict(visitor.index_and_value))
            self.gv_index_value_nested_dict[info.gv].update(dict(visitor.index_and_value))

        # time.sleep(1)  # TODO: wait for the internal database to update
        # print("=============== dict(visitor.index_and_value)", dict(visitor.index_and_value), datetime.datetime.now())
        # print("=============== self._gv_index_value_nested_dict", self._gv_index_value_nested_dict)
        # print("=============== info.gv", info.gv)

        # print("==very import== class_index_value", self._class_index_value)
        # print("---------- import args, kwargs", *args, **kwargs) # nothing here
        # print("---------- important info", info, type(info))
        # print("---------- important dir(info)", info, dir(info))
        # print('info.flagsValid', info.flagsValid, 'info.gv', info.gv,
        #       'info.headerIndex', info.headerIndex, 'info.isEventVariation', info.isEventVariation,
        #       'info.qualifier', info.qualifier, 'info.tsmode', info.tsmode,
        #       '_class_index_value: ', self._class_index_value)
        # print("_class_index__value_dict", self._class_index__value_dict)

    def Start(self):
        _log.debug('In SOEHandler.Start')

    def End(self):
        _log.debug('In SOEHandler.End')

    @property
    def gv_index_value_nested_dict(self):
        return self._gv_index_value_nested_dict


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
    print("Received command result with summary: {}".format(opendnp3.TaskCompletionToString(result.summary)))
    result.ForeachItem(collection_callback)


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
    # TODO: hard-coded for now. transfer to auto mapping
    # print("====gvId GroupVariationID", gvid)
    group: int = gvid.group
    variation: int = gvid.variation
    gv_cls: GroupVariation

    if group == 30 and variation == 6:
        gv_cls = GroupVariation.Group30Var6
    elif group == 30 and variation == 1:
        gv_cls = GroupVariation.Group30Var1
    elif group == 1 and variation == 2:
        gv_cls = GroupVariation.Group1Var2
    elif group == 40 and variation == 4:
        gv_cls = GroupVariation.Group40Var4
    elif group == 4 and variation == 1:
        gv_cls = GroupVariation.Group40Var1
    elif group == 10 and variation == 2:
        gv_cls = GroupVariation.Group10Var2
    elif group == 32 and variation == 4:
        gv_cls = GroupVariation.Group32Var4
    elif group == 2 and variation == 2:
        gv_cls = GroupVariation.Group2Var2
    elif group == 42 and variation == 8:
        gv_cls = GroupVariation.Group42Var8
    elif group == 11 and variation == 2:
        gv_cls = GroupVariation.Group11Var2

    return gv_cls
