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
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import thermoflex as tf


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


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
    """

    input(f"{message}\nPress Enter when ready...")


def cooldown_wait(seconds: int) -> None:
    """Display a simple countdown while waiting for the muscle to cool.
    
    When testing with real SMA muscles, thermal effects can influence subsequent
    measurements. This function provides a visual countdown to ensure adequate
    cooling time between tests.
    
    Args:
        seconds (int): Cooldown duration in seconds
        
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
    print(f"Waiting {seconds}s for cooldown...")
    for remaining in range(seconds, 0, -1):
        print(f"  {remaining}s remaining", end="\r", flush=True)
        time.sleep(1)
    print("  0s remaining")
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
        while time.time() - start < duration:
            elapsed = time.time() - start
            
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

            # Maintain consistent sampling rate
            time.sleep(max(0, interval))

    # Safety: Always disable muscle after test completion
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
    cooldown: int = 30,
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
        cooldown (int): Cooldown time in seconds when testing with muscles
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
    """
    
    # Initialize connection to ThermoFlex node
    node = tf.get_usb_node(timeout=10.0)
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

    print(f"Output directory: {run_dir}")
    print(f"Node ID: {node_id}")
    print(f"Firmware: {firmware}\n")

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
                    context = {
                        "supply": supply,
                        "load": load,
                        "waveform": f"pwm_{int(level)}",
                    }
                    csv_file = (
                        run_dir / f"port{port}_{supply}_{load}_pwm{int(level)}.csv"
                    )
                    print(f"Running PWM {level}% test -> {csv_file.name}")
                    
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
                    
                    # Cooldown only needed when testing with real muscles
                    # (prevents thermal effects from affecting subsequent tests)
                    if load == "muscle":
                        cooldown_wait(cooldown)

                # DYNAMIC PWM RAMP TEST: Test response to changing power levels
                context = {
                    "supply": supply,
                    "load": load,
                    "waveform": "pwm_ramp",
                }
                ramp_file = run_dir / f"port{port}_{supply}_{load}_ramp.csv"
                print(f"Running PWM ramp test -> {ramp_file.name}")
                
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
                
                # Cooldown after ramp test if using real muscle
                if load == "muscle":
                    cooldown_wait(cooldown)

    # Collect operator comments for test documentation
    comment = input("\nEnter any comments about this test run (optional): ")
    with meta_path.open("a", newline="") as metafile:
        writer = csv.writer(metafile)
        writer.writerow(["user_comment", comment])

    print("Validation flow complete. Files saved to:", run_dir)


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
        type=int,
        default=30,
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
