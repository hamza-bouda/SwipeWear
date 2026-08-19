#!/usr/bin/env python3
"""Run a one-shot backend command as a resilient periodic service.

This supervisor lets ingestion, indexing, alert matching and notification
delivery remain independent containers without introducing a queue framework.
It never overlaps two executions of the same job.
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_LOG = logging.getLogger("swipewear.service_runner")


def seconds_until_daily_run(now: datetime, hour: int, minute: int) -> float:
    """Return the delay until the next local wall-clock execution."""
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _run(command: list[str]) -> None:
    _LOG.info("Starting: %s", " ".join(command))
    completed = subprocess.run(command, check=False)
    if completed.returncode:
        _LOG.error("Command exited with status %d", completed.returncode)
    else:
        _LOG.info("Command completed successfully")


def run_interval(command: list[str], seconds: float, run_immediately: bool) -> None:
    if not run_immediately:
        time.sleep(seconds)
    while True:
        _run(command)
        time.sleep(seconds)


def run_daily(command: list[str], at: str, timezone: str) -> None:
    try:
        hour, minute = (int(part) for part in at.split(":", 1))
    except (ValueError, TypeError) as exc:
        raise ValueError("--at must use HH:MM") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("--at must use a valid HH:MM time")
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {timezone}") from exc

    while True:
        delay = seconds_until_daily_run(datetime.now(tz), hour, minute)
        _LOG.info("Next execution in %.0f seconds", delay)
        time.sleep(delay)
        _run(command)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    interval = subparsers.add_parser("interval")
    interval.add_argument("--seconds", type=float, required=True)
    interval.add_argument("--no-immediate", action="store_true")
    interval.add_argument("command", nargs=argparse.REMAINDER)
    daily = subparsers.add_parser("daily")
    daily.add_argument("--at", required=True, help="local time as HH:MM")
    daily.add_argument("--timezone", default="Europe/Paris")
    daily.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    args = _parser().parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("ERROR: a command is required after --", file=sys.stderr)
        return 2

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s %(message)s",
    )
    if args.mode == "interval":
        if args.seconds <= 0:
            print("ERROR: --seconds must be positive", file=sys.stderr)
            return 2
        run_interval(command, args.seconds, not args.no_immediate)
    else:
        try:
            run_daily(command, args.at, args.timezone)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
