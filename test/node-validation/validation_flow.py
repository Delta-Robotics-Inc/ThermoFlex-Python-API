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
    """Prompt the user and wait for confirmation."""

    input(f"{message}\nPress Enter when ready...")


def cooldown_wait(seconds: int) -> None:
    """Display a simple countdown while waiting for the muscle to cool."""

    if seconds <= 0:
        return
    print(f"Waiting {seconds}s for cooldown...")
    for remaining in range(seconds, 0, -1):
        print(f"  {remaining}s remaining", end="\r", flush=True)
        time.sleep(1)
    print("  0s remaining")
    print()


def ensure_dir(path: Path) -> None:
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
    """Generic sampling loop used by all waveform tests."""

    with csv_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
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
            setpoint = setpoint_func(elapsed)
            muscle.setSetpoint(conmode="percent", setpoint=setpoint)
            muscle.setEnable(True)

            node.status("compact", device="all")
            time.sleep(0.05)

            supply_v = node.get_supply_voltage()
            vdrop = muscle.get_voltage_drop()
            load_v = (
                (supply_v - vdrop)
                if supply_v is not None and vdrop is not None
                else None
            )
            current = muscle.get_current()
            resistance = muscle.get_resistance()
            enabled = muscle.is_enabled()

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

            time.sleep(max(0, interval))

    muscle.setEnable(False)


# ---------------------------------------------------------------------------
# Waveform implementations
# ---------------------------------------------------------------------------


def static_pwm(level: float) -> Callable[[float], float]:
    return lambda _elapsed: level


def pwm_ramp(start: float, end: float, ramp_time: float) -> Callable[[float], float]:
    def func(elapsed: float) -> float:
        if elapsed >= ramp_time:
            return end
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
    node = tf.get_usb_node(timeout=10.0)
    node_id = node.get_node_id_string()
    firmware = node.get_firmware_version()
    board = node.get_board_version()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(outdir) / f"{node_id}_{timestamp}"
    ensure_dir(run_dir)

    # Write metadata
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

    ports = [0, 1]
    supply_conditions = [
        ("no_power", "Ensure only USB power is connected (no battery)."),
        ("11v", "Connect the 11.1V battery input."),
        ("22v", "Connect the 22.2V battery input."),
    ]
    load_conditions = [
        ("open", "No load connected"),
        ("muscle", "Connect TF Mk.1 muscle"),
        ("resistor", "Connect known power resistor"),
    ]
    pwm_levels = [20.0, 50.0, 80.0]

    for supply, supply_msg in supply_conditions:
        prompt_wait(f"Set supply condition: {supply_msg}")

        for port in ports:
            muscle = (
                node.muscles[str(port)]
                if isinstance(node.muscles, dict)
                else node.muscles[port]
            )
            for load, load_msg in load_conditions:
                prompt_wait(f"Port {port}: {load_msg}")

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
                    sample_loop(
                        node,
                        muscle,
                        static_pwm(level),
                        duration,
                        interval,
                        csv_file,
                        context,
                    )
                    if load == "muscle":
                        cooldown_wait(cooldown)

                # PWM ramp
                context = {
                    "supply": supply,
                    "load": load,
                    "waveform": "pwm_ramp",
                }
                ramp_file = run_dir / f"port{port}_{supply}_{load}_ramp.csv"
                print(f"Running PWM ramp test -> {ramp_file.name}")
                sample_loop(
                    node,
                    muscle,
                    pwm_ramp(0.0, 100.0, duration),
                    duration,
                    interval,
                    ramp_file,
                    context,
                )
                if load == "muscle":
                    cooldown_wait(cooldown)

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
