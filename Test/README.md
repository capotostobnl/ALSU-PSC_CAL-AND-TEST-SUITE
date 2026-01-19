# **PSC Automated Test Environment (ATE) – Test Suite**

This repository contains the full automated test environment (ATE) and reporting framework for **ALSu Power Supply Controller (PSC)** validation.  
It performs end-to-end testing of PSC hardware, ATE interfaces, EVR timing, DCCT/IGND/SPARE regulation, FOFB behavior, and produces a formatted PDF report for shipment documentation.

The system integrates:

- **PSC EPICS IOC communication** (`EPICS_Adapters/psc_epics.py`)
- **ATE Tester IOC communication** (`EPICS_Adapters/ate_epics.py`)
- Automated test modules (jump, smooth ramp, regulation, EVR timing, FOFB)
- Auto-generated reports with plots and pass/fail tables
- Automated directory management and shipment logging

---

## **Repository Structure**

```
├── main.py                          # Top-level test runner (Entry Point)
├── initialize_dut.py                # DUT Config: Serial numbers, PV prefixes, directory logic
├── report_generator.py              # ReportLab PDF engine, context managers, and styling
├── psc_models.py                    # Data models representing PSC states/signals
│
├── EPICS_Adapters/                  # Drivers for Hardware Communication
│   ├── ate_epics.py                 # Driver: Robust adapter for ATE Tester IOC
│   └── psc_epics.py                 # Driver: Adapter for PSC IOC (waveforms, setpoints)
│
├── Functional_Tests/                # Individual Test Modules
│   ├── ate_fault_tests.py           # Hardware Interlock Validation (FLT1/2/Spare/DCCT)
│   ├── evr_timing_test.py           # EVR 1Hz Timestamp monotonicity check
│   ├── fofb_test.py                 # FOFB Integration: UDP packet capture & HDF5 logging
│   ├── jump_test.py                 # Transient Response Analysis (Step response, Settling)
│   ├── ps_regulation_test.py        # DAC Loopback & Regulation verification
│   ├── smooth_ramp_test.py          # Ramp Tracking & Stability Analysis
│   ├── caen_fast_genpacket.c        # Low-level UDP packet generator (C source)
│   └── caen_fast_genpacket_loop_inf.sh  # Shell script wrapper for continuous packet generation
│
├── ate_init.py                      # Initialization sequence (Safety defaults, Gain setup)
├── requirements.txt                 # Python dependencies
└── README.md                        # Project documentation
```

---

## **Overview of the Test Flow**

The main entry point is:

```
python3 main.py
```

The test sequence inside `main.py`:

1. **DUT Initialization**
   - User enters serial number, shipment number, operator, etc.
   - Creates a new `Shipment #XX/` directory
   - Creates raw data and PDF report folders

2. **ATE & PSC Initialization (`ate_init.py`)**
   - Clears faults and resets PSC
   - Configures IGND routing and DCCT channels
   - Configures gains, polarity, and calibration state

3. **Tests Executed**
   - **EVR Timing Test**
   - **ATE Fault Tests**  
     - FLT1, FLT2, SPARE, and DCCT fault injection
   - **PSC Regulation Test**
   - **Jump Test**
   - **Smooth Ramp Test**
   - **FOFB Packet Test** *(fast-bandwidth PSC only)*

4. **PDF Report Generation**
   - Plots of all waveforms  
   - Pass/Fail tables  
   - EVR timestamp plot  
   - FOFB results (if applicable)  
   - Auto-naming based on DUT info  

---

## **Key Modules**

### **`EPICS_Adapters/psc_epics.py`**
Handles PSC-specific PV interactions:
- DAC/SP, GND/SP, MODE, RATE
- DCCT1/2 waveforms
- IGND readbacks
- Snapshot triggers and waveform extraction
- Fault masks, resets, live & latched faults

### **`EPICS_Adapters/ate_epics.py`**
Abstraction layer for the ATE tester IOC:
- Sets IGND channel and IGND setpoint
- DCCT fault routing
- Fault injection (FLT1, FLT2, Spare, PCFault)
- Tester2 command interface
- Tester status readback

### **`Functional_Tests/ate_fault_tests.py`**
Fault injection & verification:
- Checks live + latched fault bits
- Uses bit masks (0x80, 0x100, 0x200, 0x40)
- Clears faults and verifies zero state
- Builds Pass/Fail report table

### **`Functional_Tests/jump_test.py`**
Transient measurement of PSC performance:
- Detects fast transitions (diff → argmax)
- Extracts pre/post transition windows
- Plots DAC, DCCT1/2, ERR, REG, VOLT, GND, SPARE

### **`Functional_Tests/smooth_ramp_test.py`**
Smooth-ramp behavior & loop stability:
- Slow directional ramps (positive/negative)
- IGND stability verification
- DCCT and ERR tracking

### **`Functional_Tests/ps_regulation_test.py`**
Regulation loop stability tests:
- DAC and Regulation waveform capture
- Overshoot/settling visualization

### **`Functional_Tests/evr_timing_test.py`**
Verifies EVR 1 Hz timestamps increment correctly.

### **`Functional_Tests/fofb_test.py`**
Daisy packet monotonicity test:
- Uses CAEN generator (C version + shell script)
- Validates packet ordering & RX timing

---

## **Installation**

Install Python dependencies:

```
pip install -r requirements.txt
```

Includes:
- `numpy`
- `matplotlib`
- `pyepics`
- `reportlab`
- `h5py`

## **Compile the Packet Generator**
Compile the caen_fast_genpacket.c to caen_fast_genpacket
Set the caen_fast_genpacket_loop_inf.sh to eXecutable

---

## **Supported Environment**

- Python **3.10+**
- EPICS Channel Access available on the network
- Access to PSC IOC and ATE Tester IOC

---

## **Output Directory Structure**

Every test run creates:

```
Shipment #{N}/		     # If it does not yet exist
├── Raw_Data/                # PNG waveform images
└── Test_Report_{SN}.pdf     # Final auto-generated report

```

---



---

## **Contact**
Maintainer: **Michael Capotosto**

NSLS-II Diagnostics & Instrumentation Group  
Brookhaven National Laboratory  

---
