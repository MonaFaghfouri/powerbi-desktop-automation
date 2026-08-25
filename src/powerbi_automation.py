from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

import win32con
import win32gui
from pywinauto import Desktop
from pywinauto.keyboard import send_keys


# =============================================================================
# Configuration
# =============================================================================

PBIX_FOLDER = Path(
    os.getenv(
        "PBIX_FOLDER",
        str(Path.home() / "Desktop" / "BI"),
    )
)

POWER_BI_START_TIMEOUT_SECONDS = int(
    os.getenv("POWER_BI_START_TIMEOUT_SECONDS", "120")
)

AFTER_OPEN_WAIT_SECONDS = int(
    os.getenv("AFTER_OPEN_WAIT_SECONDS", "60")
)

REFRESH_START_TIMEOUT_SECONDS = int(
    os.getenv("REFRESH_START_TIMEOUT_SECONDS", "45")
)

REFRESH_TIMEOUT_SECONDS = int(
    os.getenv("REFRESH_TIMEOUT_SECONDS", str(2 * 60 * 60))
)

NO_DIALOG_SETTLE_SECONDS = int(
    os.getenv("NO_DIALOG_SETTLE_SECONDS", "30")
)

CLOSE_TIMEOUT_SECONDS = int(
    os.getenv("CLOSE_TIMEOUT_SECONDS", "60")
)

POLL_INTERVAL_SECONDS = float(
    os.getenv("POLL_INTERVAL_SECONDS", "1")
)


# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


# =============================================================================
# PBIX Discovery
# =============================================================================

def find_all_pbix(folder: Path) -> list[Path]:
    """
    Find all PBIX files in the configured folder.

    Args:
        folder: Directory containing Power BI reports.

    Returns:
        Sorted list of PBIX file paths.

    Raises:
        FileNotFoundError:
            If the folder does not exist or no PBIX files are found.
    """

    if not folder.is_dir():
        raise FileNotFoundError(
            f"PBIX folder does not exist: {folder}"
        )

    pbix_files = sorted(
        path
        for path in folder.glob("*.pbix")
        if path.is_file()
    )

    if not pbix_files:
        raise FileNotFoundError(
            f"No PBIX files were found in: {folder}"
        )

    return pbix_files


# =============================================================================
# Window Helpers
# =============================================================================

def desktop_windows():
    """
    Return all currently visible top-level desktop windows.

    Transient windows that disappear during inspection are ignored.
    """

    windows = []

    for window in Desktop(backend="uia").windows():
        try:
            if window.is_visible():
                windows.append(window)
        except Exception:
            continue

    return windows


def power_bi_windows():
    """
    Return visible Power BI Desktop windows.
    """

    windows = []

    for window in desktop_windows():
        try:
            title = window.window_text().casefold()

            if "power bi desktop" in title:
                windows.append(window)

        except Exception:
            continue

    return windows


def get_fresh_main_window():
    """
    Re-detect and return the current Power BI Desktop main window.

    Power BI can recreate or replace its top-level window while loading
    reports or closing modal dialogs. Therefore, cached window references
    can become stale.
    """

    windows = power_bi_windows()

    if not windows:
        raise RuntimeError(
            "Power BI Desktop window was not found. "
            "Power BI may have closed or crashed."
        )

    return windows[0]


def force_focus(window) -> None:
    """
    Bring a Power BI window to the foreground.

    This improves the reliability of keyboard shortcuts and ribbon actions.
    """

    try:
        handle = window.handle

        if win32gui.IsIconic(handle):
            win32gui.ShowWindow(
                handle,
                win32con.SW_RESTORE,
            )

        win32gui.SetForegroundWindow(handle)

    except Exception:
        pass

    window.set_focus()
    time.sleep(0.5)


# =============================================================================
# Power BI Launch
# =============================================================================

def open_power_bi(pbix_path: Path):
    """
    Open a PBIX file in Power BI Desktop.

    Args:
        pbix_path: PBIX report to open.

    Returns:
        Power BI Desktop window object.

    Raises:
        RuntimeError:
            If another Power BI Desktop window is already open.

        TimeoutError:
            If Power BI does not open within the configured timeout.
    """

    existing_windows = power_bi_windows()

    if existing_windows:
        titles = ", ".join(
            repr(window.window_text())
            for window in existing_windows
        )

        raise RuntimeError(
            "A Power BI Desktop window is already open. "
            "Close it before processing the next file. "
            f"Currently open: {titles}"
        )

    logger.info("Opening: %s", pbix_path.name)

    os.startfile(str(pbix_path))

    deadline = (
        time.monotonic()
        + POWER_BI_START_TIMEOUT_SECONDS
    )

    while time.monotonic() < deadline:

        windows = power_bi_windows()

        if windows:
            window = windows[0]

            force_focus(window)

            logger.info(
                "Power BI Desktop is ready: %s",
                window.window_text(),
            )

            return window

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(
        "Power BI Desktop did not open within "
        f"{POWER_BI_START_TIMEOUT_SECONDS} seconds."
    )


