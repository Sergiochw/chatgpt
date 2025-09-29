"""Core utilities for demonstrating the entire :mod:`turtle` action surface.

This module offers a :class:`TurtleActions` wrapper that mirrors the public
methods of :class:`turtle.Turtle` so we can document, log, and replay every
movement in both graphical and headless environments.
"""
from __future__ import annotations

import logging
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

try:  # pragma: no cover - importing is part of runtime detection.
    import tkinter  # type: ignore  # noqa: F401
    TK_AVAILABLE = True
except Exception:  # pragma: no cover - best effort detection.
    TK_AVAILABLE = False

import turtle

LOGGER_NAME = "turtle_actions"
logger = logging.getLogger(LOGGER_NAME)

PYTHON_VERSION = sys.version_info
TELEPORT_AVAILABLE = PYTHON_VERSION >= (3, 12)


@dataclass
class DemoAction:
    """A single scripted action used by demos and the control panel."""

    name: str
    args: Tuple[Any, ...] = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    expect_result: bool = False
    note: str | None = None


def configure_logging(debug: bool = False) -> None:
    """Configure module-wide logging.

    Parameters
    ----------
    debug:
        When ``True`` the root logger switches to ``DEBUG`` level, otherwise
        ``INFO``.
    """

    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")
    logger.debug("Logging initialised at %s", logging.getLevelName(level))


def detect_dry_run() -> tuple[bool, str | None]:
    """Return ``(dry_run, reason)`` based on environment availability."""

    if not TK_AVAILABLE:
        return True, "tkinter is unavailable"
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return True, "DISPLAY environment variable is not set"
    return False, None


def _summary_from_doc(name: str) -> str:
    """Return the first sentence of the turtle docstring for ``name``."""

    try:
        doc = getattr(turtle.Turtle, name).__doc__
    except AttributeError:
        if name == "teleport":
            return "Teleport the turtle without drawing (requires Python 3.12+)"
        raise
    if not doc:
        return "(no documentation available)"
    first_line = doc.strip().splitlines()[0].strip()
    return first_line.rstrip(".") + "."


# Canonical categories with aliases kept alongside to help with documentation.
_CANONICAL_DEFINITIONS: Dict[str, Dict[str, Sequence[str]]] = {
    "Motion": {
        "forward": ("fd",),
        "backward": ("bk", "back"),
        "right": ("rt",),
        "left": ("lt",),
        "goto": ("setpos", "setposition"),
        "teleport": tuple(),
        "setx": tuple(),
        "sety": tuple(),
        "setheading": ("seth",),
        "home": tuple(),
        "circle": tuple(),
        "dot": tuple(),
        "stamp": tuple(),
        "clearstamp": tuple(),
        "clearstamps": tuple(),
        "undo": tuple(),
        "speed": tuple(),
    },
    "State": {
        "position": ("pos",),
        "towards": tuple(),
        "xcor": tuple(),
        "ycor": tuple(),
        "heading": tuple(),
        "distance": tuple(),
    },
    "Measurement": {
        "degrees": tuple(),
        "radians": tuple(),
    },
    "Pen (drawing)": {
        "pendown": ("pd", "down"),
        "penup": ("pu", "up"),
        "pensize": tuple(),
        "width": tuple(),
        "pen": tuple(),
        "isdown": tuple(),
    },
    "Pen (color)": {
        "color": tuple(),
        "pencolor": tuple(),
        "fillcolor": tuple(),
    },
    "Pen (fill)": {
        "filling": tuple(),
        "begin_fill": tuple(),
        "end_fill": tuple(),
    },
    "Pen (more)": {
        "reset": tuple(),
        "clear": tuple(),
        "write": tuple(),
    },
    "Visibility": {
        "showturtle": ("st",),
        "hideturtle": ("ht",),
        "isvisible": tuple(),
    },
    "Appearance": {
        "shape": tuple(),
        "resizemode": tuple(),
        "shapesize": tuple(),
        "turtlesize": tuple(),
        "shearfactor": tuple(),
        "tiltangle": tuple(),
        "tilt": tuple(),
        "shapetransform": tuple(),
        "get_shapepoly": tuple(),
    },
    "Events": {
        "onclick": tuple(),
        "onrelease": tuple(),
        "ondrag": tuple(),
    },
    "Specials": {
        "begin_poly": tuple(),
        "end_poly": tuple(),
        "get_poly": tuple(),
        "clone": tuple(),
        "getturtle": tuple(),
        "getpen": tuple(),
        "getscreen": tuple(),
        "setundobuffer": tuple(),
        "undobufferentries": tuple(),
    },
}


