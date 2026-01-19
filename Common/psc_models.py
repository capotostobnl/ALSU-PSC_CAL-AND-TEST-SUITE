"""
PSC Model Definitions and Selection Utilities.

This module defines the `PSCModel` dataclass, which serves as the Single Source
of Truth (SSOT) for the Power Supply Controller (PSC) software suite. It reconciles
hardware-specific constants required for calibration with behavioral parameters
required for functional verification.

Key Components:
    - PSCModel: The primary configuration object encapsulating all physical and
      operational parameters for a specific device version.
    - ChannelValues: A flexible data container mapping settings to 2 or 4 physical
      channels.
    - TestParams: Nested dataclasses (Regulator, SmoothRamp, Jump) that define
      pass/fail criteria for automated testing.

Usage:
    This module is intended to be imported by both the Calibration script (cal_main.py)
    and the Functional Test script (test_main.py) to ensure consistent device
    definitions across the project lifecycle.
"""
# flake8: noqa: E501
# pylint: disable=line-too-long

import sys
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ChannelValues:
    """
    A unified data container for per-channel PSC parameters.

    This class provides an explicit mapping of values (e.g., currents, voltages,
    logic flags, or resistance) to physical PSC channels. It is designed to support
    both legacy 2-channel hardware and modern 4-channel hardware seamlessly.

    Attributes:
        ch1 (float): The parameter value assigned to Channel 1.
        ch2 (float): The parameter value assigned to Channel 2.
        ch3 (Optional[float]): The parameter value assigned to Channel 3.
            Defaults to None for 2-channel devices.
        ch4 (Optional[float]): The parameter value assigned to Channel 4.
            Defaults to None for 2-channel devices.

    Methods:
        as_list(): Returns a list containing only the active (non-None) channel values.
        get(index): Safe accessor for retrieving a value by zero-based channel index.
    """
    ch1: float
    ch2: float
    ch3: float | None = None
    ch4: float | None = None

    def as_list(self) -> List[float]:
        """Returns the non-None values as a list."""
        vals = [self.ch1, self.ch2]
        if self.ch3 is not None:
            vals.append(self.ch3)
        if self.ch4 is not None:
            vals.append(self.ch4)
        return vals

    def get(self, index: int) -> float:
        """Retrieves value by 0-based index (0=ch1, 1=ch2, etc)."""
        return self.as_list()[index]

@dataclass(frozen=True)
class RegulatorTestParams:
    """
        Encapsulates configuration parameters for the Power Supply
        Regulation test.

        This class defines the target setpoints, timing, and acceptance
        criteria used to evaluate the stability and accuracy of a PSC
        channel over a fixed duration.

        Attributes:
            setpoints: A ChannelValues instance mapping specific current
                setpoints (Amps) to each physical channel.
            settling_time: The duration (seconds) to wait after applying the
                setpoint before beginning data collection.
            tolerance: The maximum allowable deviation (Amps) between the
                measured average and the setpoint for a 'PASS' result.
            ramp_rate: The slew rate (Amps/second) at which the PSC should
                transition to the target setpoint.
            num_samples: The total number of data points to capture during
                the regulation stability window.
            sample_interval: The time delay (seconds) between successive
                register reads during data collection.
        """
    setpoints: ChannelValues  # Set Regulator Test Current SP
    settling_time: float = 10  # Default settling time of 10 seconds
    tolerance: float = 0.050  # Default Pass/Fail Threshold to 50mA
    ramp_rate: float = 10  # Default to 10A/s
    num_samples: int = 180  # Total number of data points to collect
    sample_interval: float = 0.3  # Default 300ms between samples


@dataclass(frozen=True)
class SmoothRampTestParams:
    """
    Encapsulates configuration parameters for the Smooth Ramp Test.

    Validates that the PSC can transition between a 'Start' and 'End'
    setpoint at a specific rate without regulation errors.

    Attributes:
        start_setpoints: The starting current (Amps) for the ramp.
        end_setpoints: The target current (Amps) to reach.
        ramp_rate: The slew rate (Amps/second) for the move.
        settling_time: Extra buffer time (seconds) to wait after the
            calculated ramp duration to ensure the waveform is captured.
        tolerance: The allowable deviation (Amps) for ground current checks.
    """

    start_setpoints: ChannelValues  # Set START current for the ramp test
    end_setpoints: ChannelValues  # Set the END current for the ramp test
    ramp_rate: ChannelValues  # Set Per-Channel Ramp Rates for Smooth Test
    settling_time: float = 10  # Default settling time of 10 seconds
    tolerance: float = 0.050  # Default Pass/Fail Threshold to 50mA


