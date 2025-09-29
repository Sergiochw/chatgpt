"""Interactive control panel for stepping through turtle actions."""
from __future__ import annotations

import argparse
import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, List

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


class TkLogHandler(logging.Handler):
    """Route logging records into a Tkinter text widget."""

    def __init__(self, widget: tk.Text):
        super().__init__()
        self.widget = widget

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - UI only.
        message = self.format(record) + "\n"
        self.widget.after(0, self._append, message)

    def _append(self, message: str) -> None:
        self.widget.configure(state=tk.NORMAL)
        self.widget.insert(tk.END, message)
        self.widget.see(tk.END)
        self.widget.configure(state=tk.DISABLED)


class TurtleControlApp:
    """Wrap a Tk application that controls :class:`TurtleActions`."""

    def __init__(self, root: tk.Tk, *, dry_run: bool) -> None:
        self.root = root
        self.dry_run = dry_run
        self.root.title("Turtle Actions Control Panel")
        self.playing = False
        self.speed_value = 5
        self.current_index = 0
        self.stamp_state: Dict[str, int] = {}

        self.sequence: List[DemoAction] = []
        for category, entries in ACTIONS_INDEX.items():
            for name, _summary in entries:
                if name in EVENT_METHODS:
                    continue
                self.sequence.append(get_demo_action(name))

        self._build_ui()
        self._setup_logging()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        canvas_frame = ttk.Frame(main)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        control_frame = ttk.Frame(main)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(canvas_frame, width=500, height=500, background="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        if not self.dry_run:
            self.screen = turtle.TurtleScreen(self.canvas)
            self.screen.title("Embedded Turtle")
            self.screen.tracer(1, 10)
            self._raw_turtle = turtle.RawTurtle(self.screen)
            self.actions = TurtleActions(turtle_obj=self._raw_turtle)
        else:
            self.screen = None
            self._raw_turtle = None
            self.actions = TurtleActions(dry_run=True)

        buttons = ttk.Frame(control_frame)
        buttons.pack(fill=tk.X)

        self.play_button = ttk.Button(buttons, text="Play", command=self.toggle_play)
        self.play_button.pack(fill=tk.X, pady=2)

        self.step_button = ttk.Button(buttons, text="Step", command=self.step_once)
        self.step_button.pack(fill=tk.X, pady=2)

        self.reset_button = ttk.Button(buttons, text="Reset", command=self.reset)
        self.reset_button.pack(fill=tk.X, pady=2)

        speed_label = ttk.Label(control_frame, text="Speed")
        speed_label.pack(pady=(10, 2))
        self.speed_slider = ttk.Scale(control_frame, from_=1, to=10, orient=tk.HORIZONTAL, command=self._on_speed_change)
        self.speed_slider.set(self.speed_value)
        self.speed_slider.pack(fill=tk.X)

        log_label = ttk.Label(control_frame, text="Log")
        log_label.pack(pady=(10, 2))
        log_frame = ttk.Frame(control_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_frame, width=40, height=20, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self._bind_keys()

    def _setup_logging(self) -> None:
        handler = TkLogHandler(self.log_text)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logging.getLogger().addHandler(handler)

    def _bind_keys(self) -> None:
        self.root.bind("<space>", lambda _event: self.toggle_play())
        self.root.bind("s", lambda _event: self.step_once())
        self.root.bind("S", lambda _event: self.step_once())
        self.root.bind("r", lambda _event: self.reset())
        self.root.bind("R", lambda _event: self.reset())
        self.root.bind("+", lambda _event: self._adjust_speed(1))
        self.root.bind("-", lambda _event: self._adjust_speed(-1))

    def _adjust_speed(self, delta: int) -> None:
        new_value = min(10, max(1, self.speed_value + delta))
        self.speed_slider.set(new_value)
        self.speed_value = new_value

    def _on_speed_change(self, _value: str) -> None:
        self.speed_value = int(float(_value))

    def toggle_play(self) -> None:
        self.playing = not self.playing
        self.play_button.configure(text="Pause" if self.playing else "Play")
        if self.playing:
            self._schedule_step()

    def _schedule_step(self) -> None:
        delay = int(1000 / max(1, self.speed_value))
        self.root.after(delay, self._auto_step)

    def _auto_step(self) -> None:
        if not self.playing:
            return
        finished = self.step_once()
        if not finished:
            self._schedule_step()
        else:
            self.playing = False
            self.play_button.configure(text="Play")

    def step_once(self) -> bool:
        if self.current_index >= len(self.sequence):
            logging.info("Demo sequence complete")
            return True
        action = self.sequence[self.current_index]
        self.current_index += 1
        args = list(action.args)
        kwargs = dict(action.kwargs)
        if action.name == "clearstamp":
            stamp_id = self.stamp_state.get("last_stamp", 0)
            if not stamp_id:
                logging.info("No stamp available yet; skipping clearstamp")
                return False
            args = [stamp_id]
            self.stamp_state.pop("last_stamp", None)
        if action.name == "clearstamps":
            self.stamp_state.clear()
        if action.name == "stamp":
            result = getattr(self.actions, action.name)(*args, **kwargs)
            if result is not None:
                self.stamp_state["last_stamp"] = int(result)
        else:
            try:
                result = getattr(self.actions, action.name)(*args, **kwargs)
            except RuntimeError as exc:
                logging.warning("Skipping %s: %s", action.name, exc)
                return False
        if action.expect_result:
            logging.info("%s -> %r", action.name, result)
        else:
            logging.info("%s executed", action.name)
        return self.current_index >= len(self.sequence)

    def reset(self) -> None:
        self.playing = False
        self.play_button.configure(text="Play")
        self.current_index = 0
        self.stamp_state.clear()
        self.actions.safe_reset()
        logging.info("Sequence reset")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode")
    args = parser.parse_args()

    configure_logging(debug=args.debug)
    detected_dry, reason = detect_dry_run()
    dry_run = args.dry_run or detected_dry
    if dry_run and reason:
        logging.info("Running control panel in DRY-RUN mode: %s", reason)

    root = tk.Tk()
    app = TurtleControlApp(root, dry_run=dry_run)
    root.mainloop()


if __name__ == "__main__":
    main()
