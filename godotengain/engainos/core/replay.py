import copy
from typing import Dict, List

from combat3d_mr import step_combat

class ReplayError(RuntimeError):
    pass


from typing import Iterable, Any, List

def replay_from_events(initial_snapshot, events: List[Any], kernel=None):
    """
    Replay by applying events to the kernel.

    - Supports kernels that expect either:
        A) a single event per call, or
        B) a batch/list of events per call (like step_combat)
    - Supports both dict events and dataclass events for error labeling.
    """
    if kernel is None:
        # If you hardcode kernel elsewhere, keep it. Otherwise pass it in.
        from combat3d_mr import step_combat as kernel

    snapshot = initial_snapshot

    for i, event in enumerate(events):
        try:
            # step_combat expects a LIST/ITERABLE of DamageEvent
            out = kernel(snapshot, [event])

            # Kernel returns CombatOutput(new_snapshot=..., alerts=...)
            snapshot = getattr(out, "new_snapshot", out)

        except Exception as e:
            # Robust event labeling for dict or dataclass
            if isinstance(event, dict):
                eid = event.get("@id", "unknown")
            else:
                eid = getattr(event, "@id", None) or getattr(event, "event_id", None) or repr(event)

            raise RuntimeError(
                f"Replay failed at event #{i} ({eid}): {e}"
            ) from e

    return snapshot