@dataclass(frozen=True)
class JumpTestParams:
    """
    Configuration for the Jump (Step Response) Test.
    
    Used to evaluate the control loop stability by measuring overshoot, 
    ringing, and settling time during a sudden current step.
    """
    start_setpoints: ChannelValues  # Baseline current before the jump
    step_size: ChannelValues       # The magnitude of the jump (Amps)
    sample_window: int = 500        # Points to show before/after the jump
    tolerance: float = 0.050        # Ground current pass/fail threshold (A)


@dataclass(frozen=True, kw_only = True)
class PSCModel:
    """
    Represents the technical specifications and test limits for a specific
    PSC model.

    Attributes:
        model_id: Unique internal identifier for the unit type (e.g., "R1-HSS").
        display_name: Short name used for console menus and reporting titles.
        description: Full hardware string (e.g., "PSC-2CH-HSS-AR-QD-QF").
        channels: The physical number of channels (2 or 4).
        reg: An instance of RegulatorTestParams defining stability test criteria.
        smooth: An instance of SmoothRampTestParams defining slew rate and range.
        jump: An instance of JumpTestParams defining step response behavior.
    """

    ################################################################################
    #      Common Parameters
    ################################################################################
    model_id: str         # Internal ID (e.g., "R1-HSS")
    display_name: str     # Short name for menu (e.g., "R1 2Ch")
    description: str      # Full description (e.g., "PSC-2CH-HSS-AR-QD-QF")
    channels: int
    designation: str

    ################################################################################
    #      Calibration Parameters
    ################################################################################
    ndcct: float
    burden_resistors: ChannelValues
    ovc1_threshold: ChannelValues
    ovc2_threshold: ChannelValues
    ovv_threshold: ChannelValues
    num_runs: int = 5
    sp0: float = 1.0

    # -------------------------------------------------------------------------
    # Scale Factors
    # -------------------------------------------------------------------------
    current_full_scale_dividend: float = 1.0
    g_target_multiplier: float = 10.0

    sf_ramp_rate: float = 4.0
    sf_dcct_scale: float | None = None  # Will use p_scale_factor if None
    sf_vout: ChannelValues
    sf_ignd: float = 1.0
    sf_spare: ChannelValues
    sf_regulator: float = 1.0
    sf_error: float = 1.0

    # -------------------------------------------------------------------------
    # Fault Thresholds
    # -------------------------------------------------------------------------
    ovc1_threshold: ChannelValues
    ovc2_threshold: ChannelValues
    ovv_threshold: ChannelValues
    err1_threshold: float = 10
    err2_threshold: float = 10
    ignd_threshold: float = 10

    # -------------------------------------------------------------------------
    # Fault Count Limits
    # -------------------------------------------------------------------------
    ovc1_flt_cnt: float = 0.01
    ovc2_flt_cnt: float = 0.01
    ovv_flt_cnt: float = 0.01
    err1_flt_cnt: float = 0.1
    err2_flt_cnt: float = 0.1
    ignd_flt_cnt: float = 0.2
    dcct_flt_cnt: float = 0.2
    flt1_flt_cnt: float = 0.1
    flt2_flt_cnt: float = 3
    flt3_flt_cnt: float = 0.5
    flt_on_cnt: float = 3
    flt_heartbeat_cnt: float = 3

    # -------------------------------------------------------------------------
    # Dynamic Calculation Methods
    # -------------------------------------------------------------------------

    def get_current_full_scale(self, channel: int) -> float:
        """Calculates Max burden current for a specific channel."""
        rb = getattr(self.burden_resistors, f"ch{channel}")
        return self.current_full_scale_dividend / rb

    def get_s_scale_factor(self, channel: int) -> float:
        """Calculates V/A scaling factor: Burden * Target Multiplier."""
        rb = getattr(self.burden_resistors, f"ch{channel}")
        return rb * self.g_target_multiplier

    def get_p_scale_factor(self, channel: int) -> float:
        """Calculates PS scaling factor A/V: ndcct / s_scale_factor."""
        s_scale = self.get_s_scale_factor(channel)
        return self.ndcct / s_scale


    ################################################################################
    #      Test Parameters
    ################################################################################
    reg: RegulatorTestParams  # Regulator Test Parameters Class
    smooth: SmoothRampTestParams  # Smooth Ramp Test Parameters Class
    jump: JumpTestParams  # Jump Test Parameters Class


