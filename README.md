# ALSU-PSC Calibration and Functional Test Suite

A comprehensive software suite for the automated calibration and functional verification of Power Supply Controllers (PSC).

> **CRITICAL WARNING:** > At the present commit, the new calibration script located in the `/Cal` directory is non-functional and **NOT ready for release**. Please continue using David Bergman's calibration script. All files in the `/Cal` directory are NOT ready for release.

## Project Overview

This application provides a unified interface to calibrate and test PSC units. It utilizes EPICS (Experimental Physics and Industrial Control System) to interface with hardware, captures high-precision measurements via HP 3458A DMMs, and generates comprehensive PDF reports.

### Key Features
* **Unified Launcher:** A single entry point for selecting execution modes (Calibration, Functional Testing, or both).
* **Hardware Discovery:** Automatically queries PSC EEPROM settings (channels, resolution, bandwidth) to prevent configuration errors.
* **Intelligent Directory Management:** Anchors all data to the project root and dynamically creates reporting folders only when required.

---

## Setup and Installation

### 1. Prerequisites
* **Python:** Version 3.11 or higher.
* **EPICS:** The EPICS IOCs for both the ATE and the PSC **must** be actively running on the network.

### 2. Dependencies
Install the required Python packages via pip:
```bash
pip install -r Common/requirements.txt
```

### 3. FOFB SFP Testing Compilation
If you are testing the Fast PSC's FOFB SFPs, you must compile the `caen_fast_genpacket.c` application in place. This executable binary is called by the shell script wrapper, which is subsequently called by the `fofb_test.py` module.

---

## Usage

### 1. Hardware Initialization
Before launching the software, verify the physical test stand setup:
* Connect the DCCT Cable and the Channel 1/2/3/4 BPC cables to the ATE.
* Verify the SD card is installed, properly configured with the correct IP Address, and that the EEPROM has been initialized via the front USB port.
* Ensure the correct tuning boards are populated in the ATE.

### 2. Launching the Suite
Run the main launcher from the project root. (The application is fully portable and dynamically resolves file paths using `os.path.abspath(__file__)`, so it can be run from any directory location).
```bash
python Launcher.py
```

### 3. Execution Modes
Upon launching, you will be prompted to select a mode:
* **Calibrate Only:** Executes high-precision DAC/ADC calibration. *(Currently disabled/under development)*
* **Test Only:** Runs functional verification, including Ramp Tracking, Step Response, and Stability tests.
* **Calibrate and Test:** Performs full end-to-end verification.

### 4. Data Output
Generated reports and logs are saved directly to `Test_And_Cal_Data/`. The system utilizes the following naming convention for PDF reports:
`Calibration_[Model]_SN[Serial]_[Timestamp].pdf`

---

## Architecture Notes

### The DUT (Device Under Test) Object
Located in `Common/initialize_dut.py`, the `DUT` class acts as the centralized session manager and state handler for the entire application. 
* **Session Persistence:** Operator inputs (such as Serial Number and Shipment ID) are captured once upon instantiation and shared across all active sub-modules.
* **Dynamic Pathing:** It utilizes Python `@property` decorators for attributes like `cal_report_dir` and `test_report_dir`. This "lazy instantiation" ensures that empty directories are not created unless a test actually runs and generates a report.

### Shared Infrastructure (`/Common`)
The `/Common` directory houses the foundational modules and configurations required by both the testing and calibration routines:
* **`initialize_dut.py`:** Instantiates the core `DUT` object.
* **`psc_models.py`:** A data class serving as a registry of PSC hardware specifications and tolerances.
* **`direct_ate.py`:** A module currently under development, initially designed to support legacy calibration hardware interactions.

### EPICS Communication Layer
All EPICS communication is abstracted into wrappers located in `/Common/EPICS_Adapters/`:
* **`ate_epics.py`:** A driver dedicated to interacting with the ATE Tester IOC.
* **`psc_epics.py`:** A driver dedicated to interacting with the PSC IOC

### Calibration Logic
When functional, the calibration routine computes correction constants using linear analysis ($y = mx + b$). These constants are derived from high-precision DMM measurements and are written directly to the PSC's internal registers via the EPICS adapter layer.

---

## Directory Structure

```text
ALSU-PSC_CAL-AND-TEST-SUITE/
├── Launcher.py             # Main entry point for the application
├── Cal/                    # Calibration-specific logic and instruments (IN DEV)
│   ├── cal_main.py         # Primary calibration orchestration
│   └── Instruments/        # Driver support for DMMs
│     ├── hp_3458a.py       # Driver for HP 3458A DMM
│     └── keithley_2401.py  # Driver for Keithley 2401 SMU (Deprecated)
├── Common/                 # Shared utilities and hardware adapters
│   ├── initialize_dut.py   # DUT class (Session management & Path anchoring)
│   ├── psc_models.py       # Registry of PSC hardware specifications
│   ├── direct_ate.py       # Legacy calibration support (IN DEV)
│   └── EPICS_Adapters/     # Low-level EPICS communication layers
│     ├── ate_epics.py      # Driver: Adapter for ATE Tester IOC
│     └── psc_epics.py      # Driver: Adapter for PSC IOC 
├── Test/                   # Functional verification suite
│   ├── main.py             # Primary test orchestration
│   └── Functional_Tests/   # Specific test modules
│     ├── ate_fault_tests.py              # Hardware Interlock Validation
│     ├── evr_timing_test.py              # EVR 1Hz Timestamp monotonicity check
│     ├── fofb_test.py                    # FOFB Integration (UDP capture & HDF5)
│     ├── jump_test.py                    # Transient Response Analysis
│     ├── ps_regulation_test.py           # DAC Loopback & Regulation verification
│     ├── smooth_ramp_test.py             # Ramp Tracking & Stability Analysis
│     ├── caen_fast_genpacket.c           # Low-level UDP packet generator (C)
│     └── caen_fast_genpacket_loop_inf.sh # Shell wrapper for packet generation
└── Test_And_Cal_Data/      # Unified data repository
    ├── Cal_Reports/        # Auto-generated calibration PDFs
    ├── Test_Reports/       # Auto-generated functional test PDFs
    └── Raw_Logs/           # Diagnostic raw data indexed by Shipment ID
```

*For more specific technical information regarding the calibration or functional testing logic, please refer to the individual `README.md` files located within the `/Test` and `/Cal` directories.*