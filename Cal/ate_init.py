"""ATE Initializtion Submodule
Modified M. Capotosto 1-19-2026
"""

from time import sleep
from Common.initialize_dut import DUT
from Common.EPICS_Adapters.ate_epics import ATE


def ate_init(ate: ATE, dut: DUT) -> None:
    """Initialize ATE"""
    assert dut.psc is not None
    assert ate is not None
    sleep(0)
