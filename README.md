# ALSU-PSC Calibration and Functional Test Suite

A comprehensive software suite for the automated calibration and functional verification of Power Supply Controllers (PSC) used in High Energy Physics research.

## 🚀 Project Overview
This application provides a unified interface to calibrate and test PSC units. It utilizes EPICS (Experimental Physics and Industrial Control System) to interface with hardware, captures high-precision measurements via HP 3458A DMMs, and generates comprehensive PDF reports for data auditing.

### Key Features
* **Unified Launcher:** Single entry point for selecting execution modes (Calibration, Functional Testing, or both).
* **Hardware Discovery:** Automatically queries PSC EEPROM settings (channels, resolution, bandwidth) to prevent configuration errors.
* **Smart Directory Management:** Anchors all data to the project root and uses lazy initialization to create report folders only when required.
* **Single Source of Truth:** Centralized PSC model definitions (`psc_models.py`) ensure consistent math and limits across both calibration and testing.

---

## 📂 Directory Structure

```text
ALSU-PSC_CAL-AND-TEST-SUITE/
├── Launcher.py             # Main entry point for the application
├── Cal/                    # Calibration-specific logic and instruments
│   ├── cal_main.py         # Primary calibration orchestration
│   └── Instruments/        # Driver support for DMMs (HP 3458A)
├── Common/                 # Shared utilities and hardware adapters
│   ├── initialize_dut.py   # DUT class (Session management & Path 
│                             anchoring)
│   ├── psc_models.py       # Registry of PSC hardware specifications
│   └── EPICS_Adapters/     # Low-level EPICS communication layers
├── Test/                   # Functional verification suite
│   ├── main.py             # Primary test orchestration
│   └── Functional_Tests/   # Specific test modules (Regulation, Ramp, etc.)
└── Test_And_Cal_Data/      # Unified data repository
    ├── Cal_Reports/        # Auto-generated calibration PDFs
    ├── Test_Reports/       # Auto-generated functional test PDFs
    └── Raw_Logs/           # Diagnostic raw data indexed by Shipment ID
```

##  Setup and Installation

### Prerequisites
* **Python 3.11+**.

* **EPICS IOCs for ATE and PSC must be running**.

* **Dependencies**: Install required packages via pip:
    ```bash
    pip install -r Common/requirements.txt
    ```

### Path Anchoring
The application is designed to be portable. It dynamically resolves the project root using `os.path.abspath(__file__)` within the `Common/initialize_dut.py` module. You can move the entire project folder to any location on the system without breaking file paths.

---

##  Usage

### 1. Launching the Suite
Run the main launcher from the project root:
```bash
python Launcher.py
```

### 2. Execution Modes
* **Calibrate Only**: Executes high-precision DAC/ADC calibration.
* **Test Only**: Runs functional verification including Ramps, Steps, and Stability.
* **Calibrate and Test**: Performs full end-to-end verification.

### 3. Data Output
* Reports are saved to `Test_And_Cal_Data/`.
* The system uses the following naming convention for files:
  `Calibration_[Model]_SN[Serial]_[Timestamp].pdf`

##  Architecture Notes

### The DUT (Device Under Test) Object
The `DUT` class in `Common/initialize_dut.py` serves as the shared session manager. It handles:
* **Lazy Properties**: `cal_report_dir` and `test_report_dir` use Python `@property` decorators to ensure folders are only created on your hard drive when a report is actually generated.
* **Session Persistence**: Operator inputs such as Serial Number and Shipment ID are captured once and shared across all sub-modules.



### Calibration Logic
Calibration constants are computed using linear analysis ($y = mx + b$) based on high-precision DMM measurements and applied directly to the PSC internal registers via EPICS.