def _build_actions_index() -> Dict[str, List[Tuple[str, str]]]:
    index: Dict[str, List[Tuple[str, str]]] = {}
    for category, mapping in _CANONICAL_DEFINITIONS.items():
        entries: List[Tuple[str, str]] = []
        for canonical, aliases in mapping.items():
            entries.append((canonical, _summary_from_doc(canonical)))
            for alias in aliases:
                entries.append((alias, _summary_from_doc(alias)))
        index[category] = entries
    return index


ACTIONS_INDEX: Dict[str, List[Tuple[str, str]]] = _build_actions_index()
_ALL_ACTION_NAMES: List[str] = [name for entries in ACTIONS_INDEX.values() for name, _ in entries]
_CANONICAL_LOOKUP: Dict[str, str] = {}
for category in _CANONICAL_DEFINITIONS.values():
    for canonical, aliases in category.items():
        _CANONICAL_LOOKUP[canonical] = canonical
        for alias in aliases:
            _CANONICAL_LOOKUP[alias] = canonical


class _DryRunTurtle:
    """A lightweight turtle stand-in that records calls and mimics state."""

    def __init__(self, log: logging.Logger) -> None:
        self._log = log
        self._position = (0.0, 0.0)
        self._heading = 0.0
        self._isdown = True
        self._isvisible = True
        self._fill = False
        self._fullcircle = 360.0
        self._pensize = 1
        self._pencolor = "black"
        self._fillcolor = "white"
        self._shape = "classic"
        self._resizemode = "noresize"
        self._stretch_wid = 1.0
        self._stretch_len = 1.0
        self._outline = 1
        self._shear = 0.0
        self._tiltangle = 0.0
        self._speed = 3
        self._stamp_counter = 0
        self._poly_points: List[Tuple[float, float]] = []
        self._poly_recording = False
        self._undobuffer = 1000

    # --- helpers -----------------------------------------------------
    def _log_call(self, name: str, *args: Any, **kwargs: Any) -> None:
        self._log.info("DRY-RUN %s args=%s kwargs=%s", name, args, kwargs)

    def _move(self, distance: float) -> None:
        radians = math.radians(self._heading if self._fullcircle == 360.0 else math.degrees(self._heading))
        if self._fullcircle != 360.0:
            radians = self._heading
        dx = math.cos(radians) * distance
        dy = math.sin(radians) * distance
        x, y = self._position
        self._position = (x + dx, y + dy)
        if self._poly_recording:
            self._poly_points.append(self._position)

    def _set_position(self, x: float, y: float) -> None:
        self._position = (float(x), float(y))
        if self._poly_recording:
            self._poly_points.append(self._position)

    def _update_heading(self, angle: float) -> None:
        if self._fullcircle == 360.0:
            self._heading = (angle % 360.0)
        else:
            self._heading = angle

    # --- movement ----------------------------------------------------
    def forward(self, distance: float) -> None:
        self._log_call("forward", distance)
        self._move(float(distance))

    fd = forward

    def backward(self, distance: float) -> None:
        self._log_call("backward", distance)
        self._move(-float(distance))

    bk = backward
    back = backward

    def right(self, angle: float) -> None:
        self._log_call("right", angle)
        if self._fullcircle == 360.0:
            self._heading = (self._heading - float(angle)) % 360.0
        else:
            self._heading -= float(angle)

    rt = right

    def left(self, angle: float) -> None:
        self._log_call("left", angle)
        if self._fullcircle == 360.0:
            self._heading = (self._heading + float(angle)) % 360.0
        else:
            self._heading += float(angle)

    lt = left

    def goto(self, x: float | Tuple[float, float], y: Optional[float] = None) -> None:
        self._log_call("goto", x, y)
        if isinstance(x, (tuple, list)):
            x_val, y_val = x
        else:
            assert y is not None
            x_val, y_val = x, y
        self._set_position(float(x_val), float(y_val))

    setpos = goto
    setposition = goto

    def teleport(self, x: float | Tuple[float, float], y: Optional[float] = None) -> None:
        self._log_call("teleport", x, y)
        self.goto(x, y)

    def setx(self, x: float) -> None:
        self._log_call("setx", x)
        _, y = self._position
        self._set_position(float(x), y)

    def sety(self, y: float) -> None:
        self._log_call("sety", y)
        x, _ = self._position
        self._set_position(x, float(y))

    def setheading(self, angle: float) -> None:
        self._log_call("setheading", angle)
        self._update_heading(float(angle))

    seth = setheading

    def home(self) -> None:
        self._log_call("home")
        self._set_position(0.0, 0.0)
        self._update_heading(0.0)

    def circle(self, radius: float, extent: Optional[float] = None, steps: Optional[int] = None) -> None:
        self._log_call("circle", radius, extent, steps)

    def dot(self, size: Optional[float] = None, *color: Any) -> None:
        self._log_call("dot", size, color)

    def stamp(self) -> int:
        self._log_call("stamp")
        self._stamp_counter += 1
        return self._stamp_counter

    def clearstamp(self, stampid: int) -> None:
        self._log_call("clearstamp", stampid)

    def clearstamps(self, n: Optional[int] = None) -> None:
        self._log_call("clearstamps", n)
        if n is None:
            self._stamp_counter = 0
        elif n >= 0:
            self._stamp_counter = max(0, self._stamp_counter - n)

    def undo(self) -> None:
        self._log_call("undo")

    def speed(self, speed: Optional[int | float] = None) -> int | float:
        self._log_call("speed", speed)
        if speed is None:
            return self._speed
        self._speed = speed  # type: ignore[assignment]
        return self._speed

    # --- state queries ------------------------------------------------
    def position(self) -> Tuple[float, float]:
        self._log_call("position")
        return self._position

    pos = position

    def towards(self, x: float | Tuple[float, float], y: Optional[float] = None) -> float:
        self._log_call("towards", x, y)
        if isinstance(x, (tuple, list)):
            x_val, y_val = x
        else:
            assert y is not None
            x_val, y_val = x, y
        dx = x_val - self._position[0]
        dy = y_val - self._position[1]
        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360.0
        return angle

    def xcor(self) -> float:
        self._log_call("xcor")
        return self._position[0]

    def ycor(self) -> float:
        self._log_call("ycor")
        return self._position[1]

    def heading(self) -> float:
        self._log_call("heading")
        return self._heading

    def distance(self, x: float | Tuple[float, float], y: Optional[float] = None) -> float:
        self._log_call("distance", x, y)
        if isinstance(x, (tuple, list)):
            x_val, y_val = x
        else:
            assert y is not None
            x_val, y_val = x, y
        dx = x_val - self._position[0]
        dy = y_val - self._position[1]
        return math.hypot(dx, dy)

    # --- measurement --------------------------------------------------
    def degrees(self, fullcircle: float = 360.0) -> None:
        self._log_call("degrees", fullcircle)
        self._fullcircle = float(fullcircle)

    def radians(self) -> None:
        self._log_call("radians")
        self._fullcircle = 2 * math.pi

    # --- pen drawing --------------------------------------------------
    def pendown(self) -> None:
        self._log_call("pendown")
        self._isdown = True

    pd = pendown
    down = pendown

    def penup(self) -> None:
        self._log_call("penup")
        self._isdown = False

    pu = penup
    up = penup

    def pensize(self, width: Optional[float] = None) -> float:
        self._log_call("pensize", width)
        if width is None:
            return self._pensize
        self._pensize = float(width)
        return self._pensize

    def width(self, width: Optional[float] = None) -> float:
        self._log_call("width", width)
        return self.pensize(width)

    def pen(self, pen: Optional[Mapping[str, Any]] = None, **pendict: Any) -> Mapping[str, Any]:
        self._log_call("pen", pen, pendict)
        if pen:
            for key, value in pen.items():
                setattr(self, f"_{key}", value)
        for key, value in pendict.items():
            setattr(self, f"_{key}", value)
        return {
            "pensize": self._pensize,
            "pencolor": self._pencolor,
            "fillcolor": self._fillcolor,
            "speed": self._speed,
        }

    def isdown(self) -> bool:
        self._log_call("isdown")
        return self._isdown

    # --- pen colour ---------------------------------------------------
    def color(self, *args: Any) -> Tuple[str, str]:
        self._log_call("color", args)
        if not args:
            return self._pencolor, self._fillcolor
        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            pencolor, fillcolor = args[0]
        elif len(args) == 2:
            pencolor, fillcolor = args
        else:
            pencolor, fillcolor = args[0], args[0]
        self._pencolor = str(pencolor)
        self._fillcolor = str(fillcolor)
        return self._pencolor, self._fillcolor

    def pencolor(self, *args: Any) -> str:
        self._log_call("pencolor", args)
        if not args:
            return self._pencolor
        self._pencolor = str(args[0])
        return self._pencolor

    def fillcolor(self, *args: Any) -> str:
        self._log_call("fillcolor", args)
        if not args:
            return self._fillcolor
        self._fillcolor = str(args[0])
        return self._fillcolor

    # --- fill ---------------------------------------------------------
    def filling(self) -> bool:
        self._log_call("filling")
        return self._fill

    def begin_fill(self) -> None:
        self._log_call("begin_fill")
        self._fill = True

    def end_fill(self) -> None:
        self._log_call("end_fill")
        self._fill = False

    # --- pen extras ---------------------------------------------------
    def reset(self) -> None:
        self._log_call("reset")
        self.__init__(self._log)

    def clear(self) -> None:
        self._log_call("clear")

    def write(self, arg: Any, move: bool = False, align: str = "left", font: Tuple[str, int, str] = ("Arial", 8, "normal")) -> None:
        self._log_call("write", arg, move, align, font)

    # --- visibility ---------------------------------------------------
    def showturtle(self) -> None:
        self._log_call("showturtle")
        self._isvisible = True

    st = showturtle

    def hideturtle(self) -> None:
        self._log_call("hideturtle")
        self._isvisible = False

    ht = hideturtle

    def isvisible(self) -> bool:
        self._log_call("isvisible")
        return self._isvisible

    # --- appearance ---------------------------------------------------
    def shape(self, name: Optional[str] = None) -> str:
        self._log_call("shape", name)
        if name is not None:
            self._shape = str(name)
        return self._shape

    def resizemode(self, rmode: Optional[str] = None) -> str:
        self._log_call("resizemode", rmode)
        if rmode is not None:
            self._resizemode = str(rmode)
        return self._resizemode

    def shapesize(self, stretch_wid: Optional[float] = None, stretch_len: Optional[float] = None, outline: Optional[int] = None) -> Tuple[float, float, int]:
        self._log_call("shapesize", stretch_wid, stretch_len, outline)
        if stretch_wid is not None:
            self._stretch_wid = float(stretch_wid)
        if stretch_len is not None:
            self._stretch_len = float(stretch_len)
        if outline is not None:
            self._outline = int(outline)
        return self._stretch_wid, self._stretch_len, self._outline

    turtlesize = shapesize

    def shearfactor(self, shear: Optional[float] = None) -> float:
        self._log_call("shearfactor", shear)
        if shear is not None:
            self._shear = float(shear)
        return self._shear

    def tiltangle(self, angle: Optional[float] = None) -> float:
        self._log_call("tiltangle", angle)
        if angle is not None:
            self._tiltangle = float(angle)
        return self._tiltangle

    def tilt(self, angle: float) -> None:
        self._log_call("tilt", angle)
        self._tiltangle += float(angle)

    def shapetransform(self, t11: Optional[float] = None, t12: Optional[float] = None, t21: Optional[float] = None, t22: Optional[float] = None) -> Tuple[float, float, float, float]:
        self._log_call("shapetransform", t11, t12, t21, t22)
        return (1.0, 0.0, 0.0, 1.0)

    def get_shapepoly(self) -> List[Tuple[float, float]]:
        self._log_call("get_shapepoly")
        return [(0.0, 0.0)]

    # --- events -------------------------------------------------------
    def onclick(self, fun: Optional[Callable[..., Any]], btn: int = 1, add: Optional[bool] = None) -> None:
        self._log_call("onclick", fun, btn, add)

    def onrelease(self, fun: Optional[Callable[..., Any]], btn: int = 1) -> None:
        self._log_call("onrelease", fun, btn)

    def ondrag(self, fun: Optional[Callable[..., Any]], btn: int = 1, add: Optional[bool] = None) -> None:
        self._log_call("ondrag", fun, btn, add)

    # --- specials -----------------------------------------------------
    def begin_poly(self) -> None:
        self._log_call("begin_poly")
        self._poly_points = [self._position]
        self._poly_recording = True

    def end_poly(self) -> None:
        self._log_call("end_poly")
        self._poly_recording = False

    def get_poly(self) -> List[Tuple[float, float]]:
        self._log_call("get_poly")
        return list(self._poly_points)

    def clone(self) -> "_DryRunTurtle":
        self._log_call("clone")
        clone = _DryRunTurtle(self._log)
        clone._position = self._position
        clone._heading = self._heading
        clone._pensize = self._pensize
        clone._pencolor = self._pencolor
        clone._fillcolor = self._fillcolor
        return clone

    def getturtle(self) -> "_DryRunTurtle":
        self._log_call("getturtle")
        return self

    def getpen(self) -> "_DryRunTurtle":
        self._log_call("getpen")
        return self

    def getscreen(self) -> None:
        self._log_call("getscreen")
        return None

    def setundobuffer(self, size: Optional[int]) -> None:
        self._log_call("setundobuffer", size)
        if size is not None:
            self._undobuffer = int(size)

    def undobufferentries(self) -> int:
        self._log_call("undobufferentries")
        return self._undobuffer


