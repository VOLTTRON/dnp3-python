import datetime
import logging
import sys
import time

from pydnp3 import opendnp3, openpal, asiopal, asiodnp3
from .visitors import *
from pydnp3.opendnp3 import GroupVariation, GroupVariationID

from typing import Callable, Union, Dict, Tuple, List, Optional, Type, TypeVar

from .master_utils import MasterCmdType

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)
# _log.setLevel(logging.INFO)

# alias
OutstationCmdType = Union[opendnp3.Analog, opendnp3.Binary, opendnp3.AnalogOutputStatus,
                          opendnp3.BinaryOutputStatus]  # based on asiodnp3.UpdateBuilder.Update(**args)
# MasterCmdType = Union[opendnp3.AnalogOutputDouble64,
#                       opendnp3.AnalogOutputFloat32,
#                       opendnp3.AnalogOutputInt32,
#                       opendnp3.AnalogOutputInt16,
#                       opendnp3.ControlRelayOutputBlock]
MeasurementType = TypeVar("MeasurementType", bound=opendnp3.Measurement)  # inheritance, e.g., opendnp3.Analog,

# TODO: combine outstation util with master_utils

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
