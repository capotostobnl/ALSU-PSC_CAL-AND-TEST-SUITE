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
ALSU-PSC_CAL-AND-TEST-SUITE/
├── Launcher.py             # Main entry point for the application
├── Cal/                    # Calibration-specific logic and instruments
│   ├── cal_main.py         # Primary calibration orchestration
│   └── Instruments/        # Driver support for DMMs (HP 3458A)
│     ├── hp_3458a.py                  #  Driver for HP 3458A DMM
│     └── keithley_2401.py             #  Driver for Keithley 2401 SMU (No longer used in current procedure)
├── Common/                 # Shared utilities and hardware adapters
│   ├── initialize_dut.py   # DUT class (Session management & Path anchoring)
│   ├── psc_models.py       # Registry of PSC hardware specifications
│   └── EPICS_Adapters/     # Low-level EPICS communication layers
      ├── ate_epics.py                 # Driver: Robust adapter for ATE Tester IOC
      └── psc_epics.py                 # Driver: Adapter for PSC IOC (waveforms, setpoints)
├── Test/                   # Functional verification suite
│   ├── main.py             # Primary test orchestration
│   └── Functional_Tests/   # Specific test modules (Regulation, Ramp, etc.)
│     ├── ate_fault_tests.py           # Hardware Interlock Validation (FLT1/2/Spare/DCCT)
│     ├── evr_timing_test.py           # EVR 1Hz Timestamp monotonicity check
│     ├── fofb_test.py                 # FOFB Integration: UDP packet capture & HDF5 logging
│     ├── jump_test.py                 # Transient Response Analysis (Step response, Settling)
│     ├── ps_regulation_test.py        # DAC Loopback & Regulation verification
│     ├── smooth_ramp_test.py          # Ramp Tracking & Stability Analysis
│     ├── caen_fast_genpacket.c        # Low-level UDP packet generator (C source)
│     └── caen_fast_genpacket_loop_inf.sh  # Shell script wrapper for continuous packet generation
└── Test_And_Cal_Data/      # Unified data repository
    ├── Cal_Reports/        # Auto-generated calibration PDFs
    ├── Test_Reports/       # Auto-generated functional test PDFs
    └── Raw_Logs/           # Diagnostic raw data indexed by Shipment ID