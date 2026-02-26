# EngAIn System Manifest

## Core Architecture Truths
*Established: 2026-02-25*

### 1. The Unified Dispatcher
- **Single Entry Point**: All commands (HTTP POST, Text, Internal) MUST pass through `CommandDispatcher.dispatch()`.
- **Normalization**: The dispatcher resolves collisions between JSON keys (`command` vs `action` vs `text`) and prioritizes specific intent over generic labels.
- **Legacy Compatibility**: URL paths (e.g., `/scene/load`) are automatically mapped to dispatcher actions to support older client versions while using the new centralized logic.

### 2. State Management (SSOT)
- **Definitive State**: `EngAInRuntime.snapshot` is the **Single Source of Truth**.
- **Scene Storage**: 
    - `snapshot["scene"]`: Normalized view optimized for the `look/examine` pipeline.
    - `snapshot["scene_raw"]`: Immutable copy of the original ZONJ document.
- **Entity Dict**: `snapshot["entities"]` is a dictionary keyed by ID, ensuring O(1) lookups during simulation ticks.

### 3. Communication Protocol
- **Port**: `8080` (Default).
- **Synchronous Queries**: Text commands (`look`, `status`, `segments`) are processed **synchronously**. The HTTP response contains the result immediately—no polling required.
- **Asynchronous Actions**: Simulation mutations (`spawn_entity`, `update_entity`, `interact`) are **queued** for the next simulation tick and return an `ack`.
- **Safe Serialization**: All responses use `SafeJSONEncoder`. It gracefully handles `sets`, `tuples`, and custom objects by converting to lists or strings, preventing "Empty Reply" (Curl 52) errors.

### 4. Component Integration
- **MR Kernels**: Logic is partitioned into `spatial3d_mr`, `perception_mr`, and `behavior3d_mr`.
- **Adapters**: State-to-Kernel mapping is handled by specific adapters (Combat, Inventory, Dialogue).

## System Victories
- [x] **Unification**: Unified `/scene/load`, `/command`, `/inventory/*`, and `/combat/*` into a single dispatch pipeline.
- [x] **Responsiveness**: Eliminated the 250ms wait-loop for text commands; queries now return instant results.
- [x] **Stability**: Implemented `SafeJSONEncoder` to stop silent server crashes.
- [x] **Transparency**: Added verbose server-side logging for every incoming request and internal dispatch decision.