# Define the Registry of all known units
MODELS = {
    # 2-Channel Units
    "AR-QD-QF": PSCModel(model_id="AR-QD-QF",
                       display_name="2CH-HSS-AR-QD-QF",
                       description="PSC-2CH-HSS-AR-QD-QF",
                       designation="PSC-2CH-HSS-AR-QD-QF_",
                       channels=2,

                       #####################################################################
                       #      Calibration                                                  #
                       #####################################################################
                       ndcct=1000.0,
                       burden_resistors=ChannelValues(ch1=18.0, ch2=9.0),
                       sf_vout=ChannelValues(ch1=-1.25, ch2=-1.25),
                       sf_spare=ChannelValues(ch1=-6.0, ch2=-12.0),
                       ovc1_threshold=ChannelValues(ch1=51.0, ch2=101.0),
                       ovc2_threshold=ChannelValues(ch1=51.0, ch2=101.0),
                       ovv_threshold=ChannelValues(ch1=12.7, ch2=12.7),

                       #######################################################################
                       #      Test                                                           #
                       #######################################################################
                       reg=RegulatorTestParams(
                           setpoints=(reg_pts := ChannelValues(ch1=30,
                                                   ch2=50)),
                           settling_time=10),


                       smooth=SmoothRampTestParams(
                           start_setpoints=ChannelValues(ch1=0,
                                                         ch2=0,
                                                         ),
                           end_setpoints=ChannelValues(ch1=49.9,
                                                       ch2=99.9,
                                                       ),
                           ramp_rate=ChannelValues(ch1=10,
                                                   ch2=20),
                           settling_time=10,
                           tolerance=0.05),
                       jump=JumpTestParams(
                           start_setpoints=reg_pts,
                           step_size=ChannelValues(ch1=0.05,
                                                   ch2=0.05),
                           sample_window=500,
                           tolerance=0.05
                        )
                       ),

    "ABEND-QFA": PSCModel(model_id="ABEND-QFA",
                          display_name="ABEND QFA - R3 2Ch",
                          description="PSC-2CH-HSS-AR-Abend-QFA",
                          channels=2,

                          #####################################################################
                          #      Calibration                                                  #
                          #####################################################################
                          ndcct=2000.0,
                          burden_resistors=ChannelValues(ch1=4.5, ch2=9.0),
                          sf_vout=ChannelValues(ch1=-47.5, ch2=-20.0),
                          sf_spare=ChannelValues(ch1=-40.0, ch2=-20.0),
                          ovc1_threshold=ChannelValues(ch1=390.0, ch2=195.0),
                          ovc2_threshold=ChannelValues(ch1=390.0, ch2=195.0),
                          ovv_threshold=ChannelValues(ch1=470.0, ch2=190.0),

                          #######################################################################
                          #      Test                                                           #
                          #######################################################################
                          reg=RegulatorTestParams(
                           setpoints=(reg_pts := ChannelValues(ch1=200,
                                                   ch2=100)),
                           settling_time=30),

                          smooth=SmoothRampTestParams(
                              start_setpoints=ChannelValues(ch1=0,
                                                            ch2=0,
                                                            ),
                              end_setpoints=ChannelValues(ch1=385,
                                                          ch2=185,
                                                          ),
                              ramp_rate=ChannelValues(ch1=60,
                                                      ch2=30),
                              settling_time=10,
                              tolerance=0.05),
                          jump=JumpTestParams(
                              start_setpoints=reg_pts,
                              step_size=ChannelValues(ch1=0.5,
                                                      ch2=0.5),
                              sample_window=500,
                              tolerance=0.05
                           )
                          ),

    # 4-Channel Units
    "AR-Slow-XY-Corr": PSCModel(model_id="AR-Slow-XY-Corr",
                       display_name="4CH-MSS-AR Slow XY Corr",
                       description="PSC-4CH-MSS-AR-Slow XY Corr.",
                       designation="4CH-MSS-AR Slow XY Corr_",
                       channels=4,

                          #######################################################################
                          #      Calibration                                                    #
                          #######################################################################
                          ndcct=1000.0,
                          burden_resistors=ChannelValues(ch1=33.333333, ch2=33.333333,
                                       ch3=33.333333, ch4=33.333333),
                          sf_vout=ChannelValues(ch1=1.9, ch2=1.9, ch3=1.9, ch4=1.9),
                          sf_spare=ChannelValues(ch1=-5.0, ch2=-5.0, ch3=-5.0, ch4=-5.0),
                          ovc1_threshold=ChannelValues(ch1=24.5, ch2=24.5, ch3=24.5, ch4=24.5),
                          ovc2_threshold=ChannelValues(ch1=24.5, ch2=24.5, ch3=24.5, ch4=24.5),
                          ovv_threshold=ChannelValues(ch1=18.5, ch2=18.5, ch3=18.5, ch4=18.5),
                          #######################################################################
                          #      Test                                                           #
                          #######################################################################
                       reg=RegulatorTestParams(
                           setpoints=(reg_pts := ChannelValues(ch1=10,
                                                   ch2=10,
                                                   ch3=10,
                                                   ch4=10)),
                           settling_time=10),


                       smooth=SmoothRampTestParams(
                           start_setpoints=ChannelValues(ch1=-23.9,
                                                         ch2=-23.9,
                                                         ch3=-23.9,
                                                         ch4=-23.9),
                           end_setpoints=ChannelValues(ch1=23.9,
                                                       ch2=23.9,
                                                       ch3=23.9,
                                                       ch4=23.9),
                           ramp_rate=ChannelValues(ch1=10,
                                                   ch2=10,
                                                   ch3=10,
                                                   ch4=10),
                           settling_time=10,
                           tolerance=0.05),
                       jump=JumpTestParams(
                           start_setpoints=reg_pts,
                           step_size=ChannelValues(ch1=0.05,
                                                   ch2=0.05,
                                                   ch3=0.05,
                                                   ch4=0.05),
                           sample_window=500,
                           tolerance=0.05
                        )
                       ),

    "AR-Fast-XY-Corr": PSCModel(model_id="AR-Fast-XY-Corr",
                       display_name="4CH-MSF-AR-Fast XY Corr",
                       description="PSC-4CH-MSF-AR-Fast XY Corr.",
                       designation="4CH-MSF-AR-Fast XY Corr_",
                       channels=4,

                          #######################################################################
                          #      Calibration                                                    #
                          #######################################################################
                          ndcct=1000.0,
                          burden_resistors=ChannelValues(ch1=33.333333, ch2=33.333333,
                                       ch3=33.333333, ch4=33.333333),
                          sf_vout=ChannelValues(ch1=1.9, ch2=1.9, ch3=1.9, ch4=1.9),
                          sf_spare=ChannelValues(ch1=-5.0, ch2=-5.0, ch3=-5.0, ch4=-5.0),
                          ovc1_threshold=ChannelValues(ch1=24.5, ch2=24.5, ch3=24.5, ch4=24.5),
                          ovc2_threshold=ChannelValues(ch1=24.5, ch2=24.5, ch3=24.5, ch4=24.5),
                          ovv_threshold=ChannelValues(ch1=18.5, ch2=18.5, ch3=18.5, ch4=18.5),

                          #######################################################################
                          #      Test                                                           #
                          #######################################################################
                       reg=RegulatorTestParams(
                           setpoints=(reg_pts := ChannelValues(ch1=10,
                                                   ch2=10,
                                                   ch3=10,
                                                   ch4=10)),
                           settling_time=10),
                       smooth=SmoothRampTestParams(
                           start_setpoints=ChannelValues(ch1=-23.9,
                                                         ch2=-23.9,
                                                         ch3=-23.9,
                                                         ch4=-23.9),
                           end_setpoints=ChannelValues(ch1=23.9,
                                                       ch2=23.9,
                                                       ch3=23.9,
                                                       ch4=23.9),
                           ramp_rate=ChannelValues(ch1=10,
                                                   ch2=10,
                                                   ch3=10,
                                                   ch4=10),
                           settling_time=10,
                           tolerance=0.05),
                       jump=JumpTestParams(
                           start_setpoints=reg_pts,
                           step_size=ChannelValues(ch1=0.05,
                                                   ch2=0.05,
                                                   ch3=0.05,
                                                   ch4=0.05),
                           sample_window=500,
                           tolerance=0.05
                        )
                       ),

    "AR-SK": PSCModel(model_id="AR-SK",
                       display_name="4CH-MSS-AR-SK",
                       description="PSC-4CH-MSS-AR-SK",
                       designation="4CH-MSS-AR-SK_",
                       channels=4,

                      #######################################################################
                      #      Calibration                                                    #
                      #######################################################################
                      ndcct=1000.0,
                      burden_resistors=ChannelValues(ch1=33.333333, ch2=33.333333,
                                       ch3=33.333333, ch4=33.333333),
                      sf_vout=ChannelValues(ch1=1.9, ch2=1.9, ch3=1.9, ch4=1.9),
                      sf_spare=ChannelValues(ch1=-5.0, ch2=-5.0, ch3=-5.0, ch4=-5.0),
                      ovc1_threshold=ChannelValues(ch1=24.5, ch2=24.5, ch3=24.5, ch4=24.5),
                      ovc2_threshold=ChannelValues(ch1=24.5, ch2=24.5, ch3=24.5, ch4=24.5),
                      ovv_threshold=ChannelValues(ch1=18.5, ch2=18.5, ch3=18.5, ch4=18.5),

                      #######################################################################
                      #      Test                                                           #
                      #######################################################################
                       reg=RegulatorTestParams(
                           setpoints=(reg_pts := ChannelValues(ch1=10,
                                                   ch2=10,
                                                   ch3=10,
                                                   ch4=10)),
                           settling_time=10
                                                   ),
                       smooth=SmoothRampTestParams(
                           start_setpoints=ChannelValues(ch1=-23.9,
                                                         ch2=-23.9,
                                                         ch3=-23.9,
                                                         ch4=-23.9),
                           end_setpoints=ChannelValues(ch1=23.9,
                                                       ch2=23.9,
                                                       ch3=23.9,
                                                       ch4=23.9),
                           ramp_rate=ChannelValues(ch1=10,
                                                   ch2=10,
                                                   ch3=10,
                                                   ch4=10),
                           settling_time=10,
                           tolerance=0.05),
                       jump=JumpTestParams(
                           start_setpoints=reg_pts,
                           step_size=ChannelValues(ch1=0.05,
                                                   ch2=0.05,
                                                   ch3=0.05,
                                                   ch4=0.05),
                           sample_window=500,
                           tolerance=0.05
                        )
                       ),

    "AR-SD-SF": PSCModel(model_id="AR-SD-SF",
                            display_name="R2 4Ch MSS AR-SD-SF",
                            description="PSC-4CH-MSS-AR-SD-SF",
                            designation="4CH-MSS-AR-SD-SF_",
                            channels=4,


                          #######################################################################
                          #      Calibration                                                    #
                          #######################################################################
                          ndcct=1000.0,
                          burden_resistors=ChannelValues(ch1=15.38462, ch2=7.14286,
                                       ch3=15.38462, ch4=7.14286),
                          sf_vout=ChannelValues(ch1=-12.5, ch2=-10.0, ch3=-12.5, ch4=-10.0),
                          sf_spare=ChannelValues(ch1=-8.0, ch2=-15.0, ch3=-8.0, ch4=-15.0),
                          ovc1_threshold=ChannelValues(ch1=78.0, ch2=148.0, ch3=78.0, ch4=148.0),
                          ovc2_threshold=ChannelValues(ch1=78.0, ch2=148.0, ch3=78.0, ch4=148.0),
                          ovv_threshold=ChannelValues(ch1=120.0, ch2=95.0, ch3=120.0, ch4=95.0),
                          #######################################################################
                          #      Test                                                           #
                          #######################################################################
                            reg=RegulatorTestParams(
                                setpoints=(reg_pts := ChannelValues(ch1=30,
                                                        ch2=65,
                                                        ch3=30,
                                                        ch4=65)),
                                settling_time=10),
                            smooth=SmoothRampTestParams(
                                start_setpoints=ChannelValues(ch1=0,
                                                              ch2=0,
                                                              ch3=0,
                                                              ch4=0),
                                end_setpoints=ChannelValues(ch1=59,
                                                            ch2=124,
                                                            ch3=59,
                                                            ch4=124),
                                ramp_rate=ChannelValues(ch1=20,
                                                        ch2=20,
                                                        ch3=20,
                                                        ch4=20),
                                settling_time=10,
                                tolerance=0.05),
                            jump=JumpTestParams(
                                start_setpoints=reg_pts,
                                step_size=ChannelValues(ch1=0.05,
                                                        ch2=0.1,
                                                        ch3=0.05,
                                                        ch4=0.1),
                                sample_window=500,
                                tolerance=0.05
                             )
                            ),

    "AR-QFA-SHUNT": PSCModel(model_id="AR-QFA-SHUNT",
                             display_name="R3 4Ch MSS QFA SHUNT",
                             description="PSC-4CH-MSS-QFA Shunt",
                             designation="4CH-MSS-AR-QFA_Shunt_",
                             channels=4,


                          #######################################################################
                          #      Calibration                                                    #
                          #######################################################################
                          ndcct=1000.0,
                          burden_resistors=ChannelValues(ch1=83.333333, ch2=83.333333,
                                       ch3=83.333333, ch4=83.333333),
                          sf_vout=ChannelValues(ch1=-2, ch2=-2, ch3=-2, ch4=-2),
                          sf_spare=ChannelValues(ch1=-20, ch2=-20, ch3=-20, ch4=-20),
                          ovc1_threshold=ChannelValues(ch1=6, ch2=6, ch3=6, ch4=6),
                          ovc2_threshold=ChannelValues(ch1=6, ch2=6, ch3=6, ch4=6),
                          ovv_threshold=ChannelValues(ch1=12, ch2=12, ch3=12, ch4=12),
                          #######################################################################
                          #      Test                                                           #
                          #######################################################################
                             reg=RegulatorTestParams(
                                setpoints=(reg_pts := ChannelValues(ch1=5,
                                                        ch2=5,
                                                        ch3=5,
                                                        ch4=5)),
                                settling_time=10),
                             smooth=SmoothRampTestParams(
                                 start_setpoints=ChannelValues(ch1=-5.9,
                                                               ch2=-5.9,
                                                               ch3=-5.9,
                                                               ch4=-5.9),
                                 end_setpoints=ChannelValues(ch1=5.9,
                                                             ch2=5.9,
                                                             ch3=5.9,
                                                             ch4=5.9),
                                 ramp_rate=ChannelValues(ch1=10,
                                                         ch2=10,
                                                         ch3=10,
                                                         ch4=10),
                                 settling_time=10,
                                 tolerance=0.05),
                             jump=JumpTestParams(
                                 start_setpoints=reg_pts,
                                 step_size=ChannelValues(ch1=0.05,
                                                         ch2=0.05,
                                                         ch3=0.05,
                                                         ch4=0.05),
                                 sample_window=500,
                                 tolerance=0.05
                              )
                             ),
}


