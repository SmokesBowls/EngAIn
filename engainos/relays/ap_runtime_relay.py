#!/usr/bin/env python3
"""
AP Runtime Relay

Location:
  engainos/relays/ap_runtime_relay.py

Classification:
  ENGAINOS_RELAY_BOUNDARY

Doctrine:
  Adapters convert.
  Gates judge.
  Relays carry approved calls.
  Runtime executes.

Purpose:
  Provide a controlled EngAInOS-side caller boundary for the repaired historical
  AP runtime bridge:

    godotengain/engainos/core/ap_runtime.py

This relay does not:
  - instantiate ZWAPEngine directly
  - mutate StateProvider directly
  - load scene files directly
  - write timeline directly
  - call execute_tick directly
  - manufacture allow_execute=True
  - manufacture enable_timeline_write=True
  - manufacture allow_history_read=True
  - declare runtime truth

It only forwards caller-supplied AP messages after validating that the caller
has an accepted EngAInOS context marker.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
from typing import Any, Dict, Optional


ENGAIN_ROOT = Path(__file__).resolve().parents[2]
AP_RUNTIME_PATH = ENGAIN_ROOT / "godotengain/engainos/core/ap_runtime.py"


class APRuntimeRelay:
    """
    Thin relay for forwarding accepted AP runtime messages.

    The relay is allowed to hold a runtime bridge instance.
    The relay is not allowed to become runtime execution logic.
    """

    def __init__(
        self,
        runtime_integration: Optional[Any] = None,
        require_accepted_context: bool = True,
        accepted_context_key: str = "engainos_accepted",
    ):
        self.require_accepted_context = require_accepted_context
        self.accepted_context_key = accepted_context_key
        self.runtime_integration = runtime_integration or self._load_default_runtime_integration()

    def _load_default_runtime_integration(self) -> Any:
        """
        Load the repaired historical APRuntimeIntegration class from its
        godotengain location.

        This does not initialize it.
        This does not load scene files.
        This does not execute ticks.
        """

        spec = importlib.util.spec_from_file_location(
            "godotengain_repaired_ap_runtime_for_relay",
            AP_RUNTIME_PATH,
        )

        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load AP runtime bridge from {AP_RUNTIME_PATH}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["godotengain_repaired_ap_runtime_for_relay"] = module
        spec.loader.exec_module(module)

        return module.APRuntimeIntegration()

    def initialize_runtime(self, *args: Any, **kwargs: Any) -> Any:
        """
        Forward initialization to the repaired runtime bridge.

        This is permitted because the runtime bridge owns its own initialization.
        The relay does not load scenes directly or instantiate ZWAPEngine directly.
        """
        return self.runtime_integration.initialize(*args, **kwargs)

    def validate_message(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Return None when allowed.
        Return an error dict when rejected.
        """

        if not isinstance(msg, dict):
            return {
                "error": "invalid_ap_relay_message",
                "message": "AP runtime relay expected a dict message.",
            }

        msg_type = msg.get("type")

        if not isinstance(msg_type, str) or not msg_type.startswith("ap_"):
            return {
                "error": "not_ap_runtime_message",
                "type": msg_type,
            }

        if self.require_accepted_context and msg.get(self.accepted_context_key) is not True:
            return {
                "error": "engainos_acceptance_required",
                "message": f"AP runtime relay requires {self.accepted_context_key}: true",
                "type": msg_type,
            }

        return None

    def forward(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forward an accepted AP message to the repaired runtime bridge.

        Important:
          This method forwards caller-supplied intent.
          It does not add allow_execute.
          It does not add enable_timeline_write.
          It does not add allow_history_read.
        """

        rejection = self.validate_message(msg)
        if rejection is not None:
            return rejection

        # Copy without adding authority consent.
        # This prevents the relay from manufacturing allow_execute,
        # enable_timeline_write, or allow_history_read.
        forwarded_msg = dict(msg)

        return self.runtime_integration.handle_message(forwarded_msg)


def build_ap_runtime_relay(
    runtime_integration: Optional[Any] = None,
    require_accepted_context: bool = True,
    accepted_context_key: str = "engainos_accepted",
) -> APRuntimeRelay:
    """
    Factory for AP runtime relay creation.
    """

    return APRuntimeRelay(
        runtime_integration=runtime_integration,
        require_accepted_context=require_accepted_context,
        accepted_context_key=accepted_context_key,
    )
