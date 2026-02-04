"""
PSC Automation Suite Launcher
=============================

This module serves as the primary entry point for the ALSU-PSC Calibration
and Functional Test Suite. It coordinates the high-level execution flow
by managing shared session state and user configuration.

The launcher facilitates:
- **Execution Mode Selection**: Allows operators to run calibration,
  functional testing, or both in a single session.
- **Session Management**: Initializes a shared `DUT` (Device Under Test)
  instance to anchor project paths and perform hardware discovery.
- **Dependency Injection**: Captures hardware identifiers and model
  specifications once, passing them into downstream sub-suites to
  prevent redundant user prompts.

Workflow:
    1. Prompt user for execution mode (Cal/Test/Both).
    2. Initialize `DUT` object to resolve project-relative paths.
    3. Prompt for shipment/hardware identifiers via `dut.prompt_inputs()`.
    4. If Calibration is selected, retrieve the specific `PSCModel`
       configuration.
    5. Execute selected suites using the shared `DUT` and `config_instance`.
"""
import time
from Cal.cal_main import run_calibration_suite
from Test.test_main import run_psc_test_suite
from Common.initialize_dut import DUT
from Common.psc_models import get_psc_model_from_user


def prompt_execution_mode():
    """
    Prompts the user to select an execution mode.
    Guards against invalid inputs.

    Returns:
        str: The selected mode ('cal_only', 'test_only', or 'cal_and_test')
    """
    while True:
        print("\n--------------------------------")
        print("Select Execution Mode:")
        print("1. Calibrate Only")
        print("2. Test Only")
        print("3. Calibrate and Test")
        print("--------------------------------")

        selection = input("\nEnter selection (1-3): ").strip()

        if selection == "1":  # Cal Only
            cal_sel = True
            test_sel = False
            return cal_sel, test_sel
        elif selection == "2":  # Test Only
            cal_sel = False
            test_sel = True
            return cal_sel, test_sel
        elif selection == "3":  # Cal and Test
            cal_sel = True
            test_sel = True
            return cal_sel, test_sel
        else:
            print(
                f"\n[!] Invalid input: '{selection}'. "
                "Please enter 1, 2, or 3."
                )


def main():
    """
    Coordinates the primary execution flow for the PSC automation suite.

    This function serves as the central orchestrator for the application
    session. It performs the following sequence:
    1.  Prompts the operator to select the execution mode (Calibration,
        Functional Testing, or both).
    2.  Instantiates the shared DUT (Device Under Test) object, which
        anchors project-relative file paths and queries hardware
        configuration via EPICS.
    3.  Collects operator inputs and discovery data once to establish
        a single source of truth for the session.
    4.  Injects the shared DUT and PSCModel configuration into the
        selected sub-suites (Calibration and/or Testing) to ensure
        data consistency and eliminate redundant prompts.
    """
    cal, test = prompt_execution_mode()

    dut = DUT()
    dut.prompt_inputs()
    sleep_option = False
    sleep_option = input("Sleep 20 minutes?")
    if sleep_option == "1":
        sleep_option = True
    elif sleep_option == "0":
        sleep_option = False
    else: 
        print("Enter 1 to sleep, or 0 to continue immediately")

    if sleep_option:
        print(f"Sleeping 20 Minutes")
        #total_seconds = (20*60)
        total_seconds = ((15+20)*60)
        print(f"Minutes remaining: {total_seconds/60}")
        while total_seconds >= 0:
                mins = total_seconds // 60
                secs = total_seconds % 60
                
                timer_display = f"{mins:02d}:{secs:02d}"
                
                print(f"Time remaining: {timer_display}")
                
                time.sleep(1)
                total_seconds -= 1
    

    if cal:
        print("Beginning Calibration...")
        run_calibration_suite(dut)

    if test:
        print("Beginning functional test...")
        run_psc_test_suite(dut)


if __name__ == "__main__":
    main()
