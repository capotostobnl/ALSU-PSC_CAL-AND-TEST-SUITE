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
    from Common.initialize_dut import DUT


# Standardize column widths to 12
HDR_6COL = (f"{'Itest':>12}{'dacSP':>12}{'dcct1':>12}{'dcct2':>12}"
            f"{'dacRB':>12}{'err':>12}")

# Standardize header for 4-column tables
HDR_4COL = f"{' ':>26}{'dacSP':>12}{'dcct1':>12}{'dcct2':>12}{'dacRB':>12}"


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
    # Use 12.6f to match the header width
    log_report(
        f"{tp.dmm_current:>12.6f}{tp.dac_setpoint:>12.6f}"
        f"{tp.dcct1:>12.6f}{tp.dcct2:>12.6f}"
        f"{tp.dac_readback:>12.6f}{tp.error:>12.6f}"
    )


def log_run_header(
        chan: int,
        burden: float,
        report_obj: CalibrationReport,
        dut: DUT
        ):
    """Fixed: This should not use log_report for the header to avoid repetition in PDF."""
    line1 = f"{dut.pv_prefix}:Chan{chan}"
    line2 = f"Burden resistor = {burden:.4f}"
    
    # We use report_obj.write_line directly or ensure the loop doesn't re-trigger this
    # to avoid the 'repeating header' seen in your provided image.
    print(line1)
    print(line2)
    print("")
    report_obj.write_line(line1)
    report_obj.write_line(line2)
    report_obj.write_line("")



def log_gains_offsets(
        bdac: float, b1: float, b2: float,
        mdac: float, m1: float, m2: float, m3: float
        ) -> None:
    log_report("")
    log_report(HDR_4COL)
    # Using 12.6f and standardizing label width to 26
    log_report(f"{'Initial measured offsets: ':>26}{bdac:>12.6f}{b1:>12.6f}{b2:>12.6f}{0:>12.6f}")
    log_report(f"{'Initial measured gains:   ':>26}{mdac:>12.6f}{m1:>12.6f}{m2:>12.6f}{m3:>12.6f}")
    log_report(f"{'Gain corrections:         ':>26}{mdac:>12.6f}{1/m1:>12.6f}{1/m2:>12.6f}{1:>12.6f}")
    log_report("")
    log_report("Writing gain and offset corrections for dacSP, dcct1, and dcct2 to PSC")


def log_statistics(results_matrix: np.ndarray) -> None:
    """Calculates and logs the mean and standard deviation for the run."""
    mean_vector = np.mean(results_matrix, axis=0)
    std_vector = np.std(results_matrix, axis=0)

    log_report("\n")
    log_report(HDR_4COL)
    log_report(f"{'Final measured offsets mean: ':>26}{mean_vector[4]:>12.6f}{mean_vector[5]:>12.6f}"
               f"{mean_vector[6]:>12.6f}{mean_vector[7]:>12.6f}")
    log_report(f"{'Final measured offsets stdev:':>26}{std_vector[4]:>12.6f}{std_vector[5]:>12.6f}"
               f"{std_vector[6]:>12.6f}{std_vector[7]:>12.6f}")
    log_report(f"{'Final measured gains mean:   ':>26}{mean_vector[0]:>12.6f}{mean_vector[1]:>12.6f}"
               f"{mean_vector[2]:>12.6f}{mean_vector[3]:>12.6f}")
    log_report(f"{'Final measured gains stdev:  ':>26}{std_vector[0]:>12.6f}{std_vector[1]:>12.6f}"
               f"{std_vector[2]:>12.6f}{std_vector[3]:>12.6f}\n\n")
