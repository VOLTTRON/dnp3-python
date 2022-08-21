import logging
import sys

from pydnp3 import opendnp3, openpal, asiopal, asiodnp3
import time

from typing import Union

LOG_LEVELS = opendnp3.levels.NORMAL | opendnp3.levels.ALL_COMMS
LOCAL_IP = "0.0.0.0"
PORT = 20000
# PORT = 20001

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)
# _log.setLevel(logging.ERROR)  # TODO: encapsulate this


class MyOutStationNew(opendnp3.IOutstationApplication):
    """
            Interface for all outstation callback info except for control requests.

            DNP3 spec section 5.1.6.2:
                The Application Layer provides the following services for the DNP3 User Layer in an outstation:
                    - Notifies the DNP3 User Layer when action requests, such as control output,
                      analog output, freeze and file operations, arrive from a master.
                    - Requests data and information from the outstation that is wanted by a master
                      and formats the responses returned to a master.
                    - Assures that event data is successfully conveyed to a master (using
                      Application Layer confirmation).
                    - Sends notifications to the master when the outstation restarts, has queued events,
                      and requires time synchronization.

            DNP3 spec section 5.1.6.3:
                The Application Layer requires specific services from the layers beneath it.
                    - Partitioning of fragments into smaller portions for transport reliability.
                    - Knowledge of which device(s) were the source of received messages.
                    - Transmission of messages to specific devices or to all devices.
                    - Message integrity (i.e., error-free reception and transmission of messages).
                    - Knowledge of the time when messages arrive.
                    - Either precise times of transmission or the ability to set time values
                      into outgoing messages.
        """

    outstation = None

    def __init__(self,
                 masterstation_ip_str: str = "0.0.0.0",
                 outstation_ip_str: str = "127.0.0.1",
                 port: int = 20000,
                 masterstation_id_int: int = 2,
                 outstation_id_int: int = 1,
                 concurrencyHint: int = 1,
                 ):
        super().__init__()

        self.masterstation_id_int = masterstation_id_int
        self.outstation_id_int = outstation_id_int

        _log.debug('Configuring the DNP3 stack.')
        _log.debug('Configuring the outstation database.')
        self.stack_config = self.configure_stack()  # TODO: refactor it to outside of the class

        # TODO: Justify if this is is really working? (Not sure if it really takes effect yet.)
        #  but needs to add docstring. Search for "intriguing" in "data_retrieval_demo.py"
        # Note: dbconfig signature at cpp/libs/include/asiodnp3/DatabaseConfig.h
        # which has sizes parameter
        self.configure_database(self.stack_config.dbConfig)  # TODO: refactor it to outside of the class.
        # print("=====verify self.stack_config.dbConfig.analog[0].svariation",
        #       self.stack_config.dbConfig.analog[0].svariation)
        # self.stack_config.dbConfig.analog[0].svariation = opendnp3.StaticAnalogVariation.Group30Var5
        # print("=====verify again self.stack_config.dbConfig.analog[0].svariation",
        #       self.stack_config.dbConfig.analog[0].svariation)
        #
        # print("====self.stack_config.dbConfig.analog[0].svariation type", type(self.stack_config.dbConfig.analog[0].svariation ))
        #
        # # print("=======experiment", self.stack_config.dbConfig.binary.toView)
        # print("=======after self.stack_config", self.stack_config.dbConfig)
        # print("=======experiment", self.stack_config.dbConfig.sizes.numAnalog)


        # threads_to_allocate = 1
        # self.log_handler = MyLogger()
        self.log_handler = asiodnp3.ConsoleLogger().Create()  # (or use this during regression testing)
        # self.manager = asiodnp3.DNP3Manager(threads_to_allocate, self.log_handler)
        # print("====outstation self.log_handler = log_handler", self.log_handler)

        # init steps: DNP3Manager(manager) -> TCPClient(channel) -> Master(master)
        # init DNP3Manager(manager)
        _log.debug('Creating a DNP3Manager.')
        self.manager = asiodnp3.DNP3Manager(concurrencyHint, self.log_handler)  # TODO: play with concurrencyHint

        # init TCPClient(channel)
        _log.debug('Creating the DNP3 channel, a TCP server.')
        self.retry_parameters = asiopal.ChannelRetry().Default()
        self.listener = AppChannelListener()
        # self.listener = asiodnp3.PrintingChannelListener().Create()       # (or use this during regression testing)
        level = opendnp3.levels.NORMAL | opendnp3.levels.ALL_COMMS  # seems not working
        self.channel = self.manager.AddTCPServer(id="server",
                                                 levels=level,
                                                 retry=self.retry_parameters,
                                                 endpoint=outstation_ip_str,
                                                 port=port,
                                                 listener=self.listener)

        _log.debug('Adding the outstation to the channel.')
        self.command_handler = OutstationCommandHandler()
        # self.command_handler =  opendnp3.SuccessCommandHandler().Create() # (or use this during regression testing)
        # self.outstation_application = OutstationApplication()
        self.outstation_application = self
        self.outstation = self.channel.AddOutstation(id="outstation",
                                                     commandHandler=self.command_handler,
                                                     # application=self,
                                                     application=self.outstation_application,
                                                     config=self.stack_config)

        # Put the Outstation singleton in OutstationApplication so that it can be used to send updates to the Master.
        MyOutStationNew.set_outstation(self.outstation)  # TODO: change MyOutStationNew to cls

        _log.debug('Enabling the outstation. Traffic will now start to flow.')
        self.outstation.Enable()

        # TODO: the master and outstation init takes time (i.e., configuration). Hard-coded here
        time.sleep(3)  # TODO: justify the neccessity

        # TODO: add tcp/ip connection validation process, e.g., using socket. Python - Test the TCP port connectivity

        # print("===========self init __dict__", self.__dict__)
        # print("===========super init __dict__", super.__dict__)

    # @staticmethod
    def configure_stack(self):
        """Set up the OpenDNP3 configuration."""
        # stack_config = asiodnp3.OutstationStackConfig(opendnp3.DatabaseSizes.AllTypes(10))
        # stack_config = asiodnp3.OutstationStackConfig(opendnp3.DatabaseSizes.Empty())
        # stack_config = asiodnp3.OutstationStackConfig(dbSizes=opendnp3.DatabaseSizes.AnalogOnly(8))
        # TODO: expose DatabaseSizes to public interface
        stack_config = asiodnp3.OutstationStackConfig(dbSizes=opendnp3.DatabaseSizes(numBinary=10,
                                                                                     numDoubleBinary=0,
                                                                                     numAnalog=8,
                                                                                     numCounter=0,
                                                                                     numFrozenCounter=0,
                                                                                     numBinaryOutputStatus=0,
                                                                                     numAnalogOutputStatus=0,
                                                                                     numTimeAndInterval=0))

        stack_config.outstation.eventBufferConfig = opendnp3.EventBufferConfig().AllTypes(10)
        stack_config.outstation.params.allowUnsolicited = True  # TODO: create interface for this
        stack_config.link.LocalAddr = self.outstation_id_int  # meaning for outstation, use 1 to follow simulator's default
        stack_config.link.RemoteAddr = self.masterstation_id_int  # meaning for master station, use 2 to follow simulator's default
        stack_config.link.KeepAliveTimeout = openpal.TimeDuration().Max()
        return stack_config

    @staticmethod
    def configure_database(db_config):
        """
            Configure the Outstation's database of input point definitions.

            # Configure two Analog points (group/variation 30.1) at indexes 1 and 2.
            Configure two Analog points (group/variation 30.1) at indexes 0, 1.
            Configure two Binary points (group/variation 1.2) at indexes 1 and 2.
        """
        # TODO: figure out the right way to configure

        # AnalogInput
        db_config.analog[0].clazz = opendnp3.PointClass.Class2
        # db_config.analog[0].svariation = opendnp3.StaticAnalogVariation.Group30Var1
        db_config.analog[0].svariation = opendnp3.StaticAnalogVariation.Group30Var5  # note: experiment, Analog input - double-precision, floating-point with flag ref: https://docs.stepfunc.io/dnp3/0.9.0/dotnet/namespacednp3.html#aa326dc3592a41ae60222051044fb084f
        db_config.analog[0].evariation = opendnp3.EventAnalogVariation.Group32Var7
        db_config.analog[1].clazz = opendnp3.PointClass.Class2
        db_config.analog[1].svariation = opendnp3.StaticAnalogVariation.Group30Var1
        db_config.analog[1].evariation = opendnp3.EventAnalogVariation.Group32Var7
        # db_config.analog[2].clazz = opendnp3.PointClass.Class2
        # db_config.analog[2].svariation = opendnp3.StaticAnalogVariation.Group30Var1
        # db_config.analog[2].evariation = opendnp3.EventAnalogVariation.Group32Var7

        # BinaryInput
        db_config.binary[0].clazz = opendnp3.PointClass.Class2
        db_config.binary[0].svariation = opendnp3.StaticBinaryVariation.Group1Var2
        db_config.binary[0].evariation = opendnp3.EventBinaryVariation.Group2Var2
        db_config.binary[1].clazz = opendnp3.PointClass.Class2
        db_config.binary[1].svariation = opendnp3.StaticBinaryVariation.Group1Var2
        db_config.binary[1].evariation = opendnp3.EventBinaryVariation.Group2Var2
        db_config.binary[2].clazz = opendnp3.PointClass.Class2
        db_config.binary[2].svariation = opendnp3.StaticBinaryVariation.Group1Var2
        db_config.binary[2].evariation = opendnp3.EventBinaryVariation.Group2Var2

        # Kefei's wild guess for analog output config
        db_config.aoStatus[0].clazz = opendnp3.PointClass.Class2
        db_config.aoStatus[0].svariation = opendnp3.StaticAnalogOutputStatusVariation.Group40Var1
        # db_config.aoStatus[0].evariation = opendnp3.StaticAnalogOutputStatusVariation.Group40Var1
        db_config.boStatus[0].clazz = opendnp3.PointClass.Class2
        db_config.boStatus[0].svariation = opendnp3.StaticBinaryOutputStatusVariation.Group10Var2
        # db_config.boStatus[0].evariation = opendnp3.StaticBinaryOutputStatusVariation.Group10Var2

    def shutdown(self):
        """
            Execute an orderly shutdown of the Outstation.

            The debug messages may be helpful if errors occur during shutdown.
        """
        # TODO: cannot shut down: see Outstation and master hang on shutdown #1 at
        # https: // github.com / ChargePoint / pydnp3 / issues / 1

        _outstation = self.get_outstation()
        del _outstation
        del self.channel
        del self.log_handler
        del self.outstation_application
        del self.stack_config
        del self.command_handler
        del self.listener
        del self.retry_parameters
        # del self.manager

        self.manager.Shutdown()  # Process finished with exit code 134 (interrupted by signal 6: SIGABRT)
        # self.manager.__del__()  # Process finished with exit code 134 (interrupted by signal 6: SIGABRT)

    @classmethod  # TODO: Justify the necessity to use class method
    def get_outstation(cls):
        """Get the singleton instance of IOutstation."""
        return cls.outstation

    @classmethod
    def set_outstation(cls, outstn):
        """
            Set the singleton instance of IOutstation, as returned from the channel's AddOutstation call.

            Making IOutstation available as a singleton allows other classes (e.g. the command-line UI)
            to send commands to it -- see apply_update().
        """
        cls.outstation = outstn

    @classmethod
    def process_point_value(cls, command_type, command, index, op_type):
        """
            A PointValue was received from the Master. Process its payload.

        :param command_type: (string) Either 'Select' or 'Operate'.
        :param command: A ControlRelayOutputBlock or else a wrapped data value (AnalogOutputInt16, etc.).
        :param index: (integer) DNP3 index of the payload's data definition.
        :param op_type: An OperateType, or None if command_type == 'Select'.
        """
        # print("======I am evoked, right?")
        # print("command_type ", command_type)
        # print("command ", command)
        # print("command status ", command.status)
        #
        # print("command dir ", dir(command))
        # # print("command var ", vars(command))
        # # print("command rawCode ", command.rawCode) # TODO: this is working for binaryoutput 3 for ON, 4 for OFF
        # print("command value ", command.value)  # TODO: this is working for analogoutput
        # print("command __getattribute__ ", command.__getattribute__)
        # print("op_type ", op_type)
        _log.debug('Processing received point value for index {}: {}'.format(index, command))

        # TODO: need to update the XXXOutput points
        builder = asiodnp3.UpdateBuilder()
        # builder.Update(opendnp3.BinaryOutputStatus(True), index)  # TODO: half way there. this is how to update BinaryOutput
        builder.Update(opendnp3.AnalogOutputStatus(int(command.value)),
                       index)  # TODO: half way there. this is how to update AnalogOutput
        update = builder.Build()
        cls.get_outstation().Apply(update)

    @classmethod
    def apply_update(cls,
                     value: Union[opendnp3.Analog, opendnp3.Binary,
                                  opendnp3.AnalogOutputStatus, opendnp3.BinaryOutputStatus],
                     index):
        """
            Record an opendnp3 data value (Analog, Binary, etc.) in the outstation's database.

            The data value gets sent to the Master as a side-effect.

        :param value: An instance of Analog, Binary, or another opendnp3 data value.
        :param index: (integer) Index of the data definition in the opendnp3 database.
        """
        _log.debug('Recording {} measurement, index={}, '
                   'value={}, flag={}, time={}'
                   .format(type(value), index, value.value, value.flags.value, value.time.value))
        builder = asiodnp3.UpdateBuilder()
        builder.Update(value, index)
        update = builder.Build()
        cls.get_outstation().Apply(update)


