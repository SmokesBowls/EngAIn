# Facade Witness Lane Instructions

## Lane

facade_0_5lane_safe_import_boundary

## Purpose

The Facade Witness guards the boundary between legacy source code and clean authority systems.

It validates safe imports, packet shape, side-effect boundaries, and migration visibility.

## This Lane May

- Validate safe import surfaces.
- Reject side-effect imports.
- Normalize packet shape.
- Confirm runtime entrypoints are intentionally not imported.
- Confirm legacy source is wrapped before migration.
- Report exact import exceptions and packet-shape failures.
- Keep migration honest by saying what is not complete yet.

## This Lane May Not

- Claim runtime truth.
- Claim canon truth.
- Claim simulation truth.
- Claim asset truth.
- Claim renderer truth.
- Start workers.
- Import runtime entrypoints during contract supervision.
- Replace legacy source during a facade check.

## TRUE

A facade boundary promise passed.

## FALSE

An import, packet, or migration boundary is unsafe.

## SKIPPED

An optional migration surface was inspected, but no claim was made.