def safe_demo_defaults() -> Dict[str, Any]:
    """Return conservative demo defaults shared by all entry points."""

    return {
        "distance": 60.0,
        "short_distance": 30.0,
        "angle": 45.0,
        "radius": 40.0,
        "dot_size": 12,
        "write_text": "Hello Turtle",
        "write_font": ("Arial", 12, "normal"),
        "position": (80.0, 40.0),
        "teleport_position": (-40.0, 80.0),
        "second_position": (-60.0, -30.0),
        "stamp_repetitions": 2,
    }


def _demo_arguments(defaults: Mapping[str, Any]) -> Dict[str, DemoAction]:
    dist = defaults["distance"]
    short = defaults["short_distance"]
    angle = defaults["angle"]
    radius = defaults["radius"]
    dot_size = defaults["dot_size"]
    pos = defaults["position"]
    tele_pos = defaults["teleport_position"]
    second_pos = defaults["second_position"]
    font = defaults["write_font"]
    text = defaults["write_text"]
    stamp_reps = defaults["stamp_repetitions"]

    demo: Dict[str, DemoAction] = {
        "forward": DemoAction("forward", (dist,), {}),
        "fd": DemoAction("fd", (short,), {}),
        "backward": DemoAction("backward", (short,), {}),
        "bk": DemoAction("bk", (short / 2,), {}),
        "back": DemoAction("back", (short / 2,), {}),
        "right": DemoAction("right", (angle,), {}),
        "rt": DemoAction("rt", (angle / 2,), {}),
        "left": DemoAction("left", (angle,), {}),
        "lt": DemoAction("lt", (angle / 2,), {}),
        "goto": DemoAction("goto", pos, {}),
        "setpos": DemoAction("setpos", second_pos, {}),
        "setposition": DemoAction("setposition", (0.0, 0.0), {}),
        "teleport": DemoAction("teleport", tele_pos, {}, note="Requires Python 3.12+"),
        "setx": DemoAction("setx", (40.0,), {}),
        "sety": DemoAction("sety", (-30.0,), {}),
        "setheading": DemoAction("setheading", (90.0,), {}),
        "seth": DemoAction("seth", (180.0,), {}),
        "home": DemoAction("home"),
        "circle": DemoAction("circle", (radius,), {}),
        "dot": DemoAction("dot", (dot_size,), {"color": "blue"}),
        "stamp": DemoAction("stamp", expect_result=True),
        "clearstamp": DemoAction("clearstamp", (0,), {}),
        "clearstamps": DemoAction("clearstamps", (), {}),
        "undo": DemoAction("undo"),
        "speed": DemoAction("speed", (5,), {}, expect_result=True),
        "position": DemoAction("position", expect_result=True),
        "pos": DemoAction("pos", expect_result=True),
        "towards": DemoAction("towards", second_pos, {}, expect_result=True),
        "xcor": DemoAction("xcor", expect_result=True),
        "ycor": DemoAction("ycor", expect_result=True),
        "heading": DemoAction("heading", expect_result=True),
        "distance": DemoAction("distance", pos, {}, expect_result=True),
        "degrees": DemoAction("degrees", (360.0,), {}),
        "radians": DemoAction("radians"),
        "pendown": DemoAction("pendown"),
        "pd": DemoAction("pd"),
        "down": DemoAction("down"),
        "penup": DemoAction("penup"),
        "pu": DemoAction("pu"),
        "up": DemoAction("up"),
        "pensize": DemoAction("pensize", (3,), {}, expect_result=True),
        "width": DemoAction("width", (2,), {}, expect_result=True),
        "pen": DemoAction("pen", expect_result=True),
        "isdown": DemoAction("isdown", expect_result=True),
        "color": DemoAction("color", ("green", "yellow"), {}, expect_result=True),
        "pencolor": DemoAction("pencolor", ("purple",), {}, expect_result=True),
        "fillcolor": DemoAction("fillcolor", ("orange",), {}, expect_result=True),
        "filling": DemoAction("filling", expect_result=True),
        "begin_fill": DemoAction("begin_fill"),
        "end_fill": DemoAction("end_fill"),
        "reset": DemoAction("reset"),
        "clear": DemoAction("clear"),
        "write": DemoAction("write", (text,), {"font": font}),
        "showturtle": DemoAction("showturtle"),
        "st": DemoAction("st"),
        "hideturtle": DemoAction("hideturtle"),
        "ht": DemoAction("ht"),
        "isvisible": DemoAction("isvisible", expect_result=True),
        "shape": DemoAction("shape", ("turtle",), {}, expect_result=True),
        "resizemode": DemoAction("resizemode", ("user",), {}, expect_result=True),
        "shapesize": DemoAction("shapesize", (1.5, 1.0, 3), {}, expect_result=True),
        "turtlesize": DemoAction("turtlesize", (2.0, 1.0, 1), {}, expect_result=True),
        "shearfactor": DemoAction("shearfactor", (0.5,), {}, expect_result=True),
        "tiltangle": DemoAction("tiltangle", (15.0,), {}, expect_result=True),
        "tilt": DemoAction("tilt", (10.0,), {}),
        "shapetransform": DemoAction("shapetransform", expect_result=True),
        "get_shapepoly": DemoAction("get_shapepoly", expect_result=True),
        "onclick": DemoAction("onclick"),
        "onrelease": DemoAction("onrelease"),
        "ondrag": DemoAction("ondrag"),
        "begin_poly": DemoAction("begin_poly"),
        "end_poly": DemoAction("end_poly"),
        "get_poly": DemoAction("get_poly", expect_result=True),
        "clone": DemoAction("clone", expect_result=True),
        "getturtle": DemoAction("getturtle", expect_result=True),
        "getpen": DemoAction("getpen", expect_result=True),
        "getscreen": DemoAction("getscreen", expect_result=True),
        "setundobuffer": DemoAction("setundobuffer", (50,), {}),
        "undobufferentries": DemoAction("undobufferentries", expect_result=True),
    }

    return demo


