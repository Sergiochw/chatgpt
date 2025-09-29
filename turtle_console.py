"""Simple REPL for experimenting with :class:`turtle.Turtle` actions."""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import shlex
from pathlib import Path
from typing import Any, Tuple

from turtle_actions import ACTIONS_INDEX, TurtleActions, configure_logging, detect_dry_run

try:  # pragma: no cover - optional nicety for POSIX systems.
    import readline  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover - optional feature.
    pass

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
PROMPT = "turtle> "
HELP_HEADER = "Available turtle actions (aliases included):"


def format_help() -> str:
    lines = [HELP_HEADER]
    for category, entries in ACTIONS_INDEX.items():
        lines.append(f"\n[{category}]")
        for name, summary in entries:
            lines.append(f"  {name:<15} - {summary}")
    return "\n".join(lines)


def auto_cast(token: str) -> Any:
    lowered = token.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if token.startswith("0") and token != "0" and not token.startswith("0."):
            raise ValueError
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return token


def parse_command(line: str) -> Tuple[str, Tuple[Any, ...]]:
    parts = shlex.split(line)
    if not parts:
        return "", ()
    command = parts[0]
    args = tuple(auto_cast(part) for part in parts[1:])
    return command, args


def ensure_logger(recording: bool) -> logging.Handler | None:
    if not recording:
        return None
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    logfile = LOGS_DIR / f"session-{timestamp}.log"
    handler = logging.FileHandler(logfile, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(handler)
    logging.info("Recording session to %s", logfile)
    return handler


def repl(actions: TurtleActions) -> None:
    print("Type 'help' to list commands, 'quit' to exit.")
    recording_handler: logging.Handler | None = None
    recording_enabled = False
    help_text = format_help()

    while True:
        try:
            line = input(PROMPT)
        except EOFError:
            print()
            break
        command, args = parse_command(line)
        if not command:
            continue
        if command in {"quit", "exit"}:
            break
        if command == "help":
            print(help_text)
            continue
        if command == "record":
            if not args:
                print("Usage: record on|off")
                continue
            mode = str(args[0]).lower()
            if mode not in {"on", "off"}:
                print("record expects 'on' or 'off'")
                continue
            if mode == "on" and not recording_enabled:
                recording_handler = ensure_logger(True)
                recording_enabled = True
            elif mode == "off" and recording_enabled:
                assert recording_handler is not None
                logging.getLogger().removeHandler(recording_handler)
                recording_handler.close()
                recording_handler = None
                recording_enabled = False
                print("Recording stopped.")
            else:
                print(f"Recording already {mode}.")
            continue
        if not hasattr(actions, command):
            print(f"Unknown command: {command}")
            continue
        method = getattr(actions, command)
        try:
            result = method(*args)
        except RuntimeError as exc:
            print(f"Error: {exc}")
            continue
        except Exception as exc:  # pragma: no cover - runtime errors bubbled up.
            logging.exception("Command failed: %s", exc)
            print(f"Exception: {exc}")
            continue
        if result is not None:
            print(result)

    if recording_handler is not None:
        logging.getLogger().removeHandler(recording_handler)
        recording_handler.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode")
    args = parser.parse_args()

    configure_logging(debug=args.debug)
    detected_dry, reason = detect_dry_run()
    dry_run = args.dry_run or detected_dry
    if dry_run and reason:
        logging.info("Turtle console running in DRY-RUN mode: %s", reason)

    actions = TurtleActions(dry_run=dry_run)
    repl(actions)


if __name__ == "__main__":
    main()
