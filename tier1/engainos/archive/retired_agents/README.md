# retired_agents

Archived 2026-10-17 during the Tier 1 authority audit. Preserved as historical
evidence; not imported by any live code. Trae and clutterbot are retired as
authority candidates (Trae: `docs/contracts/SUPPORT_LANE_DISTRIBUTION/retired_agents/TRAE_RETIRED_20260704.md`).

| File | Was | Classification |
|---|---|---|
| `agent_gateway.py` | `tier1/engainos/core/agent_gateway.py` | Legacy Agent Gateway — historically implemented, currently unwired, authority model superseded or unresolved. Hard-coded roster trae=1, mrlore=2, clutterbot=3. Still named as "Gate 1: Policy" in `docs/contracts/PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1.md` and `docs/contracts/SHARED_SESSION_CONTINUITY_CONTRACT_v1.md`; never called (`tier1/engainos/bridgeroom/shared_session_bridge.py:41`). |
| `trae_observer.py` | `tier1/engainos/core/trae_observer.py` | Legacy Trae failure-analysis: reads IntentShadow rejections and writes learning feedback through HistoryXeon DREAM mode. No live use; its `from .reality_mode import` was already unresolvable from `core/` before the move. The responsibility (failed attempts / learning evidence / canonical history kept separate) may be worth keeping independent of Trae. |

Related: `TRAE_MRLORE.md` (Trae as an operator under MrLore, with mandatory
review and stop conditions) moved from `tier1/mrlore/schema/` to
`docs/contracts/SUPPORT_LANE_DISTRIBUTION/retired_agents/`. Its responsibility
differs from `trae_observer.py`'s; neither gives Trae a place in the current
authority hierarchy.
