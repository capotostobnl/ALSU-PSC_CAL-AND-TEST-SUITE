"""
Calibration Analysis Module
===========================

Contains pure mathematical logic and data structures for the calibration
process. This module is decoupled from hardware to allow for easy unit testing.
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class TestPoint:
    """
    Mutable structure to hold measurement data for a single setpoint.
    """
    dmm_current: float
    dac_setpoint: float
    dcct1: float
    dcct2: float
    dac_readback: float
    error: float


def compute_m_b(low: TestPoint, high: TestPoint) -> Tuple[float, ...]:
    """
    Calculates slope (m) and intercept (b) for:
    DAC_SP (idx 1), DCCT1 (idx 2), DCCT2 (idx 3), DAC_RB (idx 4)

    Args:
        low: TestPoint object for the zero/low measurement.
        high: TestPoint object for the span/high measurement.

    Returns:
        Tuple containing (mdac, m1, m2, m3, bdac, b1, b2, b3)
    """
    # Calculate Deltas
    delta_i = high.dmm_current - low.dmm_current
    delta_dac = high.dac_setpoint - low.dac_setpoint

    # Slopes (Rise over Run)
    m1 = (high.dcct1 - low.dcct1) / delta_i
    m2 = (high.dcct2 - low.dcct2) / delta_i
    m3 = (high.dac_readback - low.dac_readback) / delta_dac
    mdac = delta_dac / delta_i

    # Intercepts (b = y - mx)
    b1 = low.dcct1 - (m1 * low.dmm_current)
    b2 = low.dcct2 - (m2 * low.dmm_current)
    b3 = low.dac_readback - (m3 * low.dac_setpoint)
    bdac = low.dac_setpoint - (mdac * low.dmm_current)

    return -mdac, m1, m2, m3, -bdac, b1, b2, b3
