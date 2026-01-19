"""
Calibration Logging Module
==========================

Handles all reporting and console output for the PSC calibration process.
This module separates the 'presentation layer' (logging/PDF generation)
from the hardware interaction and mathematical analysis layers.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from cal_report_generator import CalibrationReport
    from cal_analysis import TestPoint


HDR_6COL = (f"{'Itest':>14}{'dacSP':>14}{'dcct1':>14}{'dcct2':>14}"
            f"{'dacRB':>14}{'err':>14}")
HDR_4COL = f"{'dacSP':>40}{'dcct1':>14}{'dcct2':>14}{'dacRB':>14}"


class CalibrationLogger:
    """
    Handles dual-destination logging for calibration procedures.

    This logger directs output to the standard console (stdout) and optionally
    to a PDF report generator object. It handles newline formatting to ensure
    visual consistency between the console output and the PDF document
    structure.

    Attributes:
        report_obj (CalibrationReport, optional): The report generator instance
            where logs should be written. Defaults to None.
    """
    def __init__(self):
        self.report_obj: CalibrationReport | None = None

    def set_report(self, report_obj: CalibrationReport) -> None:
        """
        Assigns the PDF report object to the logger.

        Args:
            report_obj: An instance of the report generator class (e.g.,
                CalibrationReport) capable of writing lines to a PDF.
        """
        self.report_obj = report_obj

    def log(self, msg: str) -> None:
        """
        Writes a message to the console and, if configured, the PDF report.

        Splits multi-line strings to process standard newlines ('\n') correctly
        within the PDF report's line-by-line writing method.

        Args:
            msg (str): The text message to log.
        """
        print(msg)  # Print to console exactly as is

        if self.report_obj:
            lines = msg.split('\n')

            for line in lines:
                # write_line automatically moves the cursor down
                # (y -= line_height)
                # allowing "" to act as a spacer without printing a glyph.
                self.report_obj.write_line(line)


logger = CalibrationLogger()


def log_report(msg="") -> None:
    """
    Global helper function to log messages to the active CalibrationLogger.

    This acts as a shorthand wrapper for `logger.log(msg)`, sending output
    to both the console and the PDF report if one is attached.

    Args:
        msg (str, optional): The message string to log. Defaults to "".
    """
    logger.log(msg)


def log_testpoint_data(
        tp: TestPoint,
        header: bool = False
        ) -> None:
    """Logs the formatted testpoint data to the console and report."""
    if header:
        log_report(HDR_6COL)

    log_report(
        f"{tp.dmm_current:>14.6f}{tp.dac_setpoint:>14.6f}"
        f"{tp.dcct1:>14.6f}{tp.dcct2:>14.6f}"
        f"{tp.dac_readback:>14.6f}{tp.error:>14.6f}"
    )


def log_run_header(
        chan: int,
        burden: float,
        report_obj: CalibrationReport
        ):
    """Logs the channel start information."""
    msg = (f"PSCtest:Chan{chan}\n"
           f"Burden resistor = {burden:3.4f}\n\n"
           "Measuring initial gains and offsets")
    print(msg)
    report_obj.write_line(msg)


def log_gains_offsets(
        bdac: float, b1: float, b2: float,
        mdac: float, m1: float, m2: float, m3: float
        ) -> None:
    """Logs the calculated gains and offsets."""
    log_report("")
    log_report(HDR_4COL)
    log_report(
        f"{'Initial measured offsets: '}{bdac:>14.6f}{b1:>14.6f}{b2:>14.6f}"
        f"{0:>14.6f}"
        )
    log_report(
        f"{'Initial measured gains:   '}{mdac:>14.6f}{m1:>14.6f}{m2:>14.6f}"
        f"{m3:>14.6f}"
        )
    log_report(
        f"{'Gain corrections:         '}{mdac:>14.6f}{1 / m1:>14.6f}"
        f"{1 / m2:>14.6f}{1:>14.6f}"
        )
    log_report("")
    log_report(
        "Writing gain and offset corrections for dacSP, dcct1, and "
        "dcct2 to PSC"
    )


def log_statistics(results_matrix: np.ndarray) -> None:
    """Calculates and logs the mean and standard deviation for the run."""
    mean_vector = np.mean(results_matrix, axis=0)
    std_vector = np.std(results_matrix, axis=0)

    log_report("\n")
    log_report(f"{'dacSP':>38}{'dcct1':>14}{'dcct2':>14}{'dacRB':>14}")

    # 0-3 are Gains (mdac, m1, m2, m3), 4-7 are Offsets (bdac, b1, b2, b3)
    # Note: Your original code had 'offsets' printing indices 4,5,6,7 and
    # 'gains' printing 0,1,2,3

    log_report(
        f"{'Final measured offsets mean: '}{mean_vector[4]:>9.6f}"
        f"{mean_vector[5]:>14.6f}{mean_vector[6]:>14.6f}"
        f"{mean_vector[7]:>14.6f}"
    )
    log_report(
        f"{'Final measured offsets stdev:'}{std_vector[4]:>9.6f}"
        f"{std_vector[5]:>14.6f}{std_vector[6]:>14.6f}"
        f"{std_vector[7]:>14.6f}"
    )
    log_report(
        f"{'Final measured gains mean:   '}{mean_vector[0]:>9.6f}"
        f"{mean_vector[1]:>14.6f}{mean_vector[2]:>14.6f}"
        f"{mean_vector[3]:>14.6f}"
    )
    log_report(
        f"{'Final measured gains stdev:  '}{std_vector[0]:>9.6f}"
        f"{std_vector[1]:>14.6f}{std_vector[2]:>14.6f}"
        f"{std_vector[3]:>14.6f}\n\n"
    )
