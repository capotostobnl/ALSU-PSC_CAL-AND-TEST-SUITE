# PSC Calibration and Verification Suite


## Overview

This software suite automates the calibration and verification procedures for Power Supply Controllers (PSC). It interfaces with laboratory test equipment (HP3458A DMM) and the Device Under Test (DUT) via EPICS to characterize performance, calculate correction factors (Gain/Offset), and generate certification reports.

## Key Features

* **Automated Measurements:** Controls high-precision DMMs to measure current/voltage with sub-millivolt accuracy.
* **Iterative Nulling:** Uses a software feedback loop to nullify DAC setpoint errors before calibration.
* **Correction Calculation:** Automatically computes `m` (Slope/Gain) and `b` (Intercept/Offset) for:
    * DAC Setpoint (`dacSP`)
    * DCCT Readbacks (`dcct1`, `dcct2`)
    * DAC Readback (`dacRB`)
* **Hardware Flashing:** Uploads calculated calibration constants directly to the PSC's QSPI memory.
* **PDF Reporting:** Generates detailed, multi-page calibration certificates with statistical analysis.

## Hardware Requirements

* **Host Machine:** PC/Linux Box with Python 3.11+ and network access to the test subnet.
* **DMM:** HP3458A (GPIB/Ethernet controlled).
* **Interface:** Automated Test Equipment (ATE) Adapter board.
* **DUT:** Power Supply Controller (PSC) with EPICS IOC running.

## Project Structure

The project has been refactored into a modular architecture to separate business logic from hardware operations:

```text
.
├── cal_main.py              # Entry point: Orchestrates the calibration sequence
├── cal_analysis.py          # Pure math & data structures
├── calibration_utils.py     # Hardware operations (Loops, Config, Measurements)
├── calibration_logger.py    # Output handling (Console printing & PDF logging)
├── cal_report_generator.py  # PDF generation logic
├── initialize_dut.py        # DUT discovery and connection
├── ate_init.py              # ATE board initialization
├── psc_models.py            # Configuration models for different PSC types
├── EPICS_Adapters/          # EPICS communication wrappers
│   ├── ate_epics.py
│   └── psc_epics.py
├── Instruments/             # Lab equipment drivers
│   ├── hp_3458a.py
│   └── keithley_2401.py
├── cal_reports/             # Output directory for PDF reports
└── requirements.txt         # Python dependencies