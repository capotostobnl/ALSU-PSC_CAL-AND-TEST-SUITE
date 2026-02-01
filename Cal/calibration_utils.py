"""
Calibration Utilities Module
============================

Handles low-level hardware interactions, configuration, and measurement loops.
"""
from __future__ import annotations
from time import sleep
from typing import TYPE_CHECKING

# IMPORTS: Get the data structure from the analysis module

from Cal.cal_analysis import TestPoint

if TYPE_CHECKING:
    from Common.initialize_dut import DUT
    from Common.EPICS_Adapters.psc_epics import PSC
    from Common.EPICS_Adapters.ate_epics import ATE
    from Common.psc_models import PSCModel
    from Instruments.hp_3458a import HP3458A

# --- Constants (Defined here where they are actually used) ---
MAX_DAC_ITERATIONS = 12
DAC_ADJUST_DIVISOR = 400.0
SETTLING_TIME_SEC = 2.0
DMM_HIGH_RANGE_THRESHOLD = 0.11


def configure_channel_settings(
    dut: DUT,
    chan: int
) -> None:
    """Applies all scale factors and thresholds to the PSC."""

    scales = dut.model.psc_scale_factors
    faults = dut.model.psc_fault_thresholds_limits

    p_scale = dut.model.calc.get_p_scale_factor(chan)
    dcct_val = (scales.sf_dcct_scale
                if scales.sf_dcct_scale else p_scale)

    dut.psc.set_sf_dcct_scale(chan, dcct_val)
    dut.psc.set_sf_ramp_rate(chan, scales.sf_ramp_rate)
    dut.psc.set_sf_ignd(chan, scales.sf_ignd)
    dut.psc.set_sf_regulator(chan, scales.sf_regulator)
    dut.psc.set_sf_error(chan, scales.sf_error)
    dut.psc.set_sf_vout(chan, scales.sf_vout.get(chan - 1))
    dut.psc.set_sf_spare(chan, scales.sf_spare.get(chan - 1))

    # Apply Thresholds
    dut.psc.set_threshold_err1(chan, faults.err1_threshold)
    dut.psc.set_threshold_err2(chan, faults.err2_threshold)
    dut.psc.set_threshold_ignd(chan, faults.ignd_threshold)

    # Fault Limits
    fault_limits = {
        "ovc1_flt_cnt": "set_count_limit_ovc1",
        "ovc2_flt_cnt": "set_count_limit_ovc2",
        "ovv_flt_cnt": "set_count_limit_ovv",
        "err1_flt_cnt": "set_count_limit_err1",
        "err2_flt_cnt": "set_count_limit_err2",
        "ignd_flt_cnt": "set_count_limit_ignd",
        "dcct_flt_cnt": "set_count_limit_dcct",
        "flt1_flt_cnt": "set_count_limit_flt1",
        "flt2_flt_cnt": "set_count_limit_flt2",
        "flt3_flt_cnt": "set_count_limit_flt3",
        "flt_on_cnt": "set_count_limit_on",
        "flt_heartbeat_cnt": "set_count_limit_heartbeat"
    }
    for attr, method in fault_limits.items():
        val = getattr(faults, attr)
        getattr(dut.psc, method)(chan, val)

    dut.psc.set_op_mode(chan, 3)
    dut.psc.set_averaging(chan, 1)


def measure_testpoints(
    ate_obj: ATE,
    dmm_obj: HP3458A,
    psc_hw: PSC,
    psc_config: PSCModel,
    current: float,
    sp: float,
    chan: int,
    dmm_offset: float,
    verbose: bool = False,
    verification: bool = False
) -> TestPoint:
    """
    Performs a single test point measurement with iterative DAC adjustment.
    """
    for _ in range(5):
        ate_obj.set_cal_dac_w_os(current)
        sleep(0.5)

    full_scale = psc_config.calc.get_current_full_scale(chan)
    p_scale = psc_config.calc.get_p_scale_factor(chan)
    s_scale = psc_config.calc.get_s_scale_factor(chan)

    iteration = 0
    psc_hw.set_dac_setpt(chan, sp)
    sleep(SETTLING_TIME_SEC)

    err = psc_hw.get_error_i(chan)
    dac = 0

    # Iterative Nulling Loop
    while ((abs(err) > full_scale * 2 and iteration < MAX_DAC_ITERATIONS)
           or iteration == 0):
        if verbose:
            print(f"adjustment {iteration}")

        dac = sp - (err / DAC_ADJUST_DIVISOR) * p_scale
        sp = dac
        psc_hw.set_dac_setpt(chan, sp)
        sleep(SETTLING_TIME_SEC)
        err = psc_hw.get_error_i(chan)

        iteration += 1
    
    if iteration == MAX_DAC_ITERATIONS+1:
        print("Calibration failed. Could not null error after "
              f"{MAX_DAC_ITERATIONS} attempts. Try again.")
        #sys.exit()

    rb = psc_config.calibration_parameters.burden_resistors.get(chan - 1)
    dmm_val = dmm_obj.read_value() - dmm_offset
    ndcct = psc_config.calibration_parameters.ndcct

    itest = dmm_val * ndcct
    
    return TestPoint(
        dmm_current=itest,
        dac_setpoint=dac,
        dcct1=psc_hw.get_dcct1(chan),
        dcct2=psc_hw.get_dcct2(chan),
        dac_readback=psc_hw.get_dac(chan),
        error=err
    )
