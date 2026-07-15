"""Public facade. Do not place implementation here yet. Legacy source remains in renderer adapters.

PlacementPacket JSON IO boundary:
- Python world truth -> deterministic JSON packet list
- JSON packet list -> renderer consumption contract

Pure Python only. No engine imports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


_REQUIRED_PACKET_KEYS = {"tile_id", "grid", "chunk", "world", "render"}


def _normalize_path(path: str | Path) -> Path:
    return path if isinstance(path, Path) else Path(path)


def _packet_to_dict(packet: Any) -> dict[str, Any]:
    if hasattr(packet, "to_dict") and callable(packet.to_dict):
        data = packet.to_dict()
    elif isinstance(packet, dict):
        data = packet
    else:
        raise ValueError("packets must contain PlacementPacket-like objects with to_dict() or dicts")

    if not isinstance(data, dict):
        raise ValueError("packet conversion must yield a dictionary")

    missing = _REQUIRED_PACKET_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"malformed packet missing keys: {sorted(missing)}")

    return data


def write_packets_json(path: str | Path, packets: Iterable[Any]) -> None:
    """Write packets as deterministic JSON list.

    Determinism guarantees:
    - UTF-8
    - indent=2
    - sort_keys=True
    - trailing newline
    """

    out_path = _normalize_path(path)
    normalized = [_packet_to_dict(p) for p in packets]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    out_path.write_text(text, encoding="utf-8")


def read_packets_json(path: str | Path) -> list[dict[str, Any]]:
    """Read JSON packet list and return packet dictionaries."""

    in_path = _normalize_path(path)
    data = json.loads(in_path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("malformed packet list: root JSON must be a list")

    packets: list[dict[str, Any]] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"malformed packet list: item at index {idx} is not an object")
        missing = _REQUIRED_PACKET_KEYS - set(item.keys())
        if missing:
            raise ValueError(f"malformed packet at index {idx}: missing keys {sorted(missing)}")
        packets.append(item)

    return packets