# -----------------------------------------------------------------------------
# Selection Utility
# -----------------------------------------------------------------------------

def get_psc_model_from_user(num_channels: int) -> PSCModel:
    """
    Filters models and prompts operator with aligned columns.
    
    Args:
        num_channels: The integer number of detected channels (e.g., 2 or 4).

    Returns:
        PSCModel: The selected configuration object.

    Raises:
        ValueError: If no models exist for the given channel count.
        SystemExit: If the user aborts selection.
    """

    try:
        available_models = [m for m in MODELS.values()
                            if m.channels == num_channels]

        if not available_models:
            raise ValueError(f"No models defined for {num_channels} channels.")

        # Calculate padding: find the longest display name string
        # We add quotes in the length calc to match the print format
        max_label_len = max(len(f"'{m.display_name}'")
                            for m in available_models) + 2

        print(f"\n--- Select {num_channels}-Channel PSC Type ---")
        for i, model in enumerate(available_models, 1):
            label = f"'{model.display_name}'".ljust(max_label_len)
            print(f"{i}. {label} | {model.description}")

        while True:
            try:
                choice = input("\nEnter Type (or 'q' to quit): ")\
                    .strip().lower()

                if choice == 'q':
                    print("Testing aborted by operator.")
                    sys.exit(0)

                idx = int(choice) - 1
                if 0 <= idx < len(available_models):
                    selected = available_models[idx]
                    print(f"--> Selected: {selected.display_name}\n")
                    return selected

                print(f"Invalid choice. Select 1-{len(available_models)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    except KeyboardInterrupt:
        print("\n\nExecution interrupted by operator (Ctrl+C). Exiting...")
        sys.exit(0)