# =============================================================================
# Refresh Detection
# =============================================================================

def refresh_indicators(main_window) -> set[tuple]:
    """
    Detect UI elements that indicate an active Power BI refresh.

    Depending on the Power BI version, refresh progress may appear either:

    1. As a top-level Refresh window.
    2. As a child panel containing a Cancel button.

    Returns:
        A set containing stable identifiers for detected refresh indicators.
    """

    indicators: set[tuple] = set()

    # -------------------------------------------------------------------------
    # Detect top-level Refresh windows
    # -------------------------------------------------------------------------

    for window in desktop_windows():

        try:
            title = (
                window
                .window_text()
                .strip()
                .casefold()
            )

            if (
                title == "refresh"
                or title.startswith("refresh ")
            ):
                indicators.add(
                    (
                        "window",
                        window.handle,
                    )
                )

        except Exception:
            continue

    # -------------------------------------------------------------------------
    # Detect Refresh panel via its Cancel button
    # -------------------------------------------------------------------------

    try:

        buttons = main_window.descendants(
            control_type="Button"
        )

        for button in buttons:

            try:

                text = (
                    button
                    .window_text()
                    .strip()
                    .casefold()
                )

                if text != "cancel":
                    continue

                if not button.is_visible():
                    continue

                runtime_id = (
                    button
                    .element_info
                    .runtime_id
                )

                if runtime_id:

                    indicators.add(
                        (
                            "cancel",
                            *tuple(runtime_id),
                        )
                    )

                else:

                    rect = button.rectangle()

                    indicators.add(
                        (
                            "cancel",
                            rect.left,
                            rect.top,
                            rect.right,
                            rect.bottom,
                        )
                    )

            except Exception:
                continue

    except Exception:
        pass

    return indicators


# =============================================================================
# Refresh Button Detection
# =============================================================================

def find_ribbon_refresh_button(main_window):
    """
    Find Power BI's Refresh ribbon button.

    Directly clicking the UI Automation control is more reliable than
    relying entirely on keyboard shortcuts.
    """

    try:
        buttons = main_window.descendants(
            control_type="Button"
        )
    except Exception:
        return None

    for button in buttons:

        try:

            if not button.is_visible():
                continue

            name = (
                button
                .window_text()
                .strip()
                .casefold()
            )

            if name == "refresh":
                return button

        except Exception:
            continue

    return None


# =============================================================================
# Refresh Report
# =============================================================================

def refresh_and_wait(main_window) -> None:
    """
    Refresh the currently open Power BI report.

    The function:

    1. Tries to click the Refresh ribbon button directly.
    2. Falls back to Alt -> H -> R if necessary.
    3. Detects refresh progress.
    4. Waits until the refresh completes.
    """

    main_window = get_fresh_main_window()
    force_focus(main_window)

    # Record indicators that existed before refresh.
    before_refresh = refresh_indicators(main_window)

    logger.info("Starting Refresh...")

    clicked = False

    # -------------------------------------------------------------------------
    # Preferred method: direct Refresh button click
    # -------------------------------------------------------------------------

    refresh_button = find_ribbon_refresh_button(
        main_window
    )

    if refresh_button is not None:

        try:

            refresh_button.click_input()

            clicked = True

            logger.info(
                "Clicked the Refresh ribbon button."
            )

        except Exception as error:

            logger.warning(
                "Could not click Refresh directly (%s). "
                "Falling back to keyboard shortcuts.",
                error,
            )

    # -------------------------------------------------------------------------
    # Fallback: Power BI keyboard sequence
    # -------------------------------------------------------------------------

    if not clicked:

        force_focus(main_window)

        send_keys(
            "%",
            pause=0.3,
        )

        send_keys(
            "h",
            pause=0.3,
        )

        send_keys(
            "r",
            pause=0.3,
        )

        logger.info(
            "Sent Alt -> H -> R refresh sequence."
        )

    # -------------------------------------------------------------------------
    # Wait for refresh to start
    # -------------------------------------------------------------------------

    started_deadline = (
        time.monotonic()
        + REFRESH_START_TIMEOUT_SECONDS
    )

    observed_indicators: set[tuple] = set()

    while (
        time.monotonic()
        < started_deadline
    ):

        main_window = get_fresh_main_window()

        current_indicators = (
            refresh_indicators(main_window)
        )

        observed_indicators.update(
            current_indicators
            - before_refresh
        )

        if observed_indicators:

            logger.info(
                "Refresh progress detected."
            )

            break

        time.sleep(POLL_INTERVAL_SECONDS)

    else:

        logger.warning(
            "No Refresh dialog was detected. "
            "Waiting %s seconds before continuing.",
            NO_DIALOG_SETTLE_SECONDS,
        )

        time.sleep(
            NO_DIALOG_SETTLE_SECONDS
        )

        logger.info(
            "Refresh assumed complete."
        )

        return

    # -------------------------------------------------------------------------
    # Wait for refresh to finish
    # -------------------------------------------------------------------------

    refresh_deadline = (
        time.monotonic()
        + REFRESH_TIMEOUT_SECONDS
    )

    while (
        time.monotonic()
        < refresh_deadline
    ):

        main_window = get_fresh_main_window()

        current_indicators = (
            refresh_indicators(
                main_window
            )
        )

        if observed_indicators.isdisjoint(
            current_indicators
        ):

            # Allow Power BI to complete final background work.
            time.sleep(3)

            logger.info(
                "Refresh completed."
            )

            return

        time.sleep(
            POLL_INTERVAL_SECONDS
        )

    raise TimeoutError(
        "Refresh did not finish within "
        f"{REFRESH_TIMEOUT_SECONDS} seconds."
    )


