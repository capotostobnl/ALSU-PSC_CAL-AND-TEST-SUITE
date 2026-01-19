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
    from Common.psc_models import PSCConfig


def calibrate_channel(
    dut: DUT,
    ate: ATE,
    dmm: HP3458A,
    config: PSCConfig,
    report: CalibrationReport,
    chan: int
) -> None:
    """Executes the full calibration for a single channel."""

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
    current_fs = config.get_current_full_scale(chan)
    burden = getattr(config.burden_resistors, f"ch{chan}")
    p_scale = config.get_p_scale_factor(chan)

    zero_sp = -1.0 / config.ndcct
    sp0 = config.sp0
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
    results = np.zeros((config.num_runs, 8))

    for run in range(config.num_runs):
        is_last = run == config.num_runs - 1
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


def main() -> None:
    """Entry point for the calibration script."""
    # Init Hardware
    dmm = HP3458A()
    dmm.dmm_init()

    dut = DUT()
    dut.prompt_inputs()
    dut.init()

    ate = ATE(prefix="PSCtest:", ch_fmt="CH{ch}:")
    ate_init(ate, dut)

    config = get_psc_model_from_user(dut.num_channels)

    # Init Report
    pdf_filename = f"Calibration_{config.designation}SN{dut.psc_sn}.pdf"
    pdf_path = os.path.join(dut.report_dir, pdf_filename)

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
    main()
