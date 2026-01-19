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


if __name__ == "__main__":
    cal, test = prompt_execution_mode()

    dut = DUT()
    dut.prompt_inputs()

    config_instance = None

    if cal:
        config_instance = get_psc_model_from_user(dut.num_channels)
        print("Beginning Calibration...")
        run_calibration_suite(dut, config_instance)

    if test:
        print("Beginning functional test...")
        run_psc_test_suite(dut)
