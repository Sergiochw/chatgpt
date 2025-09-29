"""Generate ``turtle_actions_notebook.ipynb`` without third-party helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

NOTEBOOK_PATH = Path("turtle_actions_notebook.ipynb")


def code_cell(source: str) -> Dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.strip().splitlines()],
    }


def markdown_cell(source: str) -> Dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.strip().splitlines()],
    }


def build_notebook() -> Dict[str, Any]:
    cells: List[Dict[str, Any]] = []
    cells.append(
        markdown_cell(
            """
            # Turtle Actions Sampler

            This notebook loads ``turtle_actions.py`` and demonstrates a few
            of the available commands. When the environment cannot open a GUI,
            the module automatically switches to DRY-RUN mode so you can still
            inspect the call log output below each cell.
            """
        )
    )
    cells.append(code_cell("%run turtle_actions.py"))
    cells.append(
        code_cell(
            """
            from turtle_actions import ACTIONS_INDEX, TurtleActions, get_demo_action

            actions = TurtleActions()
            sample = [get_demo_action(name) for name, _ in list(ACTIONS_INDEX["Motion"])[:4]]
            for action in sample:
                method = getattr(actions, action.name)
                result = method(*action.args, **action.kwargs)
                if action.expect_result:
                    print(f"{action.name} -> {result}")
            print("Current position:", actions.position())
            print("Heading:", actions.heading())
            """
        )
    )
    cells.append(
        code_cell(
            """
            from pathlib import Path

            reference_path = Path("turtle_actions_reference.md")
            if reference_path.exists():
                print(reference_path.read_text())
            else:
                print("Reference file not generated yet. Run demo_all_actions.py first.")
            """
        )
    )
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.12",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return notebook


def main() -> None:
    notebook = build_notebook()
    NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    print(f"Notebook written to {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