_DEMO_ARGUMENTS = _demo_arguments(safe_demo_defaults())


def get_demo_action(name: str) -> DemoAction:
    """Return the reusable demo action for ``name``."""

    return _DEMO_ARGUMENTS[name]


def iter_demo_actions() -> Iterator[DemoAction]:
    """Yield demo actions in the order defined by :data:`ACTIONS_INDEX`."""

    for category in ACTIONS_INDEX.values():
        for name, _ in category:
            yield _DEMO_ARGUMENTS[name]


class TurtleActions:
    """Wrapper around :class:`turtle.Turtle` with extra safety and logging."""

    def __init__(
        self,
        *,
        turtle_obj: Optional[turtle.Turtle] = None,
        dry_run: Optional[bool] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.logger = logger or logging.getLogger(LOGGER_NAME)
        env_dry, reason = detect_dry_run()
        if dry_run is None:
            dry_run = env_dry
        if dry_run and not env_dry:
            self.logger.info("DRY-RUN mode forced by caller")
        if env_dry and not dry_run:
            self.logger.warning("Environment suggests DRY-RUN (%s) but caller requested GUI", reason)
        self.dry_run = dry_run
        self.dry_run_reason = reason if dry_run else None
        if self.dry_run:
            self.logger.info("Using dry-run turtle backend (%s)", reason or "requested")
            self._turtle: Any = _DryRunTurtle(self.logger)
        else:
            if turtle_obj is None:
                turtle_obj = turtle.Turtle()
            self._turtle = turtle_obj
        self.call_history: List[Tuple[str, Tuple[Any, ...], Dict[str, Any]]] = []
        self.logger.debug("TurtleActions initialised (dry_run=%s)", self.dry_run)

    # --- helpers -----------------------------------------------------
    def _log_call(self, name: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> None:
        self.call_history.append((name, args, kwargs))
        self.logger.debug("Calling %s args=%s kwargs=%s", name, args, kwargs)

    def _invoke(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "teleport" and not TELEPORT_AVAILABLE:
            message = "teleport requires Python 3.12 or newer"
            self.logger.warning(message)
            raise RuntimeError(message)
        self._log_call(name, args, kwargs)
        target = getattr(self._turtle, name)
        result = target(*args, **kwargs)
        self.logger.debug("%s returned %r", name, result)
        return result

    def safe_reset(self) -> None:
        """Reset the turtle safely regardless of backend."""

        self.logger.info("Performing safe reset")
        try:
            self.reset()
        except Exception as exc:  # pragma: no cover - best effort safety.
            self.logger.exception("Reset failed: %s", exc)
            if not self.dry_run:
                raise

    # --- dynamic action methods --------------------------------------


def _generate_action_method(name: str) -> Callable[..., Any]:
    def method(self: TurtleActions, *args: Any, **kwargs: Any) -> Any:
        return self._invoke(name, *args, **kwargs)

    method.__name__ = name
    method.__qualname__ = f"TurtleActions.{name}"
    method.__doc__ = _summary_from_doc(name)
    return method


for _name in _ALL_ACTION_NAMES:
    setattr(TurtleActions, _name, _generate_action_method(_name))


__all__ = [
    "ACTIONS_INDEX",
    "DemoAction",
    "TurtleActions",
    "configure_logging",
    "detect_dry_run",
    "get_demo_action",
    "iter_demo_actions",
    "safe_demo_defaults",
]
