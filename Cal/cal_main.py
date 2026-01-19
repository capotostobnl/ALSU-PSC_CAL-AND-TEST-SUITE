"""
PSC Calibration and Verification Script
=======================================

Orchestrates the calibration process by coordinating hardware interactions,
analysis, and reporting.
"""
from __future__ import annotations
import os
from time import sleep
from typing import TYPE_CHECKING

import numpy as np

# pylint: disable=wrong-import-position
# flake8: noqa: E402
###############################################################################
#   Add outer directory to path, so app can find Common dir when run standalone
if __name__ == "__main__":
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
###############################################################################

from Common.initialize_dut import DUT
from Common.EPICS_Adapters.ate_epics import ATE
from Common.psc_models import get_psc_model_from_user
from Cal.ate_init import ate_init
from Cal.Instruments.hp_3458a import HP3458A
from Cal.cal_report_generator import CalibrationReport

# --- Local Module Imports ---
from Cal.calibration_logger import (
    logger,
    log_run_header,
    log_testpoint_data,
    log_gains_offsets,
    log_statistics
)
from Cal.cal_analysis import compute_m_b
from Cal.calibration_utils import (
    configure_channel_settings,
    measure_testpoints,
    DMM_HIGH_RANGE_THRESHOLD
)


if TYPE_CHECKING:
    from Common.psc_models import PSCModel


def calibrate_channel(
    dut: DUT,
    ate: ATE,
    dmm: HP3458A,
    config: PSCModel,
    report: CalibrationReport,
    chan: int
) -> None:
    """Executes the full calibration for a single channel."""

    params = config.calibration_parameters

    # 1. Reset Hardware for Test
    for chan_dex in range(1, dut.num_channels + 1):
        dut.psc.set_power_on1(chan_dex, 0)
        ate.set_mode(chan_dex, 'TEST')
        ate.set_cal_dac(0)
        sleep(1)

    # 2. Capture Environment
    dmm_offs = float(dmm.read_value())
    print(f"DMM zero offset: {dmm_offs:.7f}")
    ate.set_mode(chan, 'CAL')
    sleep(1)

    # 3. Calculate Limits
    current_fs = config.calc.get_current_full_scale(chan)
    burden = params.burden_resistors.get(chan - 1)
    p_scale = config.calc.get_p_scale_factor(chan)

    zero_sp = -1.0 / params.ndcct
    sp0 = params.sp0
    span_sp = -(float(round(current_fs * 0.9 * 1000) / 1000))
    sp1 = float(round(10 * p_scale * 0.9))

    # Use the constant imported from calibration_utils
    if abs(span_sp) > DMM_HIGH_RANGE_THRESHOLD:
        dmm.set_range(1.0)
    else:
        dmm.set_range(0.1)

    configure_channel_settings(dut, config, chan)
    print(f"{dut.pv_prefix}:Chan{chan} (Burden: {burden:.4f})")

    # 4. Calibration Loop
    results = np.zeros((params.num_runs, 8))

    for run in range(params.num_runs):
        is_last = run == params.num_runs - 1
        print(f"\nRun #: {run + 1}")
        dut.psc.reset_gains_offsets(chan)
        log_run_header(chan, burden, report)

        # --- Measure Low ---
        y_low = measure_testpoints(
            ate, dmm, dut.psc, config,
            zero_sp, sp0, chan, dmm_offs
        )
        if is_last:
            log_testpoint_data(y_low, header=True)

        # --- Measure High ---
        y_high = measure_testpoints(
            ate, dmm, dut.psc, config,
            span_sp, sp1, chan, dmm_offs
        )
        if is_last:
            log_testpoint_data(y_high, header=False)

        # --- Compute & Apply ---
        corrections = compute_m_b(y_low, y_high)
        # Explicit unpacking for clarity and correct ordering
        mdac, m1, m2, m3, bdac, b1, b2, _ = corrections

        if is_last:
            log_gains_offsets(bdac, b1, b2, mdac, m1, m2, m3)

        sleep(2)
        dut.psc.set_gain_dcct1(chan, 1 / m1)
        dut.psc.set_gain_dcct2(chan, 1 / m2)
        dut.psc.set_gain_dac_setpoint(chan, mdac)
        dut.psc.set_offset_dcct1(chan, b1)
        dut.psc.set_offset_dcct2(chan, b2)
        dut.psc.set_offset_dac_setpoint(chan, bdac)

        # --- Verification (DAC Readback) ---
        print("\nVerifying DAC Readback...")
        dut.psc.set_dac_setpt(chan, sp0)
        sleep(1)
        y_low.dac_readback = dut.psc.get_dac(chan)

        dut.psc.set_dac_setpt(chan, sp1)
        sleep(1)
        y_high.dac_readback = dut.psc.get_dac(chan)

        # Recalculate DAC Readback Gain/Offset
        m3_new = (y_high.dac_readback - y_low.dac_readback) / (sp1 - sp0)
        b3_new = y_low.dac_readback - (m3_new * sp0)

        # Write DAC Readback corrections
        dut.psc.set_gain_dac_setpoint(chan, 1 / m3_new)
        dut.psc.set_offset_dac_setpoint(chan, b3_new)

        # Store results (using original m3/b3 for report stats)
        results[run, :] = corrections

    # 5. Finalize
    log_statistics(results)
    print(f"Saving channel {chan} to QSPI...")
    report.write_line(f"Saving channel {chan} calibration constants to qspi")
    dut.psc.write_qspi(chan)

    report.draw_footer(current_page=chan, total_pages=dut.num_channels)
    if chan < dut.num_channels:
        report.next_page()


def run_calibration_suite(
        dut_instance = None,
        config_instance = None
        ) -> None:
    """Entry point for the calibration script.
    
    Args:
        dut_instance: A pre-configured DUT object. If None, prompts user.
        config_instance: A pre-configured PSCModel object. If None, prompts user.
    """

    # Init Hardware
    dmm = HP3458A()
    dmm.dmm_init()

    if dut_instance is None:
        # STANDALONE: Create and prompt
        dut = DUT()
        dut.prompt_inputs()
        dut.init()
    else:
        # LAUNCHER: Use provided object
        dut = dut_instance
        # Ensure connection is active (safe to call multiple times if idempotent)
        dut.init()

    if config_instance is None:
        # STANDALONE: Prompt
        config = get_psc_model_from_user(dut.num_channels)
    else:
        # LAUNCHER: Use provided
        config = config_instance

    ate = ATE(prefix="PSCtest:", ch_fmt="CH{ch}:")
    ate_init(ate, dut)

    # Init Report
    pdf_filename = (f"Calibration_{config.designation}SN{dut.psc_sn}"
                    f"_{dut.dir_timestamp}.pdf")
    pdf_path = os.path.join(dut.cal_report_dir, pdf_filename)

    report = CalibrationReport(
        filename=pdf_path,
        psc_designation=config.designation,
        serial_number=dut.psc_sn
    )
    logger.set_report(report)
    report.write_header()

    try:
        for chan in range(1, dut.num_channels + 1):
            calibrate_channel(dut, ate, dmm, config, report, chan)
    finally:
        report.save()
        print("Calibration Sequence Complete.")


if __name__ == "__main__":
    run_calibration_suite(dut_instance=None, config_instance=None)