# alias
PointValueType = Union[opendnp3.Analog, opendnp3.Binary, opendnp3.AnalogOutputStatus, opendnp3.BinaryOutputStatus]


class OutstationCommandHandler(opendnp3.ICommandHandler):
    """
        Override ICommandHandler in this manner to implement application-specific command handling.

        ICommandHandler implements the Outstation's handling of Select and Operate,
        which relay commands and data from the Master to the Outstation.
    """

    outstation_application = MyOutStationNew

    def Start(self):
        _log.debug('In OutstationCommandHandler.Start')

    def End(self):
        _log.debug('In OutstationCommandHandler.End')

    def Select(self, command, index):
        """
            The Master sent a Select command to the Outstation. Handle it.

        :param command: ControlRelayOutputBlock,
                        AnalogOutputInt16, AnalogOutputInt32, AnalogOutputFloat32, or AnalogOutputDouble64.
        :param index: int
        :return: CommandStatus
        """
        # print("===========command, ", command)
        # print("===========index, ", index)
        self.outstation_application.process_point_value('Select', command, index, None)
        return opendnp3.CommandStatus.SUCCESS

    def Operate(self, command, index, op_type):
        """
            The Master sent an Operate command to the Outstation. Handle it.

        :param command: ControlRelayOutputBlock,
                        AnalogOutputInt16, AnalogOutputInt32, AnalogOutputFloat32, or AnalogOutputDouble64.
        :param index: int
        :param op_type: OperateType
        :return: CommandStatus
        """
        # print("Operate===========command, ", command)
        # print("Operate===========index, ", index)
        # print("Operate===========op_type, ", op_type)
        self.outstation_application.process_point_value('Operate', command, index, op_type)
        return opendnp3.CommandStatus.SUCCESS


class AppChannelListener(asiodnp3.IChannelListener):
    """
        Override IChannelListener in this manner to implement application-specific channel behavior.
    """

    def __init__(self):
        super(AppChannelListener, self).__init__()

    def OnStateChange(self, state):
        _log.debug('In AppChannelListener.OnStateChange: state={}'.format(state))


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
