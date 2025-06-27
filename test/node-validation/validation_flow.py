#!/usr/bin/env python3
"""Comprehensive Node Validation Flow

This interactive script guides an operator through a sequence of sensor
validation tests across multiple conditions.  Data is logged to ``test/out``
in timestamped folders and can later be compared across controllers.

The following measurements are collected for each condition:
    - Supply voltage
    - Load voltage (derived from supply minus voltage drop)
    - Load current
    - Load resistance

Each test condition logs to its own CSV file.  A ``metadata.csv`` file in the
output directory records node information and operator comments.

TEST FLOW OVERVIEW:
==================
The validation flow systematically tests each muscle port under various conditions:

1. SUPPLY CONDITIONS: Tests with different power sources (USB only, 11V, 22V)
2. LOAD CONDITIONS: Tests with different loads (open circuit, muscle, resistor)
3. PWM LEVELS: Tests at different PWM levels (20%, 50%, 80%)
4. WAVEFORM TYPES: Tests both static PWM and ramped PWM

For each combination, the script:
- Prompts operator to set up the physical test condition
- Configures the muscle controller with specified PWM settings
- Captures time-series data of voltage, current, and resistance
- Saves data to CSV files for later analysis
- Provides cooldown periods when testing with actual muscles

This comprehensive approach allows validation of:
- Sensor accuracy across different power levels
- Controller behavior under various load conditions
- Thermal effects and muscle heating characteristics
- Cross-controller calibration consistency
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import thermoflex as tf


# ---------------------------------------------------------------------------
# Color utilities
# ---------------------------------------------------------------------------

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Standard colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Background colors
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'


def colored(text: str, color: str = '', bold: bool = False) -> str:
    """Return colored text for terminal output.
    
    Args:
        text (str): Text to colorize
        color (str): Color code from Colors class
        bold (bool): Whether to make text bold
        
    Returns:
        str: Formatted text with color codes
    """
    prefix = ''
    if bold:
        prefix += Colors.BOLD
    if color:
        prefix += color
    
    if prefix:
        return f"{prefix}{text}{Colors.RESET}"
    return text


def print_step(message: str) -> None:
    """Print a step message in cyan."""
    print(colored(f"🔧 {message}", Colors.CYAN, bold=True))


def print_info(message: str) -> None:
    """Print an info message in blue."""
    print(colored(f"ℹ️  {message}", Colors.BLUE))


def print_success(message: str) -> None:
    """Print a success message in green."""
    print(colored(f"✅ {message}", Colors.GREEN, bold=True))


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    print(colored(f"⚠️  {message}", Colors.YELLOW, bold=True))


def print_error(message: str) -> None:
    """Print an error message in red."""
    print(colored(f"❌ {message}", Colors.RED, bold=True))


def print_auto_mode(message: str) -> None:
    """Print an auto mode message in magenta."""
    print(colored(f"🤖 [AUTO MODE] {message}", Colors.MAGENTA))


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

# Auto mode can be activated by typing 'all' at any prompt
auto_mode = False


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def play_chime() -> None:
    """Play a system chime to alert the operator.
    
    This function attempts to play a system notification sound to alert the
    operator that input is required. It tries multiple methods across different
    operating systems for maximum compatibility.
    
    Purpose:
        - Provides audio notification when operator input is needed
        - Helps operators notice prompts in noisy environments
        - Works across different operating systems
        
    Behavior:
        - Tries Windows system beep first (most common in lab environments)
        - Falls back to terminal bell character for Unix-like systems
        - Fails gracefully if no audio method is available
    """
    try:
        # Try Windows system beep
        if sys.platform.startswith('win'):
            import winsound
            winsound.Beep(800, 500)  # 800Hz for 500ms
        else:
            # Fallback to terminal bell for Unix-like systems
            print('\a', end='', flush=True)
    except ImportError:
        # winsound not available, use terminal bell
        print('\a', end='', flush=True)
    except Exception:
        # No audio available, continue silently
        pass


def prompt_wait(message: str) -> None:
    """Prompt the user and wait for confirmation.
    
    This function displays a message to the operator and waits for them to
    press Enter, ensuring they have time to physically set up test conditions
    before the automated measurement begins.
    
    Args:
        message (str): Instructions to display to the operator
        
    Purpose:
        - Provides human-in-the-loop control for physical test setup
        - Ensures proper test conditions before data collection
        - Allows operator to verify connections and configurations
        - Type 'all' at any prompt to enable auto mode for remaining tests
    """
    global auto_mode
    
    if auto_mode:
        print_auto_mode(message)
        print_auto_mode("Continuing automatically...")
        time.sleep(0.5)  # Brief pause for readability
        return
    
    play_chime()  # Alert operator that input is needed
    prompt_text = colored(f"{message}", Colors.CYAN, bold=True)
    hint_text = colored("(or type 'all' for auto mode)", Colors.YELLOW)
    user_input = input(f"{prompt_text}\nPress Enter when ready {hint_text}...")
    
    # Check if user wants to switch to auto mode
    if user_input.strip().lower() == 'all':
        auto_mode = True
        print(f"\n{colored('*** SWITCHING TO AUTO MODE ***', Colors.MAGENTA, bold=True)}")
        print_auto_mode("No more operator prompts or audio alerts will be played.")
        print_auto_mode("The test will continue automatically through all conditions.")
        print()


def cooldown_wait(seconds: float) -> None:
    """Display a simple countdown while waiting for test loads to cool.
    
    When testing with real SMA muscles or power resistors, thermal effects can 
    influence subsequent measurements. This function provides a visual countdown 
    to ensure adequate cooling time between tests.
    
    Args:
        seconds (float): Cooldown duration in seconds
        
    Purpose:
        - Prevents thermal carryover effects between tests
        - Ensures consistent starting conditions for each measurement
        - Provides visual feedback to operator during wait periods
        
    Behavior:
        - Displays countdown timer with remaining seconds
        - Updates display in real-time
        - Returns immediately if seconds <= 0
    """

    if seconds <= 0:
        return
    
    # Convert to integer for countdown display
    seconds_int = int(seconds)
    print_info(f"Waiting {seconds}s for cooldown...")
    for remaining in range(seconds_int, 0, -1):
        countdown_text = colored(f"  ⏱️  {remaining}s remaining", Colors.YELLOW)
        print(countdown_text, end="\r", flush=True)
        time.sleep(1)
    print(colored("  ✅ Cooldown complete", Colors.GREEN))
    print()


def ensure_dir(path: Path) -> None:
    """Create directory structure if it doesn't exist.
    
    Args:
        path (Path): Directory path to create
        
    Purpose:
        - Ensures output directories exist before writing files
        - Creates parent directories as needed
        - Handles existing directories gracefully
    """
    path.mkdir(parents=True, exist_ok=True)


def check_node_active_status(node: tf.Node) -> bool:
    """Check if the ThermoFlex node is still active and communicating.
    
    This function verifies that the node is still responding and in an active
    state before proceeding with tests. If the node becomes unresponsive or
    reports an inactive status, testing should be halted.
    
    Args:
        node (tf.Node): ThermoFlex node object to check
        
    Returns:
        bool: True if node is active and responding, False otherwise
        
    Purpose:
        - Prevents attempting tests on disconnected or failed nodes
        - Provides early detection of communication failures
        - Ensures test data integrity by validating node state
        
    Behavior:
        - Requests fresh status from node
        - Checks node active status flag
        - Returns False if any communication errors occur
    """
    try:
        # Request fresh status to ensure we have current information
        node.status("dump", device="all")
        time.sleep(0.1)  # Brief pause for status update
        
        # Check if node reports as active
        is_active = node.get_node_active_status()
        return is_active
    except Exception as e:
        print_error(f"Error checking node status: {e}")
        return False


# ---------------------------------------------------------------------------
# Data capture helpers
# ---------------------------------------------------------------------------


def sample_loop(
    node: tf.Node,
    muscle: tf.Muscle,
    setpoint_func: Callable[[float], float],
    duration: float,
    interval: float,
    csv_path: Path,
    context: dict[str, str],
) -> None:
    """Generic sampling loop used by all waveform tests.
    
    This is the core data collection function that executes a single test
    condition. It applies a time-varying setpoint to the muscle controller
    and captures sensor data at regular intervals.
    
    Args:
        node (tf.Node): ThermoFlex node object for status queries
        muscle (tf.Muscle): Specific muscle port being tested
        setpoint_func (Callable): Function that returns PWM setpoint vs time
                                 Signature: setpoint_func(elapsed_time) -> pwm_percent
        duration (float): Total test duration in seconds
        interval (float): Time between sensor readings in seconds
        csv_path (Path): Output file path for this test's data
        context (dict): Test condition metadata (supply, load, waveform type)
        
    Purpose:
        - Executes a single test condition with time-series data collection
        - Applies dynamic setpoints (static or ramped) to muscle controller
        - Captures comprehensive sensor data for validation analysis
        - Ensures consistent data format across all test conditions
        
    Data Collection Process:
        1. Set up CSV file with standardized headers
        2. For each time step:
           a. Calculate setpoint based on elapsed time
           b. Apply setpoint to muscle controller
           c. Enable muscle for measurement
           d. Request fresh status from node
           e. Read all sensor values using accessor methods
           f. Calculate derived values (load voltage)
           g. Write timestamped data row to CSV
        3. Disable muscle after test completion
        
    CSV Output Columns:
        - timestamp: Unix timestamp of measurement
        - node_id: Node identifier string
        - firmware: Node firmware version
        - port: Muscle port number
        - supply_cond: Power supply condition (no_power, 11v, 22v)
        - load_cond: Load condition (open, muscle, resistor)
        - waveform: Waveform type (pwm_20, pwm_50, pwm_80, pwm_ramp)
        - setpoint_pct: PWM setpoint percentage
        - supply_v: Supply voltage measurement
        - load_v: Calculated load voltage (supply - voltage drop)
        - current_a: Load current measurement
        - resistance_mohms: Load resistance measurement
        - enabled: Muscle enable status
    """

    try:
        with csv_path.open("w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            # Write standardized CSV header for all test conditions
            writer.writerow(
                [
                    "timestamp",
                    "node_id",
                    "firmware",
                    "port",
                    "supply_cond",
                    "load_cond",
                    "waveform",
                    "setpoint_pct",
                    "supply_v",
                    "load_v",
                    "current_a",
                    "resistance_mohms",
                    "enabled",
                ]
            )
            csvfile.flush()

            start = time.time()
            next_sample_time = start
            
            while time.time() - start < duration:
                # Calculate when this sample should be taken for consistent timing
                sample_start_time = time.time()
                elapsed = sample_start_time - start
                
                # Calculate setpoint based on waveform function (static or dynamic)
                setpoint = setpoint_func(elapsed)
                
                # Configure muscle controller for this measurement
                muscle.setSetpoint(conmode="percent", setpoint=setpoint)
                muscle.setEnable(True)

                # Request fresh sensor data from node
                node.status("compact", device="all")
                time.sleep(0.05)  # Brief wait for status response

                # Collect sensor readings using clean accessor methods
                supply_v = node.get_supply_voltage()
                vdrop = muscle.get_voltage_drop()
                
                # Calculate load voltage (voltage actually applied to load)
                # This is critical for understanding actual power delivery
                load_v = (
                    (supply_v - vdrop)
                    if supply_v is not None and vdrop is not None
                    else None
                )
                
                current = muscle.get_current()
                resistance = muscle.get_resistance()
                enabled = muscle.is_enabled()

                # Write timestamped data row with all measurements and metadata
                writer.writerow(
                    [
                        time.time(),
                        node.get_node_id_string(),
                        node.get_firmware_version(),
                        muscle.get_port_number(),
                        context["supply"],
                        context["load"],
                        context["waveform"],
                        setpoint,
                        supply_v,
                        load_v,
                        current,
                        resistance,
                        enabled,
                    ]
                )
                csvfile.flush()

                # Calculate time spent on processing and sleep only for remaining interval
                processing_time = time.time() - sample_start_time
                sleep_time = max(0, interval - processing_time)
                time.sleep(sleep_time)

    finally:
        # Safety: Always disable muscle, even if an exception occurs
        muscle.setEnable(False)


# ---------------------------------------------------------------------------
# Waveform implementations
# ---------------------------------------------------------------------------


def static_pwm(level: float) -> Callable[[float], float]:
    """Create a static PWM waveform function.
    
    Returns a function that provides constant PWM output for steady-state
    measurements. Used for testing sensor accuracy at fixed power levels.
    
    Args:
        level (float): PWM percentage (0-100) to maintain throughout test
        
    Returns:
        Callable: Function that returns constant PWM level regardless of time
        
    Purpose:
        - Enables steady-state measurements for sensor calibration
        - Tests controller stability at fixed setpoints
        - Provides baseline measurements for comparison
        
    Usage Example:
        pwm_func = static_pwm(50.0)  # 50% PWM
        setpoint = pwm_func(elapsed_time)  # Always returns 50.0
    """
    return lambda _elapsed: level


def pwm_ramp(start: float, end: float, ramp_time: float) -> Callable[[float], float]:
    """Create a linear PWM ramp waveform function.
    
    Returns a function that linearly interpolates PWM from start to end value
    over the specified time period. Used for testing dynamic response and
    thermal characteristics of the system.
    
    Args:
        start (float): Initial PWM percentage
        end (float): Final PWM percentage
        ramp_time (float): Time in seconds to complete the ramp
        
    Returns:
        Callable: Function that returns PWM value based on elapsed time
        
    Purpose:
        - Tests dynamic response characteristics
        - Evaluates thermal effects during power transitions
        - Captures system behavior under changing load conditions
        - Validates controller response to setpoint changes
        
    Behavior:
        - Returns start value for elapsed < 0
        - Linear interpolation between start and end for 0 <= elapsed < ramp_time
        - Returns end value for elapsed >= ramp_time
        
    Usage Example:
        ramp_func = pwm_ramp(0.0, 100.0, 5.0)  # 0% to 100% over 5 seconds
        setpoint = ramp_func(2.5)  # Returns 50.0 at halfway point
    """
    def func(elapsed: float) -> float:
        if elapsed >= ramp_time:
            return end
        # Linear interpolation with bounds checking
        frac = max(0.0, min(1.0, elapsed / ramp_time))
        return start + (end - start) * frac

    return func


# ---------------------------------------------------------------------------
# Main validation flow
# ---------------------------------------------------------------------------


def run_validation_flow(
    duration: float = 6.0,
    interval: float = 0.1,
    cooldown: float = 30.0,
    outdir: Path | str = "test/out",
) -> None:
    """Execute the complete validation flow across all test conditions.
    
    This is the main orchestration function that guides the operator through
    a comprehensive series of validation tests. It systematically tests every
    combination of supply conditions, load conditions, muscle ports, and
    waveform types.
    
    Args:
        duration (float): Duration of each individual test in seconds
        interval (float): Time between sensor readings within each test
        cooldown (float): Cooldown time in seconds when testing with muscles
                         (resistors use half this time for their cooldown)
        outdir (Path | str): Base output directory for test results
        
    Purpose:
        - Provides comprehensive validation of sensor accuracy and consistency
        - Tests controller behavior under various operating conditions
        - Generates systematic data for cross-controller comparison
        - Ensures reproducible test conditions through operator guidance
        
    Test Matrix Overview:
        SUPPLY CONDITIONS (3):
        - no_power: USB power only (typically ~5V)
        - 11v: Single LiPo battery (11.1V nominal)
        - 22v: Dual LiPo battery (22.2V nominal)
        
        LOAD CONDITIONS (3):
        - open: No load connected (measures controller baseline)
        - muscle: ThermoFlex Mk.1 SMA muscle (real-world load)
        - resistor: Known power resistor (calibrated reference)
        
        MUSCLE PORTS (2):
        - Port 0: First muscle output
        - Port 1: Second muscle output
        
        WAVEFORMS (4 per condition):
        - Static PWM at 20%, 50%, 80% (steady-state measurements)
        - Linear ramp 0% to 100% (dynamic response)
        
        Total Tests: 3 × 3 × 2 × 4 = 72 individual test runs
        
    Data Organization:
        - Creates timestamped output directory: {node_id}_{timestamp}
        - One CSV file per test condition
        - metadata.csv with node info and operator comments
        - Systematic filename convention for easy analysis
        
    Operator Interaction:
        - Prompts for each physical configuration change
        - Waits for confirmation before starting each test
        - Provides clear instructions for setup
        - Allows comments for test documentation
        
    Safety Features:
        - Always disables muscles after each test
        - Provides cooldown periods for thermal management
        - Confirms setup before starting measurements
        - Checks node active status before each test
        - Exits gracefully if node becomes unresponsive
        - Logs failed tests to metadata for debugging
    """
    
    # Initialize connection to ThermoFlex node
    node = tf.get_usb_node(timeout=10.0)
    node.status("dump", device="all") # dump for extra info
    time.sleep(1) # wait for status to update
    node_id = node.get_node_id_string()
    firmware = node.get_firmware_version()
    board = node.get_board_version()

    # Create timestamped output directory for this validation run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(outdir) / f"{node_id}_{timestamp}"
    ensure_dir(run_dir)

    # Write metadata file with node information and test parameters
    meta_path = run_dir / "metadata.csv"
    with meta_path.open("w", newline="") as metafile:
        writer = csv.writer(metafile)
        writer.writerow(["key", "value"])
        writer.writerow(["timestamp", timestamp])
        writer.writerow(["node_id", node_id])
        writer.writerow(["firmware_version", firmware])
        writer.writerow(["board_version", board])

    print_success(f"Output directory: {run_dir}")
    print_info(f"Node ID: {node_id}")
    print_info(f"Firmware: {firmware}")
    print(colored("Type 'all' at any prompt to switch to auto mode.", Colors.YELLOW))
    print()

    # Track any failed tests for metadata logging
    failed_tests = []

    # Define test matrix - all combinations will be tested systematically
    
    # Test both muscle ports (typically 0 and 1)
    ports = [0, 1]
    
    # Supply voltage conditions - tests power supply effects on measurements
    supply_conditions = [
        ("no_power", "Ensure only USB power is connected (no battery)."),
        ("11v", "Connect the 11.1V battery input."),
        ("22v", "Connect the 22.2V battery input."),
    ]
    
    # Load conditions - tests different electrical loads
    load_conditions = [
        ("open", "No load connected"),  # Baseline/no-load measurements
        ("muscle", "Connect TF Mk.1 muscle"),  # Real-world SMA muscle load
        ("resistor", "Connect known power resistor > 300 mOhms"),  # Calibrated reference load
    ]
    
    # Static PWM test levels - steady-state measurements at different power levels
    pwm_levels = [20.0, 50.0, 80.0]

    # MAIN TEST LOOP: Iterate through all combinations systematically
    # Outer loop: Supply conditions (requires operator to change power connections)
    for supply, supply_msg in supply_conditions:
        prompt_wait(f"Set supply condition: {supply_msg}")

        # Middle loop: Muscle ports (tests both outputs on the node)
        for port in ports:
            # Get muscle object for this port (handle different muscle container types)
            muscle = (
                node.muscles[str(port)]
                if isinstance(node.muscles, dict)
                else node.muscles[port]
            )
            
            # Inner loop: Load conditions (requires operator to change physical load)
            for load, load_msg in load_conditions:
                prompt_wait(f"Port {port}: {load_msg}")

                # STATIC PWM TESTS: Test steady-state behavior at fixed power levels
                for level in pwm_levels:
                    # Check node status before each test
                    if not check_node_active_status(node):
                        test_name = f"port{port}_{supply}_{load}_pwm{int(level)}"
                        failed_tests.append(test_name)
                        print_error(f"Node is not active! Aborting test: {test_name}")
                        print_warning("Node has become unresponsive or reported inactive status.")
                        print_warning("Please check node connection and power before retrying.")
                        
                        # Write failed test info to metadata and exit
                        with meta_path.open("a", newline="") as metafile:
                            writer = csv.writer(metafile)
                            writer.writerow(["failed_test", test_name])
                            writer.writerow(["failure_reason", "Node inactive or unresponsive"])
                        
                        print_info(f"Partial results saved to: {run_dir}")
                        return  # Exit the entire validation flow
                    
                    context = {
                        "supply": supply,
                        "load": load,
                        "waveform": f"pwm_{int(level)}",
                    }
                    csv_file = (
                        run_dir / f"port{port}_{supply}_{load}_pwm{int(level)}.csv"
                    )
                    print_step(f"Running PWM {level}% test -> {csv_file.name}")
                    
                    # Execute test with static PWM waveform
                    sample_loop(
                        node,
                        muscle,
                        static_pwm(level),
                        duration,
                        interval,
                        csv_file,
                        context,
                    )
                    
                    # Cooldown needed when testing with loads that can heat up
                    # (prevents thermal effects from affecting subsequent tests)
                    if load == "muscle":
                        cooldown_wait(cooldown)
                    elif load == "resistor":
                        # Power resistors also heat up and need cooldown time
                        cooldown_wait(cooldown / 2)  # Half the muscle cooldown time

                # DYNAMIC PWM RAMP TEST: Test response to changing power levels
                # Check node status before ramp test
                if not check_node_active_status(node):
                    test_name = f"port{port}_{supply}_{load}_ramp"
                    failed_tests.append(test_name)
                    print_error(f"Node is not active! Aborting test: {test_name}")
                    print_warning("Node has become unresponsive or reported inactive status.")
                    print_warning("Please check node connection and power before retrying.")
                    
                    # Write failed test info to metadata and exit
                    with meta_path.open("a", newline="") as metafile:
                        writer = csv.writer(metafile)
                        writer.writerow(["failed_test", test_name])
                        writer.writerow(["failure_reason", "Node inactive or unresponsive"])
                    
                    print_info(f"Partial results saved to: {run_dir}")
                    return  # Exit the entire validation flow
                
                context = {
                    "supply": supply,
                    "load": load,
                    "waveform": "pwm_ramp",
                }
                ramp_file = run_dir / f"port{port}_{supply}_{load}_ramp.csv"
                print_step(f"Running PWM ramp test -> {ramp_file.name}")
                
                # Execute test with linear ramp from 0% to 100% PWM
                sample_loop(
                    node,
                    muscle,
                    pwm_ramp(0.0, 100.0, duration),
                    duration,
                    interval,
                    ramp_file,
                    context,
                )
                
                # Cooldown after ramp test if using loads that heat up
                if load == "muscle":
                    cooldown_wait(cooldown)
                elif load == "resistor":
                    # Power resistors also heat up during ramp tests
                    cooldown_wait(cooldown/2)  # Half the muscle cooldown time

    # Collect operator comments for test documentation
    comment = input("\nEnter any comments about this test run (optional): ")
    
    # Write final metadata including test completion status
    with meta_path.open("a", newline="") as metafile:
        writer = csv.writer(metafile)
        writer.writerow(["user_comment", comment])
        writer.writerow(["auto_mode_used", "yes" if auto_mode else "no"])
        
        # Record test completion status
        if failed_tests:
            writer.writerow(["failed_test", "; ".join(failed_tests)])
        else:
            writer.writerow(["failed_test", "none"])

    print_success(f"Validation flow complete! Files saved to: {run_dir}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comprehensive node validation flow")
    parser.add_argument(
        "--duration",
        type=float,
        default=6.0,
        help="Duration of each waveform test in seconds",
    )
    parser.add_argument(
        "--interval", type=float, default=0.1, help="Sampling interval in seconds"
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=30.0,
        help="Cooldown time in seconds when using a muscle load",
    )
    parser.add_argument("--outdir", default="test/out", help="Base output directory")

    args = parser.parse_args()

    run_validation_flow(
        duration=args.duration,
        interval=args.interval,
        cooldown=args.cooldown,
        outdir=args.outdir,
    )
