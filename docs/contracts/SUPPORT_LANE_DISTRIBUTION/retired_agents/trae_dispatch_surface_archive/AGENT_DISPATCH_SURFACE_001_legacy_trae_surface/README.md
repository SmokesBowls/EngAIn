# TRAE_DISPATCH_SURFACE_001

## Purpose

This folder is the manual dispatch surface for Trae repair tasks.

It exists so Trae receives declared work instead of guessing work.

Trae does not choose the repo path.
Trae does not choose the lane.
Trae does not choose the files.
Trae does not choose the gate.
Trae does not decide acceptance.

The dispatch packet declares all of that before Trae begins.

## Authority

TIER_AUTHORITY: EngAInOS TIER1
LANE: trae_2ndlane_repair_execution
SURFACE_ID: TRAE_DISPATCH_SURFACE_001
INTERACTION_MODEL: manual_only

This dispatch surface is contract-owned.

It lives under:

docs/contracts/SUPPORT_LANE_DISTRIBUTION/trae_2ndlane_repair_execution/TRAE_DISPATCH_SURFACE_001/

It does not live inside Trae's code folder.

Reason:

The mailbox is something Trae is handed.
The mailbox is not something Trae owns.

## Manual-Only Interaction Model

No daemon.
No watcher.
No automatic polling.
No background loop.
No Trae self-selecting tasks.

Human writes one task packet into incoming/.
Human manually invokes Trae against that packet.
Trae records active work in working/.
Trae writes result packet to completed/ or failed/.
Human inspects result before any merge.

## Folder Roles

incoming/
  Human-written task packets waiting for manual dispatch.

working/
  Active task packet copy and live work notes while Trae is operating.

completed/
  Result packets for tasks Trae claims completed.

failed/
  Result packets for tasks Trae could not complete or that returned FALSE.

logs/
  Gate output, command output, trajectory notes, patch summaries, and rollback notes.

## Required Files

TASK_TEMPLATE.md
  Template for a human-written task packet.

RESULT_TEMPLATE.md
  Template for Trae's result packet.

## Dispatch Law

A task packet is valid only when it declares:

- TASK_ID
- repo path
- TIER authority
- lane
- files in scope
- files forbidden
- allowed commands
- forbidden commands
- reproduce command
- gate command before patch
- gate command after patch
- done definition
- rollback snapshot requirement
- human verification requirement

If any of those are missing, Trae must stop.

## Trae Operating Law

Trae must follow this loop:

1. read task packet
2. verify repo path exists
3. verify lane is declared
4. verify files in scope are declared
5. verify rollback snapshot exists or create it only if task packet explicitly allows that
6. view files
7. grep wound
8. reproduce failure
9. run pre-patch gate
10. patch minimal scope
11. run post-patch gate
12. write result packet
13. stop

Trae may not patch before reproduction.

Trae may not call task done without gate evidence.

Trae may not expand scope without a new task packet.

Trae may not treat its own TRUE as final acceptance.

## Acceptance Law

Trae's result may be:

ACCEPTED_CANDIDATE
REJECTED
BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT

ACCEPTED_CANDIDATE means Trae believes the patch passed its declared gates.

It does not mean merged.
It does not mean final.
It does not mean human verification passed.

Human verification is required before merge.

## Rollback Law

If Trae gate returns FALSE, rollback to the pre-Trae snapshot.

If Trae gate returns TRUE but human verification finds breakage outside the gate, rollback to the pre-Trae snapshot.

No debate.
No patch archaeology.
No "almost done."

## Hard Stop Conditions

Trae must stop if:

- repo path is missing
- repo path does not exist
- TIER authority is missing
- lane is missing
- files in scope are missing
- gate command is missing
- task asks Trae to decide authority
- task asks Trae to mutate canon, AP, runtime law, visual authority, spatial authority, affect authority, or lore authority
- task asks Trae to operate outside declared target path
- task asks Trae to patch without reproduction
- task asks Trae to run as daemon or watcher
- task packet contradicts this README

## Final Rule

This surface dispatches repair work.

It does not automate Trae.
It does not authorize Trae.
It does not make Trae autonomous.

It gives Trae one bounded task, one declared path, one declared lane, one declared gate, and one place to report proof.
