import logging
import sys
import time

from pydnp3 import opendnp3, openpal, asiopal, asiodnp3
from visitors import *

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


class MyMaster:
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
                 log_handler=asiodnp3.ConsoleLogger().Create(),
                 listener=asiodnp3.PrintingChannelListener().Create(),
                 soe_handler=asiodnp3.PrintingSOEHandler().Create(),
                 master_application=asiodnp3.DefaultMasterApplication().Create(),
                 stack_config=None):
        _log.debug('Creating a DNP3Manager.')
        self.log_handler = log_handler
        self.manager = asiodnp3.DNP3Manager(1, self.log_handler)

        _log.debug('Creating the DNP3 channel, a TCP client.')
        self.retry = asiopal.ChannelRetry().Default()
        self.listener = listener
        self.channel = self.manager.AddTCPClient("tcpclient",
                                                 FILTERS,
                                                 self.retry,
                                                 HOST,
                                                 LOCAL,
                                                 PORT,
                                                 self.listener)

        _log.debug('Configuring the DNP3 stack.')
        self.stack_config = stack_config
        if not self.stack_config:
            self.stack_config = asiodnp3.MasterStackConfig()
            self.stack_config.master.responseTimeout = openpal.TimeDuration().Seconds(2)
            self.stack_config.link.RemoteAddr = 1  # meaning for outstation, use 1 to follow simulator's default
            self.stack_config.link.LocalAddr = 2  # meaning for master station, use 2 to follow simulator's default

        _log.debug('Adding the master to the channel.')
        self.soe_handler: SOEHandler = soe_handler
        self.master_application = master_application
        self.master = self.channel.AddMaster("master",
                                             # asiodnp3.PrintingSOEHandler().Create(),
                                             self.soe_handler,
                                             self.master_application,
                                             self.stack_config)

        _log.debug('Configuring some scans (periodic reads).')
        # Set up a "slow scan", an infrequent integrity poll that requests events and static data for all classes.
        self.slow_scan = self.master.AddClassScan(opendnp3.ClassField().AllClasses(),
                                                  openpal.TimeDuration().Minutes(30),
                                                  opendnp3.TaskConfig().Default())
        # Set up a "fast scan", a relatively-frequent exception poll that requests events and class 1 static data.
        self.fast_scan = self.master.AddClassScan(opendnp3.ClassField(opendnp3.ClassField.CLASS_1),
                                                  openpal.TimeDuration().Minutes(1),
                                                  opendnp3.TaskConfig().Default())

        self.channel.SetLogFilters(openpal.LogFilters(opendnp3.levels.ALL_COMMS))
        self.master.SetLogFilters(openpal.LogFilters(opendnp3.levels.ALL_COMMS))

        _log.debug('Enabling the master. At this point, traffic will start to flow between the Master and Outstations.')
        self.master.Enable()
        time.sleep(5)

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

    def shutdown(self):
        del self.slow_scan
        del self.fast_scan
        del self.master
        del self.channel
        self.manager.Shutdown()


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
    def get_class_index_value(self):
        return self._class_index_value

    def Process(self, info, values, *args, **kwargs):
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
        values.Foreach(visitor)
        for index, value in visitor.index_and_value:
            # print("=================this seems important")
            log_string = 'SOEHandler.Process {0}\theaderIndex={1}\tdata_type={2}\tindex={3}\tvalue={4}'
            _log.debug(log_string.format(info.gv, info.headerIndex, type(values).__name__, index, value))

        self._class_index_value = (visitor_class, visitor.index_and_value)
        self._class_index__value_dict[visitor_class] = visitor.index_and_value
        # print("==very import== class_index_value", self._class_index_value)
        # print("---------- import args, kwargs", *args, **kwargs) # nothing here
        print("---------- important info", info, type(info))
        print("---------- important dir(info)", info, dir(info))
        print('info.flagsValid', info.flagsValid, 'info.gv', info.gv,
              'info.headerIndex', info.headerIndex, 'info.isEventVariation', info.isEventVariation,
              'info.qualifier', info.qualifier, 'info.tsmode', info.tsmode,
              '_class_index_value: ', self._class_index_value)
        print("_class_index__value_dict", self._class_index__value_dict)

    def Start(self):
        _log.debug('In SOEHandler.Start')

    def End(self):
        _log.debug('In SOEHandler.End')