# =============================================================================
# Save Report
# =============================================================================

def save_report() -> None:
    """
    Save the currently open PBIX report.
    """

    main_window = get_fresh_main_window()

    force_focus(main_window)

    logger.info(
        "Saving PBIX..."
    )

    send_keys("^s")

    # Give Power BI enough time to complete the save operation.
    time.sleep(5)

    logger.info(
        "Save command completed."
    )


# =============================================================================
# Close Power BI
# =============================================================================

def close_power_bi(
    pbix_path: Path,
) -> None:
    """
    Close Power BI Desktop and wait until its window disappears.

    Args:
        pbix_path:
            Path of the currently processed PBIX file.
    """

    windows = power_bi_windows()

    if not windows:

        logger.info(
            "Power BI Desktop is already closed."
        )

        return

    window = windows[0]

    force_focus(window)

    logger.info(
        "Closing: %s",
        pbix_path.name,
    )

    send_keys("%{F4}")

    deadline = (
        time.monotonic()
        + CLOSE_TIMEOUT_SECONDS
    )

    while (
        time.monotonic()
        < deadline
    ):

        if not power_bi_windows():

            logger.info(
                "Power BI Desktop closed."
            )

            return

        time.sleep(
            POLL_INTERVAL_SECONDS
        )

    raise TimeoutError(
        "Power BI Desktop did not close within "
        f"{CLOSE_TIMEOUT_SECONDS} seconds. "
        "An unexpected dialog may be blocking it."
    )


# =============================================================================
# Process Individual PBIX
# =============================================================================

def process_file(
    pbix_path: Path,
) -> None:
    """
    Open, refresh, save, and close one PBIX file.
    """

    logger.info("=" * 70)

    logger.info(
        "Processing: %s",
        pbix_path.name,
    )

    open_power_bi(
        pbix_path
    )

    logger.info(
        "Waiting %s seconds for report loading...",
        AFTER_OPEN_WAIT_SECONDS,
    )

    time.sleep(
        AFTER_OPEN_WAIT_SECONDS
    )

    refresh_and_wait(
        get_fresh_main_window()
    )

    save_report()

    close_power_bi(
        pbix_path
    )

    logger.info(
        "Done: %s",
        pbix_path.name,
    )


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    """
    Process every PBIX report inside the configured directory.
    """

    logger.info(
        "PBIX folder: %s",
        PBIX_FOLDER,
    )

    pbix_files = find_all_pbix(
        PBIX_FOLDER
    )

    logger.info(
        "Found %d PBIX file(s) to process.",
        len(pbix_files),
    )

    failures: list[
        tuple[Path, Exception]
    ] = []

    for index, pbix_path in enumerate(
        pbix_files,
        start=1,
    ):

        logger.info(
            "[%d/%d] %s",
            index,
            len(pbix_files),
            pbix_path.name,
        )

        try:

            process_file(
                pbix_path
            )

        except Exception as error:

            logger.exception(
                "Failed on %s: %s",
                pbix_path.name,
                error,
            )

            failures.append(
                (
                    pbix_path,
                    error,
                )
            )

            # Try to restore a clean Power BI state
            # before processing the next report.
            try:

                close_power_bi(
                    pbix_path
                )

            except Exception:

                logger.warning(
                    "Could not confirm that Power BI "
                    "closed after failure on %s. "
                    "Manual intervention may be required.",
                    pbix_path.name,
                )

    # -------------------------------------------------------------------------
    # Final summary
    # -------------------------------------------------------------------------

    logger.info("=" * 70)

    if failures:

        logger.error(
            "Completed with %d failure(s):",
            len(failures),
        )

        for path, error in failures:

            logger.error(
                " - %s: %s",
                path.name,
                error,
            )

        sys.exit(1)

    logger.info(
        "All %d PBIX file(s) processed successfully.",
        len(pbix_files),
    )


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        logger.warning(
            "Execution interrupted by user."
        )

        sys.exit(130)

    except Exception as error:

        logger.exception(
            "Fatal error: %s",
            error,
        )

        sys.exit(1)
