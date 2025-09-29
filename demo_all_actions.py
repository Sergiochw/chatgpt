"""Hands-off demonstration that iterates through every turtle action."""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import Dict

import turtle

from turtle_actions import (
    ACTIONS_INDEX,
    DemoAction,
    TurtleActions,
    configure_logging,
    detect_dry_run,
    get_demo_action,
)

EVENT_METHODS = {"onclick", "onrelease", "ondrag"}
REFERENCE_FILE = Path("turtle_actions_reference.md")


def write_reference_markdown() -> None:
    """Generate a Markdown cheat sheet from :data:`ACTIONS_INDEX`."""

    lines = ["# Turtle Actions Reference", ""]
    for category, entries in ACTIONS_INDEX.items():
        lines.append(f"## {category}")
        lines.append("\n| Method | Summary |\n| --- | --- |")
        for name, summary in entries:
            canonical = name
            lines.append(f"| ``{canonical}`` | {summary} |")
        lines.append("")
    REFERENCE_FILE.write_text("\n".join(lines), encoding="utf-8")


def demonstrate_action(actions: TurtleActions, action: DemoAction, stamp_state: Dict[str, int]) -> None:
    method = getattr(actions, action.name)
    args = list(action.args)
    kwargs = dict(action.kwargs)
    if action.name == "clearstamp":
        stamp_id = stamp_state.get("last_stamp", 0)
        if stamp_id:
            args = [stamp_id]
        else:
            logging.info("Skipping clearstamp demonstration until a stamp exists")
            return
    if action.name == "clearstamps":
        stamp_state.pop("last_stamp", None)
    try:
        result = method(*args, **kwargs)
    except RuntimeError as exc:
        logging.warning("Skipping %s: %s", action.name, exc)
        return
    if action.name == "stamp" and result is not None:
        stamp_state["last_stamp"] = int(result)
    label = f"{action.name}({', '.join([repr(a) for a in args])}{', ' if kwargs else ''}{', '.join(f'{k}={v!r}' for k, v in kwargs.items())})"
    logging.info("Executed %s", label.rstrip("()"))
    if action.expect_result:
        print(f"{action.name} -> {result}")
    else:
        print(f"{action.name} executed")


def bind_events(actions: TurtleActions) -> None:
    logging.info("Binding event handlers for 10 seconds")

    def handler(x: float, y: float, action: str) -> None:
        logging.info("Event %s at (%.1f, %.1f)", action, x, y)

    actions.onclick(lambda x, y: handler(x, y, "onclick"))
    actions.onrelease(lambda x, y: handler(x, y, "onrelease"))
    actions.ondrag(lambda x, y: handler(x, y, "ondrag"))


def unbind_events(actions: TurtleActions) -> None:
    logging.info("Unbinding events")
    actions.onclick(None)
    actions.onrelease(None)
    actions.ondrag(None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode")
    args = parser.parse_args()

    configure_logging(debug=args.debug)
    detected_dry, reason = detect_dry_run()
    dry_run = args.dry_run or detected_dry
    if dry_run and reason:
        logging.info("Running in DRY-RUN mode: %s", reason)

    write_reference_markdown()
    logging.info("Reference documentation written to %s", REFERENCE_FILE)

    screen = None
    if not dry_run:
        screen = turtle.Screen()
        screen.title("Turtle Actions Demo")

    actions = TurtleActions(dry_run=dry_run)
    stamp_state: Dict[str, int] = {}

    for category, entries in ACTIONS_INDEX.items():
        print(f"\n=== {category} ===")
        for name, _summary in entries:
            if name in EVENT_METHODS:
                continue
            action = get_demo_action(name)
            demonstrate_action(actions, action, stamp_state)

    print("\nBinding event handlers for ~10 seconds...")
    bind_events(actions)
    if dry_run:
        time.sleep(10)
        unbind_events(actions)
        print("Dry-run complete; call history length:", len(actions.call_history))
    else:
        assert screen is not None
        screen.ontimer(lambda: unbind_events(actions), 10_000)
        screen.listen()
        print("Close the window or click once after the timer to exit.")
        screen.exitonclick()

    logging.info("Demo complete")


if __name__ == "__main__":
    main()