class MasterApplication(opendnp3.IMasterApplication):
    def __init__(self):
        super(MasterApplication, self).__init__()

        _log.debug('Configuring the DNP3 stack.')  # TODO: kefei added mimic outstation, wild guess
        self.stack_config = self.configure_stack()

        _log.debug('Configuring the outstation database.')
        # self.configure_database(self.stack_config.dbConfig)  # TODO: kefei added mimic outstation, wild guess

    @staticmethod
    def configure_stack():  # TODO: kefei added mimic outstation, wild guess
        """Set up the OpenDNP3 configuration."""
        # stack_config = asiodnp3.OutstationStackConfig(opendnp3.DatabaseSizes.AllTypes(10))
        # stack_config.outstation.eventBufferConfig = opendnp3.EventBufferConfig().AllTypes(10)
        # stack_config.outstation.params.allowUnsolicited = False
        stack_config = asiodnp3.MasterStackConfig()
        stack_config.link.LocalAddr = 2  # meaning for master station, use 2 to follow simulator's default
        stack_config.link.RemoteAddr = 1  # meaning for outstation, use 1 to follow simulator's default
        stack_config.master.disableUnsolOnStartup = True
        # stack_config.link.KeepAliveTimeout = openpal.TimeDuration().Max()
        return stack_config

    @staticmethod
    def configure_database(db_config):  # TODO: kefei added. TO mimic outstation--wild guess. And it worked.
        """
            Configure the Master station's database of input point definitions.

            # Configure two Analog points (group/variation 30.1) at indexes 1 and 2.
            Configure two Analog points (group/variation 30.1) at indexes 0, 1.
            Configure two Binary points (group/variation 1.2) at indexes 1 and 2.
        """
        # db_config.analog[0].clazz = opendnp3.PointClass.Class2
        # db_config.analog[0].svariation = opendnp3.StaticAnalogVariation.Group30Var1
        # db_config.analog[0].evariation = opendnp3.EventAnalogVariation.Group32Var7
        # db_config.analog[1].clazz = opendnp3.PointClass.Class2
        # db_config.analog[1].svariation = opendnp3.StaticAnalogVariation.Group30Var1
        # db_config.analog[1].evariation = opendnp3.EventAnalogVariation.Group32Var7
        # db_config.analog[2].clazz = opendnp3.PointClass.Class2
        # db_config.analog[2].svariation = opendnp3.StaticAnalogVariation.Group30Var1
        # db_config.analog[2].evariation = opendnp3.EventAnalogVariation.Group32Var7
        #
        # db_config.binary[0].clazz = opendnp3.PointClass.Class2
        # db_config.binary[0].svariation = opendnp3.StaticBinaryVariation.Group1Var2
        # db_config.binary[0].evariation = opendnp3.EventBinaryVariation.Group2Var2
        # db_config.binary[1].clazz = opendnp3.PointClass.Class2
        # db_config.binary[1].svariation = opendnp3.StaticBinaryVariation.Group1Var2
        # db_config.binary[1].evariation = opendnp3.EventBinaryVariation.Group2Var2
        # db_config.binary[2].clazz = opendnp3.PointClass.Class2
        # db_config.binary[2].svariation = opendnp3.StaticBinaryVariation.Group1Var2
        # db_config.binary[2].evariation = opendnp3.EventBinaryVariation.Group2Var2

        # Kefei's wild guess for analog output config
        db_config.aoStatus[0].clazz = opendnp3.PointClass.Class2
        db_config.aoStatus[0].svariation = opendnp3.StaticAnalogOutputStatusVariation.Group40Var1
        # db_config.aoStatus[0].evariation = opendnp3.StaticAnalogOutputStatusVariation.Group40Var1
        db_config.boStatus[0].clazz = opendnp3.PointClass.Class2
        db_config.boStatus[0].svariation = opendnp3.StaticBinaryOutputStatusVariation.Group10Var2
        # db_config.boStatus[0].evariation = opendnp3.StaticBinaryOutputStatusVariation.Group10Var2

    # Overridden method
    def AssignClassDuringStartup(self):
        _log.debug('In MasterApplication.AssignClassDuringStartup')
        return False

    # Overridden method
    def OnClose(self):
        _log.debug('In MasterApplication.OnClose')

    # Overridden method
    def OnOpen(self):
        _log.debug('In MasterApplication.OnOpen')

    # Overridden method
    def OnReceiveIIN(self, iin):
        _log.debug('In MasterApplication.OnReceiveIIN')

    # Overridden method
    def OnTaskComplete(self, info):
        _log.debug('In MasterApplication.OnTaskComplete')

    # Overridden method
    def OnTaskStart(self, type, id):
        _log.debug('In MasterApplication.OnTaskStart')


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


def main():
    """The Master has been started from the command line. Execute ad-hoc tests if desired."""
    # app = MyMaster()
    app = MyMaster(log_handler=MyLogger(),
                   listener=AppChannelListener(),
                   soe_handler=SOEHandler(),
                   master_application=MasterApplication())
    _log.debug('Initialization complete. In command loop.')
    # Ad-hoc tests can be performed at this point. See master_cmd.py for examples.
    app.shutdown()
    _log.debug('Exiting.')
    exit()


if __name__ == '__main__':
    main()
