from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass


@dataclass(frozen=True)
class BoardStatus:
    lane_name: str
    status: str  # "TRUE", "FALSE", "NOT_BUILT"
    message: str


def _module_exists(module_path: str) -> bool:
    try:
        return importlib.util.find_spec(module_path) is not None
    except ModuleNotFoundError:
        return False


def _try_import_and_run(module_path: str, lane_name: str) -> BoardStatus:
    """
    Attempt to import and run a lane's contract supervisor board.

    NOT_BUILT means the board module itself is not present.

    FALSE means the board exists but either:
    - import crashed,
    - run() is missing,
    - run() returned False,
    - run() crashed.

    TRUE means the board exists and run() returned True.
    """

    if not _module_exists(module_path):
        return BoardStatus(
            lane_name=lane_name,
            status="NOT_BUILT",
            message=f"Board module not found: {module_path}",
        )

    try:
        module = importlib.import_module(module_path)
    except Exception as exc:
        return BoardStatus(
            lane_name=lane_name,
            status="FALSE",
            message=(
                f"Board module exists but import failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        )

    run_function = getattr(module, "run", None)

    if run_function is None:
        return BoardStatus(
            lane_name=lane_name,
            status="FALSE",
            message="Board module exists but has no run() function",
        )

    if not callable(run_function):
        return BoardStatus(
            lane_name=lane_name,
            status="FALSE",
            message="Board module run attribute exists but is not callable",
        )

    try:
        result = run_function()
    except Exception as exc:
        return BoardStatus(
            lane_name=lane_name,
            status="FALSE",
            message=f"Board run() crashed: {type(exc).__name__}: {exc}",
        )

    if result is True:
        return BoardStatus(
            lane_name=lane_name,
            status="TRUE",
            message="Board ran and returned True",
        )

    return BoardStatus(
        lane_name=lane_name,
        status="FALSE",
        message=f"Board ran but returned non-True result: {result!r}",
    )


def run_master_board() -> bool:
    """
    Call all known contract supervisor boards.

    This is a troubleshooting board only.
    It does not grant runtime authority.
    It does not start workers.
    It does not repair missing lanes.
    """

    print("ENGAIN MASTER BOARD")
    print("")

    required_boards = [
        ("engainos.engainos_control_center", "EngAInOS"),
        ("godotsim.godotsim_control_center", "GodotSim"),
        ("ENGIONALITY.engionality_control_center", "Engionality"),
        ("mrlore.mrlore_control_center", "MrLore"),
        ("trixel.trixel_parser_control_center", "Trixel"),
    ]

    statuses: list[BoardStatus] = []

    for module_path, lane_name in required_boards:
        status = _try_import_and_run(module_path, lane_name)
        statuses.append(status)

    print("")
    print("MASTER BOARD SUMMARY")
    print("")

    for status in statuses:
        dots = "." * max(1, 20 - len(status.lane_name))
        print(f"{status.lane_name} {dots} {status.status} - {status.message}")

    all_true = all(status.status == "TRUE" for status in statuses)
    any_not_built = any(status.status == "NOT_BUILT" for status in statuses)
    any_false = any(status.status == "FALSE" for status in statuses)

    print("")

    if all_true:
        print("WHOLE_BOARD_READY ... TRUE")
    elif any_false:
        print("WHOLE_BOARD_READY ... FALSE (failed boards)")
    elif any_not_built:
        print("WHOLE_BOARD_READY ... FALSE (missing boards)")
    else:
        print("WHOLE_BOARD_READY ... FALSE (unknown board state)")

    print("")
    print("MASTER_BOARD_GRANTS_RUNTIME_AUTHORITY ... FALSE")
    print("MASTER_BOARD_STARTS_WORKERS ............ FALSE")
    print("MASTER_BOARD_TROUBLESHOOTING_ONLY ...... TRUE")
    print("")

    return all_true


if __name__ == "__main__":
    raise SystemExit(0 if run_master_board() else 1)